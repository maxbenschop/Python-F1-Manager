import json
import random
import os
import sys
import tty
import termios
from typing import Dict, List, Any, Tuple

def load_circuit_data(circuit_id: str) -> Dict[str, Any]:
    """Load circuit data from circuits.json"""
    circuits_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'data', 'circuits.json')
    with open(circuits_file_path, 'r') as f:
        circuits_data = json.load(f)

    for circuit in circuits_data:
        if circuit['id'] == circuit_id:
            return circuit
    raise ValueError(f"Circuit '{circuit_id}' not found in circuits.json")

def load_team_data() -> Dict[str, Dict[str, Any]]:
    """Load team data from teams.json"""
    teams_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'data', 'teams.json')
    with open(teams_file_path, 'r') as f:
        teams_data = json.load(f)

    # Convert to dictionary with team name as key, including aliases
    teams_dict = {}
    for team in teams_data:
        teams_dict[team['name']] = team
        # Add common aliases
        if 'Red Bull Racing' in team['name']:
            teams_dict['Red Bull'] = team
        elif 'VCARB' in team['name']:
            teams_dict['Racing Bulls'] = team
            teams_dict['RB'] = team

    return teams_dict

def load_driver_data() -> Dict[str, Dict[str, Any]]:
    """Load driver data from both drivers.json and save.json"""
    # Load F1 drivers
    drivers_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'data', 'drivers.json')
    with open(drivers_file_path, 'r') as f:
        drivers_data = json.load(f)

    # Load save data (your F2 drivers)
    save_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'data', 'save', 'save.json')
    if os.path.exists(save_file_path):
        with open(save_file_path, 'r') as f:
            save_data = json.load(f)
            if 'drivers' in save_data:
                # Add your drivers to the drivers list
                drivers_data.extend(save_data['drivers'])

    # Convert to dictionary with driver name as key
    return {driver['name']: driver for driver in drivers_data}

def calculate_team_overall_score(team: Dict[str, Any]) -> float:
    """Calculate team overall performance score (0-1 scale)"""
    return (
        team.get('aero', 0.90) * 0.20 +
        team.get('power', 0.90) * 0.18 +
        team.get('grip', 0.90) * 0.15 +
        team.get('tyre_grip', 0.90) * 0.12 +
        team.get('suspension', 0.90) * 0.10 +
        team.get('brakes', 0.90) * 0.08 +
        team.get('weight', 0.90) * 0.07 +
        team.get('fuel_efficiency', 0.90) * 0.05 +
        team.get('wear', 0.90) * 0.05
    )

def calculate_driver_overall_score(driver: Dict[str, Any]) -> float:
    """Calculate driver overall performance score (0-100 scale)"""
    return (
        driver.get('pace', 80) * 0.40 +
        driver.get('qualifying', 80) * 0.30 +
        driver.get('racecraft', 80) * 0.20 +
        driver.get('experience', 80) * 0.10
    )

def get_track_overtaking_difficulty(circuit: Dict[str, Any]) -> float:
    """Get track overtaking difficulty modifier"""
    circuit_name = circuit['name'].lower()
    notes = circuit.get('notes', '').lower()

    # Monaco/Street circuits - very hard to overtake
    if 'monaco' in circuit_name or 'singapore' in circuit_name or 'baku' in circuit_name or 'street' in notes:
        return 0.3
    # High-speed circuits - easier to overtake
    elif 'monza' in circuit_name or 'spa' in circuit_name or 'jeddah' in circuit_name or 'speed' in notes:
        return 1.2
    # Normal circuits
    else:
        return 0.7

def apply_track_specific_modifiers(team_score: float, team: Dict[str, Any], circuit: Dict[str, Any]) -> float:
    """Apply track-specific modifiers to team score"""
    circuit_name = circuit['name'].lower()
    notes = circuit.get('notes', '').lower()

    # Power tracks (Monza, Baku, etc.)
    if 'monza' in circuit_name or 'baku' in circuit_name or 'speed' in notes:
        team_score += (team.get('power', 0.90) - 0.90) * 0.5
    # Grip/street tracks (Monaco, Singapore)
    elif 'monaco' in circuit_name or 'singapore' in circuit_name or 'street' in notes:
        team_score += (team.get('grip', 0.90) - 0.90) * 0.5
    # Aero tracks (Suzuka, Silverstone)
    elif 'suzuka' in circuit_name or 'silverstone' in circuit_name or 'aero' in notes:
        team_score += (team.get('aero', 0.90) - 0.90) * 0.5

    return team_score

def simulate_qualifying(driver: Dict[str, Any], team: Dict[str, Any], circuit: Dict[str, Any]) -> float:
    """Simulate qualifying lap time for a driver"""
    base_time = 90.0  # Arbitrary baseline in seconds

    driver_score = calculate_driver_overall_score(driver)
    team_score = calculate_team_overall_score(team)
    team_score = apply_track_specific_modifiers(team_score, team, circuit)

    # Calculate time components - balanced driver and team influence
    driver_factor = driver.get('qualifying', 80) * 0.12
    team_factor = team_score * 13.0

    # Add randomness based on experience - moderate variance for realistic but varied results
    experience = driver.get('experience', 70)
    if experience > 85:
        random_var = random.uniform(-0.15, 0.15)
    elif experience > 65:
        random_var = random.uniform(-0.30, 0.30)
    else:
        random_var = random.uniform(-0.45, 0.45)

    quali_time = base_time - driver_factor - team_factor + random_var
    return quali_time

def simulate_dnf(driver: Dict[str, Any], team: Dict[str, Any]) -> Tuple[bool, str]:
    """Simulate if a driver has a DNF (Did Not Finish)"""
    dnf_chance = (1.0 - team.get('reliability', 0.95)) * 100

    # Rookies break cars more
    if driver.get('experience', 70) < 70:
        dnf_chance += 3

    if random.uniform(0, 100) < dnf_chance:
        # Random DNF reason
        reasons = ["Engine failure", "Gearbox issue", "Crash", "Suspension failure", "Brake failure"]
        return True, random.choice(reasons)

    return False, None

def get_all_available_drivers() -> List[str]:
    """Get list of all available driver names from both drivers.json and save.json"""
    all_drivers = load_driver_data()
    return list(all_drivers.keys())

def get_key_press():
    """Get a single key press from user"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def simulate_lap_events(race_state: List[Dict], lap_num: int, total_laps: int, overtaking_difficulty: float) -> List[str]:
    """Simulate events that happen during a lap and return position changes"""
    events = []

    # Calculate how many position changes should happen this lap
    # More changes early in race, fewer later
    lap_progress = lap_num / total_laps
    max_changes = int(3 * (1 - lap_progress * 0.7))  # 3 changes early, ~1 late

    # Simulate overtakes/position changes
    num_changes = random.randint(0, max_changes)

    for _ in range(num_changes):
        # Pick a random position to have a battle (not the leader)
        if len(race_state) < 2:
            break

        pos_idx = random.randint(1, len(race_state) - 1)

        # Check if driver behind can overtake (based on performance and track)
        driver_behind = race_state[pos_idx]
        driver_ahead = race_state[pos_idx - 1]

        # Calculate overtake probability
        perf_diff = driver_behind['race_performance'] - driver_ahead['race_performance']
        overtake_chance = (perf_diff / 10) * overtaking_difficulty * 100
        overtake_chance = max(5, min(40, overtake_chance))  # Clamp between 5-40%

        if random.uniform(0, 100) < overtake_chance:
            # Swap positions
            race_state[pos_idx], race_state[pos_idx - 1] = race_state[pos_idx - 1], race_state[pos_idx]
            events.append(f"  🏎️  {driver_behind['driver_name']} overtakes {driver_ahead['driver_name']} for P{pos_idx}")

    # Random incidents during the lap
    if random.uniform(0, 100) < 8:  # 8% chance per lap
        victim_idx = random.randint(0, len(race_state) - 1)
        victim = race_state[victim_idx]

        incident_type = random.choice([
            "goes off track and loses time",
            "has a moment at the chicane",
            "locks up into the corner",
            "runs wide and loses a position"
        ])

        if incident_type == "runs wide and loses a position" and victim_idx < len(race_state) - 1:
            # Swap with driver behind
            race_state[victim_idx], race_state[victim_idx + 1] = race_state[victim_idx + 1], race_state[victim_idx]
            events.append(f"  ⚠️  {victim['driver_name']} {incident_type}")
        else:
            events.append(f"  ⚠️  {victim['driver_name']} {incident_type}")

    # MANDATORY PIT STOPS - Check if drivers need to pit
    pit_window_start = int(total_laps * 0.25)  # 25% through race
    pit_window_end = int(total_laps * 0.75)    # 75% through race

    if pit_window_start <= lap_num <= pit_window_end:
        # Check each driver if they need to pit
        for driver_state in race_state:
            if not driver_state.get('has_pitted', False):
                # Determine if this driver should pit this lap
                # Spread pit stops across the window
                laps_in_window = pit_window_end - pit_window_start
                pit_probability = 100 / laps_in_window  # Evenly distribute

                # Add urgency if getting close to end of window
                laps_remaining = pit_window_end - lap_num
                if laps_remaining < 5:
                    pit_probability *= 2  # Double chance if running out of time

                if random.uniform(0, 100) < pit_probability:
                    driver_state['has_pitted'] = True
                    current_pos = race_state.index(driver_state) + 1

                    # Pit stop drops driver back ~3-6 positions
                    positions_lost = random.randint(3, 6)
                    new_pos_idx = min(race_state.index(driver_state) + positions_lost, len(race_state) - 1)

                    # Move driver back in order
                    race_state.remove(driver_state)
                    race_state.insert(new_pos_idx, driver_state)

                    events.append(f"  🔧 {driver_state['driver_name']} pits from P{current_pos}")

    # Force pit stops for anyone who hasn't pitted by lap 75% + 1
    if lap_num == pit_window_end + 1:
        for driver_state in race_state:
            if not driver_state.get('has_pitted', False):
                driver_state['has_pitted'] = True
                current_pos = race_state.index(driver_state) + 1
                events.append(f"  🔧 {driver_state['driver_name']} makes MANDATORY pit stop from P{current_pos}")

                # Emergency pit - bigger drop
                positions_lost = random.randint(5, 8)
                new_pos_idx = min(race_state.index(driver_state) + positions_lost, len(race_state) - 1)
                race_state.remove(driver_state)
                race_state.insert(new_pos_idx, driver_state)

    return events

def race_simulation(circuit_id: str, driver_names: List[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    Simulate an F1 race using the MVP simulation algorithm

    Args:
        circuit_id: ID of the circuit from circuits.json
        driver_names: List of driver names to participate in the race.
                     If None, all available drivers will be used.

    Returns:
        Dictionary with race results for each driver
    """
    # Load data
    circuit = load_circuit_data(circuit_id)
    all_drivers = load_driver_data()
    all_teams = load_team_data()

    # If no specific drivers provided, use all available drivers
    if driver_names is None:
        driver_names = get_all_available_drivers()

    print(f"🏁 Simulating race at {circuit['name']}")
    print(f"📍 Location: {circuit['location']}")
    print(f"🏎️  Circuit length: {circuit['length_km']} km")
    print(f"🔄 Number of laps: {circuit['num_laps']}")
    print(f"📝 Notes: {circuit['notes']}")
    print(f"👥 Drivers participating: {len(driver_names)}")
    print("-" * 60)

    # Phase 1: Calculate overall scores and run qualifying
    qualifying_results = []

    for driver_name in driver_names:
        driver = all_drivers.get(driver_name)
        if not driver:
            continue

        team = all_teams.get(driver.get('team', 'Unknown'))
        if not team:
            # Create default team if not found
            team = {
                'name': driver.get('team', 'Unknown'),
                'reliability': 0.90,
                'aero': 0.85,
                'power': 0.85,
                'grip': 0.85,
                'tyre_grip': 0.85,
                'suspension': 0.85,
                'brakes': 0.85,
                'weight': 0.85,
                'fuel_efficiency': 0.85,
                'wear': 0.85,
                'tyre_wear': 0.85
            }

        # Calculate qualifying time
        quali_time = simulate_qualifying(driver, team, circuit)

        qualifying_results.append({
            'driver_name': driver_name,
            'driver': driver,
            'team': team,
            'quali_time': quali_time
        })

    # Sort by qualifying time
    qualifying_results.sort(key=lambda x: x['quali_time'])

    print("\n📊 QUALIFYING RESULTS:")
    print("-" * 60)
    for i, result in enumerate(qualifying_results, 1):
        print(f"P{i:2d}. {result['driver_name']:<20} [{result['team']['name']:<12}] {result['quali_time']:.3f}s")

    # Phase 2: Initialize race state
    print("\n🏁 STARTING RACE...")
    print("-" * 60)

    race_results = []
    overtaking_difficulty = get_track_overtaking_difficulty(circuit)
    total_laps = circuit['num_laps']

    # Build initial race state (all drivers starting from grid positions)
    for grid_pos, quali_result in enumerate(qualifying_results, 1):
        driver = quali_result['driver']
        team = quali_result['team']
        driver_name = quali_result['driver_name']

        # Calculate race performance score - balanced formula
        race_performance = (
            driver.get('pace', 80) * 0.28 +
            driver.get('racecraft', 80) * 0.18 +
            driver.get('experience', 80) * 0.12 +
            calculate_team_overall_score(team) * 100 * 0.38 +
            team.get('tyre_wear', 0.90) * 100 * 0.04
        )

        # Add moderate race variance
        race_performance += random.uniform(-3, 3)

        race_results.append({
            'driver_name': driver_name,
            'driver': driver,
            'team': team,
            'grid_position': grid_pos,
            'current_position': grid_pos,
            'final_position': None,
            'status': 'Running',
            'incident': None,
            'race_performance': race_performance,
            'total_time': 0,
            'has_pitted': False  # Track mandatory pit stop
        })

    # LAP-BY-LAP SIMULATION
    print(f"\nPress ENTER for next lap, or 'S' to skip to results\n")
    input("Press ENTER to start the race...")

    skip_to_end = False
    dnf_drivers = []
    safety_car_lap = random.randint(int(total_laps * 0.3), int(total_laps * 0.7)) if random.uniform(0, 100) < 30 else None

    for lap_num in range(1, total_laps + 1):
        if skip_to_end:
            break

        print(f"\n{'=' * 60}")
        print(f"LAP {lap_num}/{total_laps}")
        print(f"{'=' * 60}")

        # Get current running drivers
        running_drivers = [r for r in race_results if r['status'] == 'Running']

        # Safety car event
        if lap_num == safety_car_lap:
            print("\n🚨 SAFETY CAR DEPLOYED!")
            overtaking_difficulty *= 0.3

        # Simulate DNFs (rare per lap)
        for driver_state in running_drivers:
            if random.uniform(0, 100) < 1.5:  # 1.5% chance per lap
                is_dnf, dnf_reason = simulate_dnf(driver_state['driver'], driver_state['team'])
                if is_dnf:
                    driver_state['status'] = 'DNF'
                    driver_state['incident'] = dnf_reason
                    dnf_drivers.append(driver_state)
                    print(f"\n❌ {driver_state['driver_name']} retires - {dnf_reason}")

        # Update running drivers after DNFs
        running_drivers = [r for r in race_results if r['status'] == 'Running']

        # Sort by current position for lap events
        running_drivers.sort(key=lambda x: x['current_position'])

        # Simulate lap events
        lap_events = simulate_lap_events(running_drivers, lap_num, total_laps, overtaking_difficulty)

        # Update current positions based on sorted order
        for idx, driver_state in enumerate(running_drivers, 1):
            driver_state['current_position'] = idx

        # Display current standings
        print("\nCurrent Positions:")
        for idx, driver_state in enumerate(running_drivers[:10], 1):  # Show top 10
            print(f"  P{idx:2d}. {driver_state['driver_name']:<20} [{driver_state['team']['name']:<12}]")

        if len(running_drivers) > 10:
            print(f"  ... and {len(running_drivers) - 10} more")

        # Display lap events
        if lap_events:
            print("\nLap Events:")
            for event in lap_events:
                print(event)
        else:
            print("\n  No significant events this lap")

        # Wait for user input
        if lap_num < total_laps:
            print(f"\n[ENTER = Next lap | S = Skip to results]")
            key = get_key_press()
            if key.lower() == 's':
                skip_to_end = True
                print("\n⏩ Skipping to final results...")

    # Final race simulation (if skipped, simulate remaining laps)
    if skip_to_end:
        # Quickly simulate remaining laps
        running_drivers = [r for r in race_results if r['status'] == 'Running']
        running_drivers.sort(key=lambda x: (-x['race_performance'], x['grid_position']))
        for position, driver_state in enumerate(running_drivers, 1):
            driver_state['final_position'] = position
    else:
        # Use final positions from lap-by-lap
        running_drivers = [r for r in race_results if r['status'] == 'Running']
        running_drivers.sort(key=lambda x: x['current_position'])
        for position, driver_state in enumerate(running_drivers, 1):
            driver_state['final_position'] = position

    # Phase 3: Calculate realistic time gaps
    winner_time = 5400.0  # Base race time (~90 minutes)

    # Sort running drivers by final position
    running_drivers = [r for r in race_results if r['status'] == 'Running']
    running_drivers.sort(key=lambda x: x['final_position'])

    for result in running_drivers:
        if result['final_position'] == 1:
            result['total_time'] = winner_time
        else:
            prev_result = running_drivers[result['final_position'] - 2]

            # Calculate gap based on position with more realistic spreads
            if result['final_position'] == 2:
                # P2 usually 0.2s to 20s behind (close battles or clear wins)
                if random.uniform(0, 100) < 30:  # 30% chance of close battle
                    gap = random.uniform(0.2, 5.0)
                else:
                    gap = random.uniform(5.0, 20.0)
            elif result['final_position'] == 3:
                # P3 can be close to P2 or further back
                gap = random.uniform(0.5, 15.0)
            elif result['final_position'] <= 6:
                # Top 6 usually within reasonable gaps
                gap = random.uniform(2.0, 20.0)
            elif result['final_position'] <= 10:
                # Points positions
                gap = random.uniform(3.0, 15.0)
            else:
                # Back markers - bigger gaps
                gap = random.uniform(5.0, 25.0)

            result['total_time'] = prev_result['total_time'] + gap

            # Occasionally create lapped cars (gap > 90s means 1 lap down)
            if result['final_position'] > 12 and random.uniform(0, 100) < 20:
                # Some backmarkers get lapped
                additional_gap = random.uniform(20, 50)
                result['total_time'] += additional_gap

    # Combine all results
    all_results = running_drivers + dnf_drivers

    # Print final results
    print("\n" + "=" * 60)
    print("🏆 FINAL RACE RESULTS")
    print("=" * 60)

    for result in running_drivers:
        position = result['final_position']
        driver_name = result['driver_name']
        team_name = result['team']['name']

        # Calculate gap to leader
        if position == 1:
            gap = "WINNER"
        else:
            gap_seconds = result['total_time'] - running_drivers[0]['total_time']
            if gap_seconds < 60:
                gap = f"+{gap_seconds:.3f}s"
            else:
                minutes = int(gap_seconds // 60)
                seconds = gap_seconds % 60
                gap = f"+{minutes}:{seconds:06.3f}"

        incident_str = f" ⚠️  {result['incident']}" if result['incident'] else ""
        print(f"P{position:2d}. {driver_name:<20} [{team_name:<12}] {gap:<12}{incident_str}")

    # Print DNFs
    if dnf_drivers:
        print("\n❌ RETIREMENTS:")
        for result in dnf_drivers:
            print(f"    {result['driver_name']:<20} [{result['team']['name']:<12}] - {result['incident']}")

    print("\n" + "=" * 60)

    # Convert to dictionary format for compatibility
    results_dict = {}
    for result in all_results:
        results_dict[result['driver_name']] = {
            'position': result['final_position'],
            'total_time': result['total_time'],
            'lap_time': result['total_time'] / circuit['num_laps'] if result['status'] == 'Running' else 0,
            'performance_score': result['race_performance'],
            'incident': result['incident'],
            'driver_stats': result['driver'],
            'status': result['status']
        }

    return results_dict

# Example usage
if __name__ == "__main__":
    # Example race simulation using all available drivers
    print("Running race simulation with all available drivers...")
    race_results = race_simulation("saudi_arabia")
    
    # Alternative: race with specific drivers
    # specific_drivers = ["Max Verstappen", "Lewis Hamilton", "Charles Leclerc", "Lando Norris"]
    # race_results = race_simulation("saudi_arabia", specific_drivers)