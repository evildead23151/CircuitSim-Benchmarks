import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import os
import json

def train_v3_model():
    DATA_PATH = 'sample_data/topological_v3_dataset.csv'
    MODEL_DIR = 'sample_data'
    MODEL_PATH = os.path.join(MODEL_DIR, 'topological_v3_model.pkl')
    
    if not os.path.exists(DATA_PATH):
        print(f"Error: Dataset {DATA_PATH} not found.")
        return

    print("Loading Phase 3 Deep Theory dataset...")
    df = pd.read_csv(DATA_PATH)
    
    # Target columns for multi-output regression
    target_cols = ['vout', 'iin', 'efficiency', 'rise_time', 'settling_time', 'overshoot']
    X = df.drop(target_cols, axis=1)
    y = df[target_cols]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42)
    
    print(f"Training Advanced MultiOutput Regressor on {len(X_train)} samples...")
    # Optimized for massive multi-target data
    base_rf = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
    model = MultiOutputRegressor(base_rf)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    
    metrics = {}
    print("\nDeep Theory Model Evaluation:")
    for i, col in enumerate(target_cols):
        mae = mean_absolute_error(y_test.iloc[:, i], y_pred[:, i])
        r2 = r2_score(y_test.iloc[:, i], y_pred[:, i])
        metrics[col] = {"mae": float(mae), "r2": float(r2)}
        print(f" - {col:15}: MAE={mae:.6f}, R2={r2:.4f}")
    
    # Save the model
    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
        
    print(f"\nModel saved to {MODEL_PATH}")
    
    # Save metadata for frontend consumption
    metadata = {
        "version": "3.0-Textbook",
        "timestamp": pd.Timestamp.now().isoformat(),
        "architecture": "MultiOutput(RandomForestRegressor)",
        "input_features": list(X.columns),
        "target_features": target_cols,
        "metrics": metrics,
        "theory_alignment": "Non-ideal RLC + Transient Dynamics"
    }
    with open(os.path.join(MODEL_DIR, 'topo_v3_meta.json'), 'w') as f:
        json.dump(metadata, f, indent=2)

if __name__ == "__main__":
    train_v3_model()
