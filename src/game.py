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


def start_new_game():
    start_script = os.path.join(os.path.dirname(__file__), 'team', 'start.py')
    subprocess.run([sys.executable, start_script])

def check_save_file():
    save_file_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'data', 'save', 'save.json')
    
    try:
        # Check if file exists and is not empty
        if not os.path.exists(save_file_path) or os.path.getsize(save_file_path) == 0:
            return False
            
        # Try to load and validate the save data
        with open(save_file_path, 'r') as f:
            data = json.load(f)
            
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
    # Always try to load from save file first
    save_team, save_driver1, save_driver2 = load_save_data()
    
    # Use saved data if available, otherwise use passed parameters
    selected_team = save_team if save_team else selected_team
    selected_driver1 = save_driver1 if save_driver1 else selected_driver1
    selected_driver2 = save_driver2 if save_driver2 else selected_driver2
    
    # If still no data available, prompt to start new game
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
        "3. Start Race",
        "4. View Race History",
        "5. Exit Game"
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
    elif selected_option == "3. Start Race":
        start_race(selected_team, selected_driver1, selected_driver2)
    elif selected_option == "4. View Race History":
        view_race_history(selected_team, selected_driver1, selected_driver2)
    elif selected_option == "5. Exit Game":
        exit_game()

def view_team_details(team):
    clear_screen()
    print_header("🏎️  F1 MANAGER 2026  🏁")
    print_section("TEAM DETAILS")
    print(f"\nDetails for Team: {team}")
    
    # Load team details from teams.json
    teams_file_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'data', 'teams.json')
    with open(teams_file_path, 'r') as f:
        teams_data = json.load(f)
    
    team_info = next((t for t in teams_data if t['name'] == team), None)
    if team_info:
        print(f"\nTeam Name: {team_info['name']}")
        print(f"Base: {team_info.get('base', 'Unknown')}")
        print(f"Team Principal: {team_info.get('principal', 'Unknown')}")
        print(f"Championships: {team_info.get('championships', 0)}")
        print(f"Budget: ${team_info.get('budget', 0):,}")
    else:
        print("\nTeam details not found.")
    
    input("\nPress ENTER to return to the main menu...")
    main_menu(team, None, None)  # Pass None for drivers as they are not changed

def view_driver_details(driver1, driver2):
    clear_screen()
    print_header("🏎️  F1 MANAGER 2026  🏁")
    print_section("DRIVER DETAILS")
    
    # Load driver details from f2_drivers.json
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
    
    # Load save data to check completed races
    save_file_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'data', 'save', 'save.json')
    completed_circuits = set()
    with open(save_file_path, 'r') as f:
        save_data = json.load(f)
        if 'races' in save_data:
            completed_circuits = {race['circuit']['id'] for race in save_data['races']}
    
    # Load available circuits
    circuits_file_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'data', 'circuits.json')
    with open(circuits_file_path, 'r') as f:
        circuits_data = json.load(f)
    
    # Filter out completed circuits and create menu options
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
    
    # Run the race simulation with your drivers and AI drivers
    race_results = race_simulation(selected_circuit['id'])
    
    if not race_results:
        print("\n❌ Error occurred during race simulation.")
        input("\nPress ENTER to return to the main menu...")
        main_menu(team, driver1, driver2)
        return
    
    # Save race results to save.json
    save_file_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'data', 'save', 'save.json')
    with open(save_file_path, 'r') as f:
        save_data = json.load(f)
    
    # Create race result entry
    race_entry = {
        "circuit": {
            "id": selected_circuit['id'],
            "name": selected_circuit['name'],
            "location": selected_circuit['location']
        },
        "results": []
    }
    
    # Convert race results to list of placements
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

    # Sort results by position (DNFs have None position, so handle them separately)
    race_entry["results"].sort(key=lambda x: (x["position"] is None, x["position"] if x["position"] is not None else 999))
    
    # Add race to the races list in save data
    if "races" not in save_data:
        save_data["races"] = []
    save_data["races"].append(race_entry)
    
    # Save updated data back to file
    with open(save_file_path, 'w') as f:
        json.dump(save_data, f, indent=4)
    
    input("\nPress ENTER to return to the main menu...")
    main_menu(team, driver1, driver2)

def view_race_history(team, driver1, driver2):
    clear_screen()
    print_header("🏎️  F1 MANAGER 2026  🏁")
    print_section("RACE HISTORY")
    
    # Load race history from save.json
    save_file_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'data', 'save', 'save.json')
    with open(save_file_path, 'r') as f:
        save_data = json.load(f)
    
    if not save_data.get("races"):
        print("\nNo races completed yet.")
        input("\nPress ENTER to return to the main menu...")
        main_menu(team, driver1, driver2)
        return
    
    # Create menu options for each race
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
    
    # Display selected race details
    selected_race = save_data["races"][race_index]
    
    clear_screen()
    print_header("🏎️  F1 MANAGER 2026  🏁")
    print_section(f"RACE RESULTS: {selected_race['circuit']['name']}")
    print(f"\nLocation: {selected_race['circuit']['location']}")
    print("\nFinal Classifications:")
    print("─" * 60)
    
    for result in selected_race["results"]:
        # Skip drivers with no position (DNF)
        if result["position"] is None:
            continue

        # Highlight the user's drivers
        is_team_driver = result["driver"] in [driver1, driver2]
        driver_name = f"➤ {result['driver']}" if is_team_driver else f"  {result['driver']}"

        # Format the time gap
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

