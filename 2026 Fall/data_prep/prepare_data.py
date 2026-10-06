#!/usr/bin/env python3
"""Prepare the proposal's national quarterly series and state HPI panel."""

from pathlib import Path
import json

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "dataset"
OUT = Path(__file__).resolve().parent / "output"
OUT.mkdir(parents=True, exist_ok=True)

FRED_FILE = DATA / "2026-03-QD.csv"
STATE_FILES = {
    "AZ": "AZSTHPI.csv",
    "CA": "CASTHPI.csv",
    "FL": "FLSTHPI.csv",
    "IL": "ILSTHPI.csv",
    "NY": "NYSTHPI.csv",
    "OH": "OHSTHPI.csv",
    "TX": "TXSTHPI.csv",
}
FRED_COLUMNS = ["CPIAUCSL", "FEDFUNDS", "GS10", "HOUST", "PERMIT", "PAYEMS"]


def quarter_period(values):
    dates = pd.to_datetime(values, errors="coerce")
    return dates.dt.to_period("Q")


def fred_transform(series, code):
    """Apply the official FRED-QD transformation code to a numeric series."""
    if code == 1:
        return series
    if code == 2:
        return series.diff()
    if code == 3:
        return series.diff().diff()
    if code == 4:
        return series.apply(lambda x: x**2).diff()
    if code == 5:
        return series.apply(lambda x: pd.NA if x <= 0 else __import__("math").log(x)).diff()
    if code == 6:
        logged = series.apply(lambda x: pd.NA if x <= 0 else __import__("math").log(x))
        return logged.diff().diff()
    if code == 7:
        return series.pct_change()
    raise ValueError(f"Unsupported FRED-QD transformation code: {code}")


def read_fred():
    raw = pd.read_csv(FRED_FILE, low_memory=False)
    # FRED-QD files include factors and transform metadata as their first two records.
    transform_codes = raw.iloc[1].to_dict()
    observations = raw.iloc[2:].copy()
    observations["quarter"] = quarter_period(observations["sasdate"])
    records = observations.dropna(subset=["quarter"]).set_index("quarter")

    missing_columns = [name for name in FRED_COLUMNS if name not in records.columns]
    if missing_columns:
        raise ValueError(f"Missing FRED-QD columns: {missing_columns}")

    result = pd.DataFrame(index=records.index)
    used_codes = {}
    for name in FRED_COLUMNS:
        result[name] = pd.to_numeric(records[name], errors="coerce")
        try:
            code = int(float(transform_codes[name]))
        except (TypeError, ValueError):
            raise ValueError(f"Could not read transform code for {name}")
        used_codes[name] = code
        result[f"{name}_transformed"] = fred_transform(result[name], code)
    result.index.name = "quarter"
    return result.reset_index(), used_codes


def read_state_panel():
    frames = []
    for state, filename in STATE_FILES.items():
        path = DATA / filename
        raw = pd.read_csv(path)
        expected = f"{state}STHPI"
        if expected not in raw.columns:
            raise ValueError(f"{filename} is missing expected column {expected}")
        frame = raw.rename(columns={"observation_date": "date", expected: "hpi"})
        frame["quarter"] = quarter_period(frame["date"])
        frame["state"] = state
        frame["hpi"] = pd.to_numeric(frame["hpi"], errors="coerce")
        frame = frame.dropna(subset=["quarter", "hpi"])
        frame = frame.sort_values("quarter")
        frame["hpi_log_growth"] = frame.groupby("state")["hpi"].transform(
            lambda values: __import__("numpy").log(values).diff()
        )
        frames.append(frame[["state", "quarter", "date", "hpi", "hpi_log_growth"]])
    return pd.concat(frames, ignore_index=True).sort_values(["state", "quarter"])


def main():
    national, transform_codes = read_fred()
    panel = read_state_panel()

    # Macroeconomic data repeats across states by quarter, as required for the
    # proposal's state interaction and fixed-effects models.
    panel = panel.merge(national, on="quarter", how="left", validate="many_to_one")
    panel["covid"] = (panel["quarter"] >= pd.Period("2020Q1", freq="Q")).astype(int)

    national.to_csv(OUT / "national_quarterly.csv", index=False)
    panel.to_csv(OUT / "state_panel_long.csv", index=False)

    expected_states = set(STATE_FILES)
    per_state_counts = panel.groupby("state").agg(
        observations=("quarter", "size"),
        first_quarter=("quarter", "min"),
        last_quarter=("quarter", "max"),
        missing_macro_quarters=("CPIAUCSL", lambda values: int(values.isna().sum())),
        missing_hpi_growth=("hpi_log_growth", lambda values: int(values.isna().sum())),
    )
    summary = {
        "fred_source": FRED_FILE.name,
        "fred_transform_codes": transform_codes,
        "national_rows": int(len(national)),
        "national_first_quarter": str(national["quarter"].min()),
        "national_last_quarter": str(national["quarter"].max()),
        "panel_rows": int(len(panel)),
        "panel_states": sorted(panel["state"].unique().tolist()),
        "all_expected_states_present": expected_states.issubset(set(panel["state"].unique())),
        "duplicate_state_quarters": int(panel.duplicated(["state", "quarter"]).sum()),
        "quarter_gaps_by_state": {},
        "state_summary": {},
    }
    for state, group in panel.groupby("state"):
        quarters = group["quarter"].sort_values().drop_duplicates()
        continuous = pd.period_range(quarters.min(), quarters.max(), freq="Q")
        summary["quarter_gaps_by_state"][state] = [str(q) for q in continuous.difference(quarters)]
    for state, row in per_state_counts.iterrows():
        summary["state_summary"][state] = {
            "observations": int(row["observations"]),
            "first_quarter": str(row["first_quarter"]),
            "last_quarter": str(row["last_quarter"]),
            "missing_macro_quarters": int(row["missing_macro_quarters"]),
            "missing_hpi_growth": int(row["missing_hpi_growth"]),
        }
    (OUT / "data_quality_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    print(f"\nWrote outputs to {OUT}")


if __name__ == "__main__":
    main()
