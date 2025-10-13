#!/bin/bash
# scripts/run.sh
# Starts both backend (FastAPI) and frontend (Streamlit) for the SF Traffic MVP

# Activate virtual environment if needed (uncomment and edit if using venv)
# source venv/bin/activate

# Start backend (FastAPI)
echo "Starting backend (FastAPI) on port 8000..."
cd "$(dirname "$0")/../backend" || exit 1
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACK_PID=$!

# Wait a moment to ensure backend starts
sleep 2

# Start frontend (Streamlit)
echo "Starting frontend (Streamlit) on port 8501..."
cd "../frontend" || exit 1
streamlit run app.py --server.port 8501

# When frontend exits, stop backend
echo "Stopping backend..."
kill $BACK_PID
