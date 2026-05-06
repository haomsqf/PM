from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd


MONTHS_PER_YEAR = 12


@dataclass(frozen=True)
class ClientProfile:
    initial_wealth: float = 18_000_000.0
    annual_income: float = 200_000.0
    annual_spending_rate: float = 0.02
    horizon_years: int = 5
    target_wealth: float = 23_000_000.0
    max_drawdown_fraction_initial: float = 0.15
    drawdown_confidence: float = 0.99


def _coerce_return_series(series: pd.Series) -> pd.Series:
    """Convert raw percentage-like values to decimal monthly returns."""
    if pd.api.types.is_numeric_dtype(series):
        numeric = pd.to_numeric(series, errors="coerce")
    else:
        cleaned = (
            series.astype(str)
            .str.strip()
            .str.replace("%", "", regex=False)
            .replace({"": np.nan, "nan": np.nan})
        )
        numeric = pd.to_numeric(cleaned, errors="coerce")

    numeric = numeric.astype(float)
    if numeric.abs().max(skipna=True) and numeric.abs().max(skipna=True) > 1.0:
        numeric = numeric / 100.0
    return numeric


def load_asset_returns(
    path: str | Path,
    *,
    sheet_name: str = "Python FULL DATA",
    asset_prefix: str = "Asset ",
) -> pd.DataFrame:
    """
    Load monthly asset returns from the project workbook or a flat file.

    Expected shape for Excel input:
    - first column is a date-like index
    - asset columns are named 'Asset 1', 'Asset 2', ...
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Could not find input file: {path}. "
            "Point this script at the workbook that contains the raw asset returns."
        )

    if path.suffix.lower() in {".xlsx", ".xlsm", ".xls"}:
        frame = _load_asset_returns_from_excel(
            path,
            sheet_name=sheet_name,
            asset_prefix=asset_prefix,
        )
    elif path.suffix.lower() == ".csv":
        frame = pd.read_csv(path, index_col=0)
    else:
        raise ValueError(f"Unsupported input format: {path.suffix}")

    asset_columns = [c for c in frame.columns if str(c).startswith(asset_prefix)]
    if not asset_columns:
        raise ValueError(
            f"No columns starting with '{asset_prefix}' were found in {path}."
        )

    asset_returns = frame[asset_columns].copy()
    asset_returns.index = pd.to_datetime(asset_returns.index, errors="coerce")

    for column in asset_returns.columns:
        asset_returns[column] = _coerce_return_series(asset_returns[column])

    asset_returns = asset_returns.dropna(how="all").dropna(axis=0, how="any")
    if asset_returns.empty:
        raise ValueError("No usable monthly asset return rows were loaded.")

    return asset_returns


def _load_asset_returns_from_excel(
    path: Path,
    *,
    sheet_name: str,
    asset_prefix: str,
) -> pd.DataFrame:
    """Load asset returns from Excel, handling workbook layouts with leading blank rows."""
    workbook = pd.ExcelFile(path)
    candidate_sheets = [sheet_name]
    if sheet_name not in workbook.sheet_names:
        aliases = {
            "Python FULL DATA": ["FULL DATA"],
            "FULL DATA": ["Python FULL DATA"],
        }
        candidate_sheets.extend(aliases.get(sheet_name, []))
        candidate_sheets.extend(
            sheet for sheet in workbook.sheet_names if "FULL DATA" in sheet.upper()
        )

    tried = []
    for candidate in candidate_sheets:
        if candidate not in workbook.sheet_names or candidate in tried:
            continue
        tried.append(candidate)
        raw = pd.read_excel(path, sheet_name=candidate, header=None)
        header_row = _find_asset_header_row(raw, asset_prefix=asset_prefix)
        if header_row is None:
            continue

        header = raw.iloc[header_row].tolist()
        asset_slice = _asset_block_slice(header, asset_prefix=asset_prefix)
        if asset_slice is None:
            continue

        selected_columns = [0, *range(asset_slice.start, asset_slice.stop)]
        frame = raw.iloc[header_row + 1 :, selected_columns].copy()
        frame.columns = ["Date", *header[asset_slice.start : asset_slice.stop]]
        first_col = frame.columns[0]
        frame = frame.rename(columns={first_col: "Date"}).dropna(subset=["Date"])
        frame = frame.set_index("Date")
        return frame

    available = ", ".join(workbook.sheet_names)
    raise ValueError(
        f"Could not locate an asset-return table in workbook {path}. "
        f"Requested sheet '{sheet_name}'. Available sheets: {available}."
    )


def _find_asset_header_row(raw: pd.DataFrame, *, asset_prefix: str) -> int | None:
    for i in range(len(raw)):
        row_values = raw.iloc[i].tolist()
        asset_count = sum(
            isinstance(value, str) and value.startswith(asset_prefix)
            for value in row_values
        )
        if asset_count >= 2:
            return i
    return None


def _asset_block_slice(
    header_row: Sequence[object],
    *,
    asset_prefix: str,
) -> slice | None:
    asset_positions = [
        i
        for i, value in enumerate(header_row)
        if isinstance(value, str) and value.startswith(asset_prefix)
    ]
    if not asset_positions:
        return None

    start = asset_positions[0]
    stop = start
    while stop < len(header_row):
        value = header_row[stop]
        if not (isinstance(value, str) and value.startswith(asset_prefix)):
            break
        stop += 1
    return slice(start, stop)


def required_annual_return(profile: ClientProfile) -> float:
    """Solve the annual return needed to reach target wealth over the horizon."""

    def terminal_wealth(annual_return: float) -> float:
        wealth = profile.initial_wealth
        for _ in range(profile.horizon_years):
            wealth = (
                wealth * (1.0 + annual_return - profile.annual_spending_rate)
                + profile.annual_income
            )
        return wealth

    lo, hi = -0.99, 1.00
    for _ in range(100):
        mid = (lo + hi) / 2.0
        if terminal_wealth(mid) < profile.target_wealth:
            lo = mid
        else:
            hi = mid
    return hi


def enumerate_weight_tuples(
    n_assets: int,
    *,
    step: float = 0.05,
    max_asset_weight: float = 0.30,
    min_asset_weight: float = 0.0,
    total_weight: float = 1.0,
) -> list[tuple[float, ...]]:
    """Enumerate all feasible long-only portfolios on a fixed weight grid."""
    total_units = int(round(total_weight / step))
    max_units = int(round(max_asset_weight / step))
    min_units = int(round(min_asset_weight / step))
    solutions: list[tuple[int, ...]] = []

    def recurse(position: int, remaining_units: int, current: list[int]) -> None:
        assets_left = n_assets - position - 1
        if position == n_assets - 1:
            if min_units <= remaining_units <= max_units:
                current.append(remaining_units)
                solutions.append(tuple(current))
                current.pop()
            return

        lower = max(min_units, remaining_units - assets_left * max_units)
        upper = min(max_units, remaining_units - assets_left * min_units)
        for units in range(lower, upper + 1):
            current.append(units)
            recurse(position + 1, remaining_units - units, current)
            current.pop()

    recurse(0, total_units, [])
    return [tuple(units * step for units in weights) for weights in solutions]


def simulate_wealth_path(
    portfolio_returns: pd.Series, profile: ClientProfile
) -> pd.DataFrame:
    monthly_income = profile.annual_income / MONTHS_PER_YEAR
    monthly_spend_rate = profile.annual_spending_rate / MONTHS_PER_YEAR

    wealth = profile.initial_wealth
    peak = wealth
    rows = []

    for date, monthly_return in portfolio_returns.items():
        monthly_return = float(monthly_return)
        wealth = wealth * (1.0 + monthly_return) + monthly_income - wealth * monthly_spend_rate
        peak = max(peak, wealth)

        drawdown_dollars = wealth - peak
        rows.append(
            {
                "date": date,
                "portfolio_return": monthly_return,
                "wealth": wealth,
                "peak_wealth": peak,
                "drawdown_dollars": drawdown_dollars,
                "drawdown_pct_peak": wealth / peak - 1.0,
                "drawdown_pct_initial": drawdown_dollars / profile.initial_wealth,
            }
        )

    return pd.DataFrame(rows).set_index("date")


def annualized_return(monthly_returns: pd.Series) -> float:
    compounded = (1.0 + monthly_returns).prod()
    return compounded ** (MONTHS_PER_YEAR / len(monthly_returns)) - 1.0


def annualized_volatility(monthly_returns: pd.Series) -> float:
    if len(monthly_returns) < 2:
        return np.nan
    return monthly_returns.std(ddof=1) * np.sqrt(MONTHS_PER_YEAR)


def summarize_rolling_windows(
    portfolio_returns: pd.Series,
    profile: ClientProfile,
) -> dict[str, float]:
    window = profile.horizon_years * MONTHS_PER_YEAR
    if len(portfolio_returns) < window:
        raise ValueError(
            f"Need at least {window} monthly observations for a {profile.horizon_years}-year study; "
            f"received {len(portfolio_returns)}."
        )

    ending_wealths = []
    max_drawdowns_initial = []
    target_hits = []
    drawdown_hits = []

    for start in range(0, len(portfolio_returns) - window + 1):
        window_returns = portfolio_returns.iloc[start : start + window]
        wealth_path = simulate_wealth_path(window_returns, profile)
        ending_wealth = float(wealth_path["wealth"].iloc[-1])
        max_drawdown_initial = float(wealth_path["drawdown_pct_initial"].min())

        ending_wealths.append(ending_wealth)
        max_drawdowns_initial.append(max_drawdown_initial)
        target_hits.append(ending_wealth >= profile.target_wealth)
        drawdown_hits.append(
            max_drawdown_initial >= -profile.max_drawdown_fraction_initial
        )

    return {
        "rolling_windows": float(len(ending_wealths)),
        "rolling_mean_terminal_wealth": float(np.mean(ending_wealths)),
        "rolling_median_terminal_wealth": float(np.median(ending_wealths)),
        "rolling_worst_terminal_wealth": float(np.min(ending_wealths)),
        "rolling_best_terminal_wealth": float(np.max(ending_wealths)),
        "rolling_target_hit_rate": float(np.mean(target_hits)),
        "rolling_drawdown_safe_rate": float(np.mean(drawdown_hits)),
        "rolling_worst_drawdown_pct_initial": float(np.min(max_drawdowns_initial)),
        "rolling_best_drawdown_pct_initial": float(np.max(max_drawdowns_initial)),
    }


def analyze_portfolio(
    asset_returns: pd.DataFrame,
    weights: Sequence[float],
    profile: ClientProfile,
) -> dict[str, float]:
    weights_array = np.asarray(weights, dtype=float)
    portfolio_returns = asset_returns @ weights_array
    wealth_path = simulate_wealth_path(portfolio_returns, profile)
    required_return = required_annual_return(profile)
    rolling = summarize_rolling_windows(portfolio_returns, profile)

    ann_return = annualized_return(portfolio_returns)
    ann_vol = annualized_volatility(portfolio_returns)
    empirical_monthly_var_99 = -float(np.quantile(portfolio_returns, 0.01))

    row: dict[str, float] = {
        "annualized_return": ann_return,
        "annualized_volatility": ann_vol,
        "sharpe_zero_rf": ann_return / ann_vol if ann_vol else np.nan,
        "required_annual_return": required_return,
        "full_history_terminal_wealth": float(wealth_path["wealth"].iloc[-1]),
        "full_history_max_drawdown_pct_peak": float(
            wealth_path["drawdown_pct_peak"].min()
        ),
        "full_history_max_drawdown_pct_initial": float(
            wealth_path["drawdown_pct_initial"].min()
        ),
        "monthly_var_99_empirical": empirical_monthly_var_99,
        "meets_return_goal_average": float(ann_return >= required_return),
    }
    row.update(rolling)
    row["meets_target_goal_99pct"] = float(
        row["rolling_target_hit_rate"] >= profile.drawdown_confidence
    )
    row["meets_drawdown_goal_99pct"] = float(
        row["rolling_drawdown_safe_rate"] >= profile.drawdown_confidence
    )
    row["meets_all_goals_99pct"] = float(
        row["meets_target_goal_99pct"] and row["meets_drawdown_goal_99pct"]
    )
    return row


def build_results_table(
    asset_returns: pd.DataFrame,
    profile: ClientProfile,
    *,
    step: float,
    max_asset_weight: float,
    min_asset_weight: float = 0.0,
) -> pd.DataFrame:
    weight_tuples = enumerate_weight_tuples(
        asset_returns.shape[1],
        step=step,
        max_asset_weight=max_asset_weight,
        min_asset_weight=min_asset_weight,
    )

    records = []
    asset_columns = list(asset_returns.columns)
    for weights in weight_tuples:
        record = {asset: weight for asset, weight in zip(asset_columns, weights)}
        record["weights_tuple"] = tuple(round(weight, 4) for weight in weights)
        record.update(analyze_portfolio(asset_returns, weights, profile))
        records.append(record)

    results = pd.DataFrame(records)
    sort_columns = [
        "meets_all_goals_99pct",
        "meets_drawdown_goal_99pct",
        "rolling_target_hit_rate",
        "rolling_drawdown_safe_rate",
        "annualized_return",
    ]
    return results.sort_values(sort_columns, ascending=False).reset_index(drop=True)


def _format_weight_tuple(weights: Iterable[float]) -> str:
    return "(" + ", ".join(f"{100 * weight:.0f}%" for weight in weights) + ")"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enumerate portfolio weights and evaluate them against client goals."
    )
    parser.add_argument(
        "--input",
        default="1 Project - Data.xlsx",
        help="Workbook or CSV containing monthly asset returns.",
    )
    parser.add_argument(
        "--sheet",
        default="Python FULL DATA",
        help="Excel sheet name containing the five asset return series.",
    )
    parser.add_argument(
        "--step",
        type=float,
        default=0.05,
        help="Weight increment size. Example: 0.05 for 5%% steps.",
    )
    parser.add_argument(
        "--max-asset-weight",
        type=float,
        default=0.30,
        help="Maximum allowed weight in a single asset.",
    )
    parser.add_argument(
        "--output",
        default="portfolio_enumeration_results.csv",
        help="Where to write the analysis table.",
    )
    parser.add_argument(
        "--enumerate-only",
        action="store_true",
        help="Only generate feasible weight tuples; skip historical analysis.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="How many top portfolios to print in the terminal summary.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    profile = ClientProfile()

    if args.enumerate_only:
        tuples = enumerate_weight_tuples(
            n_assets=5,
            step=args.step,
            max_asset_weight=args.max_asset_weight,
        )
        weights_frame = pd.DataFrame(
            {
                "weights_tuple": [tuple(round(weight, 4) for weight in weights) for weights in tuples],
                "weights_pretty": [_format_weight_tuple(weights) for weights in tuples],
            }
        )
        weights_frame.to_csv(args.output, index=False)
        print(f"Enumerated {len(tuples)} feasible portfolios.")
        print(f"Saved tuples to {args.output}")
        return

    asset_returns = load_asset_returns(args.input, sheet_name=args.sheet)
    results = build_results_table(
        asset_returns,
        profile,
        step=args.step,
        max_asset_weight=args.max_asset_weight,
    )
    results.to_csv(args.output, index=False)

    goal_columns = [
        "weights_tuple",
        "annualized_return",
        "annualized_volatility",
        "rolling_target_hit_rate",
        "rolling_drawdown_safe_rate",
        "meets_all_goals_99pct",
    ]
    print("Client profile:", asdict(profile))
    print(f"Required annual return: {required_annual_return(profile):.2%}")
    print(f"Enumerated portfolios: {len(results)}")
    print(f"Saved results to {args.output}")
    print()
    print(results.loc[: args.top - 1, goal_columns].to_string(index=False))


if __name__ == "__main__":
    main()
