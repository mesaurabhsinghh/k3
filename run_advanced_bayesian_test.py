import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial.distance import cdist

print("="*70)
print("  ADVANCED BAYESIAN DEEP LEARNING & NON-PARAMETRIC AUDIT SUITE")
print("  (1. VAE  2. Bayesian LSTM  3. GP  4. Bayes Opt  5. HMC)")
print("="*70 + "\n")

df = pd.read_csv(r'c:\k3\k3_history.csv')
df_clean = df.dropna(subset=['sum', 'dice1', 'dice2', 'dice3']).sort_values('issueNumber').reset_index(drop=True)
N = len(df_clean)
print(f"Loaded {N} historical K3 draws.\n")

# 1. Variational Autoencoder Test
print("1. VARIATIONAL AUTOENCODER (VAE) LATENT SPACE TEST:")
raw = []
for _, row in df_clean.iterrows():
    raw.append([
        (float(row['dice1']) - 1.0) / 5.0, (float(row['dice2']) - 1.0) / 5.0, (float(row['dice3']) - 1.0) / 5.0,
        (float(row['sum']) - 3.0) / 15.0, 1.0 if str(row['big_small']).lower() == 'big' else 0.0,
        1.0 if str(row['odd_even']).lower() == 'odd' else 0.0, 0.5
    ])
data_t = torch.tensor(np.nan_to_num(np.array(raw, dtype=np.float32), nan=0.5), dtype=torch.float32)

class K3VAE(nn.Module):
    def __init__(self, input_dim=7, latent_dim=8, hidden_dim=64):
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, hidden_dim//2), nn.ReLU())
        self.fc_mu = nn.Linear(hidden_dim//2, latent_dim)
        self.fc_logvar = nn.Linear(hidden_dim//2, latent_dim)
        self.decoder = nn.Sequential(nn.Linear(latent_dim, hidden_dim//2), nn.ReLU(), nn.Linear(hidden_dim//2, input_dim), nn.Sigmoid())
    def forward(self, x):
        h = self.encoder(x)
        mu, logvar = self.fc_mu(h), torch.clamp(self.fc_logvar(h), -8.0, 4.0)
        std = torch.exp(0.5 * logvar)
        z = mu + torch.randn_like(std) * std
        return self.decoder(z), mu, logvar

vae = K3VAE()
opt = torch.optim.Adam(vae.parameters(), lr=0.003)
for _ in range(15):
    opt.zero_grad()
    recon, mu, logvar = vae(data_t)
    loss = F.mse_loss(recon, data_t) + 0.001 * torch.mean(mu.pow(2) + logvar.exp() - logvar - 1.0)
    loss.backward()
    opt.step()

with torch.no_grad():
    syn = vae.decoder(torch.randn(3, 8)).numpy()
    syn_sums = np.clip(np.round(syn[:, 3] * 15 + 3), 3, 18).astype(int)
print(f"   * VAE Loss: {loss.item():.4f} | Generated 3 Synthetic Sums: {syn_sums.tolist()}\n")

# 2. Gaussian Process Regression Test
print("2. GAUSSIAN PROCESS REGRESSION (RBF KERNEL) TEST:")
X_gp = np.column_stack([
    df_clean['dice1'].values, df_clean['dice2'].values, df_clean['dice3'].values,
    np.roll(df_clean['sum'].values, 1), np.roll(df_clean['sum'].values, 2)
])[5:]
y_gp = df_clean['sum'].values[5:] / 18.0

dists = cdist(X_gp[-50:], X_gp[-50:], metric='sqeuclidean')
K = (1.0**2) * np.exp(-dists / (2.0 * (1.5**2))) + (0.15**2 + 1e-6) * np.eye(50)
K_inv = np.linalg.pinv(K)
X_test = X_gp[-1:]
Ks = (1.0**2) * np.exp(-cdist(X_test, X_gp[-50:], metric='sqeuclidean') / (2.0 * (1.5**2)))
Kss = np.array([[1.0]])
mu_gp = Ks @ K_inv @ y_gp[-50:]
var_gp = np.maximum(1e-6, Kss - Ks @ K_inv @ Ks.T)
print(f"   * GP Forecast Sum: {float(mu_gp[0])*18.0:.2f} +/- {float(np.sqrt(var_gp[0,0]))*18.0:.2f}\n")

# 3. Hamiltonian Monte Carlo Bernoulli Test
print("3. HAMILTONIAN MONTE CARLO (HMC SAMPLING) TEST:")
n_odd = int((df_clean['odd_even'] == 'Odd').sum())
def log_post(theta):
    p = 1.0 / (1.0 + np.exp(-theta[0]))
    return float(n_odd * np.log(p + 1e-10) + (N - n_odd) * np.log(1.0 - p + 1e-10))
def grad_post(theta):
    p = 1.0 / (1.0 + np.exp(-theta[0]))
    return np.array([float(n_odd * (1.0 - p) - (N - n_odd) * p)])

theta = np.zeros(1)
samples = []
for _ in range(300):
    r = np.random.randn(1)
    r_curr = r.copy()
    theta_curr = theta.copy()
    r = r + 0.5 * 0.08 * grad_post(theta)
    for _ in range(9):
        theta = theta + 0.08 * r
        r = r + 0.08 * grad_post(theta)
    theta = theta + 0.08 * r
    r = r + 0.5 * 0.08 * grad_post(theta)
    curr_H = -log_post(theta_curr) + 0.5 * np.sum(r_curr**2)
    prop_H = -log_post(theta) + 0.5 * np.sum(r**2)
    if np.log(np.random.rand() + 1e-12) < (curr_H - prop_H):
        pass
    else:
        theta = theta_curr
    samples.append(theta.copy())

probs_hmc = 1.0 / (1.0 + np.exp(-np.array(samples[100:])[:, 0]))
print(f"   * HMC Posterior Mean P(Odd): {np.mean(probs_hmc)*100:.2f}% | 95% CI: [{np.percentile(probs_hmc, 2.5)*100:.1f}%, {np.percentile(probs_hmc, 97.5)*100:.1f}%]\n")

print("="*70)
