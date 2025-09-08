import aiohttp
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class BTCDataFetcher:
    def __init__(self):
        self.coindesk_api_key = os.getenv('COINDESK_API_KEY')
        self.newsapi_key = os.getenv('NEWSAPI_KEY')
        
    async def get_btc_price(self) -> Dict:
        """Get current BTC price from CoinDesk"""
        try:
            url = "https://data-api.coindesk.com/index/cc/v2/historical/messages"
            params = {
                "market": "sda",
                "instrument": "XBX-USD", 
                "after_ts": int(datetime.now().timestamp()) - 60,
                "limit": 1,
                "groups": "MESSAGE"
            }
            headers = {"Authorization": f"Bearer {self.coindesk_api_key}"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("Data") and len(data["Data"]) > 0:
                            latest = data["Data"][-1]
                            return {
                                "price": latest.get("VALUE"),
                                "timestamp": latest.get("LAST_UPDATE"),
                                "instrument": "BTC-USD",
                                "source": "coindesk"
                            }
        except Exception as e:
            print(f"CoinDesk API error: {e}")
            
        return await self._fallback_btc_price()
    
    async def _fallback_btc_price(self) -> Dict:
        """Fallback to multiple free APIs if CoinDesk fails"""
        # Try CoinGecko first
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "price": float(data["bitcoin"]["usd"]),
                            "timestamp": datetime.now().isoformat(),
                            "instrument": "BTC-USD",
                            "source": "coingecko"
                        }
        except Exception as e:
            print(f"CoinGecko API error: {e}")
        
        # Try CoinDesk free API
        try:
            url = "https://api.coindesk.com/v1/bpi/currentprice/USD.json"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        price_str = data["bpi"]["USD"]["rate"].replace(",", "").replace("$", "")
                        return {
                            "price": float(price_str),
                            "timestamp": datetime.now().isoformat(),
                            "instrument": "BTC-USD",
                            "source": "coindesk_free"
                        }
        except Exception as e:
            print(f"CoinDesk free API error: {e}")
        
        # Return mock data if all APIs fail
        return {
            "price": 45000.0,  # Mock price for testing
            "timestamp": datetime.now().isoformat(),
            "instrument": "BTC-USD",
            "source": "mock",
            "note": "Using mock data - APIs unavailable"
        }
    
    async def get_btc_news(self, limit: int = 10) -> List[Dict]:
        """Get BTC news from NewsAPI"""
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": "bitcoin OR BTC",
                "sortBy": "publishedAt",
                "pageSize": limit,
                "language": "en"
            }
            headers = {"X-API-Key": self.newsapi_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        articles = []
                        for article in data.get("articles", []):
                            if article.get("title"):  # Only include articles with titles
                                articles.append({
                                    "title": article.get("title", ""),
                                    "description": article.get("description", ""),
                                    "url": article.get("url", ""),
                                    "published_at": article.get("publishedAt", ""),
                                    "source": article.get("source", {}).get("name", "Unknown") if article.get("source") else "Unknown",
                                    "sentiment": "neutral"
                                })
                        return articles
                    else:
                        print(f"NewsAPI error: {response.status}")
                        return self._mock_news()
        except Exception as e:
            print(f"NewsAPI error: {e}")
            return self._mock_news()
    
    def _mock_news(self) -> List[Dict]:
        """Return mock news data for testing"""
        return [
            {
                "title": "Bitcoin Shows Strong Performance Amid Market Volatility",
                "description": "BTC maintains resilience as institutional interest continues to grow",
                "url": "https://example.com/btc-news-1",
                "published_at": datetime.now().isoformat(),
                "source": "Mock Financial News",
                "sentiment": "positive"
            },
            {
                "title": "Cryptocurrency Market Analysis: BTC Technical Indicators",
                "description": "Technical analysis suggests potential support levels for Bitcoin",
                "url": "https://example.com/btc-news-2", 
                "published_at": datetime.now().isoformat(),
                "source": "Mock Crypto Times",
                "sentiment": "neutral"
            },
            {
                "title": "Regulatory Updates Impact Bitcoin Trading Volume",
                "description": "New regulations create uncertainty in the cryptocurrency market",
                "url": "https://example.com/btc-news-3",
                "published_at": datetime.now().isoformat(),
                "source": "Mock Regulatory Watch",
                "sentiment": "negative"
            }
        ]
    
    async def get_market_data(self) -> Dict:
        """Get comprehensive BTC market data"""
        price_data = await self.get_btc_price()
        news_data = await self.get_btc_news()
        
        return {
            "price": price_data,
            "news": news_data,
            "timestamp": datetime.now().isoformat(),
            "market_status": "open" if datetime.now().weekday() < 5 else "closed"
        }

async def main():
    fetcher = BTCDataFetcher()
    data = await fetcher.get_market_data()
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
