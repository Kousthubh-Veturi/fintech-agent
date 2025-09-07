#!/bin/bash

echo "Starting FinTech Trading Agent System..."
echo "======================================"

cd /Users/kousthubhveturi/fintech-agent

echo "1. Starting Redis and PostgreSQL..."
docker-compose up -d

echo "2. Starting Backend API..."
cd python
source venv/bin/activate
python ../main.py &
BACKEND_PID=$!

echo "Backend started with PID: $BACKEND_PID"

echo "3. Starting Frontend..."
cd ../frontend
npm start &
FRONTEND_PID=$!

echo "Frontend started with PID: $FRONTEND_PID"

echo ""
echo "System started successfully!"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop all services"

trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; docker-compose down; exit" INT

wait
