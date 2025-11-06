#!/usr/bin/env python3
"""
Non-interactive test of the realistic race simulation algorithm.
Simulates qualifying and race results without lap-by-lap interaction.
"""

import sys
import os
import random
sys.path.insert(0, 'src')

from race.simulation import (
    load_driver_data, load_team_data, load_circuit_data,
    calculate_qualifying_score, calculate_race_performance, check_reliability
)

def simulate_race_quick(circuit_id):
    """Quick non-interactive race simulation"""
    # Load data
    drivers = load_driver_data()
    teams = load_team_data()
    circuit = load_circuit_data(circuit_id)

    print(f"\n{'='*70}")
    print(f"🏁 {circuit['name']}")
    print(f"📍 {circuit['location']} | {circuit['length_km']}km | {circuit['num_laps']} laps")
    print(f"📝 {circuit['notes']}")
    print(f"{'='*70}")

    # QUALIFYING
    quali_results = []
    for name, driver in drivers.items():
        team = teams.get(driver.get('team', 'Unknown'))
        if not team:
            continue

        quali_score = calculate_qualifying_score(driver, team, circuit)
        quali_results.append({
            'name': name,
            'team': driver['team'],
            'driver': driver,
            'car': team,
            'score': quali_score
        })

    quali_results.sort(key=lambda x: x['score'], reverse=True)

    print("\n📊 QUALIFYING RESULTS (Top 10):")
    print("-" * 70)
    for i, result in enumerate(quali_results[:10], 1):
        print(f"P{i:2d}. {result['name']:<20} [{result['team']:<15}] {result['score']:.2f}")

    # RACE SIMULATION
    race_results = []
    dnfs = []

    for i, quali_entry in enumerate(quali_results, 1):
        driver = quali_entry['driver']
        car = quali_entry['car']

        # Reliability check (DNF before race)
        if not check_reliability(car):
            dnfs.append({
                'name': quali_entry['name'],
                'team': quali_entry['team'],
                'reason': random.choice(['Engine failure', 'Gearbox issue', 'Crash', 'Suspension failure'])
            })
            continue

        # Calculate race performance
        race_perf = calculate_race_performance(driver, car, circuit, i)

        race_results.append({
            'name': quali_entry['name'],
            'team': quali_entry['team'],
            'starting_pos': i,
            'race_score': race_perf
        })

    # Sort by race performance
    race_results.sort(key=lambda x: x['race_score'], reverse=True)

    # Display results
    print("\n🏆 RACE RESULTS:")
    print("-" * 70)
    for i, result in enumerate(race_results, 1):
        grid_pos = result['starting_pos']
        pos_change = grid_pos - i

        if pos_change > 0:
            change_str = f"(↑{pos_change})"
        elif pos_change < 0:
            change_str = f"(↓{abs(pos_change)})"
        else:
            change_str = "(→)"

        print(f"P{i:2d}. {result['name']:<20} [{result['team']:<15}] Started P{grid_pos:2d} {change_str}")

    if dnfs:
        print(f"\n❌ DNFs ({len(dnfs)}):")
        for dnf in dnfs:
            print(f"    {dnf['name']:<20} [{dnf['team']:<15}] - {dnf['reason']}")

    # Analysis
    print(f"\n📊 RACE ANALYSIS:")
    print("-" * 70)

    # Check top 6
    top_6_teams = [race_results[i]['team'] for i in range(min(6, len(race_results)))]
    top_teams = ['Red Bull', 'McLaren', 'Ferrari', 'Mercedes']
    top_team_in_top6 = sum(1 for team in top_6_teams if any(t in team for t in top_teams))

    winner = race_results[0]['name']
    winner_team = race_results[0]['team']

    print(f"Winner: {winner} ({winner_team})")
    print(f"Top 6 from elite teams (RB/McL/Fer/Mer): {top_team_in_top6}/6")

    # Top 3
    podium = [race_results[i]['name'] for i in range(3)]
    print(f"Podium: {', '.join(podium)}")

    return {
        'circuit': circuit['name'],
        'winner': winner,
        'podium': podium,
        'top_6': [r['name'] for r in race_results[:6]],
        'dnfs': len(dnfs)
    }


if __name__ == "__main__":
    # Test on different track types
    test_tracks = [
        'monaco',       # Street - track position critical
        'monza',        # Speed - power critical
        'japan',        # High downforce - aero critical
        'bahrain',      # Mixed - braking + traction
        'silverstone'   # High-speed aero
    ]

    print("\n" + "=" * 70)
    print("REALISTIC F1 RACE SIMULATION TEST")
    print("Testing algorithm on 5 different track types")
    print("=" * 70)

    all_results = []

    for track in test_tracks:
        result = simulate_race_quick(track)
        all_results.append(result)
        input("\nPress ENTER for next race...")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY ACROSS ALL RACES")
    print("=" * 70)

    all_winners = [r['winner'] for r in all_results]
    winner_counts = {}
    for w in all_winners:
        winner_counts[w] = winner_counts.get(w, 0) + 1

    print("\nWinners:")
    for winner, count in sorted(winner_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {winner}: {count} win(s)")

    all_podiums = []
    for r in all_results:
        all_podiums.extend(r['podium'])

    podium_counts = {}
    for p in all_podiums:
        podium_counts[p] = podium_counts.get(p, 0) + 1

    print("\nMost podiums:")
    for driver, count in sorted(podium_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  • {driver}: {count} podium(s)")

    avg_dnf = sum(r['dnfs'] for r in all_results) / len(all_results)
    print(f"\nAverage DNFs per race: {avg_dnf:.1f}")

    print("\n✅ Test complete! Check if patterns match 2024 F1 season.")
