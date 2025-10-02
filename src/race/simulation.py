import json
import random
import os
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

    # Phase 2: Simulate race
    print("\n🏁 STARTING RACE...")
    print("-" * 60)

    race_results = []
    overtaking_difficulty = get_track_overtaking_difficulty(circuit)
    safety_car = random.uniform(0, 100) < 30  # 30% chance of safety car

    if safety_car:
        print("⚠️  SAFETY CAR deployed during the race!")
        overtaking_difficulty *= 0.5

    for grid_pos, quali_result in enumerate(qualifying_results, 1):
        driver = quali_result['driver']
        team = quali_result['team']
        driver_name = quali_result['driver_name']

        # Check for DNF
        is_dnf, dnf_reason = simulate_dnf(driver, team)

        if is_dnf:
            race_results.append({
                'driver_name': driver_name,
                'driver': driver,
                'team': team,
                'grid_position': grid_pos,
                'final_position': None,
                'status': 'DNF',
                'incident': dnf_reason,
                'race_performance': 0,
                'total_time': 999999
            })
            print(f"❌ {driver_name} - DNF ({dnf_reason})")
            continue

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

        # Calculate position change potential - more conservative
        position_change_potential = (race_performance - 85) / 4.0
        position_change_potential *= overtaking_difficulty

        # Lap 1 chaos for rookies (moderate chance)
        if driver.get('experience', 70) < 70 and random.uniform(0, 100) < 12:
            position_change_potential += random.uniform(2, 6)
            incident = "Lap 1 incident"
        else:
            incident = None

        # Driver mistakes
        mistake_chance = (100 - driver.get('experience', 70)) * 0.12
        if random.uniform(0, 100) < mistake_chance:
            position_change_potential += random.uniform(1, 4)
            if not incident:
                incident = "Driver mistake"

        # Random race incidents (strategy, traffic, etc.)
        if random.uniform(0, 100) < 15 and not incident:
            position_change_potential += random.uniform(-2, 2)
            if random.uniform(0, 100) < 40:
                incident = random.choice(["Slow pit stop", "Traffic", "Lock-up", "Track limits"])

        # Add final randomness
        position_change = position_change_potential + random.uniform(-2, 2)

        # Calculate estimated position
        estimated_position = grid_pos + position_change
        estimated_position = max(1, min(20, estimated_position))

        race_results.append({
            'driver_name': driver_name,
            'driver': driver,
            'team': team,
            'grid_position': grid_pos,
            'estimated_position': estimated_position,
            'final_position': None,
            'status': 'Finished',
            'incident': incident,
            'race_performance': race_performance,
            'total_time': 0  # Will be calculated later
        })

    # Sort by estimated position and race performance
    running_drivers = [r for r in race_results if r['status'] == 'Finished']
    dnf_drivers = [r for r in race_results if r['status'] == 'DNF']

    running_drivers.sort(key=lambda x: (x['estimated_position'], -x['race_performance']))

    # Assign final positions
    for position, result in enumerate(running_drivers, 1):
        result['final_position'] = position

    # Phase 3: Calculate realistic time gaps
    winner_time = 5400.0  # Base race time (~90 minutes)

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
    print("\n🏆 FINAL RACE RESULTS:")
    print("-" * 60)

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

    # Convert to dictionary format for compatibility
    results_dict = {}
    for result in all_results:
        results_dict[result['driver_name']] = {
            'position': result['final_position'],
            'total_time': result['total_time'],
            'lap_time': result['total_time'] / circuit['num_laps'] if result['status'] == 'Finished' else 0,
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