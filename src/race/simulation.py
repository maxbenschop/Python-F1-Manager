import json
import random
import os
from typing import Dict, List, Any

def load_circuit_data(circuit_id: str) -> Dict[str, Any]:
    """Load circuit data from circuits.json"""
    circuits_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'data', 'circuits.json')
    with open(circuits_file_path, 'r') as f:
        circuits_data = json.load(f)
    
    for circuit in circuits_data:
        if circuit['id'] == circuit_id:
            return circuit
    raise ValueError(f"Circuit '{circuit_id}' not found in circuits.json")

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

def calculate_driver_performance(driver_stats: Dict[str, Any], circuit: Dict[str, Any]) -> float:
    """Calculate driver performance based on their stats and circuit characteristics"""
    if not driver_stats:
        # Default stats for unknown drivers
        base_performance = 75.0
    else:
        # Weight different stats based on circuit type
        racecraft_weight = 0.3
        pace_weight = 0.4
        qualifying_weight = 0.2
        experience_weight = 0.1
        
        # Adjust weights based on circuit characteristics
        if circuit.get('notes', '').lower().find('monaco') != -1 or 'tight' in circuit.get('notes', '').lower():
            # Monaco-style circuits favor racecraft and experience
            racecraft_weight = 0.4
            experience_weight = 0.2
            pace_weight = 0.3
        elif 'speed' in circuit.get('notes', '').lower() or circuit.get('length_km', 0) > 6:
            # High-speed circuits favor raw pace
            pace_weight = 0.5
            qualifying_weight = 0.3
        
        base_performance = (
            driver_stats['racecraft'] * racecraft_weight +
            driver_stats['pace'] * pace_weight +
            driver_stats['qualifying'] * qualifying_weight +
            driver_stats['experience'] * experience_weight
        )
    
    # Add some randomness (luck factor)
    luck_factor = random.uniform(0.85, 1.15)  # ±15% variance
    
    # Circuit-specific modifiers
    circuit_modifier = 1.0
    if circuit.get('weather_factor'):
        circuit_modifier *= circuit['weather_factor']
    
    return base_performance * luck_factor * circuit_modifier

def calculate_lap_time(driver_performance: float, circuit: Dict[str, Any]) -> float:
    """Calculate a realistic lap time based on driver performance and circuit"""
    # Base lap time estimation (in seconds)
    # Using a formula: base_time = (length_km * 60) / average_speed_factor
    base_speed_factor = 4.5  # Rough estimate for F1 cars
    base_lap_time = (circuit['length_km'] * 60) / base_speed_factor
    
    # Adjust based on driver performance (better drivers are faster)
    performance_factor = (100 - driver_performance) / 100 * 0.05  # Max 5% difference
    lap_time = base_lap_time * (1 + performance_factor)
    
    return lap_time

def get_all_available_drivers() -> List[str]:
    """Get list of all available driver names from both drivers.json and save.json"""
    all_drivers = load_driver_data()
    return list(all_drivers.keys())

def race_simulation(circuit_id: str, driver_names: List[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    Simulate an F1 race using circuit data and driver stats
    
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
    
    # If no specific drivers provided, use all available drivers
    if driver_names is None:
        driver_names = get_all_available_drivers()
    
    print(f"🏁 Simulating race at {circuit['name']}")
    print(f"📍 Location: {circuit['location']}")
    print(f"🏎️  Circuit length: {circuit['length_km']} km")
    print(f"🔄 Number of laps: {circuit['num_laps']}")
    print(f"📝 Notes: {circuit['notes']}")
    print(f"👥 Drivers participating: {len(driver_names)}")
    print("-" * 50)
    
    results = {}
    
    for driver_name in driver_names:
        driver_stats = all_drivers.get(driver_name)
        
        # Calculate driver performance for this circuit
        performance = calculate_driver_performance(driver_stats, circuit)
        
        # Calculate lap time
        lap_time = calculate_lap_time(performance, circuit)
        
        # Calculate total race time
        total_race_time = lap_time * circuit['num_laps']
        
        # Add some race incidents/randomness
        incident_chance = random.random()
        if incident_chance < 0.05:  # 5% chance of major incident
            total_race_time += random.uniform(20, 60)  # Pit stop penalty
            incident = "Slow pitstop"
        elif incident_chance < 0.1:  # Additional 5% chance of minor incident
            total_race_time += random.uniform(5, 15)  # Minor delay
            incident = "Minor incident"
        else:
            incident = None
        
        results[driver_name] = {
            "total_time": total_race_time,
            "lap_time": lap_time,
            "performance_score": performance,
            "position": None,  # To be filled later
            "incident": incident,
            "driver_stats": driver_stats
        }
    
    # Sort results by total time to determine positions
    sorted_results = sorted(results.items(), key=lambda item: item[1]["total_time"])
    
    print("🏆 RACE RESULTS:")
    print("-" * 50)
    
    for position, (driver_name, data) in enumerate(sorted_results, start=1):
        data["position"] = position
        
        # Calculate time gap to winner
        if position == 1:
            gap = "WINNER"
        else:
            gap_seconds = data["total_time"] - sorted_results[0][1]["total_time"]
            if gap_seconds < 60:
                gap = f"+{gap_seconds:.3f}s"
            else:
                minutes = int(gap_seconds // 60)
                seconds = gap_seconds % 60
                gap = f"+{minutes}:{seconds:06.3f}"
        
        incident_str = f" ({data['incident']})" if data['incident'] else ""
        stats = data['driver_stats']
        team = stats['team'] if stats else "Unknown"
        
        print(f"{position:2d}. {driver_name:<20} [{team:<12}] {gap:<12} (Perf: {data['performance_score']:.1f}){incident_str}")
    
    return results

# Example usage
if __name__ == "__main__":
    # Example race simulation using all available drivers
    print("Running race simulation with all available drivers...")
    race_results = race_simulation("saudi_arabia")
    
    # Alternative: race with specific drivers
    # specific_drivers = ["Max Verstappen", "Lewis Hamilton", "Charles Leclerc", "Lando Norris"]
    # race_results = race_simulation("saudi_arabia", specific_drivers)