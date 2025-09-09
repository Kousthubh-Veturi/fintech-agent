#!/bin/bash

# Vercel Frontend Deployment Script

echo "🎯 Deploying Frontend to Vercel..."
echo "Backend API: https://fintech-agent-production.up.railway.app/"
echo ""

# Check if we're in the right directory
if [ ! -f "frontend/package.json" ]; then
    echo "❌ Error: Run this script from the project root directory"
    exit 1
fi

# Navigate to frontend
cd frontend

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "📦 Installing Vercel CLI..."
    npm install -g vercel
fi

# Verify environment file
if [ -f ".env.production" ]; then
    echo "✅ Production environment file found:"
    cat .env.production
else
    echo "❌ .env.production not found!"
    exit 1
fi

echo ""
echo "🚀 Starting Vercel deployment..."
echo ""

# Deploy to Vercel
vercel --prod

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔗 Your app architecture:"
echo "   Frontend: Vercel (React app)"
echo "   Backend:  Railway (https://fintech-agent-production.up.railway.app/)"
echo "   Database: Neon PostgreSQL"
echo ""
echo "🎉 Your fintech app is now live!"
