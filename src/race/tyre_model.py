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
    # Global scaling for degradation impact on lap time.
    PACE_PENALTY_SCALE: float = 0.6
    # Small pace boost on fresh tyres that fades as wear builds to reward aggressive undercuts.
    FRESH_TYRE_BONUS: Dict[str, float] = {
        "soft": 0.35,
        "medium": 0.28,
        "hard": 0.22,
    }
    FRESH_WINDOW_WEAR: float = 0.20

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

    def _fresh_tyre_bonus(self, wear: float, compound: TyreCompound) -> float:
        peak_bonus = self.FRESH_TYRE_BONUS.get(compound.name.lower(), 0.0)
        if peak_bonus <= 0 or wear >= self.FRESH_WINDOW_WEAR:
            return 0.0
        # Linear fade to zero across the opening wear window.
        return peak_bonus * (1.0 - (wear / self.FRESH_WINDOW_WEAR))

    def _calculate_penalty(self, tyre_state: TyreState, compound: TyreCompound) -> float:
        """
        Convert tyre wear into a lap time penalty.
        Uses linear interpolation across the degradation curve so every percent of wear
        slows the car down instead of only applying chunked penalties at thresholds.
        """
        penalty = 0.0

        if tyre_state.laps_on_tyre <= compound.warmup_laps:
            penalty += compound.warmup_penalty

        wear = tyre_state.wear
        curve = compound.degradation_curve

        if not curve:
            # Fallback: 2.0s penalty at 100% wear, scaled linearly.
            return penalty + wear * 2.0

        # If we're before the first defined point, scale up from 0.
        first_point = curve[0]
        if wear <= first_point.wear:
            scale = first_point.pace_penalty / max(first_point.wear, 1e-6)
            deg_penalty = wear * scale
            adjusted = deg_penalty * self.PACE_PENALTY_SCALE
            fresh_bonus = self._fresh_tyre_bonus(wear, compound)
            return penalty + max(0.0, adjusted - fresh_bonus)

        # Walk the curve and interpolate between neighbours.
        for prev_point, next_point in zip(curve[:-1], curve[1:]):
            if wear <= next_point.wear:
                span = max(next_point.wear - prev_point.wear, 1e-6)
                progress = (wear - prev_point.wear) / span
                deg_penalty = prev_point.pace_penalty + progress * (
                    next_point.pace_penalty - prev_point.pace_penalty
                )
                adjusted = deg_penalty * self.PACE_PENALTY_SCALE
                fresh_bonus = self._fresh_tyre_bonus(wear, compound)
                return penalty + max(0.0, adjusted - fresh_bonus)

        # Beyond the final point: continue the last slope so wear keeps hurting pace.
        if len(curve) == 1:
            deg_penalty = curve[-1].pace_penalty
            adjusted = deg_penalty * self.PACE_PENALTY_SCALE
            fresh_bonus = self._fresh_tyre_bonus(wear, compound)
            return penalty + max(0.0, adjusted - fresh_bonus)

        last = curve[-1]
        second_last = curve[-2]
        tail_span = max(last.wear - second_last.wear, 1e-6)
        tail_slope = (last.pace_penalty - second_last.pace_penalty) / tail_span
        deg_penalty = last.pace_penalty + max((wear - last.wear) * tail_slope, 0.0)
        adjusted = deg_penalty * self.PACE_PENALTY_SCALE
        fresh_bonus = self._fresh_tyre_bonus(wear, compound)
        return penalty + max(0.0, adjusted - fresh_bonus)

    def check_random_puncture(self, tyre_state: TyreState) -> bool:
        compound = self.get_compound(tyre_state.compound)
        if compound is None:
            return False
        if tyre_state.wear < compound.puncture_risk_wear:
            return False
        return random.random() < compound.puncture_probability


TYRE_MODEL = TyreModel()
