import numpy as np
import pandas as pd
import math
import os
import random

def get_impedance(comp_type, value, freq):
    omega = 2 * math.pi * freq
    if comp_type == 'R':
        return complex(value, 0)
    elif comp_type == 'L':
        return complex(0, omega * value)
    elif comp_type == 'C':
        if value == 0 or omega == 0: return complex(1e12, 0) # High impedance
        return complex(0, -1 / (omega * value))
    return complex(0, 0)

def solve_ladder(stages, freq, vin=1.0):
    """
    Solves a ladder network using ABCD matrices.
    stages: list of (tag, type, value)
    tag 1: series, tag 2: shunt, tag 0: open/terminate
    """
    M = np.identity(2, dtype=complex)
    
    for tag, c_type, val in stages:
        if tag == 0: break
        Z = get_impedance(c_type, val, freq)
        
        if tag == 1: # Series
            matrix = np.array([[1, Z], [0, 1]])
        elif tag == 2: # Shunt
            if Z == 0: Y = complex(1e12, 0)
            else: Y = 1 / Z
            matrix = np.array([[1, 0], [Y, 1]])
        else:
            continue
            
        M = M @ matrix
    
    # Pre-calculated M_11 relates Vin to Vout when Iout = 0
    # Vin = M11 * Vout + M12 * Iout
    # For open output, Iout = 0 -> Vout = Vin / M11
    m11 = M[0, 0]
    if abs(m11) == 0: return 0.0
    vout = vin / abs(m11)
    return vout

def generate_dataset(num_samples=5000, max_stages=5):
    data = []
    comp_types = ['R', 'L', 'C']
    
    print(f"Generating {num_samples} topological samples...")
    
    for _ in range(num_samples):
        # Randomize parameters for each component
        # Encoding: [Tag1, Type1, Val1, Tag2, Type2, Val2, Tag3, Type3, Val3, Tag4, Type4, Val4, Tag5, Type5, Val5, Freq]
        row = []
        stages = []
        
        freq = 10 ** random.uniform(1, 4) # 10Hz to 10kHz
        
        for i in range(max_stages):
            tag = random.choice([1, 2]) # Series or Shunt
            c_type = random.choice(comp_types)
            
            # Sampling values in typical ranges
            if c_type == 'R': val = 10 ** random.uniform(1, 4) # 10 to 10k
            elif c_type == 'L': val = 10 ** random.uniform(-3, 0) # 1mH to 1H
            elif c_type == 'C': val = 10 ** random.uniform(-8, -4) # 10nF to 100uF
            
            stages.append((tag, c_type, val))
            
            # Feature engineering for ML: Convert type to numeric
            # R=1, L=2, C=3
            type_num = 1 if c_type == 'R' else (2 if c_type == 'L' else 3)
            row.extend([tag, type_num, val])
            
        vout = solve_ladder(stages, freq)
        row.append(freq)
        row.append(vout)
        data.append(row)
        
    columns = []
    for i in range(1, max_stages + 1):
        columns.extend([f'tag_{i}', f'type_{i}', f'val_{i}'])
    columns.extend(['freq', 'vout'])
    
    df = pd.DataFrame(data, columns=columns)
    
    # Ensure directory exists
    os.makedirs('sample_data', exist_ok=True)
    df.to_csv('sample_data/topological_dataset.csv', index=False)
    print("Dataset saved to sample_data/topological_dataset.csv")

if __name__ == "__main__":
    generate_dataset()
