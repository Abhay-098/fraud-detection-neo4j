"""Download PaySim through Kaggle Hub.

This requires internet access and, depending on Kaggle's current authentication
requirements, a Kaggle account/token.

If this does not work, download the dataset manually from:
https://www.kaggle.com/datasets/ealaxi/paysim1
"""
from pathlib import Path

OUT = Path("data/raw")
OUT.mkdir(parents=True, exist_ok=True)

try:
    import kagglehub
except ImportError as exc:
    raise SystemExit("Install requirements.txt first: pip install -r requirements.txt") from exc

path = kagglehub.dataset_download("ealaxi/paysim1")
print("Downloaded dataset directory:", path)
print("Copy PS_20174392719_1491204439457_log.csv into data/raw/")
