# Quick Start

## 1. Get API Keys
- CoinDesk: https://data-api.coindesk.com
- Neon: https://neon.tech  
- NewsAPI: https://newsapi.org

## 2. Configure
```bash
cp env.example .env
# Edit .env with your keys
```

## 3. Run
```bash
docker-compose up -d
pip install -r requirements.txt
python main.py
```

## 4. Test
```bash
curl http://localhost:8000/health
curl http://localhost:8000/portfolio/1
```

## 5. Start Agent
```bash
python run_agent.py 1 --instrument XBX-USD
```
