#!/bin/bash

# Multi-Crypto Trading System Deployment Script

set -e

echo "Starting deployment of Multi-Crypto Trading System..."

# Check if required environment variables are set
if [ -z "$COINDESK_API_KEY" ] || [ -z "$NEWSAPI_KEY" ]; then
    echo "Error: COINDESK_API_KEY and NEWSAPI_KEY environment variables must be set"
    echo "Export them first:"
    echo "export COINDESK_API_KEY=your_key_here"
    echo "export NEWSAPI_KEY=your_key_here"
    exit 1
fi

# Stop existing containers
echo "Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down

# Build and start services
echo "Building and starting services..."
docker-compose -f docker-compose.prod.yml up --build -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Check service health
echo "Checking service health..."
if curl -f http://localhost:8000/status > /dev/null 2>&1; then
    echo "Backend is healthy"
else
    echo "Warning: Backend health check failed"
fi

if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "Frontend is healthy"
else
    echo "Warning: Frontend health check failed"
fi

echo "Deployment complete!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Services:"
echo "- Backend: Multi-crypto trading API with 8 cryptocurrencies"
echo "- Frontend: React dashboard with portfolio management"
echo "- Redis: Caching and rate limiting"
echo ""
echo "To stop: docker-compose -f docker-compose.prod.yml down"
echo "To view logs: docker-compose -f docker-compose.prod.yml logs -f"
