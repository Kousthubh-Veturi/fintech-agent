#!/bin/bash

# Quick Start Script for Fintech Agent
# Choose your deployment method

echo "🚀 Fintech Agent - Quick Start"
echo "=============================="
echo ""
echo "Choose your deployment method:"
echo ""
echo "1) 🏭 Production Deployment (Docker - Recommended)"
echo "   - Full Docker setup with all services"
echo "   - Production-ready with health checks"
echo "   - Runs on ports 80 (frontend) and 8000 (backend)"
echo ""
echo "2) 🛠️  Development Setup (Local)"
echo "   - Hot-reload for development"
echo "   - Runs on ports 3000 (frontend) and 8000 (backend)"
echo "   - Requires Node.js and Python"
echo ""
echo "3) 📖 View Deployment Documentation"
echo "   - Complete deployment guide"
echo "   - Configuration instructions"
echo "   - Troubleshooting help"
echo ""
echo "4) ❌ Exit"
echo ""

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo ""
        echo "🏭 Starting Production Deployment..."
        echo ""
        if [ ! -f ".env" ]; then
            echo "⚠️  No .env file found. Creating from template..."
            cp env.example .env
            echo ""
            echo "📝 Please edit .env file with your actual values:"
            echo "   - DATABASE_URL (Neon PostgreSQL)"
            echo "   - SECRET_KEY (JWT secret)"
            echo "   - SENDGRID_API_KEY (Email service)"
            echo "   - FROM_EMAIL (Verified sender email)"
            echo ""
            read -p "Press Enter after editing .env file..."
        fi
        ./deploy.production.sh
        ;;
    2)
        echo ""
        echo "🛠️ Starting Development Setup..."
        echo ""
        ./deploy.dev.sh
        ;;
    3)
        echo ""
        echo "📖 Opening deployment documentation..."
        if command -v less &> /dev/null; then
            less DEPLOYMENT.md
        elif command -v more &> /dev/null; then
            more DEPLOYMENT.md
        else
            cat DEPLOYMENT.md
        fi
        ;;
    4)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac
