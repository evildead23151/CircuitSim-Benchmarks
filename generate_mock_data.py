
import numpy as np
import pandas as pd
import pickle
import math
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# Constants
Vin = 1.0
f = 1000.0
omega = 2 * math.pi * f

def calculate_vout(row):
    R = row['R']
    L = row['L']
    C = row['C']
    
    # Avoid zero division
    if C <= 0: return 0.0
    
    Zc_mag = 1 / (omega * C)
    denom = math.sqrt(R**2 + (omega * L - Zc_mag)**2)
    
    if denom == 0:
        return Vin
        
    return Vin * (Zc_mag / denom)

print("Generating synthetic data...")
# Generate random data
np.random.seed(42)
n_samples = 1000

# Ranges similar to what might be expected
R_vals = np.random.uniform(10, 1000, n_samples)   # 10 to 1k Ohm
L_vals = np.random.uniform(1e-6, 100e-3, n_samples) # 1uH to 100mH
C_vals = np.random.uniform(1e-9, 100e-6, n_samples) # 1nF to 100uF

df = pd.DataFrame({
    'R': R_vals,
    'L': L_vals,
    'C': C_vals
})

# Calculate Ground Truth
df['Vout'] = df.apply(calculate_vout, axis=1)

# Log transform output as per user request contract: Output is log10(Vout)
df['log_Vout'] = np.log10(df['Vout'] + 1e-9) # Avoid log(0)

# Save Dataset
csv_path = "sample_data/RLC_Vout_dataset_1000_samples.csv"
df.to_csv(csv_path, index=False)
print(f"Saved dataset to {csv_path}")

# Train Model
print("Training mock AI model...")
X = df[['R', 'L', 'C']]
y = df['log_Vout']

# Simple pipeline
# Using Random Forest for non-linearity capturing, allowing a better 'fit' than Linear
from sklearn.ensemble import RandomForestRegressor
model = Pipeline([
    ('scaler', StandardScaler()),
    ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
])

model.fit(X, y)

# Save Model
pkl_path = "sample_data/rlc_vout_model.pkl"
with open(pkl_path, 'wb') as f:
    pickle.dump(model, f)

print(f"Saved model to {pkl_path}")
print("Mock data generation complete.")
