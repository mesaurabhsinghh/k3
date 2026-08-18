import pandas as pd
import numpy as np
from scipy import stats
from scipy.special import gammaln

df = pd.read_csv(r'c:\k3\k3_history.csv')
d1 = pd.to_numeric(df['dice1'], errors='coerce').dropna().values.astype(int)
d2 = pd.to_numeric(df['dice2'], errors='coerce').dropna().values.astype(int)
d3 = pd.to_numeric(df['dice3'], errors='coerce').dropna().values.astype(int)
sums = pd.to_numeric(df['sum'], errors='coerce').dropna().values.astype(int)
bs = (df['big_small'] == 'Big').astype(int).values
oe = (df['odd_even'] == 'Odd').astype(int).values
N = len(sums)

print("="*65)
print(f"  BAYESIAN INFERENCE & BAYES FACTOR AUDIT (N = {N} DRAWS)")
print("="*65 + "\n")

def bayes_factor_binomial(successes, trials, null_prob=0.5, a0=1.0, b0=1.0):
    failures = trials - successes
    log_lik_h0 = successes * np.log(null_prob) + failures * np.log(1.0 - null_prob)
    log_marginal_h1 = (gammaln(a0 + successes) + gammaln(b0 + failures) - 
                       gammaln(a0 + b0 + trials) + gammaln(a0 + b0) - 
                       gammaln(a0) - gammaln(b0))
    log_bf = log_marginal_h1 - log_lik_h0
    return float(np.exp(np.clip(log_bf, -50, 50))), float(log_bf)

# 1. Big vs Small
n_big = int(np.sum(bs))
bf_bs, log_bf_bs = bayes_factor_binomial(n_big, N, null_prob=0.5)
ci_bs_low = stats.beta.ppf(0.025, 1 + n_big, 1 + (N - n_big))
ci_bs_high = stats.beta.ppf(0.975, 1 + n_big, 1 + (N - n_big))
print("1. BIG / SMALL BAYESIAN POSTERIOR ESTIMATION:")
print(f"   * Posterior Mean: {((1 + n_big)/(2 + N))*100:.2f}%")
print(f"   * 95% Credible Interval: [{ci_bs_low*100:.2f}%, {ci_bs_high*100:.2f}%]")
print(f"   * Bayes Factor (H1/H0): {bf_bs:.4f} -> {'Evidence for Fairness (H0)' if bf_bs < 1.0 else 'Evidence for Bias (H1)'}\n")

# 2. Odd vs Even
n_odd = int(np.sum(oe))
bf_oe, log_bf_oe = bayes_factor_binomial(n_odd, N, null_prob=0.5)
ci_oe_low = stats.beta.ppf(0.025, 1 + n_odd, 1 + (N - n_odd))
ci_oe_high = stats.beta.ppf(0.975, 1 + n_odd, 1 + (N - n_odd))
print("2. ODD / EVEN BAYESIAN POSTERIOR ESTIMATION:")
print(f"   * Posterior Mean: {((1 + n_odd)/(2 + N))*100:.2f}%")
print(f"   * 95% Credible Interval: [{ci_oe_low*100:.2f}%, {ci_oe_high*100:.2f}%]")
print(f"   * Bayes Factor (H1/H0): {bf_oe:.4f} -> {'Evidence for Fairness (H0)' if bf_oe < 1.0 else 'Evidence for Bias (H1)'}\n")

# 3. Dice 3 Face 3 Anomaly
d3_eq_3 = int(np.sum(d3 == 3))
bf_d3, log_bf_d3 = bayes_factor_binomial(d3_eq_3, N, null_prob=1/6.0)
print("3. DICE 3 FACE 3 ANOMALY CHECK (Null: 1/6 = 16.67%):")
print(f"   * Observed Rate: {d3_eq_3}/{N} = {d3_eq_3/N*100:.2f}%")
print(f"   * Bayes Factor: {bf_d3:.4f} -> {'Evidence for Fairness (H0)' if bf_d3 < 1.0 else 'Evidence for Bias (H1)'}\n")

print("="*65)
