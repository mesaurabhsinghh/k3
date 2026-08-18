import pandas as pd
from pathlib import Path
from k3 import run_backtest_and_ensemble

BASE = Path(__file__).resolve().parent
csv_path = BASE / 'k3_history.csv'

# Load your data
df = pd.read_csv(csv_path)

# Run complete pipeline
results, prediction = run_backtest_and_ensemble(df)
