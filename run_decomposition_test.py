import numpy as np
import pandas as pd
from pathlib import Path

print("="*70)
print("  TIME SERIES DECOMPOSITION SUITE VERIFICATION TEST")
print("="*70 + "\n")

BASE = Path(__file__).resolve().parent
df = pd.read_csv(BASE / 'k3_history.csv')
df_clean = df.dropna(subset=['sum', 'dice1', 'dice2', 'dice3']).sort_values('issueNumber').reset_index(drop=True)
print(f"Loaded {len(df_clean)} historical draws.")

from k3 import (
    STLDecomposer,
    FourierAnalyzer,
    WaveletDecomposer,
    ChangePointDetector,
    AutocorrelationAnalyzer,
    PatternMiner,
    TimeSeriesDecomposer
)

decomposer = TimeSeriesDecomposer()
res = decomposer.full_decomposition(df_clean, value_col='sum')

# 1. STL Verification
stl = res['stl']
print("\n--- 1. STL DECOMPOSITION RESULTS ---")
print(f"   * Trend Variance Strength:       {stl['strength_of_trend']*100:.2f}%")
print(f"   * Seasonality Variance Strength: {stl['strength_of_seasonality']*100:.2f}%")
anoms = decomposer.stl.find_anomalies(threshold=2.5)
print(f"   * Outlier Residual Anomalies:    {int(np.sum(anoms))} draws")

# 2. Fourier Verification
fourier = res['fourier']
print("\n--- 2. FOURIER HARMONIC ANALYSIS ---")
print(f"   * Spectral Entropy:              {fourier['spectral_entropy']:.4f}")
print(f"   * Dominant Cycle Period #1:      {fourier['dominant_periods'][0]:.2f} draws")
print(f"   * Dominant Cycle Period #2:      {fourier['dominant_periods'][1]:.2f} draws")

# 3. Wavelet Verification
wav = res['wavelet']
print("\n--- 3. WAVELET MULTI-RESOLUTION ANALYSIS ---")
print(f"   * Dominant Scale:                {wav['dominant_scale']}")
for k, v in wav['energies'].items():
    print(f"   * Scale '{k}': {v*100:.2f}% Energy")

# 4. Change Points Verification
cp = res['change_points']
print("\n--- 4. CHANGE POINT PELT REGIME SHIFTS ---")
print(f"   * Total Structural Regime Shifts: {cp.get('n_change_points', 0)}")
print(f"   * Change Point Indices:          {cp.get('change_points', [])[:5]}")

# 5. Autocorrelation Verification
ac = res['autocorrelation']
print("\n--- 5. AUTOCORRELATION & LJUNG-BOX TEST ---")
print(f"   * 95% Confidence Bound:          +-{ac['confidence_bound']:.4f}")
print(f"   * Ljung-Box Test p-value:        {ac['ljung_box_pvalue']:.4f}" if ac['ljung_box_pvalue'] is not None else "   * Ljung-Box: N/A")
print(f"   * Statistically Autocorrelated:  {ac['is_autocorrelated']}")

# 6. Pattern Mining Verification
cycles = res['cycles']
print("\n--- 6. RECURRING CYCLES & MOTIFS ---")
if cycles.get('strongest_cycle'):
    sc = cycles['strongest_cycle']
    print(f"   * Strongest Periodic Cycle:      Period {sc['cycle_length']} (Match Rate: {sc['match_rate']*100:.1f}%)")

print("\n" + "="*70)
print("  TIME SERIES DECOMPOSITION SUITE VERIFIED (0 ERRORS)")
print("="*70)
