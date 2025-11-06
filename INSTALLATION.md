# Installation & Setup Guide

## Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

## Installation Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install simple-term-menu>=1.6.1
```

### 2. Verify Installation

Run the test script to verify everything is working:

```bash
python3 test_race_results.py
```

This will run 5 test races and show you sample results.

## Running the Game

### Option 1: Start a New Game

If you don't have a saved game:

```bash
python3 src/team/start.py
```

This will guide you through:
- Selecting a team
- Choosing your drivers
- Creating your save file

### Option 2: Continue Existing Game

If you already have a saved game:

```bash
python3 src/game.py
```

Or:

```bash
python3 -m src.game
```

### Option 3: Run Quick Race Test

To test the new realistic race simulation without setting up a full game:

```bash
python3 test_race_results.py
```

## Troubleshooting

### Import Error: No module named 'simple_term_menu'

Install the required dependency:
```bash
pip install simple-term-menu
```

### No saved game found

Start a new game first:
```bash
python3 src/team/start.py
```

### Python version error

Make sure you're using Python 3.7+:
```bash
python3 --version
```

## Project Structure

```
Python-F1-Manager/
├── src/
│   ├── game.py              # Main game entry point
│   ├── race/
│   │   ├── simulation.py    # Realistic race simulation (UPDATED)
│   │   ├── pit_strategy.py
│   │   └── ...
│   ├── team/
│   │   └── start.py         # New game setup
│   └── utils/
├── assets/
│   └── data/
│       ├── drivers.json
│       ├── teams.json
│       ├── circuits.json
│       └── save/
│           └── save.json    # Your game progress
├── test_race_results.py     # Quick simulation test
├── requirements.txt
└── setup.py
```

## What's New

The race simulation has been updated with a realistic 2024 F1 algorithm:

✅ **Realistic Results**
- Top teams (Red Bull, McLaren, Ferrari, Mercedes) dominate top 6
- Verstappen, Norris, Leclerc regularly fighting for wins
- Track position matters (Monaco, Singapore)
- Average 2-4 DNFs per race

✅ **Tunable Constants**
All weights and multipliers are adjustable at the top of `src/race/simulation.py`

✅ **Track-Specific Behavior**
- Monaco: Track position critical
- Monza: Power advantage matters
- Suzuka: Aero efficiency rewarded

## Support

If you encounter issues:
1. Verify Python version: `python3 --version`
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Check that data files exist in `assets/data/`
