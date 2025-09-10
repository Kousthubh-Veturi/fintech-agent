#!/bin/bash

echo "🚀 Vercel Deployment Debug Script"
echo "================================="

# Check current branch
echo "📍 Current branch:"
git branch --show-current

# Check recent commits
echo "📝 Recent commits:"
git log --oneline -3

# Check if TypeScript fix is present
echo "🔍 Checking TypeScript fix:"
if grep -q "type ViewType" frontend/src/App.tsx; then
    echo "✅ ViewType definition found"
else
    echo "❌ ViewType definition missing"
fi

# Test build locally
echo "🔨 Testing local build:"
cd frontend
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Local build successful"
else
    echo "❌ Local build failed"
    exit 1
fi

# Deploy to Vercel
echo "🚀 Deploying to Vercel:"
npx vercel --prod --yes

echo "✅ Deployment complete!"
