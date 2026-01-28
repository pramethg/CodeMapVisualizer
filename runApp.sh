#!/bin/bash

# Kill ports 3000 and 8000 to ensure clean start
fuser -k 3000/tcp 2>/dev/null
fuser -k 8000/tcp 2>/dev/null

# Start Backend
cd backend
# source venv/bin/activate
# Run uvicorn in background, detached
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started (PID: $BACKEND_PID)"

# Start Frontend (Production Build)
cd ../frontend
# Build if not already built (checks for .next dir)
if [ ! -d ".next" ]; then
    echo "Building frontend..."
    npm run build
fi

nohup npm start > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started (PID: $FRONTEND_PID)"

echo "App running at http://localhost:3000"
