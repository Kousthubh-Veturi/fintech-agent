#!/bin/bash

# Railway startup script for Fintech Agent
# This handles Railway-specific environment setup

set -e

echo "🚂 Starting Fintech Agent on Railway..."

# Set default PORT if not provided by Railway
export PORT=${PORT:-8000}

# Ensure database tables are created
echo "📊 Setting up database tables..."
python -c "
try:
    from auth.database import create_tables
    create_tables()
    print('✅ Database tables ready!')
except Exception as e:
    print(f'⚠️ Database setup warning: {e}')
    print('This is normal if using external database like Neon')
"

# Start the application
echo "🚀 Starting FastAPI server on port $PORT..."
exec python enhanced_main.py
