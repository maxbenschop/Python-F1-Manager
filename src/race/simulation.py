import json
import random
import os
import sys
import tty
import termios
from typing import Dict, List, Any, Tuple

def load_circuit_data(circuit_id: str) -> Dict[str, Any]:
    circuits_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'data', 'circuits.json')
    with open(circuits_file_path, 'r') as f:
        circuits_data = json.load(f)

    for circuit in circuits_data:
        if circuit['id'] == circuit_id:
            return circuit
    raise ValueError(f"Circuit '{circuit_id}' not found in circuits.json")

def load_team_data() -> Dict[str, Dict[str, Any]]:
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
    all_drivers = load_driver_data()
    return list(all_drivers.keys())

def get_key_press():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def calculate_pit_stop_time(team: Dict[str, Any]) -> float:
    # Base pit stop time: 2.0 seconds (perfect stop)
    # Range: ~1.8s (best teams) to ~3.0s (worst teams)
    base_time = 2.0
    pit_speed = team.get('pit_stop_speed', 0.90)

    # Better pit_stop_speed = faster stops
    # 0.97 speed -> ~1.8-2.2s
    # 0.90 speed -> ~2.0-2.5s
    # 0.84 speed -> ~2.3-3.0s
    time_variance = (1.0 - pit_speed) * 5.0  # Scale the variance
    pit_time = base_time + time_variance + random.uniform(-0.2, 0.4)

    return max(1.8, pit_time)  # Minimum 1.8s (world record territory)

def simulate_lap_events(race_state: List[Dict], lap_num: int, total_laps: int, overtaking_difficulty: float) -> List[str]:
    # Simulate events that happen during a lap and return position changes
    events = []

    # Calculate how many position changes should happen this lap
    # Overtakes should be very rare - only happen with significant performance differences
    # Very few overtakes per lap - F1 races typically have 10-30 overtakes total
    # With ~50-70 laps, that's about 0.2-0.6 overtakes per lap on average
    overtake_chance_this_lap = 15  # 15% chance of any overtake happening this lap (reduced from 25%)

    if random.uniform(0, 100) < overtake_chance_this_lap:
        # Only 1 overtake attempt per lap maximum
        if len(race_state) >= 2:
            # Pick a random position to have a battle (not the leader)
            pos_idx = random.randint(1, len(race_state) - 1)

            # Check if driver behind can overtake (based on performance and track)
            driver_behind = race_state[pos_idx]
            driver_ahead = race_state[pos_idx - 1]

            # Calculate overtake probability - needs significant performance difference
            perf_diff = driver_behind['race_performance'] - driver_ahead['race_performance']
            overtake_chance = (perf_diff / 10) * overtaking_difficulty * 100
            overtake_chance = max(0, min(20, overtake_chance))  # Clamp between 0-20% (reduced from 0-30%)

            # Only overtake if there's a BIG performance advantage
            if perf_diff > 5 and random.uniform(0, 100) < overtake_chance:  # Increased from 2 to 5
                # When overtaking, the faster driver gains time on the slower one
                # Adjust cumulative times slightly to reflect the overtake
                time_gain = random.uniform(0.3, 1.0)  # Overtaking driver gains 0.3-1.0s
                if 'cumulative_time' in driver_behind:
                    driver_behind['cumulative_time'] -= time_gain
                if 'cumulative_time' in driver_ahead:
                    driver_ahead['cumulative_time'] += time_gain * 0.5  # Driver ahead loses some time

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

        # Add time penalty for incidents
        time_loss = random.uniform(0.5, 2.0)
        if 'cumulative_time' in victim:
            victim['cumulative_time'] += time_loss

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

                    # Calculate pit stop time based on team performance
                    pit_time = calculate_pit_stop_time(driver_state['team'])

                    # Add pit lane time loss (entry/exit + stop time)
                    # Typical pit lane loss is 20-25 seconds total
                    total_pit_loss = 20.0 + pit_time

                    # Store the time penalty
                    driver_state['pit_time_loss'] = driver_state.get('pit_time_loss', 0) + total_pit_loss

                    events.append(f"  🔧 {driver_state['driver_name']} pits from P{current_pos} ({pit_time:.1f}s stop)")

    # Force pit stops for anyone who hasn't pitted by lap 75% + 1
    if lap_num == pit_window_end + 1:
        for driver_state in race_state:
            if not driver_state.get('has_pitted', False):
                driver_state['has_pitted'] = True
                current_pos = race_state.index(driver_state) + 1

                # Emergency pit - slower stop due to rushing
                pit_time = calculate_pit_stop_time(driver_state['team']) + 0.5
                total_pit_loss = 20.0 + pit_time
                driver_state['pit_time_loss'] = driver_state.get('pit_time_loss', 0) + total_pit_loss

                events.append(f"  🔧 {driver_state['driver_name']} makes MANDATORY pit stop from P{current_pos} ({pit_time:.1f}s)")

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
                'tyre_wear': 0.85,
                'pit_stop_speed': 0.85
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
            'has_pitted': False,  # Track mandatory pit stop
            'pit_time_loss': 0,  # Track time lost in pits
            'cumulative_time': 0,  # Track cumulative lap times
            'total_race_time': 0  # Track total race time including pits
        })

    # LAP-BY-LAP SIMULATION
    print(f"\nPress ENTER for next lap, or 'S' to skip to results\n")
    input("Press ENTER to start the race...")

    skip_to_end = False
    dnf_drivers = []
    safety_car_lap = random.randint(int(total_laps * 0.3), int(total_laps * 0.7)) if random.uniform(0, 100) < 30 else None

    # Average lap time for time calculation (in seconds)
    average_lap_time = 95.0  # ~1:35 per lap

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

        # Calculate cumulative race time for each driver FIRST
        for driver_state in running_drivers:
            if lap_num == 1:
                # Lap 1: Start everyone with base lap time, maintaining grid order
                # Give each driver a lap time based on grid position (leader gets best time)
                lap_time = 95.0 + (driver_state['grid_position'] - 1) * 0.5  # 0.5s gap per grid position (bigger gaps)
                lap_time += random.uniform(-0.02, 0.02)  # Very tiny variation
            else:
                # Normal laps: Performance matters - bigger time differences
                lap_time = 95.0 - (driver_state['race_performance'] - 85) * 0.35  # Increased from 0.15 to 0.35 for bigger gaps
                lap_time += random.uniform(-0.15, 0.15)  # Small random variation

            # Add to cumulative time (pit losses are already tracked separately)
            driver_state['cumulative_time'] += lap_time

        # NOW simulate lap events (this may modify cumulative_time and pit_time_loss)
        lap_events = simulate_lap_events(running_drivers, lap_num, total_laps, overtaking_difficulty)

        # Store previous positions before re-sorting
        previous_positions = {driver['driver_name']: driver['current_position'] for driver in running_drivers}

        # Re-sort drivers by cumulative time + pit time losses
        for driver_state in running_drivers:
            driver_state['total_race_time'] = driver_state['cumulative_time'] + driver_state['pit_time_loss']

        running_drivers.sort(key=lambda x: x['total_race_time'])

        # Update current positions based on sorted order
        for idx, driver_state in enumerate(running_drivers, 1):
            driver_state['current_position'] = idx

        # Detect ALL position changes that weren't already reported
        position_changes = []
        for driver_state in running_drivers:
            old_pos = previous_positions[driver_state['driver_name']]
            new_pos = driver_state['current_position']

            # Report any position change
            if old_pos != new_pos:
                # Check if this change was already reported in lap_events
                driver_name = driver_state['driver_name']
                already_reported = any(driver_name in event for event in lap_events)
                if not already_reported:
                    if new_pos < old_pos:
                        position_changes.append(f"  📈 {driver_name} moves up to P{new_pos}")
                    else:
                        position_changes.append(f"  📉 {driver_name} drops to P{new_pos}")

        # Add position changes to lap events
        lap_events.extend(position_changes)

        # Display current standings with cumulative gaps to leader
        print("\nCurrent Positions:")
        leader_time = running_drivers[0]['total_race_time']

        for idx, driver_state in enumerate(running_drivers, 1):  # Show all drivers
            if idx == 1:
                gap_str = ""
            else:
                gap_to_leader = driver_state['total_race_time'] - leader_time
                if gap_to_leader < 60:
                    gap_str = f" +{gap_to_leader:.1f}s"
                else:
                    minutes = int(gap_to_leader // 60)
                    seconds = gap_to_leader % 60
                    gap_str = f" +{minutes}:{seconds:04.1f}"
            print(f"  P{idx:2d}. {driver_state['driver_name']:<20} [{driver_state['team']['name']:<12}]{gap_str}")

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

    # Phase 3: Use cumulative race times calculated during the race
    # Sort running drivers by final position
    running_drivers = [r for r in race_results if r['status'] == 'Running']
    running_drivers.sort(key=lambda x: x['final_position'])

    # The total_race_time already includes cumulative_time + pit_time_loss from the race simulation
    for result in running_drivers:
        result['total_time'] = result['total_race_time']

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