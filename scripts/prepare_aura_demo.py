from pathlib import Path
import pandas as pd

INPUT = Path("data/processed/paysim_subset.csv")
OUTPUT = Path("data/aura_demo")

df = pd.read_csv(INPUT)

# Keep the cloud demo safely within AuraDB Free limits.
# Keep ALL fraud rows first, then add legitimate transactions.
TARGET = 30000

fraud = df[df["is_fraud"] == 1]
normal = df[df["is_fraud"] == 0]

remaining = max(0, TARGET - len(fraud))

demo = pd.concat(
    [fraud, normal.head(remaining)],
    ignore_index=True
).head(TARGET)

OUTPUT.mkdir(parents=True, exist_ok=True)

# Extra graph entities for deployed demo
demo["device_id"] = [
    f"D{(i % 1000) + 1:05d}"
    for i in range(len(demo))
]

demo["location_id"] = [
    f"L{(i % 100) + 1:03d}"
    for i in range(len(demo))
]

# PaySim merchant destinations start with M.
# Use the real destination ID for merchants.
demo["merchant_id"] = demo["nameDest"].apply(
    lambda x: x if str(x).startswith("M") else ""
)

demo.to_csv(
    OUTPUT / "paysim_aura_demo.csv",
    index=False
)

print(f"Prepared {len(demo):,} rows -> {OUTPUT / 'paysim_aura_demo.csv'}")
print("Fraud:", int(demo["is_fraud"].sum()))
print("Non-fraud:", int((demo["is_fraud"] == 0).sum()))