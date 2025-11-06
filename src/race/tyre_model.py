from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .strategy_models import TyreState


@dataclass(frozen=True)
class DegradationPoint:
    wear: float
    pace_penalty: float

    @staticmethod
    def from_dict(payload: Dict[str, float]) -> "DegradationPoint":
        return DegradationPoint(
            wear=float(payload.get("wear", 0.0)),
            pace_penalty=float(payload.get("pace_penalty", 0.0)),
        )


@dataclass(frozen=True)
class TyreCompound:
    name: str
    base_wear_per_lap: float
    warmup_laps: int
    warmup_penalty: float
    degradation_curve: Tuple[DegradationPoint, ...]
    puncture_risk_wear: float
    puncture_probability: float

    @staticmethod
    def from_dict(payload: Dict[str, object]) -> "TyreCompound":
        return TyreCompound(
            name=str(payload.get("compound", "")),
            base_wear_per_lap=float(payload.get("base_wear_per_lap", 0.03)),
            warmup_laps=int(payload.get("warmup_laps", 1)),
            warmup_penalty=float(payload.get("warmup_penalty", 0.4)),
            degradation_curve=tuple(
                sorted(
                    (DegradationPoint.from_dict(item) for item in payload.get("degradation_curve", [])),
                    key=lambda point: point.wear,
                )
            ),
            puncture_risk_wear=float(payload.get("puncture_risk_wear", 1.0)),
            puncture_probability=float(payload.get("puncture_probability", 0.0)),
        )


class TyreModel:
    """Provides tyre wear updates and lap-time penalties."""

    STRESS_MULTIPLIERS: Dict[str, float] = {
        "low": 0.9,
        "medium": 1.0,
        "high": 1.15,
    }

    def __init__(self, data_path: Optional[Path] = None):
        if data_path is None:
            data_path = Path(__file__).resolve().parents[2] / "assets" / "data" / "tyres.json"
        self._data_path = data_path
        self._compounds: Dict[str, TyreCompound] = {}
        self._load()

    def _load(self) -> None:
        with self._data_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        self._compounds = {entry["compound"]: TyreCompound.from_dict(entry) for entry in payload}

    def get_compound(self, compound: str) -> Optional[TyreCompound]:
        return self._compounds.get(compound.lower())

    def stress_multiplier(self, stress_profile: str) -> float:
        return self.STRESS_MULTIPLIERS.get(stress_profile.lower(), 1.0)

    def update_wear_and_penalty(
        self,
        tyre_state: TyreState,
        stress_profile: str,
    ) -> Tuple[float, float]:
        """
        Apply per-lap wear and return (wear_applied, lap_time_penalty).
        """
        compound = self.get_compound(tyre_state.compound)
        if compound is None:
            return 0.0, 0.0

        wear_delta = compound.base_wear_per_lap * self.stress_multiplier(stress_profile)
        tyre_state.add_wear(wear_delta)

        penalty = self._calculate_penalty(tyre_state, compound)
        tyre_state.performance_modifier = penalty

        return wear_delta, penalty

    def _calculate_penalty(self, tyre_state: TyreState, compound: TyreCompound) -> float:
        penalty = 0.0

        if tyre_state.laps_on_tyre <= compound.warmup_laps:
            penalty += compound.warmup_penalty

        for degradation_point in compound.degradation_curve:
            if tyre_state.wear >= degradation_point.wear:
                penalty += degradation_point.pace_penalty

        return penalty

    def check_random_puncture(self, tyre_state: TyreState) -> bool:
        compound = self.get_compound(tyre_state.compound)
        if compound is None:
            return False
        if tyre_state.wear < compound.puncture_risk_wear:
            return False
        return random.random() < compound.puncture_probability


TYRE_MODEL = TyreModel()

