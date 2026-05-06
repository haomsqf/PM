from __future__ import annotations

import argparse
from dataclasses import asdict
from typing import Sequence

import pandas as pd

from portfolio_enumerator import (
    ClientProfile,
    analyze_portfolio,
    load_asset_returns,
)


DEFAULT_SEED = (0.30, 0.10, 0.05, 0.25, 0.30)


def generate_neighbor_weights(
    seed: Sequence[float],
    *,
    step: float,
    max_shift: float,
    max_asset_weight: float,
    min_asset_weight: float = 0.0,
) -> list[tuple[float, ...]]:
    """
    Enumerate portfolios near a seed portfolio.

    Each asset may move by at most `max_shift`, weights stay on the `step` grid,
    weights sum to 1, and per-asset min/max limits are enforced.
    """
    total_units = round(1.0 / step)
    seed_units = [round(weight / step) for weight in seed]
    max_shift_units = round(max_shift / step)
    min_units = round(min_asset_weight / step)
    max_units = round(max_asset_weight / step)

    candidates: list[tuple[int, ...]] = []

    def recurse(position: int, remaining_units: int, current: list[int]) -> None:
        assets_left = len(seed_units) - position - 1
        seed_unit = seed_units[position]

        lower = max(
            min_units,
            seed_unit - max_shift_units,
            remaining_units - assets_left * max_units,
        )
        upper = min(
            max_units,
            seed_unit + max_shift_units,
            remaining_units - assets_left * min_units,
        )

        if position == len(seed_units) - 1:
            if lower <= remaining_units <= upper:
                current.append(remaining_units)
                candidates.append(tuple(current))
                current.pop()
            return

        for units in range(lower, upper + 1):
            current.append(units)
            recurse(position + 1, remaining_units - units, current)
            current.pop()

    recurse(0, total_units, [])
    return [tuple(units * step for units in weights) for weights in candidates]


def build_neighbor_table(
    asset_returns: pd.DataFrame,
    *,
    seed: Sequence[float],
    profile: ClientProfile,
    step: float,
    max_shift: float,
    max_asset_weight: float,
) -> pd.DataFrame:
    neighbors = generate_neighbor_weights(
        seed,
        step=step,
        max_shift=max_shift,
        max_asset_weight=max_asset_weight,
    )

    records = []
    asset_cols = list(asset_returns.columns)
    for weights in neighbors:
        row = {asset: weight for asset, weight in zip(asset_cols, weights)}
        row["weights_tuple"] = tuple(round(weight, 4) for weight in weights)
        row["distance_l1"] = float(sum(abs(a - b) for a, b in zip(weights, seed)))
        row.update(analyze_portfolio(asset_returns, weights, profile))
        records.append(row)

    results = pd.DataFrame(records)
    sort_cols = [
        "meets_all_goals_99pct",
        "meets_target_goal_99pct",
        "meets_drawdown_goal_99pct",
        "rolling_target_hit_rate",
        "annualized_return",
    ]
    return results.sort_values(sort_cols, ascending=False).reset_index(drop=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search for small tweaks around a seed portfolio."
    )
    parser.add_argument(
        "--input",
        default="1 Project - Data.xlsx",
        help="Workbook or CSV containing monthly asset returns.",
    )
    parser.add_argument(
        "--sheet",
        default="FULL DATA",
        help="Sheet containing the five asset return series.",
    )
    parser.add_argument(
        "--seed",
        default="0.30,0.10,0.05,0.25,0.30",
        help="Comma-separated seed weights.",
    )
    parser.add_argument(
        "--step",
        type=float,
        default=0.01,
        help="Search grid increment. Example: 0.01 for 1%% moves.",
    )
    parser.add_argument(
        "--max-shift",
        type=float,
        default=0.10,
        help="Maximum change allowed per asset versus the seed.",
    )
    parser.add_argument(
        "--max-asset-weight",
        type=float,
        default=0.30,
        help="Per-asset cap during the neighborhood search.",
    )
    parser.add_argument(
        "--output",
        default="portfolio_neighbor_results.csv",
        help="Where to write the neighborhood-search results.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=15,
        help="How many top rows to print.",
    )
    return parser.parse_args()


def parse_seed(seed_text: str) -> tuple[float, ...]:
    weights = tuple(float(part.strip()) for part in seed_text.split(","))
    if len(weights) != 5:
        raise ValueError("Expected exactly 5 seed weights.")
    if round(sum(weights), 6) != 1.0:
        raise ValueError("Seed weights must sum to 1.0.")
    return weights


def main() -> None:
    args = parse_args()
    seed = parse_seed(args.seed)
    profile = ClientProfile()
    asset_returns = load_asset_returns(args.input, sheet_name=args.sheet)

    results = build_neighbor_table(
        asset_returns,
        seed=seed,
        profile=profile,
        step=args.step,
        max_shift=args.max_shift,
        max_asset_weight=args.max_asset_weight,
    )
    results.to_csv(args.output, index=False)

    cols = [
        "weights_tuple",
        "distance_l1",
        "annualized_return",
        "annualized_volatility",
        "rolling_target_hit_rate",
        "rolling_drawdown_safe_rate",
        "meets_target_goal_99pct",
        "meets_drawdown_goal_99pct",
        "meets_all_goals_99pct",
    ]
    print("Client profile:", asdict(profile))
    print("Seed portfolio:", seed)
    print("Neighbors tested:", len(results))
    print(f"Saved results to {args.output}")
    print()
    print(results.loc[: args.top - 1, cols].to_string(index=False))


if __name__ == "__main__":
    main()
