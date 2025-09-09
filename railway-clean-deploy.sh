#!/bin/bash

# Railway Clean Deployment Script
# Forces Railway to use the current Dockerfile and requirements.txt

echo "🧹 Preparing clean Railway deployment..."

# Ensure we're using the main files
echo "📋 Verifying main deployment files exist:"
if [ -f "Dockerfile" ]; then
    echo "✅ Dockerfile found"
else
    echo "❌ Dockerfile missing!"
    exit 1
fi

if [ -f "requirements.txt" ]; then
    echo "✅ requirements.txt found"
else
    echo "❌ requirements.txt missing!"
    exit 1
fi

if [ -f "railway.toml" ]; then
    echo "✅ railway.toml found"
else
    echo "❌ railway.toml missing!"
    exit 1
fi

# Show what Railway will use
echo ""
echo "🔍 Railway will use these files:"
echo "  - Dockerfile ($(wc -l < Dockerfile) lines)"
echo "  - requirements.txt ($(wc -l < requirements.txt) lines)"
echo "  - railway.toml configuration"

echo ""
echo "🚀 Ready for Railway deployment!"
echo ""
echo "📋 Next steps:"
echo "1. Commit and push these changes to your Git repository"
echo "2. In Railway dashboard, trigger a new deployment"
echo "3. Railway will now use the correct Dockerfile and requirements.txt"
echo ""
echo "💡 If Railway still uses old files, try:"
echo "   - Delete and recreate the Railway service"
echo "   - Or disconnect and reconnect your GitHub repository"
echo ""
echo "🎯 Your app will be available at: https://your-app-name.railway.app"
