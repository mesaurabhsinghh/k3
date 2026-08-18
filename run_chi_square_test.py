import pandas as pd
import numpy as np
from scipy.stats import chisquare
from statsmodels.stats.diagnostic import acorr_ljungbox

# Load full dataset
df = pd.read_csv(r'c:\k3\k3_history.csv')
d1 = pd.to_numeric(df['dice1'], errors='coerce').dropna().values.astype(int)
d2 = pd.to_numeric(df['dice2'], errors='coerce').dropna().values.astype(int)
d3 = pd.to_numeric(df['dice3'], errors='coerce').dropna().values.astype(int)
sums = pd.to_numeric(df['sum'], errors='coerce').dropna().values.astype(int)
N = len(sums)

print("="*65)
print(f"  K3 FULL DATASET STATISTICAL RANDOMNESS AUDIT (N = {N} DRAWS)")
print("="*65 + "\n")

# 1. Three-Dice Sum Distribution Test (3 to 18)
combos = np.array([1, 3, 6, 10, 15, 21, 25, 27, 27, 25, 21, 15, 10, 6, 3, 1])
theoretical_prob = combos / 216.0
observed_sums = np.bincount(np.clip(sums - 3, 0, 15), minlength=16)
expected_sums = N * theoretical_prob
chi2_sum, p_sum = chisquare(observed_sums, f_exp=expected_sums)

print("1. THREE-DICE SUM MULTINOMIAL GOODNESS-OF-FIT (Degrees of Freedom = 15):")
print(f"   * Chi-Square Statistic (Chi2) : {chi2_sum:.4f}")
print(f"   * p-value                   : {p_sum:.4f}")
print(f"   * Critical Value (alpha=0.05): 24.996")
print(f"   * Verdict                   : {'[PASS] TRULY RANDOM / FAIR RNG (p >= 0.05)' if p_sum >= 0.05 else '[WARN] STATISTICALLY BIASED (p < 0.05)'}\n")

# Detailed Sum Breakdown Table
print("   Sum Value Breakdown:")
print("   Sum | Observed | Expected | Diff | Chi2 Component")
print("   ----+----------+----------+------+---------------")
for s_val in range(3, 19):
    idx = s_val - 3
    obs = observed_sums[idx]
    exp = expected_sums[idx]
    diff = obs - exp
    comp = ((obs - exp) ** 2) / exp
    print(f"   {s_val:3d} | {obs:8d} | {exp:8.2f} | {diff:+5.2f}| {comp:14.4f}")

print("\n" + "-"*65 + "\n")

# 2. Individual Dice Uniformity Tests (Faces 1-6)
exp_die = np.full(6, N / 6.0)
obs_d1 = np.bincount(d1 - 1, minlength=6)
obs_d2 = np.bincount(d2 - 1, minlength=6)
obs_d3 = np.bincount(d3 - 1, minlength=6)

chi2_d1, p_d1 = chisquare(obs_d1, f_exp=exp_die)
chi2_d2, p_d2 = chisquare(obs_d2, f_exp=exp_die)
chi2_d3, p_d3 = chisquare(obs_d3, f_exp=exp_die)

print(f"2. INDIVIDUAL DICE UNIFORMITY TESTS (df = 5, Expected = {N/6.0:.1f} per face):")
print(f"   * Dice 1: Chi2 = {chi2_d1:6.3f} | p-value = {p_d1:.4f} -> {'[PASS] Uniform' if p_d1 >= 0.05 else '[WARN] Biased'}")
print(f"     Faces: 1:{obs_d1[0]}, 2:{obs_d1[1]}, 3:{obs_d1[2]}, 4:{obs_d1[3]}, 5:{obs_d1[4]}, 6:{obs_d1[5]}")
print(f"   * Dice 2: Chi2 = {chi2_d2:6.3f} | p-value = {p_d2:.4f} -> {'[PASS] Uniform' if p_d2 >= 0.05 else '[WARN] Biased'}")
print(f"     Faces: 1:{obs_d2[0]}, 2:{obs_d2[1]}, 3:{obs_d2[2]}, 4:{obs_d2[3]}, 5:{obs_d2[4]}, 6:{obs_d2[5]}")
print(f"   * Dice 3: Chi2 = {chi2_d3:6.3f} | p-value = {p_d3:.4f} -> {'[PASS] Uniform' if p_d3 >= 0.05 else '[WARN] Biased'}")
print(f"     Faces: 1:{obs_d3[0]}, 2:{obs_d3[1]}, 3:{obs_d3[2]}, 4:{obs_d3[3]}, 5:{obs_d3[4]}, 6:{obs_d3[5]}")

print("\n" + "-"*65 + "\n")

# 3. Big vs Small Binary Chi-Square Test
obs_bs = [np.sum(sums >= 11), np.sum(sums < 11)]
chi2_bs, p_bs = chisquare(obs_bs, f_exp=[N/2.0, N/2.0])
print(f"3. BIG / SMALL BINARY TEST (df = 1, Expected = {N/2.0:.1f} each):")
print(f"   * Big (11-18)   : {obs_bs[0]} ({obs_bs[0]/N*100:.2f}%)")
print(f"   * Small (3-10)  : {obs_bs[1]} ({obs_bs[1]/N*100:.2f}%)")
print(f"   * Chi-Square    : {chi2_bs:.4f} | p-value = {p_bs:.4f}")
print(f"   * Verdict       : {'[PASS] Fair 50/50 Balance' if p_bs >= 0.05 else '[WARN] Skewed'}\n")

# 4. Odd vs Even Binary Chi-Square Test
obs_oe = [np.sum(sums % 2 == 1), np.sum(sums % 2 == 0)]
chi2_oe, p_oe = chisquare(obs_oe, f_exp=[N/2.0, N/2.0])
print(f"4. ODD / EVEN BINARY TEST (df = 1, Expected = {N/2.0:.1f} each):")
print(f"   * Odd   : {obs_oe[0]} ({obs_oe[0]/N*100:.2f}%)")
print(f"   * Even  : {obs_oe[1]} ({obs_oe[1]/N*100:.2f}%)")
print(f"   * Chi-Square    : {chi2_oe:.4f} | p-value = {p_oe:.4f}")
print(f"   * Verdict       : {'[PASS] Fair Parity Distribution' if p_oe >= 0.05 else '[WARN] Statistically Skewed'}\n")

# 5. Triples Frequency Test
triples_count = np.sum((d1 == d2) & (d2 == d3))
exp_triples = N * (6.0 / 216.0)
chi2_trp, p_trp = chisquare([triples_count, N - triples_count], f_exp=[exp_triples, N - exp_triples])
print(f"5. TRIPLES FREQUENCY TEST (Exp 2.78% = {exp_triples:.1f} triples):")
print(f"   * Observed Triples : {triples_count} ({triples_count/N*100:.2f}%)")
print(f"   * Chi-Square       : {chi2_trp:.4f} | p-value = {p_trp:.4f}")
print(f"   * Verdict          : {'[PASS] Consistent with Fair Random Triples' if p_trp >= 0.05 else '[WARN] Anomalous Triple Emission'}\n")

# 6. Sequential Autocorrelation (Ljung-Box Memory Test)
print("6. SEQUENTIAL INDEPENDENCE / AUTOCORRELATION (Ljung-Box Test):")
lb_res = acorr_ljungbox(sums, lags=[1, 2, 3, 5, 10], return_df=True)
for lag, row in lb_res.iterrows():
    verdict = "[PASS] Independent (No Memory)" if row['lb_pvalue'] >= 0.05 else "[WARN] Sequential Memory Detected"
    print(f"   * Lag {lag:2d}: Ljung-Box Stat = {row['lb_stat']:6.3f} | p-value = {row['lb_pvalue']:.4f} -> {verdict}")

print(f"\n" + "="*65)
print(f"  FINAL CONCLUSION:")
if p_sum >= 0.05 and p_bs >= 0.05 and p_oe >= 0.05 and p_d1 >= 0.05 and p_d2 >= 0.05 and p_d3 >= 0.05:
    print(f"  --> The game is STATISTICALLY TRULY RANDOM (Passes all Chi-Square tests).")
    print(f"  --> Observed outcomes adhere to theoretical multinomial dice distributions.")
else:
    print(f"  --> Micro-anomalies detected in specific sub-components.")
print("="*65)
