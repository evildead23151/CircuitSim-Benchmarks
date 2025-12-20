import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import os

def train_topo_model():
    DATA_PATH = 'sample_data/topological_dataset.csv'
    MODEL_DIR = 'sample_data'
    MODEL_PATH = os.path.join(MODEL_DIR, 'topological_vout_model.pkl')
    
    print("Loading topological dataset...")
    df = pd.read_csv(DATA_PATH)
    
    # Feature columns: tags, types, values for all 5 stages + frequency
    X = df.drop('vout', axis=1)
    y = df['vout']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"Training RandomForestRegressor on {len(X_train)} samples...")
    # Using RandomForest for better handling of categorical-like structural tags
    model = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"Model Evaluation:")
    print(f"Mean Absolute Error: {mae:.5f}V")
    print(f"R2 Score: {r2:.5f}")
    
    # Save the model
    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
        
    print(f"Topological model saved to {MODEL_PATH}")
    
    # Save a small metadata file for the frontend
    metadata = {
        "architecture": "RandomForestRegressor",
        "n_samples": len(df),
        "mae": float(mae),
        "r2": float(r2),
        "input_features": list(X.columns)
    }
    with open(os.path.join(MODEL_DIR, 'topo_model_meta.json'), 'w') as f:
        import json
        json.dump(metadata, f)

if __name__ == "__main__":
    train_topo_model()
