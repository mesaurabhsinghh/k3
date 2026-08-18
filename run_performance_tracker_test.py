import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

print("="*70)
print("  WALK-FORWARD MODEL PERFORMANCE TRACKER & METRICS AUDIT TEST")
print("="*70 + "\n")

BASE = Path(__file__).resolve().parent
df = pd.read_csv(BASE / 'k3_history.csv')
df_clean = df.dropna(subset=['sum', 'dice1', 'dice2', 'dice3']).sort_values('issueNumber').reset_index(drop=True)
print(f"Loaded {len(df_clean)} historical draws.")

from k3 import PredictionLogger, PerformanceMetrics, WalkForwardBacktester, run_nexus_pattern_sniper, run_nexus_k3_triple_threat, run_quantum_temporal_oracle_k3

test_logger = PredictionLogger(storage_path=BASE / 'test_prediction_audit.json')

models = {
    'NEXUS PATTERN SNIPER': run_nexus_pattern_sniper,
    'NEXUS TRIPLE THREAT': run_nexus_k3_triple_threat,
    'QUANTUM TEMPORAL ORACLE': run_quantum_temporal_oracle_k3
}

tester = WalkForwardBacktester(models, test_logger)
print("\nRunning walk-forward backtest (Initial Window = 50, Step = 5)...")
result = tester.run_backtest(df_clean, initial_window=50, step=5)

print("\n--- WALK-FORWARD AUDIT SUMMARY ---")
print(f"   * Total Draws Evaluated: {result['total_draws']}")
for m_name, cnt in result['predictions_made'].items():
    print(f"   * Model '{m_name}': {cnt} predictions validated")

report_df = tester.generate_backtest_report(df_clean, initial_window=50)
print("\n--- BACKTEST PERFORMANCE REPORT ---")
print(report_df.to_string(index=False))

print("\n" + "="*70)
