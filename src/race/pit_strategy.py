import random
from typing import Any, Dict, List, Optional, Tuple

from .strategy_models import (
    CircuitStrategyProfile,
    RaceStrategy,
    StrategyPreset,
    StrategyRepository,
    TyreState,
)

_STRATEGY_REPOSITORY = StrategyRepository()
_TYRE_WEAR_PIT_THRESHOLD = 0.78
_TYRE_CRITICAL_THRESHOLD = 0.9


def get_strategy_template(strategy_id: str) -> Optional[RaceStrategy]:
    """
    Pull a reusable strategy template by id.
    """
    return _STRATEGY_REPOSITORY.get(strategy_id)


def get_circuit_strategy_profile(circuit_data: Dict[str, Any]) -> Optional[CircuitStrategyProfile]:
    """
    Convert raw circuit JSON into a strategy profile.
    """
    presets = circuit_data.get("strategy_presets")
    if not presets:
        return None

    tyre_stress = circuit_data.get("tyre_stress_profile", "")
    return CircuitStrategyProfile.from_dict(tyre_stress, presets)


def create_tyre_state(initial_compound: str) -> TyreState:
    """
    Allocate a fresh tyre state for a driver.
    """
    return TyreState(compound=initial_compound)


def _advance_strategy_stint(driver_state: Dict[str, Any]) -> str:
    plan: Optional[RaceStrategy] = driver_state.get('strategy_plan')
    current_index = driver_state.get('strategy_stint_index', 0)

    if plan and plan.stints:
        if current_index < len(plan.stints) - 1:
            current_index += 1
            driver_state['strategy_stint_index'] = current_index
        compound = plan.stints[current_index].compound.lower()
    else:
        compound = driver_state.get('current_compound', 'medium')

    override_compound = driver_state.pop('next_compound_override', None)
    if override_compound:
        compound = override_compound.lower()

    driver_state['current_compound'] = compound
    driver_state['tyre_state'] = create_tyre_state(compound)
    return compound


def _allowed_pit_stops(driver_state: Dict[str, Any]) -> int:
    plan: Optional[RaceStrategy] = driver_state.get('strategy_plan')
    if plan and plan.stints:
        return max(len(plan.stints) - 1, 1)
    return driver_state.get('max_pit_stops', 1)


def _strategy_targets(
    plan: Optional[RaceStrategy],
    stint_index: int,
    total_laps: int,
    strategy_config: Dict[str, Any],
) -> Optional[Tuple[int, int, int]]:
    if not plan or not plan.stints or stint_index >= len(plan.stints) - 1:
        return None

    stint = plan.stints[stint_index]
    lap_bias = int(strategy_config.get('lap_bias', 0))

    def clamp(value: float) -> int:
        return max(1, int(round(value * total_laps)) + lap_bias)

    target_lap = clamp(stint.target_lap_fraction)
    window_start = clamp(stint.pit_window_fraction[0])
    window_end = clamp(stint.pit_window_fraction[1])
    if window_end < window_start:
        window_end = window_start
    return target_lap, window_start, window_end


def calculate_pit_stop_time(team: Dict[str, Any]) -> float:
    """
    Calculate pit stop duration from team capabilities, ensuring realistic bounds.
    """
    base_time = 2.0
    pit_speed = team.get('pit_stop_speed', 0.90)

    time_variance = (1.0 - pit_speed) * 5.0
    pit_time = base_time + time_variance + random.uniform(-0.2, 0.4)

    return max(1.8, pit_time)


def _apply_template_driven_strategy(
    race_state: List[Dict[str, Any]],
    lap_num: int,
    total_laps: int,
    strategy_plan: RaceStrategy,
    default_plan: Optional[RaceStrategy] = None,
) -> List[str]:
    """
    Placeholder for template-aware pit logic; currently falls back to generic behaviour.
    """
    return _apply_generic_strategy(race_state, lap_num, total_laps, default_plan=strategy_plan or default_plan)


def _apply_generic_strategy(
    race_state: List[Dict[str, Any]],
    lap_num: int,
    total_laps: int,
    default_plan: Optional[RaceStrategy] = None,
) -> List[str]:
    """
    Fallback strategy: distributes stops evenly within the middle stint of the race.
    """
    events: List[str] = []
    pit_window_start = int(total_laps * 0.25)
    pit_window_end = int(total_laps * 0.75)

    for driver_state in race_state:
        plan = driver_state.get('strategy_plan') or default_plan
        current_index = driver_state.get('strategy_stint_index', 0)
        force_pit = driver_state.get('force_pit_on_lap') == lap_num
        defer_laps = driver_state.get('defer_pit_laps', 0)
        tyre_state = driver_state.get('tyre_state')
        strategy_config = driver_state.get('strategy_config', {}) or {}

        if defer_laps > 0 and not force_pit:
            driver_state['defer_pit_laps'] = max(defer_laps - 1, 0)
            continue

        allowed_stops = _allowed_pit_stops(driver_state)
        pit_stops_taken = driver_state.get('pit_stops', 0)

        wear_threshold = float(strategy_config.get('wear_threshold', _TYRE_WEAR_PIT_THRESHOLD))
        critical_threshold = max(_TYRE_CRITICAL_THRESHOLD, wear_threshold + 0.05)

        targets = _strategy_targets(plan, current_index, total_laps, strategy_config)
        pit_probability = 0.0

        if force_pit:
            pit_probability = 100.0
        else:
            if targets:
                target_lap, window_start, window_end = targets
                if lap_num >= window_end:
                    pit_probability = max(pit_probability, 85.0)
                elif lap_num >= target_lap:
                    pit_probability = max(pit_probability, 60.0)
                elif lap_num >= window_start:
                    pit_probability = max(pit_probability, 35.0)

            if pit_window_start <= lap_num <= pit_window_end:
                laps_in_window = max(1, pit_window_end - pit_window_start)
                pit_probability = max(pit_probability, 100 / laps_in_window)

        if isinstance(tyre_state, TyreState):
            if tyre_state.wear >= critical_threshold:
                pit_probability = 100.0
            elif tyre_state.wear >= wear_threshold:
                pit_probability = max(pit_probability, 65.0)

        if pit_stops_taken >= allowed_stops and pit_probability < 80 and not force_pit:
            # Keep planned stops unless forced or tyre wear demands it
            continue

        if random.uniform(0, 100) < pit_probability:
            driver_state['pit_stops'] = pit_stops_taken + 1
            driver_state['force_pit_on_lap'] = None
            driver_state['defer_pit_laps'] = 0
            driver_state['last_pit_lap'] = lap_num

            pit_time = calculate_pit_stop_time(driver_state['team'])
            total_pit_loss = 20.0 + pit_time
            driver_state['pit_time_loss'] = driver_state.get('pit_time_loss', 0) + total_pit_loss
            next_compound = _advance_strategy_stint(driver_state)

            current_pos = race_state.index(driver_state) + 1
            tag = " (Player call)" if force_pit else ""
            events.append(
                f"  🔧 {driver_state['driver_name']} pits from P{current_pos} ({pit_time:.1f}s stop) -> {next_compound.title()}{tag}"
            )

    if lap_num == pit_window_end + 1:
        for driver_state in race_state:
            plan = driver_state.get('strategy_plan') or default_plan
            current_index = driver_state.get('strategy_stint_index', 0)
            if driver_state.get('pit_stops', 0) >= _allowed_pit_stops(driver_state):
                continue
            if plan and current_index >= len(plan.stints) - 1:
                continue
            driver_state['pit_stops'] = driver_state.get('pit_stops', 0) + 1
            driver_state['force_pit_on_lap'] = None
            driver_state['defer_pit_laps'] = 0
            driver_state['last_pit_lap'] = lap_num

            pit_time = calculate_pit_stop_time(driver_state['team']) + 0.5
            total_pit_loss = 20.0 + pit_time
            driver_state['pit_time_loss'] = driver_state.get('pit_time_loss', 0) + total_pit_loss
            next_compound = _advance_strategy_stint(driver_state)

            current_pos = race_state.index(driver_state) + 1
            events.append(
                f"  🔧 {driver_state['driver_name']} makes MANDATORY pit stop from P{current_pos} ({pit_time:.1f}s) -> {next_compound.title()}"
            )

    return events


def apply_pit_strategy(
    race_state: List[Dict[str, Any]],
    lap_num: int,
    total_laps: int,
    strategy_plan: Optional[RaceStrategy] = None,
) -> List[str]:
    """
    Apply pit strategy decisions for the current lap, mutating race_state with pit data.
    """
    if strategy_plan:
        return _apply_template_driven_strategy(race_state, lap_num, total_laps, strategy_plan, default_plan=strategy_plan)

    return _apply_generic_strategy(race_state, lap_num, total_laps, default_plan=strategy_plan)


def resolve_preset_strategy(
    circuit_profile: CircuitStrategyProfile,
    preset: StrategyPreset,
) -> Optional[RaceStrategy]:
    """
    Retrieve a ready-to-use RaceStrategy from the repository.
    """
    return get_strategy_template(preset.template)


def get_strategy_options_for_circuit(
    circuit_data: Dict[str, Any]
) -> Tuple[Optional[RaceStrategy], Optional[RaceStrategy], Optional[CircuitStrategyProfile]]:
    """
    Convenience helper returning default and alternate strategies for a circuit.
    """
    profile = get_circuit_strategy_profile(circuit_data)
    if not profile:
        return (None, None, None)

    default = resolve_preset_strategy(profile, profile.default)
    alternate = resolve_preset_strategy(profile, profile.alternate)
    return default, alternate, profile
