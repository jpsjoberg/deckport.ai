#!/usr/bin/env python3
import os
import statistics
from typing import Dict, List, Tuple
import math
import pathlib

try:
    from .config import settings
    from .generate_cards_and_insert import load_rows, GameplayRow
except ImportError:
    import sys
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    from config import settings
    from generate_cards_and_insert import load_rows, GameplayRow


def compute_power_score(row: GameplayRow) -> float:
    category = (row.category or "").upper()
    if category == "CREATURE":
        return max(0, row.attack) * 1.0 + max(0, row.health) * 0.5
    if category == "STRUCTURE":
        return max(0, row.defense) * 1.0 + max(0, row.health) * 0.6
    # Action power is unknown from CSV; return a small baseline to avoid div-by-zero
    return 1.0


def aggregate(values: List[float]) -> Tuple[float, float, float]:
    if not values:
        return (0.0, 0.0, 0.0)
    return (
        statistics.mean(values),
        statistics.median(values),
        statistics.pstdev(values),
    )


def _quantiles(values: List[float]) -> Tuple[float, float, float]:
    if not values:
        return (0.0, 0.0, 0.0)
    try:
        qs = statistics.quantiles(values, n=100, method="inclusive")
        q10 = qs[9]
        q50 = qs[49]
        q90 = qs[89]
        return (q10, q50, q90)
    except Exception:
        # Fallback: rough approximations
        sorted_vals = sorted(values)
        def pick(p: float) -> float:
            idx = max(0, min(len(sorted_vals) - 1, int(round(p * (len(sorted_vals) - 1)))))
            return sorted_vals[idx]
        return (pick(0.10), pick(0.50), pick(0.90))


def analyze() -> None:
    art_csv = os.path.join(settings.PROJECT_ROOT, "data", "cards_art.csv")
    gp_csv = os.path.join(settings.PROJECT_ROOT, "data", "cards_gameplay.csv")
    _, gp_rows = load_rows(art_csv, gp_csv)

    rows: List[GameplayRow] = list(gp_rows.values())

    # Basic distributions
    by_category: Dict[str, List[GameplayRow]] = {}
    for r in rows:
        by_category.setdefault((r.category or "").upper(), []).append(r)

    totals = {k: len(v) for k, v in by_category.items()}
    # Group by color
    by_color: Dict[str, List[GameplayRow]] = {}
    for r in rows:
        by_color.setdefault((r.color_code or "").upper(), []).append(r)

    # Efficiency: power per total cost unit
    efficiency: List[Tuple[str, float]] = []
    for r in rows:
        total_cost = max(1, r.mana_cost + r.energy_cost)
        efficiency.append((r.name, compute_power_score(r) / total_cost))

    eff_values = [v for _, v in efficiency]
    mean_eff, med_eff, sd_eff = aggregate(eff_values)
    q10, q50, q90 = _quantiles(eff_values)

    lowest15 = sorted(efficiency, key=lambda x: x[1])[:15]
    highest15 = sorted(efficiency, key=lambda x: x[1], reverse=True)[:15]

    # Energy economy checks
    hero_rows = [r for r in rows if (r.category or "").upper() in ("CREATURE", "STRUCTURE")]
    action_rows = [r for r in rows if (r.category or "").upper() == "ACTION"]

    avg_base_energy = statistics.mean([max(0, r.base_energy_per_turn) for r in hero_rows]) if hero_rows else 0
    print(f"Average base_energy_per_turn (heroes): {avg_base_energy:.2f}")

    # Share of actions playable in a single turn for common hero energies
    playable_rows: List[Tuple[int, int, float]] = []
    for ept in [1, 2, 3, 4]:
        playable = sum(1 for r in action_rows if r.energy_cost <= ept)
        share = (playable / len(action_rows) * 100.0) if action_rows else 0.0
        playable_rows.append((ept, playable, share))

    # Time-to-afford distribution for hero abilities assumed to cost their energy_cost once per turn
    # Approximation: turns_needed = ceil(energy_cost / (base_energy_per_turn + arena_bonus))
    def turns_needed(cost: int, ept: int, arena_bonus: int = 0) -> int:
        income = max(1, ept + arena_bonus)
        return (cost + income - 1) // income

    tn_no_bonus = [turns_needed(r.energy_cost, max(1, r.base_energy_per_turn), 0) for r in hero_rows]
    tn_bonus = [turns_needed(r.energy_cost, max(1, r.base_energy_per_turn), 1) for r in hero_rows]

    # Mana economy for summoning heroes (mana only)
    def summon_turns(mana_cost: int, mana_per_turn: int, discount: int = 0) -> int:
        effective_cost = max(1, mana_cost - discount)
        return max(1, (effective_cost + mana_per_turn - 1) // mana_per_turn)

    hero_mana_costs = [max(0, r.mana_cost) for r in hero_rows]
    mean_mana = statistics.mean(hero_mana_costs) if hero_mana_costs else 0
    med_mana = statistics.median(hero_mana_costs) if hero_mana_costs else 0
    q10_mana, q50_mana, q90_mana = _quantiles(hero_mana_costs) if hero_mana_costs else (0, 0, 0)

    # Scenarios
    base_summon = [summon_turns(r.mana_cost, 1, 0) for r in hero_rows]
    arena_summon = [summon_turns(r.mana_cost, 1, 1) for r in hero_rows]
    # Channel adds +1 mana/turn if base_energy_per_turn >= 2 (costing 2 energy)
    chan_summon = [
        summon_turns(r.mana_cost, 2 if max(0, r.base_energy_per_turn) >= 2 else 1, 1)
        for r in hero_rows
    ]

    def pct_leq(values: List[int], t: int) -> float:
        return (sum(1 for v in values if v <= t) / len(values) * 100.0) if values else 0.0
    report_dir = os.path.join(settings.PROJECT_ROOT, "output")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "balance_report.md")

    def line(s: str) -> str:
        return s + "\n"

    lines: List[str] = []
    lines.append(line("## Deckport Balance Report"))
    lines.append(line(""))
    lines.append(line("### Totals"))
    totals_str = ", ".join(f"{k}: {v}" for k, v in sorted(totals.items()))
    lines.append(line(f"- Totals: {totals_str}"))
    lines.append(line(""))

    lines.append(line("### Efficiency (power/(mana+energy))"))
    lines.append(line(f"- mean: {mean_eff:.2f}"))
    lines.append(line(f"- median: {med_eff:.2f}"))
    lines.append(line(f"- sd: {sd_eff:.2f}"))
    lines.append(line(f"- q10/q50/q90: {q10:.2f} / {q50:.2f} / {q90:.2f}"))
    lines.append(line(""))

    lines.append(line("### Lowest efficiency (15)"))
    for name, val in lowest15:
        lines.append(line(f"- {name}: {val:.2f}"))
    lines.append(line(""))

    lines.append(line("### Highest efficiency (15)"))
    for name, val in highest15:
        lines.append(line(f"- {name}: {val:.2f}"))
    lines.append(line(""))

    lines.append(line("### Energy Economy"))
    lines.append(line(f"- Average base energy per turn (heroes): {avg_base_energy:.2f}"))
    for ept, playable, share in playable_rows:
        lines.append(line(f"- Actions playable with {ept} energy: {playable}/{len(action_rows)} ({share:.1f}%)"))
    if tn_no_bonus:
        lines.append(line(
            f"- Hero time-to-afford (no arena bonus): mean {statistics.mean(tn_no_bonus):.2f}, median {statistics.median(tn_no_bonus):.0f}"
        ))
        lines.append(line(
            f"- Hero time-to-afford (+1 arena): mean {statistics.mean(tn_bonus):.2f}, median {statistics.median(tn_bonus):.0f}"
        ))
    lines.append(line(""))

    lines.append(line("### Mana Economy (Summoning Heroes)"))
    lines.append(line(f"- Mana cost (heroes): mean {mean_mana:.2f}, median {med_mana:.0f}, q10/q50/q90: {q10_mana:.0f}/{q50_mana:.0f}/{q90_mana:.0f}"))
    lines.append(line(f"- Turns to summon (baseline, +1 mana/turn, no discount): mean {statistics.mean(base_summon):.2f}, median {statistics.median(base_summon):.0f}"))
    lines.append(line(f"- Turns to summon (arena discount -1): mean {statistics.mean(arena_summon):.2f}, median {statistics.median(arena_summon):.0f}"))
    lines.append(line(f"- Turns to summon (arena -1 + channel when EPT>=2): mean {statistics.mean(chan_summon):.2f}, median {statistics.median(chan_summon):.0f}"))
    lines.append(line(f"- Heroes summonable by turn 2: base {pct_leq(base_summon,2):.1f}%, arena {pct_leq(arena_summon,2):.1f}%, arena+channel {pct_leq(chan_summon,2):.1f}%"))
    lines.append(line(f"- Heroes summonable by turn 3: base {pct_leq(base_summon,3):.1f}%, arena {pct_leq(arena_summon,3):.1f}%, arena+channel {pct_leq(chan_summon,3):.1f}%"))
    lines.append(line(""))

    # Color breakdowns
    lines.append(line("### Color Breakdown"))
    lines.append(line("Color-level stats for costs and efficiency."))
    for color, items in sorted(by_color.items()):
        effs = []
        mana_costs = []
        energy_costs = []
        actions = [r for r in items if (r.category or "").upper() == "ACTION"]
        heroes = [r for r in items if (r.category or "").upper() in ("CREATURE", "STRUCTURE")]
        for r in items:
            mana_costs.append(max(0, r.mana_cost))
            energy_costs.append(max(0, r.energy_cost))
            effs.append(compute_power_score(r) / max(1, r.mana_cost + r.energy_cost))
        m_mean, m_median, _ = aggregate([float(x) for x in mana_costs])
        e_mean, e_median, _ = aggregate([float(x) for x in energy_costs])
        ef_mean, ef_median, _ = aggregate(effs)
        # Action playability by color
        act_play = []
        for ept in [1, 2, 3]:
            playable = sum(1 for r in actions if r.energy_cost <= ept)
            share = (playable / len(actions) * 100.0) if actions else 0.0
            act_play.append((ept, playable, len(actions), share))
        lines.append(line(f"- {color}:"))
        lines.append(line(f"  - cards: {len(items)} (heroes {len(heroes)}, actions {len(actions)})"))
        lines.append(line(f"  - mana_cost mean/median: {m_mean:.2f}/{m_median:.0f}"))
        lines.append(line(f"  - energy_cost mean/median: {e_mean:.2f}/{e_median:.0f}"))
        lines.append(line(f"  - efficiency mean/median: {ef_mean:.2f}/{ef_median:.2f}"))
        for ept, playable, total, share in act_play:
            lines.append(line(f"  - actions playable with {ept} energy: {playable}/{total} ({share:.1f}%)"))
    lines.append(line(""))

    # Rules appendix: Mana production per README
    lines.append(line("### Rules Appendix: Mana Production"))
    lines.append(line("- Each turn, you gain 1 Mana per color you have in play (baseline)."))
    lines.append(line("- Arena Advantage: the first matching-color card you play each turn costs 1 less Mana (minimum 1)."))
    lines.append(line("- Channel (smoothing): once per turn, convert 2 Energy → 1 Mana of your hero’s color."))
    lines.append(line("- Focus (smoothing): at end of turn, you may bank 1 unused Energy as a Focus counter (max 2) to spend later as Energy."))
    lines.append(line(""))

    with open(report_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"Wrote readable report to {report_path}")


if __name__ == "__main__":
    analyze()

