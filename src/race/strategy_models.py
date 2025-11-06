from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class StintPlan:
    """Represents one stint within a race strategy."""

    compound: str
    target_lap_fraction: float
    pit_window_fraction: Tuple[float, float]

    @staticmethod
    def from_dict(payload: Dict[str, object]) -> "StintPlan":
        window = payload.get("pit_window_fraction", [0.0, 0.0])
        return StintPlan(
            compound=str(payload.get("compound", "")),
            target_lap_fraction=float(payload.get("target_lap_fraction", 0.0)),
            pit_window_fraction=(float(window[0]), float(window[1])),
        )


@dataclass(frozen=True)
class RaceStrategy:
    """Structured view over a reusable pit strategy template."""

    id: str
    name: str
    description: str
    stints: Tuple[StintPlan, ...]
    recommended_compounds: Tuple[str, ...]
    tyre_wear_expectation: str
    safety_car_adjustment: Dict[str, int]
    notes: str

    @staticmethod
    def from_dict(payload: Dict[str, object]) -> "RaceStrategy":
        stints = tuple(StintPlan.from_dict(stint) for stint in payload.get("stints", []))
        compounds = tuple(str(item) for item in payload.get("recommended_compounds", []))
        safety_adjustment = {
            str(key): int(value) for key, value in (payload.get("safety_car_adjustment") or {}).items()
        }
        return RaceStrategy(
            id=str(payload.get("id", "")),
            name=str(payload.get("name", "")),
            description=str(payload.get("description", "")),
            stints=stints,
            recommended_compounds=compounds,
            tyre_wear_expectation=str(payload.get("tyre_wear_expectation", "")),
            safety_car_adjustment=safety_adjustment,
            notes=str(payload.get("notes", "")),
        )


@dataclass(frozen=True)
class StrategyPreset:
    """Circuit supplied mapping to a strategy template."""

    template: str
    notes: str
    stint_offsets: Dict[str, float]

    @staticmethod
    def from_dict(payload: Dict[str, object]) -> "StrategyPreset":
        return StrategyPreset(
            template=str(payload.get("template", "")),
            notes=str(payload.get("notes", "")),
            stint_offsets={key: float(value) for key, value in (payload.get("stint_offsets") or {}).items()},
        )


@dataclass(frozen=True)
class CircuitStrategyProfile:
    """Circuit specific strategic defaults plus tyre stress information."""

    tyre_stress_profile: str
    default: StrategyPreset
    alternate: StrategyPreset

    @staticmethod
    def from_dict(tyre_stress: str, payload: Dict[str, object]) -> "CircuitStrategyProfile":
        default = StrategyPreset.from_dict(payload.get("default") or {})
        alternate = StrategyPreset.from_dict(payload.get("alternate") or {})
        return CircuitStrategyProfile(
            tyre_stress_profile=str(tyre_stress or ""),
            default=default,
            alternate=alternate,
        )


@dataclass
class TyreState:
    """Tracks a driver's tyre condition through the race."""

    compound: str
    wear: float = 0.0  # value between 0.0 (fresh) and 1.0 (fully worn)
    laps_on_tyre: int = 0
    performance_modifier: float = 0.0

    def add_wear(self, wear_delta: float) -> None:
        """Increment tyre wear and lap counters."""
        self.wear = min(1.0, max(0.0, self.wear + wear_delta))
        self.laps_on_tyre += 1

    @property
    def is_serviceable(self) -> bool:
        """Flag tyres that exceed safe usage thresholds."""
        return self.wear < 1.0


class StrategyRepository:
    """Lazy loader for reusable pit strategy templates."""

    def __init__(self, data_path: Optional[Path] = None):
        if data_path is None:
            data_path = Path(__file__).resolve().parents[2] / "assets" / "data" / "pit_strategies.json"
        self._data_path = data_path
        self._strategies: Optional[Dict[str, RaceStrategy]] = None

    def _ensure_loaded(self) -> None:
        if self._strategies is not None:
            return

        with self._data_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        self._strategies = {entry["id"]: RaceStrategy.from_dict(entry) for entry in payload}

    def all_strategies(self) -> Iterable[RaceStrategy]:
        self._ensure_loaded()
        return tuple(self._strategies.values())  # type: ignore[union-attr]

    def get(self, strategy_id: str) -> Optional[RaceStrategy]:
        self._ensure_loaded()
        return self._strategies.get(strategy_id)  # type: ignore[union-attr]
