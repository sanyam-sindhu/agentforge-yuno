#!/usr/bin/env bash
set -e

echo "==> AgentForge Setup"

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "==> Created .env from .env.example — fill in your API keys"
fi

echo "==> Installing backend dependencies..."
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
cd ..

echo "==> Installing frontend dependencies..."
cd frontend
npm install
cd ..

echo "==> Starting backend..."
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

echo "==> Starting frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "AgentForge is running!"
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
