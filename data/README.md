# Data

## Primary source

PaySim synthetic financial transaction dataset:
https://www.kaggle.com/datasets/ealaxi/paysim1

The public CSV is large (~494 MB), so it is intentionally excluded from the project ZIP.

Expected raw filename:

`PS_20174392719_1491204439457_log.csv`

## Demo data

`data/demo/paysim_demo.csv` is generated locally by `scripts/generate_demo_dataset.py`.

It is only a development fallback and must be labelled as synthetic demo data.

## Processed data

`scripts/prepare_paysim.py` produces:

`data/processed/paysim_subset.csv`

The default project workflow uses a configurable subset (recommended 250,000 rows for the Review 2 demo).
