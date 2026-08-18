import numpy as np
import pandas as pd
from pathlib import Path

print("="*70)
print("  MODEL PERFORMANCE TRACKER & BACKTESTING ENGINE TEST")
print("="*70 + "\n")

BASE = Path(__file__).resolve().parent
df = pd.read_csv(BASE / 'k3_history.csv').dropna(subset=['sum', 'dice1', 'dice2', 'dice3'])

from k3 import ModelPerformanceTracker, BacktestingEngine

tracker = ModelPerformanceTracker(storage_path=BASE / 'test_performance_log.json')

# 1. Log predictions
print("--- 1. LOGGING PREDICTIONS ---")
tracker.log_prediction('BNN', '20260818101010656', {'dice1': 3, 'dice2': 4, 'dice3': 4, 'sum': 11, 'bs_pred': 'Big', 'oe_pred': 'Odd'}, confidence=0.75)
tracker.log_prediction('Bayesian', '20260818101010656', {'dice1': 1, 'dice2': 2, 'dice3': 3, 'sum': 6, 'bs_pred': 'Small', 'oe_pred': 'Even'}, confidence=0.60)
tracker.log_prediction('BNN', '20260818101010657', {'dice1': 2, 'dice2': 3, 'dice3': 4, 'sum': 9, 'bs_pred': 'Small', 'oe_pred': 'Odd'}, confidence=0.82)
print("   * 3 predictions logged across BNN and Bayesian.")

# 2. Validate predictions
print("\n--- 2. VALIDATING OUTCOMES ---")
tracker.validate_prediction('BNN', '20260818101010656', {'dice1': 3, 'dice2': 4, 'dice3': 4, 'sum': 11, 'bs': 'Big', 'oe': 'Odd'})
tracker.validate_prediction('Bayesian', '20260818101010656', {'dice1': 3, 'dice2': 4, 'dice3': 4, 'sum': 11, 'bs': 'Big', 'oe': 'Odd'})
tracker.validate_prediction('BNN', '20260818101010657', {'dice1': 2, 'dice2': 3, 'dice3': 4, 'sum': 9, 'bs': 'Small', 'oe': 'Odd'})
print("   * 3 predictions validated against ground truth.")

# 3. Calculate metrics
print("\n--- 3. CALCULATING METRICS ---")
bnn_metrics = tracker.calculate_metrics('BNN')
print(f"   * BNN Total Predictions: {bnn_metrics['total_predictions']}")
print(f"   * BNN Validated:         {bnn_metrics['validated_predictions']}")
print(f"   * BNN Big/Small Acc:     {bnn_metrics['bs_accuracy']*100:.1f}%")
print(f"   * BNN Exact Match Rate:  {bnn_metrics['exact_match_rate']*100:.1f}%")

# 4. Generate report
print("\n--- 4. GENERATING REPORT ---")
report = tracker.generate_report('BNN')
print(report.encode('ascii', errors='replace').decode('ascii'))

# 5. Compare models
print("--- 5. COMPARING MODELS ---")
comp = tracker.compare_models()
for m, dat in comp.items():
    print(f"   * Model '{m}': BS Acc={dat['bs_accuracy']*100:.1f}%, Exact={dat['exact_match']*100:.1f}%")

# 6. Backtesting Engine
print("\n--- 6. BACKTESTING ENGINE ---")
model_funcs = {
    'Mean_Baseline': lambda d: {'sum': int(d['sum'].mean()), 'bs_pred': 'Big' if d['sum'].mean() >= 11 else 'Small', 'oe_pred': 'Odd', 'dice1': 3, 'dice2': 4, 'dice3': 4},
    'Median_Baseline': lambda d: {'sum': int(d['sum'].median()), 'bs_pred': 'Big' if d['sum'].median() >= 11 else 'Small', 'oe_pred': 'Even', 'dice1': 2, 'dice2': 3, 'dice3': 4}
}
engine = BacktestingEngine(model_funcs, df.head(60))
results = engine.run_backtest(lookback=20, step=2)
print(f"   * Backtested {len(results)} out-of-sample predictions.")
bt_metrics = engine.calculate_backtest_metrics()
for m, dat in bt_metrics.items():
    print(f"   * Backtest '{m}': Total={dat['total_predictions']}, BS Acc={dat['bs_accuracy']*100:.1f}%, Sum Acc={dat['sum_accuracy']*100:.1f}%")

print("\n" + "="*70)
print("  MODEL PERFORMANCE TRACKER & BACKTESTING ENGINE VERIFIED (0 ERRORS)")
print("="*70)
