import json
import os
import sys
import subprocess
from simple_term_menu import TerminalMenu

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.ui import clear_screen, print_header, print_section, print_success

clear_screen()
print_header("🏎️  F1 MANAGER 2026  🏁")
print("Welcome! Choose your team and drivers to begin your journey.\n")
input("Press ENTER to continue...")

# Load teams from JSON file
teams_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'data', 'teams.json')
with open(teams_file_path, 'r') as f:
    teams_data = json.load(f)

# Load drivers from JSON file
drivers_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'data', 'f2_drivers.json')
with open(drivers_file_path, 'r') as f:
    drivers_data = json.load(f)

# Filter for available teams
available_teams = [team['name'] for team in teams_data if team['available']]
available_drivers = [driver['name'] for driver in drivers_data]

# ============================================================================
# Team Selection
# ============================================================================

clear_screen()
print_header("🏎️  F1 MANAGER 2026  🏁")
print_section("STEP 1: Choose Your Team")
print("\nUse ↑/↓ arrow keys to navigate, ENTER to select:\n")

terminal_menu = TerminalMenu(
    available_teams,
    title="Available Teams:",
    menu_cursor="➤ ",
    menu_cursor_style=("fg_cyan", "bold"),
    menu_highlight_style=("bg_cyan", "fg_black"),
)
team_index = terminal_menu.show()
selected_team = available_teams[team_index] if team_index is not None else None

if selected_team is None:
    print("\n❌ Team selection cancelled.")
    exit()

print_success(f"Team selected: {selected_team}")
input("\nPress ENTER to continue...")

# ============================================================================
# First Driver Selection
# ============================================================================

clear_screen()
print_header("🏎️  F1 MANAGER 2026  🏁")
print_section("STEP 2: Choose Your First Driver")
print(f"\nTeam: {selected_team}")
print("\nUse ↑/↓ arrow keys to navigate, ENTER to select:\n")

terminal_menu = TerminalMenu(
    available_drivers,
    title="Available Drivers:",
    menu_cursor="➤ ",
    menu_cursor_style=("fg_cyan", "bold"),
    menu_highlight_style=("bg_cyan", "fg_black"),
)
driver_index = terminal_menu.show()
selected_driver1 = available_drivers[driver_index] if driver_index is not None else None

if selected_driver1 is None:
    print("\n❌ Driver selection cancelled.")
    exit()

print_success(f"First driver selected: {selected_driver1}")
input("\nPress ENTER to continue...")

# Remove selected driver from list
available_drivers.remove(selected_driver1)

# ============================================================================
# Second Driver Selection
# ============================================================================

clear_screen()
print_header("🏎️  F1 MANAGER 2026  🏁")
print_section("STEP 3: Choose Your Second Driver")
print(f"\nTeam: {selected_team}")
print(f"First Driver: {selected_driver1}")
print("\nUse ↑/↓ arrow keys to navigate, ENTER to select:\n")

terminal_menu = TerminalMenu(
    available_drivers,
    title="Available Drivers:",
    menu_cursor="➤ ",
    menu_cursor_style=("fg_cyan", "bold"),
    menu_highlight_style=("bg_cyan", "fg_black"),
)
driver_index = terminal_menu.show()
selected_driver2 = available_drivers[driver_index] if driver_index is not None else None

if selected_driver2 is None:
    print("\n❌ Driver selection cancelled.")
    exit()

# ============================================================================
# Save Configuration
# ============================================================================

clear_screen()
print_header("🏎️  F1 MANAGER 2026  🏁")
print_section("Configuration Complete!")

# Save selected team and drivers to a new JSON file
save_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'data', 'save', 'save.json')
if not os.path.exists(os.path.dirname(save_file_path)):
    os.makedirs(os.path.dirname(save_file_path))

selected_drivers_data = []
for driver in drivers_data:
    if driver['name'] in [selected_driver1, selected_driver2]:
        # Create a copy of the driver data to avoid modifying the original
        driver_copy = driver.copy()
        driver_copy['team'] = selected_team
        selected_drivers_data.append(driver_copy)

# Get selected team's stats from teams.json
selected_team_data = next((t for t in teams_data if t['name'] == selected_team), None)
if not selected_team_data:
    print(f"\nError: Team {selected_team} not found in teams.json")
    exit()

# Copy team stats (exclude non-stat fields)
team_stats = {
    "name": selected_team_data['name'],
    "engine": selected_team_data['engine'],
    "chassis": selected_team_data['chassis'],
    "reliability": selected_team_data['reliability'],
    "wear": selected_team_data['wear'],
    "grip": selected_team_data['grip'],
    "aero": selected_team_data['aero'],
    "power": selected_team_data['power'],
    "fuel_efficiency": selected_team_data['fuel_efficiency'],
    "pit_stop_speed": selected_team_data['pit_stop_speed'],
    "tyre_wear": selected_team_data['tyre_wear'],
    "tyre_grip": selected_team_data['tyre_grip'],
    "suspension": selected_team_data['suspension'],
    "brakes": selected_team_data['brakes'],
    "weight": selected_team_data['weight']
}

# Create new save data structure
save_data = {
    "selectedTeam": selected_team,
    "teamStats": team_stats,
    "drivers": selected_drivers_data,
    "races": [],
    "money": 0
}

# Ensure the save directory exists
save_dir = os.path.dirname(save_file_path)
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

# Write the save data with proper formatting
with open(save_file_path, 'w') as f:
    json.dump(save_data, f, indent=4)

# ============================================================================
# Display Final Summary
# ============================================================================

print("\n📋 YOUR SELECTIONS:\n")
print(f"  Team:           {selected_team}")
print(f"  First Driver:   {selected_driver1}")
print(f"  Second Driver:  {selected_driver2}")
print("\n" + "─" * 60)
print_success("Configuration saved successfully!")

# Launch the main game
print("\nStarting game...")
from src.game import main_menu
main_menu()