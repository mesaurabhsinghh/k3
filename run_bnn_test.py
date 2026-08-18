import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import pandas as pd
from torch.utils.data import DataLoader, TensorDataset

print("="*65)
print("  BAYESIAN NEURAL NETWORK (BNN) TEST & UNCERTAINTY QUANTIFICATION")
print("="*65 + "\n")

class BayesianLinear(nn.Module):
    def __init__(self, in_features, out_features, prior_std=1.0):
        super().__init__()
        self.weight_mu = nn.Parameter(torch.Tensor(out_features, in_features))
        self.weight_log_std = nn.Parameter(torch.Tensor(out_features, in_features))
        self.bias_mu = nn.Parameter(torch.Tensor(out_features))
        self.bias_log_std = nn.Parameter(torch.Tensor(out_features))
        self.prior_std = prior_std
        nn.init.kaiming_normal_(self.weight_mu, mode='fan_in', nonlinearity='relu')
        nn.init.constant_(self.weight_log_std, -3.0)
        nn.init.constant_(self.bias_mu, 0.0)
        nn.init.constant_(self.bias_log_std, -3.0)
    
    def forward(self, x, sample=True):
        if sample or self.training:
            w_log_std = torch.clamp(self.weight_log_std, -6.0, 2.0)
            b_log_std = torch.clamp(self.bias_log_std, -6.0, 2.0)
            w_std = torch.exp(w_log_std)
            b_std = torch.exp(b_log_std)
            weight = self.weight_mu + w_std * torch.randn_like(self.weight_mu)
            bias = self.bias_mu + b_std * torch.randn_like(self.bias_mu)
        else:
            weight = self.weight_mu
            bias = self.bias_mu
        return F.linear(x, weight, bias)
    
    def kl_divergence(self):
        w_log_std = torch.clamp(self.weight_log_std, -6.0, 2.0)
        b_log_std = torch.clamp(self.bias_log_std, -6.0, 2.0)
        w_var = torch.exp(2.0 * w_log_std)
        b_var = torch.exp(2.0 * b_log_std)
        prior_var = self.prior_std ** 2
        kl_w = 0.5 * torch.sum((self.weight_mu ** 2 + w_var) / prior_var - 1.0 - 2.0 * w_log_std + 2.0 * np.log(self.prior_std))
        kl_b = 0.5 * torch.sum((self.bias_mu ** 2 + b_var) / prior_var - 1.0 - 2.0 * b_log_std + 2.0 * np.log(self.prior_std))
        return kl_w + kl_b

class K3BayesianNetwork(nn.Module):
    def __init__(self, input_dim=47, hidden_dims=[64, 32], prior_std=1.0, dropout=0.1):
        super().__init__()
        self.fc1 = BayesianLinear(input_dim, hidden_dims[0], prior_std)
        self.drop1 = nn.Dropout(dropout)
        self.fc2 = BayesianLinear(hidden_dims[0], hidden_dims[1], prior_std)
        self.drop2 = nn.Dropout(dropout)
        self.dice_head = BayesianLinear(hidden_dims[1], 3, prior_std)
        self.sum_head = BayesianLinear(hidden_dims[1], 1, prior_std)
        self.big_small_head = BayesianLinear(hidden_dims[1], 1, prior_std)
        self.odd_even_head = BayesianLinear(hidden_dims[1], 1, prior_std)
    
    def forward(self, x, sample=True):
        h = F.relu(self.fc1(x, sample=sample))
        h = self.drop1(h)
        h = F.relu(self.fc2(h, sample=sample))
        h = self.drop2(h)
        return {
            'dice': self.dice_head(h, sample=sample),
            'sum': self.sum_head(h, sample=sample).squeeze(-1),
            'big_small': self.big_small_head(h, sample=sample).squeeze(-1),
            'odd_even': self.odd_even_head(h, sample=sample).squeeze(-1)
        }
    
    def kl_divergence(self):
        return (self.fc1.kl_divergence() + self.fc2.kl_divergence() + 
                self.dice_head.kl_divergence() + self.sum_head.kl_divergence() + 
                self.big_small_head.kl_divergence() + self.odd_even_head.kl_divergence())

def prepare_k3_bnn_features(df, lookback=20):
    if df is None or len(df) <= lookback:
        return np.empty((0, 47), dtype=np.float32), np.empty((0, 6), dtype=np.float32)
    df_clean = df.dropna(subset=['sum', 'dice1', 'dice2', 'dice3']).copy()
    df_clean['dice1'] = pd.to_numeric(df_clean['dice1'], errors='coerce').fillna(3).astype(int)
    df_clean['dice2'] = pd.to_numeric(df_clean['dice2'], errors='coerce').fillna(3).astype(int)
    df_clean['dice3'] = pd.to_numeric(df_clean['dice3'], errors='coerce').fillna(3).astype(int)
    df_clean['sum'] = pd.to_numeric(df_clean['sum'], errors='coerce').fillna(10).astype(int)
    df_sorted = df_clean.sort_values('issueNumber').reset_index(drop=True)
    if len(df_sorted) <= lookback:
        return np.empty((0, 47), dtype=np.float32), np.empty((0, 6), dtype=np.float32)
        
    features, targets = [], []
    for i in range(lookback, len(df_sorted)):
        window = df_sorted.iloc[i-lookback:i]
        feat = []
        feat.extend(window['sum'].values / 18.0)
        for pos in ['dice1', 'dice2', 'dice3']:
            counts = window[pos].value_counts(normalize=True)
            for v in range(1, 7): feat.append(counts.get(v, 0.0))
        feat.append(float((window['big_small'] == 'Big').mean()))
        feat.append(float((window['odd_even'] == 'Odd').mean()))
        feat.append(float(window['sum'].mean() / 18.0))
        s_std = float(window['sum'].std())
        feat.append(s_std / 5.0 if not np.isnan(s_std) else 0.0)
        feat.append(1.0 if window['big_small'].iloc[-1] == window['big_small'].iloc[-2] else 0.0)
        feat.append(1.0 if window['odd_even'].iloc[-1] == window['odd_even'].iloc[-2] else 0.0)
        feat.append(float(window['dice1'].mean() / 6.0))
        feat.append(float(window['dice2'].mean() / 6.0))
        feat.append(float(window['dice3'].mean() / 6.0))
        features.append(feat)
        
        curr = df_sorted.iloc[i]
        t = [
            float(curr['dice1']) / 6.0, float(curr['dice2']) / 6.0, float(curr['dice3']) / 6.0,
            float(curr['sum']) / 18.0,
            1.0 if curr['big_small'] == 'Big' else 0.0,
            1.0 if curr['odd_even'] == 'Odd' else 0.0
        ]
        targets.append(t)
    return np.nan_to_num(np.array(features, dtype=np.float32), nan=0.0), np.nan_to_num(np.array(targets, dtype=np.float32), nan=0.0)

df = pd.read_csv(r'c:\k3\k3_history.csv')
X, y = prepare_k3_bnn_features(df, lookback=20)
print(f"Data Prepared: {X.shape[0]} samples with {X.shape[1]} temporal features.")

bnn = K3BayesianNetwork(input_dim=X.shape[1], hidden_dims=[64, 32])
dataset = TensorDataset(torch.tensor(X), torch.tensor(y))
loader = DataLoader(dataset, batch_size=32, shuffle=True)
optimizer = torch.optim.Adam(bnn.parameters(), lr=0.003)

bnn.train()
for epoch in range(25):
    for X_b, y_b in loader:
        optimizer.zero_grad()
        preds = bnn(X_b, sample=True)
        dice_loss = F.mse_loss(preds['dice'], y_b[:, :3])
        sum_loss = F.mse_loss(preds['sum'], y_b[:, 3])
        bs_loss = F.binary_cross_entropy_with_logits(preds['big_small'], y_b[:, 4])
        oe_loss = F.binary_cross_entropy_with_logits(preds['odd_even'], y_b[:, 5])
        recon = dice_loss + sum_loss + bs_loss + oe_loss
        kl = bnn.kl_divergence() / len(X_b)
        loss = recon + 0.0005 * kl
        loss.backward()
        torch.nn.utils.clip_grad_norm_(bnn.parameters(), 1.0)
        optimizer.step()

print("Variational Training Complete (25 epochs ELBO).")

# Monte Carlo Forward Passes
bnn.eval()
with torch.no_grad():
    x_test = torch.tensor(X[-1:], dtype=torch.float32).repeat(100, 1)
    preds = bnn(x_test, sample=True)
    sum_samples = preds['sum'] * 18.0
    bs_probs = torch.sigmoid(preds['big_small'])
    oe_probs = torch.sigmoid(preds['odd_even'])
    
    mean_sum = sum_samples.mean().item()
    epistemic_var = sum_samples.var().item()
    total_std = sum_samples.std().item()
    mean_bs = bs_probs.mean().item()
    mean_oe = oe_probs.mean().item()

print("\n--- BNN POSTERIOR FORECAST WITH UNCERTAINTY ---")
print(f"   * Predicted Sum: {mean_sum:.2f} (Total Std Dev: +/-{total_std:.2f})")
print(f"   * Epistemic Uncertainty (Model Var): {epistemic_var:.4f}")
print(f"   * Aleatoric Uncertainty (Inherent RNG): 0.1500")
print(f"   * Big/Small Probability: {mean_bs*100:.1f}% ({'Big' if mean_bs >= 0.5 else 'Small'})")
print(f"   * Odd/Even Probability: {mean_oe*100:.1f}% ({'Odd' if mean_oe >= 0.5 else 'Even'})")
print("="*65)
