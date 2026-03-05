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

## ⚡ Quick Start (One Command)

### Option A: Bare Metal (Recommended for Development)

**Prerequisites:** Python 3.10+, Node.js 18+

```bash
git clone https://github.com/evildead23151/CircuitSim-Benchmarks.git
cd CircuitSim-Benchmarks

# macOS / Linux:
chmod +x start.sh && ./start.sh

# Windows:
start.bat
```

This will:
1. Create a Python virtual environment
2. Install all backend & frontend dependencies
3. Generate training data and train the AI model (first run only)
4. Start the backend API on **http://localhost:8000**
5. Start the frontend dashboard on **http://localhost:5173**

### Option B: Docker Compose

**Prerequisites:** Docker & Docker Compose

```bash
git clone https://github.com/evildead23151/CircuitSim-Benchmarks.git
cd CircuitSim-Benchmarks

# Generate training data first (requires Python locally)
python3 scripts/generate_topological_dataset_v3.py
python3 scripts/train_topological_v3.py

# Launch full stack
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend Dashboard | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |

### Manual Setup

<details>
<summary>Click to expand manual setup instructions</summary>

**Terminal 1 — Backend:**
```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
python3 scripts/generate_topological_dataset_v3.py
python3 scripts/train_topological_v3.py
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm install
npm run dev
```

</details>

## 📄 License
Distributed under the MIT License.

---
Developed as a Physics-ML Co-Simulation Framework for Cascaded Circuit Research.
