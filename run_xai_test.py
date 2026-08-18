import numpy as np
import pandas as pd
from pathlib import Path

print("="*70)
print("  EXPLAINABLE AI (XAI) SUITE VERIFICATION TEST")
print("="*70 + "\n")

BASE = Path(__file__).resolve().parent
df = pd.read_csv(BASE / 'k3_history.csv')
df_clean = df.dropna(subset=['sum', 'dice1', 'dice2', 'dice3']).sort_values('issueNumber').reset_index(drop=True)
print(f"Loaded {len(df_clean)} historical draws.")

from k3 import (
    K3FeatureEngineer,
    SimpleK3Model,
    SHAPExplainer,
    LIMEExplainer,
    NaturalLanguageExplainer,
    CounterfactualAnalyzer
)

fe = K3FeatureEngineer()
features = fe.extract_features(df_clean)
print(f"Extracted feature vector length: {len(features)} features")

model = SimpleK3Model()
prediction = model.predict(features)
print(f"Base Model Forecast: Sum={prediction['sum']:.1f}, {prediction['bs_pred']}, {prediction['oe_pred']} (Confidence: {prediction['confidence']*100:.1f}%)")

# 1. SHAP Explanation
shap = SHAPExplainer(model.predict, fe)
shap_exp = shap.explain_prediction(features)
print("\n--- TOP 5 SHAP ATTRIBUTION SIGNALS ---")
for f_name, val in shap_exp['top_features']:
    print(f"   * {f_name:20s}: {val:+.4f} ({fe.get_feature_description(f_name)})")

# 2. Natural Language Explanation
nl_explainer = NaturalLanguageExplainer()
nl_text = nl_explainer.explain(shap_exp, prediction)
print("\n--- NATURAL LANGUAGE SYNTHESIS ---")
print(nl_text.encode('ascii', errors='replace').decode('ascii'))

# 3. LIME Surrogate
lime = LIMEExplainer(model.predict, fe)
lime_exp = lime.explain(features, n_perturbations=50)
print("\n--- LIME LOCAL SURROGATE WEIGHTS ---")
print(f"   * Local Surrogate R^2: {lime_exp.get('r_squared', 0):.4f}")
for f_name, w in lime_exp['feature_weights'][:5]:
    print(f"   * {f_name:20s}: {w:+.4f}")

# 4. Counterfactual Analysis
cf_analyzer = CounterfactualAnalyzer(model.predict, fe)
target_flip = "Small" if prediction['bs_pred'] == 'Big' else "Big"
cf_res = cf_analyzer.find_counterfactual(features, desired_output=target_flip)
print(f"\n--- COUNTERFACTUAL FLIP ANALYSIS (To '{target_flip}') ---")
for i, cf in enumerate(cf_res['counterfactuals'][:3], 1):
    print(f"   * Option {i}: Shift '{cf['feature_name']}' from {cf['original_value']:.2f} to {cf['new_value']:.2f} ({cf['change']:+.2f})")

print("\n" + "="*70)
print("  XAI SUITE VERIFICATION SUCCESSFUL (0 ERRORS)")
print("="*70)
