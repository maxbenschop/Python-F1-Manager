import json
import os
import random
from typing import Dict, List, Tuple

from simple_term_menu import TerminalMenu

SAVE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "data", "save", "save.json")

TrainingEffect = Dict[str, float]

# Program effects are permanent stat bumps; confidence is also increased.
PROGRAMS: List[Tuple[str, str, TrainingEffect]] = [
    (
        "Quali Attack",
        "Sharpen one-lap pace. Best for grabbing grid position.",
        {"qualifying": 8, "pace": 3, "confidence": 0.08},
    ),
    (
        "Race Pace",
        "Long-run consistency and tyre management focus.",
        {"pace": 7, "racecraft": 3, "confidence": 0.07},
    ),
    (
        "Racecraft & Starts",
        "Wheel-to-wheel drills and launch practice.",
        {"racecraft": 8, "pace": 2, "experience": 2, "confidence": 0.07},
    ),
    (
        "Balanced",
        "A bit of everything to keep form steady.",
        {"pace": 5, "racecraft": 4, "qualifying": 5, "confidence": 0.06},
    ),
]


def _load_save() -> Dict:
    with open(SAVE_PATH, "r") as handle:
        return json.load(handle)


def _write_save(payload: Dict) -> None:
    with open(SAVE_PATH, "w") as handle:
        json.dump(payload, handle, indent=4)


def _ensure_confidence(driver: Dict) -> None:
    # Baseline confidence to 50% before any training.
    driver["confidence"] = 0.5


def _performance_factor(driver: Dict) -> float:
    avg_skill = (
        driver.get("pace", 0)
        + driver.get("racecraft", 0)
        + driver.get("qualifying", 0)
    ) / 3.0
    return max(0.5, min(1.2, avg_skill / 90.0))


def _confidence_gain(driver: Dict) -> float:
    """
    Random confidence gain scaled by driver performance.
    Designed so 1–3 sessions can push confidence toward 100%.
    """
    base = random.uniform(0.12, 0.22)
    return base * _performance_factor(driver)


def _print_driver(driver: Dict) -> None:
    print(
        f"{driver['name']} — Pace {driver.get('pace', 0):.0f}, "
        f"Quali {driver.get('qualifying', 0):.0f}, "
        f"Racecraft {driver.get('racecraft', 0):.0f}, "
        f"Confidence {driver.get('confidence', 0.0) * 100:5.1f}%"
    )


def _apply_program(driver: Dict, effects: TrainingEffect) -> None:
    # Permanent stat bumps
    for key in ("pace", "racecraft", "qualifying", "experience"):
        if key in effects:
            driver[key] = driver.get(key, 0) + int(effects[key])

    # Confidence gains from program plus performance-based randomness
    conf_gain = effects.get("confidence", 0.0) + _confidence_gain(driver)
    driver["confidence"] = min(1.0, driver.get("confidence", 0.5) + conf_gain)


def run_training_session(team: str, driver_names: List[str], *, min_sessions: int = 1, max_sessions: int = 3) -> None:
    """
    Interactive training. Enforces 1–3 sessions per race.
    Bumps are persisted to save.json (stats and confidence).
    """
    try:
        save_data = _load_save()
    except FileNotFoundError:
        print("\n❌ No save file found; cannot train.")
        return

    drivers = save_data.get("drivers", [])
    driver_lookup = {d["name"]: d for d in drivers}

    sessions_done = 0
    mandatory_sessions = max(1, min_sessions)

    print("\n🏋️  Pre-Race Training")
    print(f"Team: {team}")
    print(f"Minimum sessions: {mandatory_sessions}, Maximum: {max_sessions}")
    print("Stat gains are permanent. Confidence starts at 50% before training.")

    # Reset baseline confidence before this block for the player's drivers.
    for name in driver_names:
        driver = driver_lookup.get(name)
        if driver:
            _ensure_confidence(driver)

    while sessions_done < max_sessions:
        print(f"\nSESSION {sessions_done + 1}/{max_sessions}")
        for name in driver_names:
            driver = driver_lookup.get(name)
            if not driver:
                print(f"\n⚠️  Driver {name} not found in save; skipping.")
                continue
            _print_driver(driver)

            menu_options = [f"{title} — {desc}" for title, desc, _ in PROGRAMS]
            menu = TerminalMenu(
                menu_options,
                title=f"\nSelect program for {name}:",
                menu_cursor="➤ ",
                menu_cursor_style=("fg_cyan", "bold"),
                menu_highlight_style=("bg_cyan", "fg_black"),
            )
            idx = menu.show()
            if idx is None:
                print("Cancelled training selection; keeping previous values.")
                continue

            title, _desc, effects = PROGRAMS[idx]
            _apply_program(driver, effects)

            delta_desc = ", ".join(
                f"{k}+{v if k == 'confidence' else int(v)}"
                for k, v in effects.items()
                if k != "confidence"
            )
            print(f"✓ {name} ran '{title}' ({delta_desc or 'confidence boost'}), confidence now {driver['confidence']*100:5.1f}%")

        sessions_done += 1

        if sessions_done >= max_sessions:
            break
        if sessions_done < mandatory_sessions:
            continue

        choice = input("\nRun another training session? (y/N): ").strip().lower()
        if choice not in ("y", "yes"):
            break

    # Persist updated drivers
    save_data["drivers"] = drivers
    _write_save(save_data)
    print("\n✅ Training saved. Stats and confidence updated permanently.")
