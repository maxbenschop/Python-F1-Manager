import json
import os

# Define available upgrades
UPGRADES = {
    "aero": {
        "name": "Aerodynamics",
        "levels": [
            {"cost": 30000, "increase": 0.01},
            {"cost": 40000, "increase": 0.01},
            {"cost": 50000, "increase": 0.01},
            {"cost": 65000, "increase": 0.01},
            {"cost": 80000, "increase": 0.01},
            {"cost": 100000, "increase": 0.01},
            {"cost": 125000, "increase": 0.01},
            {"cost": 155000, "increase": 0.01},
            {"cost": 190000, "increase": 0.008},
            {"cost": 230000, "increase": 0.008},
            {"cost": 275000, "increase": 0.008},
            {"cost": 325000, "increase": 0.008},
            {"cost": 380000, "increase": 0.006},
            {"cost": 440000, "increase": 0.006},
            {"cost": 510000, "increase": 0.006},
            {"cost": 590000, "increase": 0.005},
            {"cost": 680000, "increase": 0.005},
            {"cost": 780000, "increase": 0.004},
            {"cost": 890000, "increase": 0.003},
            {"cost": 1000000, "increase": 0.002}
        ]
    },
    "power": {
        "name": "Power Unit",
        "levels": [
            {"cost": 35000, "increase": 0.01},
            {"cost": 50000, "increase": 0.01},
            {"cost": 65000, "increase": 0.01},
            {"cost": 85000, "increase": 0.01},
            {"cost": 105000, "increase": 0.01},
            {"cost": 130000, "increase": 0.01},
            {"cost": 160000, "increase": 0.01},
            {"cost": 195000, "increase": 0.01},
            {"cost": 235000, "increase": 0.008},
            {"cost": 280000, "increase": 0.008},
            {"cost": 330000, "increase": 0.008},
            {"cost": 390000, "increase": 0.008},
            {"cost": 460000, "increase": 0.006},
            {"cost": 540000, "increase": 0.006},
            {"cost": 630000, "increase": 0.006},
            {"cost": 730000, "increase": 0.005},
            {"cost": 840000, "increase": 0.005},
            {"cost": 960000, "increase": 0.004},
            {"cost": 1090000, "increase": 0.003},
            {"cost": 1230000, "increase": 0.002}
        ]
    },
    "grip": {
        "name": "Grip",
        "levels": [
            {"cost": 25000, "increase": 0.01},
            {"cost": 35000, "increase": 0.01},
            {"cost": 45000, "increase": 0.01},
            {"cost": 60000, "increase": 0.01},
            {"cost": 75000, "increase": 0.01},
            {"cost": 95000, "increase": 0.01},
            {"cost": 115000, "increase": 0.01},
            {"cost": 140000, "increase": 0.01},
            {"cost": 170000, "increase": 0.008},
            {"cost": 205000, "increase": 0.008},
            {"cost": 245000, "increase": 0.008},
            {"cost": 290000, "increase": 0.008},
            {"cost": 340000, "increase": 0.006},
            {"cost": 400000, "increase": 0.006},
            {"cost": 465000, "increase": 0.006},
            {"cost": 540000, "increase": 0.005},
            {"cost": 620000, "increase": 0.005},
            {"cost": 710000, "increase": 0.004},
            {"cost": 810000, "increase": 0.003},
            {"cost": 920000, "increase": 0.002}
        ]
    },
    "reliability": {
        "name": "Reliability",
        "levels": [
            {"cost": 30000, "increase": 0.01},
            {"cost": 45000, "increase": 0.01},
            {"cost": 60000, "increase": 0.01},
            {"cost": 80000, "increase": 0.01},
            {"cost": 100000, "increase": 0.01},
            {"cost": 125000, "increase": 0.01},
            {"cost": 155000, "increase": 0.01},
            {"cost": 190000, "increase": 0.01},
            {"cost": 230000, "increase": 0.008},
            {"cost": 275000, "increase": 0.008},
            {"cost": 325000, "increase": 0.008},
            {"cost": 380000, "increase": 0.008},
            {"cost": 445000, "increase": 0.006},
            {"cost": 515000, "increase": 0.006},
            {"cost": 595000, "increase": 0.006},
            {"cost": 685000, "increase": 0.005},
            {"cost": 785000, "increase": 0.005},
            {"cost": 895000, "increase": 0.004},
            {"cost": 1015000, "increase": 0.003},
            {"cost": 1145000, "increase": 0.002}
        ]
    },
    "suspension": {
        "name": "Suspension",
        "levels": [
            {"cost": 22000, "increase": 0.01},
            {"cost": 30000, "increase": 0.01},
            {"cost": 40000, "increase": 0.01},
            {"cost": 52000, "increase": 0.01},
            {"cost": 65000, "increase": 0.01},
            {"cost": 80000, "increase": 0.01},
            {"cost": 100000, "increase": 0.01},
            {"cost": 120000, "increase": 0.01},
            {"cost": 145000, "increase": 0.008},
            {"cost": 175000, "increase": 0.008},
            {"cost": 210000, "increase": 0.008},
            {"cost": 250000, "increase": 0.008},
            {"cost": 295000, "increase": 0.006},
            {"cost": 345000, "increase": 0.006},
            {"cost": 400000, "increase": 0.006},
            {"cost": 465000, "increase": 0.005},
            {"cost": 535000, "increase": 0.005},
            {"cost": 615000, "increase": 0.004},
            {"cost": 705000, "increase": 0.003},
            {"cost": 805000, "increase": 0.002}
        ]
    },
    "brakes": {
        "name": "Brakes",
        "levels": [
            {"cost": 22000, "increase": 0.01},
            {"cost": 30000, "increase": 0.01},
            {"cost": 40000, "increase": 0.01},
            {"cost": 52000, "increase": 0.01},
            {"cost": 65000, "increase": 0.01},
            {"cost": 80000, "increase": 0.01},
            {"cost": 100000, "increase": 0.01},
            {"cost": 120000, "increase": 0.01},
            {"cost": 145000, "increase": 0.008},
            {"cost": 175000, "increase": 0.008},
            {"cost": 210000, "increase": 0.008},
            {"cost": 250000, "increase": 0.008},
            {"cost": 295000, "increase": 0.006},
            {"cost": 345000, "increase": 0.006},
            {"cost": 400000, "increase": 0.006},
            {"cost": 465000, "increase": 0.005},
            {"cost": 535000, "increase": 0.005},
            {"cost": 615000, "increase": 0.004},
            {"cost": 705000, "increase": 0.003},
            {"cost": 805000, "increase": 0.002}
        ]
    },
    "tyre_wear": {
        "name": "Tyre Management",
        "levels": [
            {"cost": 25000, "increase": 0.01},
            {"cost": 35000, "increase": 0.01},
            {"cost": 47000, "increase": 0.01},
            {"cost": 62000, "increase": 0.01},
            {"cost": 78000, "increase": 0.01},
            {"cost": 98000, "increase": 0.01},
            {"cost": 120000, "increase": 0.01},
            {"cost": 145000, "increase": 0.01},
            {"cost": 175000, "increase": 0.008},
            {"cost": 210000, "increase": 0.008},
            {"cost": 250000, "increase": 0.008},
            {"cost": 295000, "increase": 0.008},
            {"cost": 345000, "increase": 0.006},
            {"cost": 400000, "increase": 0.006},
            {"cost": 465000, "increase": 0.006},
            {"cost": 540000, "increase": 0.005},
            {"cost": 620000, "increase": 0.005},
            {"cost": 710000, "increase": 0.004},
            {"cost": 810000, "increase": 0.003},
            {"cost": 920000, "increase": 0.002}
        ]
    },
    "pit_stop_speed": {
        "name": "Pit Crew",
        "levels": [
            {"cost": 18000, "increase": 0.01},
            {"cost": 25000, "increase": 0.01},
            {"cost": 33000, "increase": 0.01},
            {"cost": 43000, "increase": 0.01},
            {"cost": 55000, "increase": 0.01},
            {"cost": 70000, "increase": 0.01},
            {"cost": 85000, "increase": 0.01},
            {"cost": 105000, "increase": 0.01},
            {"cost": 125000, "increase": 0.008},
            {"cost": 150000, "increase": 0.008},
            {"cost": 180000, "increase": 0.008},
            {"cost": 215000, "increase": 0.008},
            {"cost": 255000, "increase": 0.006},
            {"cost": 300000, "increase": 0.006},
            {"cost": 350000, "increase": 0.006},
            {"cost": 410000, "increase": 0.005},
            {"cost": 475000, "increase": 0.005},
            {"cost": 550000, "increase": 0.004},
            {"cost": 635000, "increase": 0.003},
            {"cost": 730000, "increase": 0.002}
        ]
    },
    "fuel_efficiency": {
        "name": "Fuel Efficiency",
        "levels": [
            {"cost": 28000, "increase": 0.01},
            {"cost": 38000, "increase": 0.01},
            {"cost": 50000, "increase": 0.01},
            {"cost": 65000, "increase": 0.01},
            {"cost": 82000, "increase": 0.01},
            {"cost": 102000, "increase": 0.01},
            {"cost": 125000, "increase": 0.01},
            {"cost": 152000, "increase": 0.01},
            {"cost": 185000, "increase": 0.008},
            {"cost": 225000, "increase": 0.008},
            {"cost": 270000, "increase": 0.008},
            {"cost": 320000, "increase": 0.008},
            {"cost": 375000, "increase": 0.006},
            {"cost": 440000, "increase": 0.006},
            {"cost": 510000, "increase": 0.006},
            {"cost": 590000, "increase": 0.005},
            {"cost": 680000, "increase": 0.005},
            {"cost": 780000, "increase": 0.004},
            {"cost": 890000, "increase": 0.003},
            {"cost": 1010000, "increase": 0.002}
        ]
    },
    "weight": {
        "name": "Weight Reduction",
        "levels": [
            {"cost": 32000, "increase": 0.01},
            {"cost": 45000, "increase": 0.01},
            {"cost": 60000, "increase": 0.01},
            {"cost": 78000, "increase": 0.01},
            {"cost": 98000, "increase": 0.01},
            {"cost": 122000, "increase": 0.01},
            {"cost": 150000, "increase": 0.01},
            {"cost": 182000, "increase": 0.01},
            {"cost": 220000, "increase": 0.008},
            {"cost": 265000, "increase": 0.008},
            {"cost": 315000, "increase": 0.008},
            {"cost": 370000, "increase": 0.008},
            {"cost": 435000, "increase": 0.006},
            {"cost": 510000, "increase": 0.006},
            {"cost": 595000, "increase": 0.006},
            {"cost": 690000, "increase": 0.005},
            {"cost": 795000, "increase": 0.005},
            {"cost": 910000, "increase": 0.004},
            {"cost": 1035000, "increase": 0.003},
            {"cost": 1170000, "increase": 0.002}
        ]
    }
}


def get_save_path():
    """Get the path to save.json"""
    return os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'data', 'save', 'save.json')


def load_save_data():
    """Load save data from save.json"""
    save_path = get_save_path()
    with open(save_path, 'r') as f:
        return json.load(f)


def save_to_file(data):
    """Save data to save.json"""
    save_path = get_save_path()
    with open(save_path, 'w') as f:
        json.dump(data, f, indent=4)


def get_upgrade_level(save_data, stat_name):
    """Calculate current upgrade level for a stat"""
    # Get base stat from teams.json
    teams_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'data', 'teams.json')
    with open(teams_file_path, 'r') as f:
        teams_data = json.load(f)

    team_name = save_data.get('selectedTeam')
    base_team = next((t for t in teams_data if t['name'] == team_name), None)

    if not base_team or stat_name not in base_team:
        return 0

    base_value = base_team[stat_name]
    current_value = save_data.get('teamStats', {}).get(stat_name, base_value)

    # Calculate level based on difference
    difference = current_value - base_value

    # Count how many upgrades have been applied
    total_increase = 0
    level = 0

    if stat_name in UPGRADES:
        for upgrade_level in UPGRADES[stat_name]['levels']:
            if total_increase + upgrade_level['increase'] <= difference + 0.001:  # Small epsilon for float comparison
                total_increase += upgrade_level['increase']
                level += 1
            else:
                break

    return level


def get_available_upgrades(save_data):
    """Get list of available upgrades with their costs"""
    available = []

    for stat_key, upgrade_data in UPGRADES.items():
        current_level = get_upgrade_level(save_data, stat_key)

        if current_level < len(upgrade_data['levels']):
            next_upgrade = upgrade_data['levels'][current_level]
            current_stat_value = save_data.get('teamStats', {}).get(stat_key, 0)

            available.append({
                'stat': stat_key,
                'name': upgrade_data['name'],
                'level': current_level + 1,
                'cost': next_upgrade['cost'],
                'increase': next_upgrade['increase'],
                'current_value': current_stat_value,
                'new_value': min(1.0, current_stat_value + next_upgrade['increase'])
            })

    # Sort by cost
    available.sort(key=lambda x: x['cost'])

    return available


def purchase_upgrade(stat_name):
    """Purchase an upgrade for a specific stat"""
    save_data = load_save_data()

    # Check if upgrade exists
    if stat_name not in UPGRADES:
        return False, "Invalid upgrade"

    # Get current level
    current_level = get_upgrade_level(save_data, stat_name)

    # Check if max level reached
    if current_level >= len(UPGRADES[stat_name]['levels']):
        return False, "Maximum upgrade level reached"

    # Get upgrade details
    upgrade = UPGRADES[stat_name]['levels'][current_level]
    cost = upgrade['cost']
    increase = upgrade['increase']

    # Check if player has enough money
    current_money = save_data.get('money', 0)
    if current_money < cost:
        return False, f"Not enough money. Need ${cost:,}, have ${current_money:,}"

    # Apply upgrade
    save_data['money'] -= cost

    if 'teamStats' not in save_data:
        save_data['teamStats'] = {}

    current_value = save_data['teamStats'].get(stat_name, 0.85)
    new_value = min(1.0, current_value + increase)
    save_data['teamStats'][stat_name] = round(new_value, 3)

    # Save to file
    save_to_file(save_data)

    return True, f"Upgraded {UPGRADES[stat_name]['name']} to level {current_level + 1}. New value: {new_value:.3f}"
