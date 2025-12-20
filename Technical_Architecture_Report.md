# System Architecture & Methods Report: Cascaded Circuit Simulation Framework

This document provides a technical technical analysis of the **CircuitSim-Benchmarks** platform. It documents the mathematical foundations, system assumptions, and known limitations of the physics-ML co-simulation pipeline.

---

## 🏗️ 1. Simulation Methodology & Mathematical Foundations

### 1.1 Linear Cascaded Chain Model (Formerly "Topological")
**Description**: The system models circuits as a series of cascaded two-port networks.
**Domain of Validity**: Valid only for **Linear Time-Invariant (LTI)** components in a strictly cascaded, non-branching structure. It does not support bridge topologies, lattice networks, or active feedback loops.

#### Mathematical Foundation: ABCD (Transmission) Parameters
For each circuit stage, we define a transmission matrix $\mathbf{T}$ such that:
$$\begin{bmatrix} V_1 \\ I_1 \end{bmatrix} = \begin{bmatrix} A & B \\ C & D \end{bmatrix} \begin{bmatrix} V_2 \\ I_2 \end{bmatrix}$$

- **Series Element ($Z$)**: $\mathbf{T}_{series} = \begin{bmatrix} 1 & Z \\ 0 & 1 \end{bmatrix}$
- **Shunt Element ($Y$)**: $\mathbf{T}_{shunt} = \begin{bmatrix} 1 & 0 \\ Y & 1 \end{bmatrix}$

**The Chain Rule**: The total system matrix $\mathbf{T}_{sys}$ is derived by sequential matrix multiplication:
$$\mathbf{T}_{sys} = \mathbf{T}_1 \cdot \mathbf{T}_2 \cdot \dots \cdot \mathbf{T}_n$$

**Port Definitions & Boundary Conditions**:
- **Input Port**: Terminated at $V_{in}$ (Ideal source, no source impedance).
- **Output Port**: Measured under **Open-Load** ($I_2 = 0$) for $V_{out}$ benchmarks, and under a **Reference Load** ($R_L = 1k\Omega$) for efficiency calculations.
- **Reference Planes**: Defined at the terminal of each cascaded block.

---

## 📈 2. Solver Assumptions & Parameterization

### 2.1 Physics Assumptions Table
| Feature | Parameter | Model / Source | Justified Context |
| :--- | :--- | :--- | :--- |
| **Inductor Non-Ideality** | $ESR = 0.5 \Omega$ | Baseline Parasitic | Represents a typical 10-100mH power inductor series resistance. |
| **Capacitor Non-Ideality** | $G = 10^{-9} S$ | Baseline Leakage | $1G\Omega$ insulation resistance, standard for low-voltage ceramics. |
| **Transient Response** | Heuristic Analytics | 2nd-Order Approximation | Derived from $\zeta$ and $\omega_n$ of the equivalent RLC aggregate. |
| **Steady-State AC** | Phasor Domain | LTI Assumption | Assumes no saturation and constant frequency. |

> [!CAUTION]
> **Heuristic Transient Metrics**: The $t_r$, $t_s$, and $M_p$ metrics are derived from the lumped-equivalent damping ratio ($\zeta$) and natural frequency ($\omega_n$). This is an **approximation** and does not replace a full State-Space ODE solver (e.g., RK4) for complex multi-pole systems.

---

## 🧠 3. Machine Learning Surrogate Design

### 3.1 Model Selection & Justification
- **Model**: Multi-Output Random Forest (RF) Regressor.
- **Size**: 221MB (Warm-start inference ~0.1ms).
- **Why RF over MLP?** RF was chosen for this prototype due to its inherent handling of categorical "tags" (Series/Shunt) and robustness to non-smooth transitions in the discrete topological space.
- **Acknowledgment**: The RF model is memory-heavy and carries a cold-start penalty during the 5-second initial `pickle.load`. Compact Neural Networks (MLP/GNN) are identified as the primary path for future optimization.

### 3.2 Feature Preprocessing (Log-Transformation)
- **Input Transformation**: $x_{log} = \log_{10}(max(x, 10^{-12}))$ for $R, L, C$ values.
- **Output Scaling**: Linear Homogeneity is preserved by training the model on a $1V$ baseline and multiplying predictions by $V_{in}$ at runtime.
- **Handling Zero**: Protected via clippage at $10^{-12}$ to avoid mathematical singularities.

---

### 4. Known System Limitations

1. **Stationary Frequency Domain**: The solver assumes steady-state AC. It does not model start-up oscillations or non-linear saturation.
2. **Cascaded Topology Only**: Cannot solve non-ladder networks or loops.
3. **Metric Accuracy**: Efficiency is a relative benchmark based on a fixed load ($1k\Omega$) and should not be treated as a universal power figure.
4. **CV Extraction**: The Computer Vision engine is an **experimental prototype** restricted to binarization-based shape detection; it lacks the robust graph-grammar required for professional netlist extraction.

---
**Document Status**: *Final Technical Methods Review (Academic Correction Applied)*
