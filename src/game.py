import json
import os
import sys
import subprocess
from simple_term_menu import TerminalMenu

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.race.simulation import race_simulation
from src.utils.ui import clear_screen, print_header, print_section
from src.team.upgrades import get_available_upgrades, purchase_upgrade


def start_new_game():
    start_script = os.path.join(os.path.dirname(__file__), 'team', 'start.py')
    subprocess.run([sys.executable, start_script])

def check_save_file():
    save_file_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'data', 'save', 'save.json')

    try:
        # Check if file exists and has content
        if not os.path.exists(save_file_path) or os.path.getsize(save_file_path) == 0:
            return False

        # Load and validate save data structure
        with open(save_file_path, 'r') as f:
            data = json.load(f)

        # Verify required fields exist
        if (isinstance(data, dict) and
            'drivers' in data and
            isinstance(data['drivers'], list) and
            len(data['drivers']) >= 2 and
            all(d.get('team') and d.get('name') for d in data['drivers'][:2])):
            return True

    except (json.JSONDecodeError, IOError):
        return False

    return False

def load_save_data():
    save_file_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'data', 'save', 'save.json')
    with open(save_file_path, 'r') as f:
        data = json.load(f)
        team = data['drivers'][0]['team']
        return team, data['drivers'][0]['name'], data['drivers'][1]['name']

def main_menu(selected_team=None, selected_driver1=None, selected_driver2=None):
    # Load saved game data
    save_team, save_driver1, save_driver2 = load_save_data()

    # Use saved data or fallback to parameters
    selected_team = save_team if save_team else selected_team
    selected_driver1 = save_driver1 if save_driver1 else selected_driver1
    selected_driver2 = save_driver2 if save_driver2 else selected_driver2

    # Validate that game data exists
    if selected_team is None or selected_driver1 is None or selected_driver2 is None:
        print("\n❌ No saved game found. Please start a new game first.")
        print("Run 'python src/team/start.py' to create a new game.")
        return

    clear_screen()
    print_header("🏎️  F1 MANAGER 2026  🏁")
    print_section("MAIN MENU")
    print(f"\nTeam: {selected_team}")
    print(f"Driver 1: {selected_driver1}")
    print(f"Driver 2: {selected_driver2}")
    print("\nWhat would you like to do next?\n")

    options = [
        "1. View Team Details",
        "2. View Driver Details",
        "3. Upgrade Team",
        "4. Start Race",
        "5. View Race History",
        "6. Exit Game"
    ]
    terminal_menu = TerminalMenu(
        options,
        title="Select an option:",
        menu_cursor="➤ ",
        menu_cursor_style=("fg_cyan", "bold"),
        menu_highlight_style=("bg_cyan", "fg_black"),
    )
    option_index = terminal_menu.show()
    selected_option = options[option_index] if option_index is not None else None

    if selected_option == "1. View Team Details":
        view_team_details(selected_team)
    elif selected_option == "2. View Driver Details":
        view_driver_details(selected_driver1, selected_driver2)
    elif selected_option == "3. Upgrade Team":
        upgrade_team(selected_team, selected_driver1, selected_driver2)
    elif selected_option == "4. Start Race":
        start_race(selected_team, selected_driver1, selected_driver2)
    elif selected_option == "5. View Race History":
        view_race_history(selected_team, selected_driver1, selected_driver2)
    elif selected_option == "6. Exit Game":
        exit_game()

def view_team_details(team):
    clear_screen()
    print_header("🏎️  F1 MANAGER 2026  🏁")
    print_section("TEAM DETAILS")
    print(f"\nDetails for Team: {team}")

    # Load save data
    save_file_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'data', 'save', 'save.json')
    with open(save_file_path, 'r') as f:
        save_data = json.load(f)

    # Display team info
    team_stats = save_data.get('teamStats', {})

    print(f"\nTeam Name: {team_stats.get('name', team)}")
    print(f"Engine: {team_stats.get('engine', 'Unknown')}")
    print(f"Chassis: {team_stats.get('chassis', 'Unknown')}")
    print(f"Budget: ${save_data.get('money', 0):,}")

    print("\n" + "=" * 60)
    print("CURRENT STATS")
    print("=" * 60)

    stats_to_display = [
        ('Aero', 'aero'),
        ('Power', 'power'),
        ('Grip', 'grip'),
        ('Reliability', 'reliability'),
        ('Suspension', 'suspension'),
        ('Brakes', 'brakes'),
        ('Tyre Wear', 'tyre_wear'),
        ('Tyre Grip', 'tyre_grip'),
        ('Pit Stop Speed', 'pit_stop_speed'),
        ('Fuel Efficiency', 'fuel_efficiency'),
        ('Weight', 'weight'),
        ('Wear', 'wear')
    ]

    for display_name, stat_key in stats_to_display:
        stat_value = team_stats.get(stat_key, 0)
        percentage = stat_value * 100
        bar_length = int(percentage / 5)
        bar = '█' * bar_length + '░' * (20 - bar_length)
        print(f"{display_name:<20} {bar} {percentage:5.1f}%")

    input("\nPress ENTER to return to the main menu...")
    main_menu(team, None, None)

def upgrade_team(team, driver1, driver2):
    clear_screen()
    print_header("🏎️  F1 MANAGER 2026  🏁")
    print_section("UPGRADE TEAM")

    # Load save data
    save_file_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'data', 'save', 'save.json')
    with open(save_file_path, 'r') as f:
        save_data = json.load(f)

    current_money = save_data.get('money', 0)
    print(f"\nCurrent Budget: ${current_money:,}")

    # Get available upgrades
    available_upgrades = get_available_upgrades(save_data)

    if not available_upgrades:
        print("\nNo upgrades available. All stats are at maximum level!")
        input("\nPress ENTER to return to the main menu...")
        main_menu(team, driver1, driver2)
        return

    print("\n" + "=" * 80)
    print("AVAILABLE UPGRADES")
    print("=" * 80)
    print(f"{'#':<4} {'Upgrade':<25} {'Level':<8} {'Cost':<15} {'Current':<10} {'After':<10}")
    print("-" * 80)

    for idx, upgrade in enumerate(available_upgrades, 1):
        affordable = "✓" if current_money >= upgrade['cost'] else "✗"
        print(f"{idx:<4} {upgrade['name']:<25} L{upgrade['level']:<7} ${upgrade['cost']:<14,} {upgrade['current_value']:<10.3f} {upgrade['new_value']:<10.3f} {affordable}")

    print("-" * 80)

    # Create menu options
    upgrade_options = []
    for idx, upgrade in enumerate(available_upgrades, 1):
        upgrade_options.append(f"{idx}. {upgrade['name']} - Level {upgrade['level']} (${upgrade['cost']:,})")
    upgrade_options.append("Cancel")

    terminal_menu = TerminalMenu(
        upgrade_options,
        title="\nSelect an upgrade to purchase:",
        menu_cursor="➤ ",
        menu_cursor_style=("fg_cyan", "bold"),
        menu_highlight_style=("bg_cyan", "fg_black"),
    )

    choice_index = terminal_menu.show()

    if choice_index is None or choice_index == len(upgrade_options) - 1:
        main_menu(team, driver1, driver2)
        return

    # Purchase the selected upgrade
    selected_upgrade = available_upgrades[choice_index]
    success, message = purchase_upgrade(selected_upgrade['stat'])

    clear_screen()
    print_header("🏎️  F1 MANAGER 2026  🏁")
    print_section("UPGRADE RESULT")

    if success:
        print(f"\n✓ {message}")
        # Reload save data to show updated money
        with open(save_file_path, 'r') as f:
            save_data = json.load(f)
        print(f"\nRemaining Budget: ${save_data.get('money', 0):,}")
    else:
        print(f"\n✗ {message}")

    input("\nPress ENTER to continue...")
    upgrade_team(team, driver1, driver2)


def view_driver_details(driver1, driver2):
    clear_screen()
    print_header("🏎️  F1 MANAGER 2026  🏁")
    print_section("DRIVER DETAILS")

    # Load driver data
    drivers_file_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'data', 'f2_drivers.json')
    with open(drivers_file_path, 'r') as f:
        drivers_data = json.load(f)

    def print_driver_details(driver_name):
        driver_info = next((d for d in drivers_data if d['name'] == driver_name), None)
        if driver_info:
            print(f"\nName: {driver_info['name']}")
            print(f"Experience: {driver_info.get('experience', 0)}")
            print(f"Racecraft: {driver_info.get('racecraft', 0)}")
            print(f"Pace: {driver_info.get('pace', 0)}")
            print(f"Qualifying: {driver_info.get('qualifying', 0)}")
        else:
            print(f"\nDriver {driver_name} details not found.")

    print("\nDRIVER 1:")
    print_driver_details(driver1)
    print("\nDRIVER 2:")
    print_driver_details(driver2)

    input("\nPress ENTER to return to the main menu...")
    main_menu(None, driver1, driver2) 

def start_race(team, driver1, driver2):
    clear_screen()
    print_header("🏎️  F1 MANAGER 2026  🏁")
    print_section("RACE")

    # Load completed races from save data
    save_file_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'data', 'save', 'save.json')
    completed_circuits = set()
    with open(save_file_path, 'r') as f:
        save_data = json.load(f)
        if 'races' in save_data:
            completed_circuits = {race['circuit']['id'] for race in save_data['races']}

    # Load all circuits
    circuits_file_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'data', 'circuits.json')
    with open(circuits_file_path, 'r') as f:
        circuits_data = json.load(f)

    # Filter out completed circuits
    available_circuits = []
    circuit_options = []
    for circuit in circuits_data:
        if circuit['id'] not in completed_circuits:
            available_circuits.append(circuit)
            circuit_options.append(f"{circuit['name']} ({circuit['location']})")
    
    print("\nSelect a circuit for the race:\n")
    terminal_menu = TerminalMenu(
        circuit_options,
        title="Available Circuits:",
        menu_cursor="➤ ",
        menu_cursor_style=("fg_cyan", "bold"),
        menu_highlight_style=("bg_cyan", "fg_black"),
    )
    
    if not circuit_options:
        print("\nNo races available - you have completed all circuits!")
        input("\nPress ENTER to return to the main menu...")
        main_menu(team, driver1, driver2)
        return

    circuit_index = terminal_menu.show()
    if circuit_index is None:
        print("\nRace cancelled.")
        input("\nPress ENTER to return to the main menu...")
        main_menu(team, driver1, driver2)
        return
    
    selected_circuit = available_circuits[circuit_index]
    
    clear_screen()
    print_header("🏎️  F1 MANAGER 2026  🏁")
    print_section(f"RACE AT {selected_circuit['name'].upper()}")

    # Run race simulation
    race_results = race_simulation(
        selected_circuit['id'],
        controlled_drivers=[driver1, driver2],
    )

    if not race_results:
        print("\n❌ Error occurred during race simulation.")
        input("\nPress ENTER to return to the main menu...")
        main_menu(team, driver1, driver2)
        return

    # Load current save data
    save_file_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'data', 'save', 'save.json')
    with open(save_file_path, 'r') as f:
        save_data = json.load(f)

    # Prepare race entry
    race_entry = {
        "circuit": {
            "id": selected_circuit['id'],
            "name": selected_circuit['name'],
            "location": selected_circuit['location']
        },
        "results": []
    }

    # Convert race results to list format
    for driver_name, result in race_results.items():
        race_entry["results"].append({
            "position": result["position"],
            "driver": driver_name,
            "team": result.get("driver_stats", {}).get("team", "Unknown"),
            "total_time": result["total_time"],
            "best_lap": result["lap_time"],
            "performance_score": result["performance_score"],
            "incident": result["incident"],
            "status": result.get("status", "Finished")
        })

    # Sort by position (handle DNFs with None position)
    race_entry["results"].sort(key=lambda x: (x["position"] is None, x["position"] if x["position"] is not None else 999))

    # Calculate money earned by player's drivers
    money_earned = 0
    for result in race_entry["results"]:
        if result["driver"] in [driver1, driver2] and result["position"] is not None:
            position = result["position"]
            # Base money: decreases by position but never below 10,000
            if position == 1:
                base_money = 100000
            elif position <= 10:
                base_money = 100000 - (position - 1) * 10000
            else:
                # Positions 11-20: 10,000 + declining amount
                base_money = max(10000, 10000 + (20 - position) * 1000)

            # Podium bonus
            bonus = 0
            if position == 1:
                bonus = 50000
            elif position == 2:
                bonus = 30000
            elif position == 3:
                bonus = 10000

            total_money = base_money + bonus
            money_earned += total_money

            print(f"\n{result['driver']} earned ${total_money:,} (Base: ${base_money:,}, Bonus: ${bonus:,})")

    # Update money in save data
    if "money" not in save_data:
        save_data["money"] = 0
    save_data["money"] += money_earned

    if money_earned > 0:
        print(f"\n💵 Total money earned this race: ${money_earned:,}")
        print(f"💰 Team balance: ${save_data['money']:,}")

    # Add race to save data
    if "races" not in save_data:
        save_data["races"] = []
    save_data["races"].append(race_entry)

    # Save to file
    with open(save_file_path, 'w') as f:
        json.dump(save_data, f, indent=4)
    
    input("\nPress ENTER to return to the main menu...")
    main_menu(team, driver1, driver2)

def view_race_history(team, driver1, driver2):
    clear_screen()
    print_header("🏎️  F1 MANAGER 2026  🏁")
    print_section("RACE HISTORY")

    # Load race history
    save_file_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'data', 'save', 'save.json')
    with open(save_file_path, 'r') as f:
        save_data = json.load(f)

    if not save_data.get("races"):
        print("\nNo races completed yet.")
        input("\nPress ENTER to return to the main menu...")
        main_menu(team, driver1, driver2)
        return

    # Create menu options
    race_options = [f"{i+1}. {race['circuit']['name']} - {race['circuit']['location']}"
                   for i, race in enumerate(save_data["races"])]
    
    print("\nSelect a race to view details:\n")
    terminal_menu = TerminalMenu(
        race_options,
        title="Completed Races:",
        menu_cursor="➤ ",
        menu_cursor_style=("fg_cyan", "bold"),
        menu_highlight_style=("bg_cyan", "fg_black"),
    )
    
    race_index = terminal_menu.show()
    if race_index is None:
        main_menu(team, driver1, driver2)
        return

    # Get selected race
    selected_race = save_data["races"][race_index]

    clear_screen()
    print_header("🏎️  F1 MANAGER 2026  🏁")
    print_section(f"RACE RESULTS: {selected_race['circuit']['name']}")
    print(f"\nLocation: {selected_race['circuit']['location']}")
    print("\nFinal Classifications:")
    print("─" * 60)

    for result in selected_race["results"]:
        # Skip DNF drivers
        if result["position"] is None:
            continue

        # Highlight user's drivers
        is_team_driver = result["driver"] in [driver1, driver2]
        driver_name = f"➤ {result['driver']}" if is_team_driver else f"  {result['driver']}"

        # Calculate time gap to leader
        if result["position"] == 1:
            time_display = f"{result['total_time']:.3f}s"
        else:
            gap = result["total_time"] - selected_race["results"][0]["total_time"]
            if gap < 60:
                time_display = f"+{gap:.3f}s"
            else:
                minutes = int(gap // 60)
                seconds = gap % 60
                time_display = f"+{minutes}:{seconds:06.3f}"

        print(f"{result['position']:2d}. {driver_name:<25} {result['team']:<15} {time_display}")
        if result.get("incident"):
            print(f"    ⚠️  {result['incident']}")
    
    options = [
        "1. View another race",
        "2. Return to main menu"
    ]
    terminal_menu = TerminalMenu(
        options,
        title="\nOptions:",
        menu_cursor="➤ ",
        menu_cursor_style=("fg_cyan", "bold"),
        menu_highlight_style=("bg_cyan", "fg_black"),
    )
    
    option_index = terminal_menu.show()
    if option_index == 0:
        view_race_history(team, driver1, driver2)
    else:
        main_menu(team, driver1, driver2)

def exit_game():
    clear_screen()
    print_header("🏎️  F1 MANAGER 2026  🏁")
    print("\nThank you for playing F1 Manager 2026! Goodbye!\n")
    exit()


def main():
    """Main entry point for the F1 Manager game"""
    clear_screen()
    print_header("🏎️  F1 MANAGER 2026  🏁")
    print_section("WELCOME")

    # Check if save file exists
    if not check_save_file():
        print("\n❌ No saved game found.")
        print("\nTo start a new game, run:")
        print("  python src/team/start.py")
        print("\nOr use the full game launcher if available.")
        return

    # Load save data and start main menu
    try:
        team, driver1, driver2 = load_save_data()
        main_menu(team, driver1, driver2)
    except Exception as e:
        print(f"\n❌ Error loading save file: {e}")
        print("Please start a new game.")


if __name__ == "__main__":
    main()
