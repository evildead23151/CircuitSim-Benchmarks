import pickle
import numpy as np
import os

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "sample_data", "rlc_vout_model.pkl")

def test_inference():
    print(f"Loading model from {MODEL_PATH}")
    with open(MODEL_PATH, "rb") as f:
        ai_model = pickle.load(f)
    
    # Values from dataset row 2:
    # 157.235, 0.00883, 0.0001198
    # Expected Vout: 0.00798
    R, L, C = 157.235, 0.00883, 0.0001198
    X = np.array([[R, L, C]])
    
    if isinstance(ai_model, dict):
        predictor = ai_model['model']
        scaler = ai_model.get('scaler')
        if scaler:
            X = scaler.transform(X)
            print("Applied scaling")
    else:
        predictor = ai_model

    log_vout = predictor.predict(X)[0]
    vout = 10 ** log_vout
    
    print(f"Input: R={R}, L={L}, C={C}")
    print(f"Prediction (log10): {log_vout}")
    print(f"Calculated Vout: {vout}")
    print(f"Expected Vout: ~0.00798")

if __name__ == "__main__":
    test_inference()
