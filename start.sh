#!/usr/bin/env bash
set -e

echo "============================================"
echo "  CircuitSim Benchmarks — Local Startup"
echo "============================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Install from https://python.org"
    exit 1
fi

# Check Node
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required. Install from https://nodejs.org"
    exit 1
fi

echo -e "${CYAN}[1/5] Setting up Python virtual environment...${NC}"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

echo -e "${CYAN}[2/5] Installing backend dependencies...${NC}"
pip install -q -r backend/requirements.txt

echo -e "${CYAN}[3/5] Generating training data & training model...${NC}"
if [ ! -f "sample_data/topological_v3_model.pkl" ]; then
    echo "  → Generating dataset (20,000 samples)..."
    python3 scripts/generate_topological_dataset_v3.py
    echo "  → Training Random Forest model..."
    python3 scripts/train_topological_v3.py
else
    echo "  → Model already exists, skipping training."
fi

echo -e "${CYAN}[4/5] Installing frontend dependencies...${NC}"
cd frontend
npm install --silent
cd ..

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  ✅ Setup Complete! Starting services...${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${YELLOW}  Frontend → http://localhost:5173${NC}"
echo -e "${YELLOW}  Backend  → http://localhost:8000${NC}"
echo -e "${YELLOW}  API Docs → http://localhost:8000/docs${NC}"
echo ""

# Start backend in background
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "Waiting for backend to start..."
for i in {1..60}; do
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo -e "${GREEN}  ✅ Backend is ready!${NC}"
        break
    fi
    sleep 1
done

# Start frontend
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo -e "${GREEN}🚀 CircuitSim Benchmarks is LIVE!${NC}"
echo -e "   Press Ctrl+C to stop all services."
echo ""

# Trap Ctrl+C to kill both processes
trap "echo ''; echo 'Shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM

# Wait for either process to exit
wait
