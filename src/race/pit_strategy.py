import random
from typing import Any, Dict, List


def calculate_pit_stop_time(team: Dict[str, Any]) -> float:
    """
    Calculate pit stop duration from team capabilities, ensuring realistic bounds.
    """
    base_time = 2.0
    pit_speed = team.get('pit_stop_speed', 0.90)

    time_variance = (1.0 - pit_speed) * 5.0
    pit_time = base_time + time_variance + random.uniform(-0.2, 0.4)

    return max(1.8, pit_time)


def apply_pit_strategy(race_state: List[Dict[str, Any]], lap_num: int, total_laps: int) -> List[str]:
    """
    Apply pit strategy decisions for the current lap, mutating race_state with pit data.
    """
    events: List[str] = []

    pit_window_start = int(total_laps * 0.25)
    pit_window_end = int(total_laps * 0.75)

    if pit_window_start <= lap_num <= pit_window_end:
        for driver_state in race_state:
            if driver_state.get('has_pitted', False):
                continue

            laps_in_window = max(1, pit_window_end - pit_window_start)
            pit_probability = 100 / laps_in_window

            laps_remaining = pit_window_end - lap_num
            if laps_remaining < 5:
                pit_probability *= 2

            if random.uniform(0, 100) < pit_probability:
                driver_state['has_pitted'] = True
                current_pos = race_state.index(driver_state) + 1

                pit_time = calculate_pit_stop_time(driver_state['team'])
                total_pit_loss = 20.0 + pit_time
                driver_state['pit_time_loss'] = driver_state.get('pit_time_loss', 0) + total_pit_loss

                events.append(
                    f"  🔧 {driver_state['driver_name']} pits from P{current_pos} ({pit_time:.1f}s stop)"
                )

    if lap_num == pit_window_end + 1:
        for driver_state in race_state:
            if driver_state.get('has_pitted', False):
                continue

            driver_state['has_pitted'] = True
            current_pos = race_state.index(driver_state) + 1

            pit_time = calculate_pit_stop_time(driver_state['team']) + 0.5
            total_pit_loss = 20.0 + pit_time
            driver_state['pit_time_loss'] = driver_state.get('pit_time_loss', 0) + total_pit_loss

            events.append(
                f"  🔧 {driver_state['driver_name']} makes MANDATORY pit stop from P{current_pos} ({pit_time:.1f}s)"
            )

    return events

