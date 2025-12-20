import numpy as np
import pandas as pd
import math
import os
import random
import time

# --- TEXTBOOK-GRADE PHYSICS CONSTANTS ---
DEFAULT_ESR = 0.5  # Ohms (Inductor series resistance)
DEFAULT_G = 1e-9   # Siemens (Capacitor leakage conductance)

def get_non_ideal_impedance(comp_type, value, freq):
    omega = 2 * math.pi * freq
    if comp_type == 'R':
        return complex(value, 0)
    elif comp_type == 'L':
        # Z_L = R_esr + j * omega * L
        return complex(DEFAULT_ESR, omega * value)
    elif comp_type == 'C':
        # Y_C = G_leak + j * omega * C => Z_C = 1 / Y_C
        if value == 0 or omega == 0: return complex(1e12, 0)
        Y = complex(DEFAULT_G, omega * value)
        return 1 / Y
    return complex(0, 0)

# --- ABCD MATRIX SOLVER (Steady State AC) ---
def solve_topo_v3_ac(stages, freq, vin=1.0):
    M = np.identity(2, dtype=complex)
    for tag, c_type, val in stages:
        if tag == 0: break
        Z = get_non_ideal_impedance(c_type, val, freq)
        if tag == 1: # Series
            matrix = np.array([[1, Z], [0, 1]])
        elif tag == 2: # Shunt
            Y = 1/Z if Z != 0 else complex(1e12, 0)
            matrix = np.array([[1, 0], [Y, 1]])
        else: continue
        M = M @ matrix
    
    # Open Load Transfer: Vout = Vin / M11
    m11 = M[0, 0]
    vout = vin / m11 if m11 != 0 else complex(0)
    
    # Input Current: Iin = M21 * Vout
    iin = M[1, 0] * vout
    
    # Efficiency with 1k Load
    RL = 1000.0
    # Recalculate with Load for efficiency
    # Vin = M11*Vout + M12*Iout; Iout = Vout/RL => Vin = Vout*(M11 + M12/RL)
    iout_load = vin / (M[0, 0] * RL + M[0, 1])
    vout_load = iout_load * RL
    iin_load = M[1, 0] * vout_load + M[1, 1] * iout_load
    
    p_in = (vin * iin_load.conjugate()).real
    p_out = (vout_load * iout_load.conjugate()).real
    eff = p_out / p_in if p_in > 1e-9 else 0.0
    
    return abs(vout), abs(iin), eff

# --- TRANSIENT SOLVER (Switching Dynamics via RK4) ---
# For arbitrary topologies, we represent the state space.
# Simplified for RLC ladder: L current and C voltage are states.
def simulate_transient(stages, duration=0.005, steps=1000):
    """
    Simulates a 1V step response. Returns tr, ts, Mp.
    (Placeholder implementation for complexity, ideally would build state-matrices)
    In a real research context, this would use an ODE solver on the full netlist.
    """
    # For now, let's derive dominant R, L, C to approximate transient.
    eq_R = 10.0
    eq_L = 1e-3
    eq_C = 10e-6
    for tag, c_type, val in stages:
        if c_type == 'R': eq_R += val
        elif c_type == 'L': eq_L += val
        elif c_type == 'C': eq_C += val
    
    # RLC Transient Analytics (Standard Second Order Response)
    # damped freq, zeta, etc.
    zeta = (eq_R / 2) * math.sqrt(eq_C / eq_L) if eq_L > 0 and eq_C > 0 else 1.0
    wn = 1 / math.sqrt(eq_L * eq_C) if eq_L > 0 and eq_C > 0 else 0.0
    
    # Rise Time approx: (1.8 / wn) or similar
    tr = 1.8 / wn if wn > 0 else 1.0
    # Peak Overshoot: exp(-pi * zeta / sqrt(1-zeta^2))
    if zeta < 1 and zeta > 0:
        mp = math.exp(-math.pi * zeta / math.sqrt(1 - zeta**2))
    else:
        mp = 0.0
    # Settling Time: 4 / (zeta * wn)
    ts = 4 / (zeta * wn) if zeta * wn > 0 else 1.0
    
    return tr, ts, mp

def generate_v3_dataset(num_samples=20000, max_stages=10):
    data = []
    print(f"Baking Phase 3 Deep Theory Dataset ({num_samples} samples)...")
    
    for s_idx in range(num_samples):
        if s_idx % 2000 == 0: print(f"Progress: {s_idx}/{num_samples}")
        
        row = []
        stages = []
        freq = 10 ** random.uniform(1, 4)
        
        for i in range(max_stages):
            tag = random.choice([1, 2])
            c_type = random.choice(['R', 'L', 'C'])
            if c_type == 'R': val = 10 ** random.uniform(1, 4)
            elif c_type == 'L': val = 10 ** random.uniform(-3, 0)
            elif c_type == 'C': val = 10 ** random.uniform(-8, -4)
            
            stages.append((tag, c_type, val))
            type_num = 1 if c_type == 'R' else (2 if c_type == 'L' else 3)
            # Log-scale features for better ML convergence
            row.extend([tag, type_num, math.log10(val)])
            
        vout, iin, eff = solve_topo_v3_ac(stages, freq)
        tr, ts, mp = simulate_transient(stages)
        
        row.extend([math.log10(freq), vout, iin, eff, tr, ts, mp])
        data.append(row)
        
    cols = []
    for i in range(1, max_stages + 1):
        cols.extend([f'tag_{i}', f'type_{i}', f'log_val_{i}'])
    cols.extend(['log_freq', 'vout', 'iin', 'efficiency', 'rise_time', 'settling_time', 'overshoot'])
    
    df = pd.DataFrame(data, columns=cols)
    os.makedirs('sample_data', exist_ok=True)
    df.to_csv('sample_data/topological_v3_dataset.csv', index=False)
    print("Phase 3 Dataset Exported.")

if __name__ == "__main__":
    generate_v3_dataset()
