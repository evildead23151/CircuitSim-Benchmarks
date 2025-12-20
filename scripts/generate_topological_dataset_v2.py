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
        if value == 0 or omega == 0: return complex(1e12, 0)
        return complex(0, -1 / (omega * value))
    return complex(0, 0)

def solve_ladder_full(stages, freq, vin=1.0):
    """
    Returns (Vout_mag, Iin_mag, Efficiency)
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
    
    # Vin = M11*Vout + M12*Iout. For open load, Iout=0.
    # Iin = M21*Vout + M22*Iout
    m11 = M[0, 0]
    m21 = M[1, 0]
    
    vout = vin / m11 if m11 != 0 else complex(0)
    iin = m21 * vout
    
    # Efficiency calculation (Real Power Out / Real Power In)
    # For open load, P_out is 0. This isn't very helpful for efficiency.
    # Let's assume a standard load (e.g. 1k Ohm) for efficiency benchmarking.
    RL = 1000.0
    # Recalculate with Load
    M_load = M @ np.array([[1, 0], [1/RL, 1]])
    m11_l = M_load[0, 0]
    m21_l = M_load[1, 0]
    
    vout_l = vin / m11_l
    iout_l = vout_l / RL
    iin_l = m21_l * vout_l + M_load[1, 1] * 0 # This is wrong, Iout is not 0 now.
    
    # Correct Way: [Vin; Iin] = M * [Vout; Iout]
    # Vout = Iout * RL => Vin = M11*Iout*RL + M12*Iout = Iout * (M11*RL + M12)
    iout_load = vin / (M[0, 0] * RL + M[0, 1])
    vout_load = iout_load * RL
    iin_load = M[1, 0] * vout_load + M[1, 1] * iout_load
    
    p_in = (vin * iin_load.conjugate()).real
    p_out = (vout_load * iout_load.conjugate()).real
    eff = p_out / p_in if p_in > 1e-9 else 0.0
    
    return abs(vout), abs(iin), eff

def generate_multi_target_dataset(num_samples=5000, max_stages=10):
    data = []
    comp_types = ['R', 'L', 'C']
    
    print(f"Generating {num_samples} multi-target topological samples...")
    
    for _ in range(num_samples):
        row = []
        stages = []
        freq = 10 ** random.uniform(1, 4)
        
        for i in range(max_stages):
            tag = random.choice([1, 2])
            c_type = random.choice(comp_types)
            if c_type == 'R': val = 10 ** random.uniform(1, 4)
            elif c_type == 'L': val = 10 ** random.uniform(-3, 0)
            elif c_type == 'C': val = 10 ** random.uniform(-8, -4)
            
            stages.append((tag, c_type, val))
            type_num = 1 if c_type == 'R' else (2 if c_type == 'L' else 3)
            row.extend([tag, type_num, val])
            
        vout, iin, eff = solve_ladder_full(stages, freq)
        row.extend([freq, vout, iin, eff])
        data.append(row)
        
    cols = []
    for i in range(1, max_stages + 1):
        cols.extend([f'tag_{i}', f'type_{i}', f'val_{i}'])
    cols.extend(['freq', 'vout', 'iin', 'efficiency'])
    
    df = pd.DataFrame(data, columns=cols)
    os.makedirs('sample_data', exist_ok=True)
    df.to_csv('sample_data/topological_multi_dataset.csv', index=False)
    print("Multi-target dataset saved.")

if __name__ == "__main__":
    generate_multi_target_dataset()
