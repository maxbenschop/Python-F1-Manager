# 🏎️ Python F1 Manager

A comprehensive Formula 1 team management simulation built with Python.

## ✨ Features

### Team Management
- **Team Creation DONE** – Build and customize your own F1 team from the ground up
- **Driver Selection DONE** – Scout and recruit promising talent from the F2 circuit
- **Upgrades** – Invest in car development and team facilities to gain competitive advantage
- **Sponsorships** – Secure lucrative deals to fund your racing operations

### Race Experience
- **Race Simulation PROGRESS** – Experience realistic race dynamics and strategy calls
- **Pit Window Selection** – Make critical decisions on tire compounds and repairs
- **Damage System** – Manage car damage and make tough calls on repairs vs. track position
- **Weather Conditions** – Adapt your strategy to changing weather scenarios
- **Safety Car** – Navigate the strategic opportunities of safety car periods

#### Strategy & Tyre Management
- Circuit presets now provide default and alternate pit plans with wear thresholds.
- Live tyre degradation influences lap times, puncture risk, and pit urgency.
- Use `P` during a race to open the strategy menu for your drivers, force a stop, delay it, or change the next compound.
- Automated runs are available via `simulate_race_auto` in `src/race/simulation.py` for quick validation.

#### Quick Validation
```bash
python - <<'PY'
from src.race.simulation import simulate_race_auto
results = simulate_race_auto("australia", seed=42)
for driver, data in list(results.items())[:5]:
    print(driver, data["position"], f"{data['total_time']:.1f}s")
PY
```

### Progression
- **Rewards System** – Earn prizes based on race performance and championship standings
- **Multi-Season Career** – Build your legacy across multiple racing seasons
- **Driver Training** – Develop your drivers' skills and unlock their full potential

---

*Take the helm of an F1 team and navigate the high-stakes world of motorsport management!*

Setup

source .venv/bin/activate
