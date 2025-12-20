# CircuitSim Benchmarks: Cascaded Chain Framework 🧬⚡

**CircuitSim Benchmarks** is a research-oriented platform designed to analyze the performance of AI-driven neural surrogates against traditional physics-based circuit solvers. It focuses on **Linear Time-Invariant (LTI) cascaded two-port networks**.

## 🚀 Key Features

### 1. Cascaded-Chain Physics Engine (Solver v3.0)
The platform uses the **ABCD Matrix** method for high-speed simulation of cascaded RLC stages:
- **Baseline Parasitics**: Includes foundational non-ideal models (ESR for inductors, Leakage for capacitors) for research-grade comparisons.
- **Recursive Solver**: Efficiently computes frequency responses for arbitrary ladder networks up to 10 stages.
- **Approximative Transients**: Provides heuristic-based transient metrics ($t_r$, $t_s$, $M_p$) based on lumped-equivalent second-order analytics.

### 2. Neural Surrogate Model (Phase 3)
A **Multi-Output Random Forest Regressor** trained on 20,000 synthetic simulations:
- **Predictive Metrics**: Rapidly estimates $V_{out}$, $I_{in}$, and relative Energy Efficiency.
- **Domain of Validity**: Optimized for cascaded RLC structures within standard textbook value ranges ($pF$ to $k\Omega$).
- **Efficiency Analysis**: Computes relative power figures based on a $1k\Omega$ reference load.

### 3. Integrated Research Tools
- **Experimental CV Component Extraction**: Prototype OpenCV pipeline for basic parameter detection from diagrams.
- **Chain Editor**: Dynamic interface for building and benchmarking cascaded component stages.

## 🛠️ Architecture

- **Frontend**: React + Vite + TailwindCSS.
- **Backend**: FastAPI (Python) + NumPy + Scikit-Learn.
- **Framework**: Recursive ABCD Transmission Matrix solver for LTI two-port cascades.

## 🏁 Operational Status

> [!IMPORTANT]
> **Academic Disclaimer**: This system is designed for LTI cascaded circuits. It is not a generalized SPICE replacement and does not support bridge topologies, active feedback, or non-linear state-space integration. Transient metrics are **heuristics** and should be validated against full ODE solvers for critical research.

## 📦 Project Structure

```text
├── backend/                # FastAPI Application (Cascaded Solver)
├── frontend/               # React Dashboard (Research UI)
├── scripts/                # Data Generation & ML Training
└── sample_data/            # Phase 3 Prototype Models
```

## 📄 License
Distributed under the MIT License.

---
Developed as a Physics-ML Co-Simulation Framework for Cascaded Circuit Research.
