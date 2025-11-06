#!/usr/bin/env python3
"""
Quick test script to validate the new realistic race simulation algorithm.
Tests on different track types to ensure results match 2024 F1 patterns.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from race.simulation import race_simulation

# Test circuits representing different track types
test_circuits = [
    ("monaco", "Street Circuit - Track position critical"),
    ("monza", "High-speed - Power critical"),
    ("japan", "High downforce - Aero critical"),
    ("bahrain", "Mixed - Braking + traction"),
    ("saudi_arabia", "High-speed street layout")
]

print("=" * 80)
print("REALISTIC F1 SIMULATION TEST - 2024 Season Validation")
print("=" * 80)
print("\nTesting new algorithm on 5 different track types...")
print("Looking for patterns matching 2024 F1 season:\n")
print("✓ Top teams (Red Bull, McLaren, Ferrari, Mercedes) dominating top 6")
print("✓ Verstappen, Norris, Leclerc, Piastri, Hamilton fighting for podium")
print("✓ Midfield teams (Aston, Alpine, Williams, etc.) in P7-P15")
print("✓ Realistic DNF rate (2-4 cars)")
print("=" * 80)

all_winners = []
all_top_3 = []

for circuit_id, description in test_circuits:
    print(f"\n{'=' * 80}")
    print(f"Testing: {circuit_id.upper()} ({description})")
    print(f"{'=' * 80}\n")

    # Run simulation without interactive prompts by modifying the function
    # We'll just show qualifying and final results
    try:
        results = race_simulation(circuit_id)

        # Extract and display key information
        finishers = [(name, data) for name, data in results.items() if data['status'] == 'Running']
        finishers.sort(key=lambda x: x[1]['position'])

        dnfs = [(name, data) for name, data in results.items() if data['status'] == 'DNF']

        print(f"\n🏆 RACE RESULTS SUMMARY:")
        print("-" * 60)

        # Top 10
        for i, (name, data) in enumerate(finishers[:10], 1):
            team = data['driver_stats']['team']
            all_top_3.append(name) if i <= 3 else None
            all_winners.append(name) if i == 1 else None
            print(f"P{i:2d}. {name:<20} [{team:<15}]")

        # DNFs
        print(f"\n❌ DNFs: {len(dnfs)}")
        for name, data in dnfs:
            print(f"    {name:<20} - {data['incident']}")

        # Analysis
        print(f"\n📊 Quick Analysis:")
        top_6_teams = [finishers[i][1]['driver_stats']['team'] for i in range(min(6, len(finishers)))]
        top_teams = ['Red Bull', 'McLaren', 'Ferrari', 'Mercedes']
        top_team_count = sum(1 for team in top_6_teams if any(t in team for t in top_teams))
        print(f"   • Top 6 from elite teams: {top_team_count}/6")
        print(f"   • Winner: {finishers[0][0]} ({finishers[0][1]['driver_stats']['team']})")

    except KeyboardInterrupt:
        print("\n\n⏩ Skipping to next track...")
        continue

# Overall summary
print("\n" + "=" * 80)
print("OVERALL TEST SUMMARY")
print("=" * 80)
print(f"\nRaces simulated: {len(test_circuits)}")
print(f"\nWinners across all races:")
winner_counts = {}
for winner in all_winners:
    winner_counts[winner] = winner_counts.get(winner, 0) + 1
for winner, count in sorted(winner_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  • {winner}: {count} win(s)")

print(f"\n✅ Test complete! Check if results match 2024 F1 patterns.")
