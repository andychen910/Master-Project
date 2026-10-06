# Data preparation

Run from any directory with Python, pandas, and numpy installed:

```sh
python3 data_prep/prepare_data.py
```

The script reads the March 2026 FRED-QD vintage and the seven FHFA state HPI
files in `dataset/`. It skips the two FRED-QD metadata rows, reads each chosen
series' transformation code, and writes both original and transformed series.
FHFA indices are converted to quarterly log growth. National data are merged
onto each state's quarterly row, and a `covid` indicator starts at 2020 Q1.

Outputs are written to `data_prep/output/`:

- `national_quarterly.csv`: one row per quarter for the national baseline.
- `state_panel_long.csv`: one row per state and quarter. Use `hpi_log_growth`
  as the state-level outcome; national HOUST and PERMIT remain national series
  repeated by quarter for model comparisons, and should not be interpreted as
  state-specific housing activity.
- `data_quality_summary.json`: date coverage, gaps, missing values, and applied
  FRED-QD transformation codes.

The proposal's FRED-QD vintage is March 2026. Confirm the data coverage shown
in the quality summary before finalizing the sample, since the local CSV may
not contain observations through the end date stated in the proposal.
