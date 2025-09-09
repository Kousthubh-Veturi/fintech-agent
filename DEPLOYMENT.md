# 🚀 Fintech Agent Deployment Guide

Complete deployment guide for the Fintech Agent with authentication system.

## 📋 Prerequisites

### Required
- Docker & Docker Compose
- Git
- Domain name (for production)
- SSL certificate (for production HTTPS)

### Required API Keys & Services
- **Neon PostgreSQL Database**: Your connection URL
- **SendGrid Account**: For email verification and password resets
- **CoinDesk API**: For cryptocurrency data (optional key)
- **NewsAPI**: For market news (optional)

### Optional OAuth Providers
- Google OAuth (Client ID & Secret)
- GitHub OAuth (Client ID & Secret)

## 🛠️ Environment Setup

### 1. Clone and Configure

```bash
git clone <your-repo-url>
cd fintech-agent
cp env.example .env
```

### 2. Edit Environment Variables

Edit `.env` file with your actual values:

```bash
# Database (REQUIRED)
DATABASE_URL=postgresql://username:password@host:port/database

# Authentication (REQUIRED)
SECRET_KEY=your-super-secret-jwt-key-here
SENDGRID_API_KEY=SG.your-sendgrid-api-key-here
FROM_EMAIL=your-verified-email@domain.com

# Trading APIs (OPTIONAL)
COINDESK_API_KEY=your-coindesk-api-key
NEWSAPI_KEY=your-newsapi-key

# OAuth (OPTIONAL)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# Redis (AUTO-CONFIGURED)
REDIS_PASSWORD=fintech_redis_pass
```

## 🏗️ Deployment Options

### Option 1: Production Deployment (Recommended)

**Full Docker deployment with all services:**

```bash
# Make script executable
chmod +x deploy.production.sh

# Deploy
./deploy.production.sh
```

**Services will be available at:**
- Frontend: `http://localhost` (port 80)
- Backend API: `http://localhost:8000`
- Redis: `localhost:6379`

### Option 2: Development Setup

**For development with hot-reload:**

```bash
# Setup development environment
chmod +x deploy.dev.sh
./deploy.dev.sh

# Start backend (Terminal 1)
source python/venv/bin/activate
python enhanced_main.py

# Start frontend (Terminal 2)
cd frontend
npm start
```

**Services will be available at:**
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`

### Option 3: Manual Docker Deployment

```bash
# Production
docker-compose -f docker-compose.production.yml up --build -d

# Development (with local database)
docker-compose -f docker-compose.yml up --build -d
```

## 🔐 Authentication System Features

### ✅ Implemented Features
- **User Registration** with email verification
- **Secure Login** with JWT tokens
- **Password Reset** via email
- **2FA Support** with TOTP and backup codes
- **OAuth Ready** (Google, GitHub)
- **Session Management** with secure tokens
- **Password Hashing** with bcrypt (64-bit encryption)

### 🔧 Email Configuration
1. Create SendGrid account
2. Verify your sender email in SendGrid dashboard
3. Generate API key
4. Add both to `.env` file

### 🛡️ Security Features
- Rate limiting on authentication endpoints
- CORS protection
- Security headers (XSS, CSRF protection)
- Secure password requirements
- JWT token expiration
- SQL injection protection

## 📊 Trading System Features

### ✅ Implemented Features
- **Multi-Cryptocurrency Support**: BTC, ETH, SOL, ADA, DOT, LINK, MATIC, AVAX
- **Real-time Price Data**: Live market data updates
- **Portfolio Management**: Track holdings and performance
- **AI Trading Agent**: Automated trading recommendations
- **Paper Trading**: Safe testing environment
- **News Integration**: Market sentiment analysis
- **Technical Indicators**: Advanced trading signals

## 🌐 Production Deployment (VPS/Cloud)

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Domain & SSL Setup

```bash
# Install Certbot for Let's Encrypt SSL
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com
```

### 3. Deploy Application

```bash
# Clone repository
git clone <your-repo-url>
cd fintech-agent

# Configure environment
cp env.example .env
nano .env  # Edit with your values

# Deploy
./deploy.production.sh
```

### 4. Nginx Reverse Proxy (Optional)

Create `/etc/nginx/sites-available/fintech-agent`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🔧 Management Commands

### Docker Management
```bash
# View logs
docker-compose -f docker-compose.production.yml logs -f

# Restart services
docker-compose -f docker-compose.production.yml restart

# Stop services
docker-compose -f docker-compose.production.yml down

# Update and redeploy
git pull
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up --build -d
```

### Database Management
```bash
# Connect to database
psql $DATABASE_URL

# Backup database
pg_dump $DATABASE_URL > backup.sql

# Restore database
psql $DATABASE_URL < backup.sql
```

### Health Checks
```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend health
curl http://localhost:80/health

# Check all services
docker-compose -f docker-compose.production.yml ps
```

## 🚨 Troubleshooting

### Common Issues

**1. Database Connection Failed**
```bash
# Check DATABASE_URL format
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1;"
```

**2. Email Not Sending**
- Verify SendGrid API key
- Check sender email is verified in SendGrid
- Check spam folder

**3. Frontend Not Loading**
```bash
# Check nginx logs
docker-compose logs frontend

# Rebuild frontend
docker-compose build frontend
```

**4. Redis Connection Issues**
```bash
# Check redis logs
docker-compose logs redis

# Test redis connection
redis-cli -h localhost -p 6379 ping
```

### Log Locations
- Backend logs: `docker-compose logs backend`
- Frontend logs: `docker-compose logs frontend`
- Redis logs: `docker-compose logs redis`
- Nginx logs: Inside frontend container at `/var/log/nginx/`

## 📈 Monitoring & Scaling

### Health Monitoring
- Backend health: `GET /health`
- Frontend health: `GET /health`
- Database health: Connection pooling with retry logic
- Redis health: Built-in health checks

### Performance Optimization
- Frontend: Gzip compression, static asset caching
- Backend: Connection pooling, async operations
- Database: Neon PostgreSQL with connection pooling
- Redis: Persistent storage with AOF

### Scaling Options
- **Horizontal**: Multiple backend instances behind load balancer
- **Vertical**: Increase container resources
- **Database**: Neon PostgreSQL auto-scales
- **Redis**: Redis Cluster for high availability

## 🛡️ Security Checklist

### ✅ Implemented
- [x] HTTPS/SSL certificates
- [x] Environment variables for secrets
- [x] Password hashing with bcrypt
- [x] JWT token authentication
- [x] Rate limiting
- [x] CORS protection
- [x] Security headers
- [x] SQL injection protection
- [x] XSS protection

### 📋 Additional Recommendations
- [ ] Regular security updates
- [ ] Database backups
- [ ] Log monitoring
- [ ] Firewall configuration
- [ ] Intrusion detection
- [ ] Regular penetration testing

## 📞 Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Verify environment variables
3. Check service health endpoints
4. Review this documentation

---

**🎉 Congratulations! Your Fintech Agent with complete authentication system is now deployed!**
