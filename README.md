# CircuitSim Benchmarks 🧬⚡

**CircuitSim Benchmarks** is a research-oriented platform designed to bridge classical electrical engineering with modern machine learning. It provides a high-fidelity environment for benchmarking traditional physics-based circuit solvers against AI-driven neural surrogates.

## 🚀 Key Features

### 1. Deep Theory Physics Engine (Solver v3.0)
Unlike basic "ideal" simulators, this platform incorporates real-world parasitics:
- **Non-Ideal Inductors**: Equivalent Series Resistance (ESR) modeled per *Alexander/Sadiku*.
- **Non-Ideal Capacitors**: Leakage Conductance ($G$) modeled per *Nilsson/Riedel*.
- **Topological Generalization**: Supports arbitrary series/shunt ladder networks up to 10 stages.

### 2. Neural Surrogate Model (Phase 3)
A massive **Multi-Target Random Forest Regressor** trained on 20,000+ synthetic circuit samples:
- **Predictive Metrics**: Simultaneous inference of $V_{out}$, $I_{in}$, Energy Efficiency ($\eta$), and Transients.
- **Switching Dynamics**: Real-time prediction of **Rise Time ($t_r$)**, **Settling Time**, and **Peak Overshoot**.
- **Log-Feature Scaling**: Optimized for components spanning 6+ orders of magnitude.

### 3. Integrated Research Workbench
- **Computer Vision Extraction**: Upload circuit diagrams to automatically extract RLC parameters.
- **Topological Editor**: A dynamic GUI to build and simulate complex component chains.
- **Remote Colab Bridge**: Connect to high-performance GPU instances for heavy inference.

## 🛠️ Architecture

- **Frontend**: React + Vite + TailwindCSS + Lucide Icons.
- **Backend**: FastAPI (Python) + NumPy + Scikit-Learn.
- **Physics**: ABCD Transmission Matrix-based recursive solver.
- **Surrogate**: MultiOutput Scikit-Learn Ensemble.

## 📦 Project Structure

```text
├── backend/                # FastAPI Application
│   ├── main.py             # Core Logic & Solvers
│   └── requirements.txt    # Heavy-lifting dependencies
├── frontend/               # React Dashboard
│   ├── src/                # UI Components (Dashboard, Workbench, History)
│   └── public/             # Static Assets
├── scripts/                # Data Factory
│   ├── generate_topological_v3.py  # 20k-Sample Physics Generator
│   └── train_topological_v3.py     # Multi-target ML Training
└── sample_data/            # Trained Models & Metadata
```

## 🏁 Getting Started

### Prerequisites
- Python 3.9+
- Node.js 16+

### Local Setup
1. **Clone the repository**:
   ```bash
   git clone https://github.com/evildead23151/CircuitSim-Benchmarks.git
   cd CircuitSim-Benchmarks
   ```

2. **Start the Backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   python main.py
   ```

3. **Start the Frontend**:
   ```bash
   cd ../frontend
   npm install
   npm run dev
   ```

## 🚀 One-Click "No-Sleep" Deployment

Want to see it live right now? Use these buttons to deploy your own permanent research node:

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fevildead23151%2FCircuitSim-Benchmarks&root-directory=frontend)
> **Note**: This will host the UI permanently at `https://circuitsim-benchmarks.vercel.app`.

[![Deploy to Hugging Face](https://huggingface.co/datasets/huggingface/badges/resolve/main/deploy-to-spaces-lg.svg)](https://huggingface.co/new-space?template=evildead23151/CircuitSim-Benchmarks)
> **Note**: Connect your GitHub repo to a Docker Space on Hugging Face for a non-sleeping backend.

## 🌐 Live Deployment Guide

For a "No-Sleep" research-grade experience, we recommend the following free stack:

### Frontend (User Interface) - [Vercel](https://vercel.com)
1. Link your GitHub repository to Vercel.
2. Set the `Root Directory` to `frontend`.
3. Deploy. Vercel provides a permanent, always-ready frontend.

### Backend (Deep Theory Engine) - [Hugging Face Spaces](https://huggingface.co/spaces)
1. Create a new Space on Hugging Face (Select **Docker** as the SDK).
2. Connect your GitHub repository.
3. **Important**: Since the neural model is 221MB (exceeding GitHub's limit), manually upload `sample_data/topological_v3_model.pkl` directly to your Space's file manager.
4. Set the `Remote Config` in the Dashboard workbench to your Hugging Face URL.

## 📚 Academic References
This platform is grounded in the following core texts:
- *Fundamentals of Electric Circuits* by Alexander & Sadiku.
- *The Art of Electronics* by Horowitz & Hill.
- *Signals and Systems* by Alan V. Oppenheim.

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.

---
Created for Advanced Circuit Theory Research & AI Surrogate Validation.
