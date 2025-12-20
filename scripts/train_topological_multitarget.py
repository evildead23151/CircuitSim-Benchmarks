import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import os
import json

def train_multi_target_model():
    DATA_PATH = 'sample_data/topological_multi_dataset.csv'
    MODEL_DIR = 'sample_data'
    MODEL_PATH = os.path.join(MODEL_DIR, 'topological_multi_model.pkl')
    
    print("Loading multi-target dataset...")
    df = pd.read_csv(DATA_PATH)
    
    # Target columns: vout, iin, efficiency
    target_cols = ['vout', 'iin', 'efficiency']
    X = df.drop(target_cols, axis=1)
    y = df[target_cols]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
    
    print(f"Training MultiOutput RandomForestRegressor on {len(X_train)} samples...")
    # Wrap RandomForest in MultiOutputRegressor
    base_rf = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
    model = MultiOutputRegressor(base_rf)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    
    metrics = {}
    for i, col in enumerate(target_cols):
        mae = mean_absolute_error(y_test.iloc[:, i], y_pred[:, i])
        r2 = r2_score(y_test.iloc[:, i], y_pred[:, i])
        metrics[col] = {"mae": float(mae), "r2": float(r2)}
        print(f"{col} - MAE: {mae:.5f}, R2: {r2:.5f}")
    
    # Save the model
    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
        
    print(f"Multi-target model saved to {MODEL_PATH}")
    
    # Save metadata
    metadata = {
        "architecture": "MultiOutput(RandomForest)",
        "n_samples": len(df),
        "metrics": metrics,
        "input_features": list(X.columns),
        "target_features": target_cols
    }
    with open(os.path.join(MODEL_DIR, 'topo_multi_meta.json'), 'w') as f:
        json.dump(metadata, f, indent=2)

if __name__ == "__main__":
    train_multi_target_model()
