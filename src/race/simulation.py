import json
import random
import os
import sys
import tty
import termios
from typing import Dict, List, Any, Tuple

# Load circuit data by ID from JSON file
def load_circuit_data(circuit_id: str) -> Dict[str, Any]:
    circuits_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'data', 'circuits.json')
    with open(circuits_file_path, 'r') as f:
        circuits_data = json.load(f)

    for circuit in circuits_data:
        if circuit['id'] == circuit_id:
            return circuit
    raise ValueError(f"Circuit '{circuit_id}' not found in circuits.json")

# Load all teams and create aliases for common team names
def load_team_data() -> Dict[str, Dict[str, Any]]:
    teams_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'data', 'teams.json')
    with open(teams_file_path, 'r') as f:
        teams_data = json.load(f)

    # Convert to dictionary with team name as key
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

# Load F1 drivers and merge with user's F2 drivers from save file
def load_driver_data() -> Dict[str, Dict[str, Any]]:
    # Load F1 drivers
    drivers_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'data', 'drivers.json')
    with open(drivers_file_path, 'r') as f:
        drivers_data = json.load(f)

    # Load user's F2 drivers from save
    save_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'data', 'save', 'save.json')
    if os.path.exists(save_file_path):
        with open(save_file_path, 'r') as f:
            save_data = json.load(f)
            if 'drivers' in save_data:
                drivers_data.extend(save_data['drivers'])

    return {driver['name']: driver for driver in drivers_data}

# Calculate weighted team performance score from car stats
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

# Calculate weighted driver performance score from driver stats
def calculate_driver_overall_score(driver: Dict[str, Any]) -> float:
    return (
        driver.get('pace', 80) * 0.40 +
        driver.get('qualifying', 80) * 0.30 +
        driver.get('racecraft', 80) * 0.20 +
        driver.get('experience', 80) * 0.10
    )

def get_track_overtaking_difficulty(circuit: Dict[str, Any]) -> float:
    # Returns modifier for how easy it is to overtake on this track
    circuit_name = circuit['name'].lower()
    notes = circuit.get('notes', '').lower()

    if 'monaco' in circuit_name or 'singapore' in circuit_name or 'baku' in circuit_name or 'street' in notes:
        return 0.3  # Street circuits: very hard to overtake
    elif 'monza' in circuit_name or 'spa' in circuit_name or 'jeddah' in circuit_name or 'speed' in notes:
        return 1.2  # High-speed circuits: easier to overtake
    else:
        return 0.7  # Normal circuits

def apply_track_specific_modifiers(team_score: float, team: Dict[str, Any], circuit: Dict[str, Any]) -> float:
    # Adjust team performance based on circuit characteristics
    circuit_name = circuit['name'].lower()
    notes = circuit.get('notes', '').lower()

    if 'monza' in circuit_name or 'baku' in circuit_name or 'speed' in notes:
        team_score += (team.get('power', 0.90) - 0.90) * 0.5  # Power tracks
    elif 'monaco' in circuit_name or 'singapore' in circuit_name or 'street' in notes:
        team_score += (team.get('grip', 0.90) - 0.90) * 0.5  # Grip/street tracks
    elif 'suzuka' in circuit_name or 'silverstone' in circuit_name or 'aero' in notes:
        team_score += (team.get('aero', 0.90) - 0.90) * 0.5  # Aero tracks

    return team_score

def simulate_qualifying(driver: Dict[str, Any], team: Dict[str, Any], circuit: Dict[str, Any]) -> float:
    # Calculate qualifying lap time
    base_time = 90.0

    driver_score = calculate_driver_overall_score(driver)
    team_score = calculate_team_overall_score(team)
    team_score = apply_track_specific_modifiers(team_score, team, circuit)

    # Driver and team influence on time
    driver_factor = driver.get('qualifying', 80) * 0.12
    team_factor = team_score * 13.0

    # Add randomness based on experience level
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
    # Check if driver DNFs this lap
    dnf_chance = (1.0 - team.get('reliability', 0.95)) * 100

    # Inexperienced drivers are more likely to crash
    if driver.get('experience', 70) < 70:
        dnf_chance += 3

    if random.uniform(0, 100) < dnf_chance:
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
    # Calculate pit stop time based on team performance (1.8-3.0 seconds)
    base_time = 2.0
    pit_speed = team.get('pit_stop_speed', 0.90)

    time_variance = (1.0 - pit_speed) * 5.0
    pit_time = base_time + time_variance + random.uniform(-0.2, 0.4)

    return max(1.8, pit_time)

def simulate_lap_events(race_state: List[Dict], lap_num: int, total_laps: int, overtaking_difficulty: float) -> List[str]:
    # Simulate overtakes, incidents, and pit stops during the lap
    events = []

    # Overtake simulation (rare, only with big performance difference)
    overtake_chance_this_lap = 15

    if random.uniform(0, 100) < overtake_chance_this_lap:
        if len(race_state) >= 2:
            pos_idx = random.randint(1, len(race_state) - 1)

            driver_behind = race_state[pos_idx]
            driver_ahead = race_state[pos_idx - 1]

            # Calculate overtake probability based on performance difference
            perf_diff = driver_behind['race_performance'] - driver_ahead['race_performance']
            overtake_chance = (perf_diff / 10) * overtaking_difficulty * 100
            overtake_chance = max(0, min(20, overtake_chance))

            # Only overtake if there's a big performance advantage
            if perf_diff > 5 and random.uniform(0, 100) < overtake_chance:
                time_gain = random.uniform(0.3, 1.0)
                if 'cumulative_time' in driver_behind:
                    driver_behind['cumulative_time'] -= time_gain
                if 'cumulative_time' in driver_ahead:
                    driver_ahead['cumulative_time'] += time_gain * 0.5

                events.append(f"  🏎️  {driver_behind['driver_name']} overtakes {driver_ahead['driver_name']} for P{pos_idx}")

    # Random incidents (8% chance per lap)
    if random.uniform(0, 100) < 8:
        victim_idx = random.randint(0, len(race_state) - 1)
        victim = race_state[victim_idx]

        incident_type = random.choice([
            "goes off track and loses time",
            "has a moment at the chicane",
            "locks up into the corner",
            "runs wide and loses a position"
        ])

        time_loss = random.uniform(0.5, 2.0)
        if 'cumulative_time' in victim:
            victim['cumulative_time'] += time_loss

        events.append(f"  ⚠️  {victim['driver_name']} {incident_type}")

    # Mandatory pit stops (drivers must pit between 25% and 75% of race)
    pit_window_start = int(total_laps * 0.25)
    pit_window_end = int(total_laps * 0.75)

    if pit_window_start <= lap_num <= pit_window_end:
        for driver_state in race_state:
            if not driver_state.get('has_pitted', False):
                # Spread pit stops across the window
                laps_in_window = pit_window_end - pit_window_start
                pit_probability = 100 / laps_in_window

                # Increase urgency if near end of window
                laps_remaining = pit_window_end - lap_num
                if laps_remaining < 5:
                    pit_probability *= 2

                if random.uniform(0, 100) < pit_probability:
                    driver_state['has_pitted'] = True
                    current_pos = race_state.index(driver_state) + 1

                    pit_time = calculate_pit_stop_time(driver_state['team'])
                    total_pit_loss = 20.0 + pit_time
                    driver_state['pit_time_loss'] = driver_state.get('pit_time_loss', 0) + total_pit_loss

                    events.append(f"  🔧 {driver_state['driver_name']} pits from P{current_pos} ({pit_time:.1f}s stop)")

    # Force pit stops for any drivers who haven't pitted yet
    if lap_num == pit_window_end + 1:
        for driver_state in race_state:
            if not driver_state.get('has_pitted', False):
                driver_state['has_pitted'] = True
                current_pos = race_state.index(driver_state) + 1

                pit_time = calculate_pit_stop_time(driver_state['team']) + 0.5
                total_pit_loss = 20.0 + pit_time
                driver_state['pit_time_loss'] = driver_state.get('pit_time_loss', 0) + total_pit_loss

                events.append(f"  🔧 {driver_state['driver_name']} makes MANDATORY pit stop from P{current_pos} ({pit_time:.1f}s)")

    return events

def race_simulation(circuit_id: str, driver_names: List[str] = None) -> Dict[str, Dict[str, Any]]:
    # Main race simulation function - runs qualifying and race, returns results

    # Load circuit, drivers, and teams data
    circuit = load_circuit_data(circuit_id)
    all_drivers = load_driver_data()
    all_teams = load_team_data()

    # Use all available drivers if none specified
    if driver_names is None:
        driver_names = get_all_available_drivers()

    print(f"🏁 Simulating race at {circuit['name']}")
    print(f"📍 Location: {circuit['location']}")
    print(f"🏎️  Circuit length: {circuit['length_km']} km")
    print(f"🔄 Number of laps: {circuit['num_laps']}")
    print(f"📝 Notes: {circuit['notes']}")
    print(f"👥 Drivers participating: {len(driver_names)}")
    print("-" * 60)

    # PHASE 1: Run qualifying
    qualifying_results = []

    for driver_name in driver_names:
        driver = all_drivers.get(driver_name)
        if not driver:
            continue

        team = all_teams.get(driver.get('team', 'Unknown'))
        if not team:
            # Create default team data if team not found
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

        quali_time = simulate_qualifying(driver, team, circuit)

        qualifying_results.append({
            'driver_name': driver_name,
            'driver': driver,
            'team': team,
            'quali_time': quali_time
        })

    # Sort by fastest qualifying time
    qualifying_results.sort(key=lambda x: x['quali_time'])

    print("\n📊 QUALIFYING RESULTS:")
    print("-" * 60)
    for i, result in enumerate(qualifying_results, 1):
        print(f"P{i:2d}. {result['driver_name']:<20} [{result['team']['name']:<12}] {result['quali_time']:.3f}s")

    # PHASE 2: Initialize race state
    print("\n🏁 STARTING RACE...")
    print("-" * 60)

    race_results = []
    overtaking_difficulty = get_track_overtaking_difficulty(circuit)
    total_laps = circuit['num_laps']

    # Initialize each driver starting from their grid position
    for grid_pos, quali_result in enumerate(qualifying_results, 1):
        driver = quali_result['driver']
        team = quali_result['team']
        driver_name = quali_result['driver_name']

        # Calculate overall race performance score
        race_performance = (
            driver.get('pace', 80) * 0.28 +
            driver.get('racecraft', 80) * 0.18 +
            driver.get('experience', 80) * 0.12 +
            calculate_team_overall_score(team) * 100 * 0.38 +
            team.get('tyre_wear', 0.90) * 100 * 0.04
        )

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
            'has_pitted': False,
            'pit_time_loss': 0,
            'cumulative_time': 0,
            'total_race_time': 0
        })

    # PHASE 3: Lap-by-lap simulation
    print(f"\nPress ENTER for next lap, or 'S' to skip to results\n")
    input("Press ENTER to start the race...")

    skip_to_end = False
    dnf_drivers = []
    safety_car_lap = random.randint(int(total_laps * 0.3), int(total_laps * 0.7)) if random.uniform(0, 100) < 30 else None

    average_lap_time = 95.0

    for lap_num in range(1, total_laps + 1):
        if skip_to_end:
            break

        print(f"\n{'=' * 60}")
        print(f"LAP {lap_num}/{total_laps}")
        print(f"{'=' * 60}")

        # Get currently running drivers
        running_drivers = [r for r in race_results if r['status'] == 'Running']

        # Safety car deployment
        if lap_num == safety_car_lap:
            print("\n🚨 SAFETY CAR DEPLOYED!")
            overtaking_difficulty *= 0.3

        # Check for DNFs (1.5% chance per lap)
        for driver_state in running_drivers:
            if random.uniform(0, 100) < 1.5:
                is_dnf, dnf_reason = simulate_dnf(driver_state['driver'], driver_state['team'])
                if is_dnf:
                    driver_state['status'] = 'DNF'
                    driver_state['incident'] = dnf_reason
                    dnf_drivers.append(driver_state)
                    print(f"\n❌ {driver_state['driver_name']} retires - {dnf_reason}")

        # Update running drivers list after DNFs
        running_drivers = [r for r in race_results if r['status'] == 'Running']
        running_drivers.sort(key=lambda x: x['current_position'])

        # Calculate lap times for all drivers
        for driver_state in running_drivers:
            if lap_num == 1:
                # Lap 1: maintain grid order with small gaps
                lap_time = 95.0 + (driver_state['grid_position'] - 1) * 0.5
                lap_time += random.uniform(-0.02, 0.02)
            else:
                # Regular laps: performance based
                lap_time = 95.0 - (driver_state['race_performance'] - 85) * 0.35
                lap_time += random.uniform(-0.15, 0.15)

            driver_state['cumulative_time'] += lap_time

        # Simulate lap events (overtakes, incidents, pit stops)
        lap_events = simulate_lap_events(running_drivers, lap_num, total_laps, overtaking_difficulty)

        # Store current positions before sorting
        previous_positions = {driver['driver_name']: driver['current_position'] for driver in running_drivers}

        # Calculate total race time (lap times + pit stops)
        for driver_state in running_drivers:
            driver_state['total_race_time'] = driver_state['cumulative_time'] + driver_state['pit_time_loss']

        # Sort by total race time to update positions
        running_drivers.sort(key=lambda x: x['total_race_time'])

        # Update positions
        for idx, driver_state in enumerate(running_drivers, 1):
            driver_state['current_position'] = idx

        # Detect position changes not already reported
        position_changes = []
        for driver_state in running_drivers:
            old_pos = previous_positions[driver_state['driver_name']]
            new_pos = driver_state['current_position']

            if old_pos != new_pos:
                driver_name = driver_state['driver_name']
                # Check if already reported in lap events
                already_reported = any(driver_name in event for event in lap_events)
                if not already_reported:
                    if new_pos < old_pos:
                        position_changes.append(f"  📈 {driver_name} moves up to P{new_pos}")
                    else:
                        position_changes.append(f"  📉 {driver_name} drops to P{new_pos}")

        lap_events.extend(position_changes)

        # Display current standings
        print("\nCurrent Positions:")
        leader_time = running_drivers[0]['total_race_time']

        for idx, driver_state in enumerate(running_drivers, 1):
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

    # Finalize positions
    if skip_to_end:
        running_drivers = [r for r in race_results if r['status'] == 'Running']
        running_drivers.sort(key=lambda x: (-x['race_performance'], x['grid_position']))
        for position, driver_state in enumerate(running_drivers, 1):
            driver_state['final_position'] = position
    else:
        running_drivers = [r for r in race_results if r['status'] == 'Running']
        running_drivers.sort(key=lambda x: x['current_position'])
        for position, driver_state in enumerate(running_drivers, 1):
            driver_state['final_position'] = position

    # Set final race times
    running_drivers = [r for r in race_results if r['status'] == 'Running']
    running_drivers.sort(key=lambda x: x['final_position'])

    for result in running_drivers:
        result['total_time'] = result['total_race_time']

    all_results = running_drivers + dnf_drivers

    # Display final results
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

    # Display DNFs
    if dnf_drivers:
        print("\n❌ RETIREMENTS:")
        for result in dnf_drivers:
            print(f"    {result['driver_name']:<20} [{result['team']['name']:<12}] - {result['incident']}")

    print("\n" + "=" * 60)

    # Convert results to dictionary format
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
    print("Running race simulation with all available drivers...")
    race_results = race_simulation("saudi_arabia")