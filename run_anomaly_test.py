import numpy as np
import pandas as pd
from datetime import datetime
from collections import deque
from scipy import stats

print("="*70)
print("  REAL-TIME ANOMALY DETECTION ENGINE & STATISTICAL SURVEILLANCE TEST")
print("="*70 + "\n")

df = pd.read_csv(r'c:\k3\k3_history.csv')
df_clean = df.dropna(subset=['sum', 'dice1', 'dice2', 'dice3']).sort_values('issueNumber').reset_index(drop=True)
print(f"Loaded {len(df_clean)} historical draws.")

from k3 import AnomalyDetectionEngine

engine = AnomalyDetectionEngine(window_size=100)
for _, r in df_clean.iterrows():
    engine.process_new_draw(
        issue_number=str(r['issueNumber']),
        dice1=float(r['dice1']), dice2=float(r['dice2']), dice3=float(r['dice3']),
        sum_val=float(r['sum']), bs=str(r['big_small']), oe=str(r['odd_even']),
        premium=str(r.get('premium', f"{int(float(r['dice1']))}{int(float(r['dice2']))}{int(float(r['dice3']))}"))
    )

stats_data = engine.get_statistics()
print("\n--- SURVEILLANCE ENGINE STATISTICS ---")
print(f"   * Total Draws Audited: {stats_data['total_checks']}")
print(f"   * Anomalies Flagged: {stats_data['anomalies_detected']}")
print(f"   * Critical Severity Alerts: {stats_data['critical_alerts']}")
print(f"   * Anomaly Rate: {(stats_data['anomalies_detected']/max(1, stats_data['total_checks'])*100):.2f}%")

recent_alerts = engine.get_recent_alerts(5)
print(f"\n--- RECENT ANOMALY ALERTS ({len(recent_alerts)} samples) ---")
for a in recent_alerts:
    print(f"   - Issue #{a['issue_number']} [{a['severity']}]: {[x.get('explanation', '') for x in a['all_alerts']]}")

print("\n" + "="*70)
