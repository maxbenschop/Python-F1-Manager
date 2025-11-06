import json
import random
import os
import sys
import tty
import termios
from typing import Dict, List, Any, Tuple, Optional, Set

from .pit_strategy import apply_pit_strategy, get_strategy_options_for_circuit, create_tyre_state
from .strategy_models import RaceStrategy, StintPlan, TyreState
from .tyre_model import TYRE_MODEL

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


def format_stint_summary(stint: StintPlan, total_laps: int) -> str:
    """
    Produce a user-facing summary string for a strategy stint.
    """
    target_lap = max(1, int(round(stint.target_lap_fraction * total_laps)))
    window_start = max(1, int(round(stint.pit_window_fraction[0] * total_laps)))
    window_end = max(window_start, int(round(stint.pit_window_fraction[1] * total_laps)))
    return (
        f"Lap {target_lap} target | window L{window_start}–L{window_end} | compound: {stint.compound.title()}"
    )


def select_strategy_for_race(
    circuit: Dict[str, Any],
    auto_choice: Optional[str] = None,
    auto_mode: bool = False,
) -> Tuple[Optional[RaceStrategy], Dict[str, float]]:
    """
    Present available circuit presets and capture the user's strategy choice.
    """
    total_laps = circuit.get('num_laps', 0) or 0
    default_strategy, alternate_strategy, profile = get_strategy_options_for_circuit(circuit)

    if not default_strategy and not alternate_strategy:
        return None, {}

    options: Dict[str, Tuple[Optional[RaceStrategy], Dict[str, float]]] = {}

    if default_strategy:
        default_preset = profile.default if profile else None
        options['d'] = (
            default_strategy,
            dict(default_preset.stint_offsets) if default_preset else {},
        )

    if alternate_strategy:
        alternate_preset = profile.alternate if profile else None
        options['a'] = (
            alternate_strategy,
            dict(alternate_preset.stint_offsets) if alternate_preset else {},
        )

    if auto_mode:
        if auto_choice and auto_choice.lower() in options:
            selected_strategy, offsets = options[auto_choice.lower()]
            return selected_strategy, offsets
        selected = options.get('d')
        if selected:
            return selected[0], selected[1]
        return default_strategy, {}

    print("\n🧠 Strategy presets available for this circuit:")

    if default_strategy:
        default_preset = profile.default if profile else None
        preset_note = f" ({default_preset.notes})" if default_preset and default_preset.notes else ""
        print(f"\n[D] {default_strategy.name} — {default_strategy.description}{preset_note}")
        for idx, stint in enumerate(default_strategy.stints, 1):
            print(f"    Stint {idx}: {format_stint_summary(stint, total_laps)}")

    if alternate_strategy:
        alternate_preset = profile.alternate if profile else None
        preset_note = f" ({alternate_preset.notes})" if alternate_preset and alternate_preset.notes else ""
        print(f"\n[A] {alternate_strategy.name} — {alternate_strategy.description}{preset_note}")
        for idx, stint in enumerate(alternate_strategy.stints, 1):
            print(f"    Stint {idx}: {format_stint_summary(stint, total_laps)}")
        options['a'] = (
            alternate_strategy,
            dict(alternate_preset.stint_offsets) if alternate_preset else {},
        )

    print("\n[Enter] Keep default selection (if available)")

    while True:
        choice = input("Choose strategy for this race (D/A or Enter to skip): ").strip().lower()
        if not choice:
            selected = options.get('d')
            if selected:
                return selected[0], selected[1]
            return default_strategy, {}
        if choice in options:
            selected_strategy, offsets = options[choice]
            return selected_strategy, offsets
        print("Invalid selection, please choose again.")


def determine_initial_compound(strategy: Optional[RaceStrategy]) -> str:
    if strategy and strategy.stints:
        return strategy.stints[0].compound.lower()
    return "medium"


def tyre_state_summary(tyre_state: TyreState) -> str:
    wear_percentage = tyre_state.wear * 100
    return f"{tyre_state.compound.title()} ({wear_percentage:.0f}% wear)"


def manage_strategy_menu(
    race_state: List[Dict[str, Any]],
    lap_num: int,
    total_laps: int,
    controlled_driver_names: Optional[Set[str]] = None,
) -> None:
    running = [
        driver for driver in race_state
        if driver['status'] == 'Running'
        and (not controlled_driver_names or driver['driver_name'] in controlled_driver_names)
    ]
    running.sort(key=lambda x: x['current_position'])

    if not running:
        print("\nNo controllable drivers available to manage right now.")
        return

    print(f"\n=== Strategy Management (Lap {lap_num}/{total_laps}) ===")
    for idx, driver in enumerate(running, 1):
        tyre_state = driver.get('tyre_state')
        tyre_info = tyre_state_summary(tyre_state) if isinstance(tyre_state, TyreState) else "No tyre data"
        print(
            f"{idx:2d}. {driver['driver_name']:<20} | Pos P{driver['current_position']:2d} | "
            f"Stops: {driver.get('pit_stops', 0):d} | {tyre_info}"
        )

    selection = input("\nSelect driver number to adjust (Enter to cancel): ").strip()
    if not selection:
        return

    try:
        driver_idx = int(selection)
    except ValueError:
        print("Invalid selection.")
        return

    if driver_idx < 1 or driver_idx > len(running):
        print("Driver number out of range.")
        return

    driver_state = running[driver_idx - 1]
    print(
        "\nOptions:\n"
        " 1) Pit this lap\n"
        " 2) Delay next pit stop\n"
        " 3) Change next compound\n"
        " 4) Cancel\n"
    )

    option = input("Choose action: ").strip()
    if option == '1':
        driver_state['force_pit_on_lap'] = lap_num + 1
        driver_state['defer_pit_laps'] = 0
        print(f"Marked {driver_state['driver_name']} to pit on lap {lap_num + 1}.")
    elif option == '2':
        delay_raw = input("Delay by how many laps? (1-5): ").strip()
        try:
            delay = max(1, min(5, int(delay_raw)))
        except ValueError:
            print("Invalid delay value.")
            return
        driver_state['defer_pit_laps'] = delay
        driver_state['force_pit_on_lap'] = None
        print(f"Delaying {driver_state['driver_name']}'s next stop by {delay} laps.")
    elif option == '3':
        compound = input("Enter next compound (soft/medium/hard): ").strip().lower()
        if not compound:
            print("No compound entered.")
            return
        if TYRE_MODEL.get_compound(compound) is None:
            print("Unknown compound; keeping current plan.")
            return
        driver_state['next_compound_override'] = compound
        print(f"{driver_state['driver_name']} will switch to {compound.title()} on the next stop.")
    else:
        print("Cancelled.")

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

def simulate_lap_events(
    race_state: List[Dict],
    lap_num: int,
    total_laps: int,
    overtaking_difficulty: float,
    strategy_plan: Optional[RaceStrategy],
) -> List[str]:
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

    events.extend(apply_pit_strategy(race_state, lap_num, total_laps, strategy_plan))

    for driver_state in race_state:
        tyre_state = driver_state.get('tyre_state')
        if not isinstance(tyre_state, TyreState):
            continue
        config = driver_state.get('strategy_config', {}) or {}
        warning_threshold = float(config.get('wear_threshold', 0.8)) + 0.05
        if tyre_state.wear >= warning_threshold:
            events.append(
                f"  🔴 {driver_state['driver_name']} struggling on worn {tyre_state.compound.title()} tyres"
            )

    return events

def race_simulation(
    circuit_id: str,
    driver_names: List[str] = None,
    *,
    auto_mode: bool = False,
    strategy_choice: Optional[str] = None,
    seed: Optional[int] = None,
    controlled_drivers: Optional[List[str]] = None,
) -> Dict[str, Dict[str, Any]]:
    # Main race simulation function - runs qualifying and race, returns results

    # Load circuit, drivers, and teams data
    circuit = load_circuit_data(circuit_id)
    all_drivers = load_driver_data()
    all_teams = load_team_data()

    if seed is not None:
        random.seed(seed)

    controlled_driver_set: Set[str] = set(controlled_drivers or [])

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

    selected_strategy, strategy_offsets = select_strategy_for_race(
        circuit,
        auto_choice=strategy_choice,
        auto_mode=auto_mode,
    )
    if selected_strategy and not auto_mode:
        print(f"\n✅ Strategy selected: {selected_strategy.name}")
    elif not selected_strategy and not auto_mode:
        print("\n⚙️  No strategy preset available; using generic pit logic.")

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

        initial_compound = determine_initial_compound(selected_strategy)
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
            'pit_time_loss': 0,
            'cumulative_time': 0,
            'total_race_time': 0,
            'strategy_plan': selected_strategy,
            'strategy_stint_index': 0,
            'tyre_state': create_tyre_state(initial_compound),
            'current_compound': initial_compound,
            'strategy_config': dict(strategy_offsets),
            'pit_stops': 0,
            'force_pit_on_lap': None,
            'defer_pit_laps': 0,
            'next_compound_override': None,
            'last_pit_lap': 0,
            'is_controlled': driver_name in controlled_driver_set,
        })

    # PHASE 3: Lap-by-lap simulation
    print(f"\nPress ENTER for next lap, or 'S' to skip to results\n")
    if not auto_mode:
        input("Press ENTER to start the race...")

    skip_to_end = False
    dnf_drivers = []
    safety_car_lap = random.randint(int(total_laps * 0.3), int(total_laps * 0.7)) if random.uniform(0, 100) < 30 else None

    average_lap_time = 95.0
    stress_profile = circuit.get('tyre_stress_profile', 'medium')

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

            tyre_state = driver_state.get('tyre_state')
            if isinstance(tyre_state, TyreState) and TYRE_MODEL.check_random_puncture(tyre_state):
                driver_state['status'] = 'DNF'
                driver_state['incident'] = 'Tyre failure'
                dnf_drivers.append(driver_state)
                print(f"\n❌ {driver_state['driver_name']} retires - Tyre failure")

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

            tyre_state = driver_state.get('tyre_state')
            if isinstance(tyre_state, TyreState):
                _, tyre_penalty = TYRE_MODEL.update_wear_and_penalty(tyre_state, stress_profile)
                lap_time += tyre_penalty

            driver_state['cumulative_time'] += lap_time

        # Simulate lap events (overtakes, incidents, pit stops)
        lap_events = simulate_lap_events(
            running_drivers,
            lap_num,
            total_laps,
            overtaking_difficulty,
            selected_strategy,
        )

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
            tyre_state = driver_state.get('tyre_state')
            tyre_info = ""
            if isinstance(tyre_state, TyreState):
                tyre_info = f" | {tyre_state_summary(tyre_state)}"
            print(f"  P{idx:2d}. {driver_state['driver_name']:<20} [{driver_state['team']['name']:<12}]{gap_str}{tyre_info}")

        # Display lap events
        if lap_events:
            print("\nLap Events:")
            for event in lap_events:
                print(event)
        else:
            print("\n  No significant events this lap")

        # Wait for user input
        if lap_num < total_laps and not auto_mode:
            print(f"\n[ENTER = Next lap | S = Skip to results | P = Strategy menu]")
            while True:
                key = get_key_press()
                if key.lower() == 's':
                    skip_to_end = True
                    print("\n⏩ Skipping to final results...")
                    break
                if key.lower() == 'p':
                    manage_strategy_menu(race_results, lap_num, total_laps, controlled_driver_set or None)
                    print("\n[ENTER = Next lap | S = Skip to results | P = Strategy menu]")
                    continue
                break

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
        tyre_state = result.get('tyre_state')
        tyre_info = ""
        if isinstance(tyre_state, TyreState):
            tyre_info = f" | {tyre_state_summary(tyre_state)}"
        print(f"P{position:2d}. {driver_name:<20} [{team_name:<12}] {gap:<12}{incident_str}{tyre_info}")

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


def simulate_race_auto(
    circuit_id: str,
    driver_names: List[str] = None,
    *,
    strategy_choice: Optional[str] = None,
    seed: Optional[int] = None,
    controlled_drivers: Optional[List[str]] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Convenience wrapper for automated simulations used in tests or analysis.
    """
    return race_simulation(
        circuit_id,
        driver_names,
        auto_mode=True,
        strategy_choice=strategy_choice,
        seed=seed,
        controlled_drivers=controlled_drivers,
    )


# Example usage
if __name__ == "__main__":
    print("Running race simulation with all available drivers...")
    race_results = race_simulation("saudi_arabia")
