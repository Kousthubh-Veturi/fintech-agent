#!/bin/bash

# Production Deployment Script for Fintech Agent
# This script deploys the complete authentication-enabled trading system

set -e

echo "🚀 Starting Production Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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
    print_error ".env file not found!"
    print_status "Creating .env from template..."
    cp env.example .env
    print_warning "Please edit .env file with your actual values before continuing!"
    exit 1
fi

# Check required environment variables
print_status "Checking environment variables..."
required_vars=("DATABASE_URL" "SECRET_KEY" "SENDGRID_API_KEY" "FROM_EMAIL")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    print_error "Missing required environment variables:"
    printf '%s\n' "${missing_vars[@]}"
    print_warning "Please set these variables in your .env file"
    exit 1
fi

print_success "Environment variables check passed!"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

print_success "Docker is running!"

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose -f docker-compose.production.yml down --remove-orphans

# Remove old images (optional - uncomment if you want to rebuild everything)
# print_status "Removing old images..."
# docker-compose -f docker-compose.production.yml down --rmi all

# Build and start services
print_status "Building and starting services..."
docker-compose -f docker-compose.production.yml up --build -d

# Wait for services to be healthy
print_status "Waiting for services to be healthy..."
sleep 30

# Check service health
print_status "Checking service health..."
services=("backend" "frontend" "redis")
all_healthy=true

for service in "${services[@]}"; do
    if docker-compose -f docker-compose.production.yml ps | grep -q "$service.*healthy"; then
        print_success "$service is healthy"
    else
        print_error "$service is not healthy"
        all_healthy=false
    fi
done

if [ "$all_healthy" = true ]; then
    print_success "All services are healthy!"
else
    print_error "Some services are not healthy. Check logs:"
    print_status "docker-compose -f docker-compose.production.yml logs"
    exit 1
fi

# Display deployment information
echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📊 Service URLs:"
echo "   Frontend: http://localhost"
echo "   Backend API: http://localhost:8000"
echo "   Redis: localhost:6379"
echo ""
echo "🔐 Authentication Features:"
echo "   ✅ User Registration & Login"
echo "   ✅ Email Verification (SendGrid)"
echo "   ✅ Password Reset"
echo "   ✅ 2FA Support"
echo "   ✅ JWT Session Management"
echo "   ✅ Secure Password Hashing"
echo ""
echo "📈 Trading Features:"
echo "   ✅ Multi-Crypto Data Fetching"
echo "   ✅ Real-time Price Updates"
echo "   ✅ Portfolio Management"
echo "   ✅ AI Trading Recommendations"
echo "   ✅ Paper Trading Mode"
echo ""
echo "🔧 Management Commands:"
echo "   View logs: docker-compose -f docker-compose.production.yml logs -f"
echo "   Stop services: docker-compose -f docker-compose.production.yml down"
echo "   Restart: docker-compose -f docker-compose.production.yml restart"
echo ""
echo "🚨 Security Notes:"
echo "   • Make sure your .env file is secure and not committed to git"
echo "   • Database is using Neon PostgreSQL (external)"
echo "   • All passwords are hashed with bcrypt"
echo "   • HTTPS should be configured for production"
echo ""
