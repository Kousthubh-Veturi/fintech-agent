#!/bin/bash

# Railway Deployment Script for Fintech Agent
# This script prepares your app for Railway deployment

set -e

echo "🚂 RAILWAY DEPLOYMENT SETUP"
echo "==========================="
echo ""

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

# Check if git is initialized
if [ ! -d ".git" ]; then
    print_status "Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit - Railway deployment ready"
    print_success "Git repository initialized!"
else
    print_status "Git repository already exists"
fi

# Test Railway-compatible build locally
print_status "Testing Railway Docker build..."
if command -v docker &> /dev/null; then
    if docker build -t fintech-agent-railway . > /dev/null 2>&1; then
        print_success "Docker build successful!"
        docker rmi fintech-agent-railway > /dev/null 2>&1
    else
        print_error "Docker build failed. Check Dockerfile and requirements.txt"
        exit 1
    fi
else
    print_warning "Docker not found. Build will be tested on Railway."
fi

# Check environment variables template
if [ -f "env.railway" ]; then
    print_success "Railway environment template ready!"
else
    print_error "env.railway template missing!"
    exit 1
fi

# Display next steps
echo ""
echo "🎯 NEXT STEPS:"
echo "=============="
echo ""
echo "1. 📤 PUSH TO GITHUB:"
echo "   git remote add origin https://github.com/yourusername/fintech-agent.git"
echo "   git push -u origin main"
echo ""
echo "2. 🚂 DEPLOY ON RAILWAY:"
echo "   • Go to: https://railway.app"
echo "   • Click: New Project → Deploy from GitHub"
echo "   • Select: Your repository"
echo "   • Add PostgreSQL service"
echo ""
echo "3. ⚙️ SET ENVIRONMENT VARIABLES:"
echo "   Copy from env.railway to Railway dashboard:"
echo "   • SECRET_KEY (required)"
echo "   • SENDGRID_API_KEY (required)"
echo "   • FROM_EMAIL (required)"
echo "   • Other optional keys"
echo ""
echo "4. 🌐 DEPLOY FRONTEND TO VERCEL:"
echo "   • Go to: https://vercel.com"
echo "   • Deploy from GitHub"
echo "   • Set root directory: frontend"
echo "   • Add REACT_APP_API_URL with your Railway URL"
echo ""
echo "📖 Full guide: See RAILWAY_DEPLOYMENT.md"
echo ""
print_success "Railway deployment setup complete!"
echo ""
echo "🔗 Your app will be available at:"
echo "   Backend:  https://yourapp.railway.app"
echo "   Frontend: https://yourapp.vercel.app"
echo ""
