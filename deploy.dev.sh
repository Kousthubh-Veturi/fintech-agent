#!/bin/bash

# Development Deployment Script for Fintech Agent
# This script sets up the development environment

set -e

echo "🛠️ Starting Development Setup..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_status "Creating .env from template..."
    cp env.example .env
    print_warning "Please edit .env file with your actual values!"
fi

# Setup Python virtual environment
print_status "Setting up Python virtual environment..."
if [ ! -d "python/venv" ]; then
    python3 -m venv python/venv
fi

source python/venv/bin/activate
pip install -r requirements.txt

print_success "Python environment ready!"

# Setup frontend dependencies
print_status "Setting up frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
cd ..

print_success "Frontend dependencies installed!"

# Check required environment variables
print_status "Checking environment variables..."
source .env
required_vars=("DATABASE_URL" "SECRET_KEY" "SENDGRID_API_KEY" "FROM_EMAIL")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    print_warning "Missing environment variables (you can set these later):"
    printf '   %s\n' "${missing_vars[@]}"
fi

print_success "Development environment setup complete!"

echo ""
echo "🚀 To start development servers:"
echo ""
echo "Terminal 1 (Backend):"
echo "   cd /Users/kousthubhveturi/fintech-agent"
echo "   source python/venv/bin/activate"
echo "   python enhanced_main.py"
echo ""
echo "Terminal 2 (Frontend):"
echo "   cd /Users/kousthubhveturi/fintech-agent/frontend"
echo "   npm start"
echo ""
echo "📊 Development URLs:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "🔐 Authentication System Included:"
echo "   ✅ Login/Register Forms"
echo "   ✅ Password Reset Flow"
echo "   ✅ Email Verification"
echo "   ✅ 2FA Support"
echo "   ✅ JWT Authentication"
echo ""
