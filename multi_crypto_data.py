import aiohttp
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class MultiCryptoDataFetcher:
    def __init__(self):
        self.coindesk_api_key = os.getenv('COINDESK_API_KEY')
        self.newsapi_key = os.getenv('NEWSAPI_KEY')
        
        # Supported cryptocurrencies
        self.supported_cryptos = {
            'BTC': {'coingecko_id': 'bitcoin', 'name': 'Bitcoin'},
            'ETH': {'coingecko_id': 'ethereum', 'name': 'Ethereum'},
            'SOL': {'coingecko_id': 'solana', 'name': 'Solana'},
            'ADA': {'coingecko_id': 'cardano', 'name': 'Cardano'},
            'DOT': {'coingecko_id': 'polkadot', 'name': 'Polkadot'},
            'LINK': {'coingecko_id': 'chainlink', 'name': 'Chainlink'},
            'MATIC': {'coingecko_id': 'matic-network', 'name': 'Polygon'},
            'AVAX': {'coingecko_id': 'avalanche-2', 'name': 'Avalanche'}
        }
        
    async def get_crypto_prices(self, symbols: List[str] = None) -> Dict[str, Dict]:
        """Get current prices for multiple cryptocurrencies"""
        if not symbols:
            symbols = list(self.supported_cryptos.keys())
            
        try:
            # Get CoinGecko IDs for the symbols
            coingecko_ids = []
            symbol_map = {}
            
            for symbol in symbols:
                if symbol in self.supported_cryptos:
                    gecko_id = self.supported_cryptos[symbol]['coingecko_id']
                    coingecko_ids.append(gecko_id)
                    symbol_map[gecko_id] = symbol
            
            if not coingecko_ids:
                return {}
                
            ids_str = ','.join(coingecko_ids)
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_str}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true&include_24hr_vol=true"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        result = {}
                        for gecko_id, price_data in data.items():
                            symbol = symbol_map[gecko_id]
                            result[symbol] = {
                                "symbol": symbol,
                                "name": self.supported_cryptos[symbol]['name'],
                                "price": price_data.get("usd", 0),
                                "change_24h": price_data.get("usd_24h_change", 0),
                                "market_cap": price_data.get("usd_market_cap", 0),
                                "volume_24h": price_data.get("usd_24h_vol", 0),
                                "timestamp": datetime.now().isoformat(),
                                "source": "coingecko"
                            }
                        return result
                        
        except Exception as e:
            print(f"CoinGecko multi-crypto API error: {e}")
            
        # Return mock data if API fails
        return self._mock_crypto_prices(symbols)
    
    def _mock_crypto_prices(self, symbols: List[str]) -> Dict[str, Dict]:
        """Return mock price data for testing"""
        mock_prices = {
            'BTC': 45000,
            'ETH': 2800,
            'SOL': 95,
            'ADA': 0.45,
            'DOT': 6.2,
            'LINK': 14.5,
            'MATIC': 0.85,
            'AVAX': 18.2
        }
        
        result = {}
        for symbol in symbols:
            if symbol in mock_prices:
                result[symbol] = {
                    "symbol": symbol,
                    "name": self.supported_cryptos.get(symbol, {}).get('name', symbol),
                    "price": mock_prices[symbol],
                    "change_24h": (hash(symbol) % 20) - 10,  # Random change between -10 and 10
                    "market_cap": mock_prices[symbol] * 1000000,
                    "volume_24h": mock_prices[symbol] * 50000,
                    "timestamp": datetime.now().isoformat(),
                    "source": "mock"
                }
        return result
    
    async def get_crypto_news(self, symbols: List[str] = None, limit: int = 20) -> List[Dict]:
        """Get crypto news for multiple currencies"""
        if not symbols:
            symbols = ['BTC', 'ETH', 'SOL', 'crypto']
            
        # Create search query
        crypto_names = []
        for symbol in symbols:
            if symbol in self.supported_cryptos:
                crypto_names.append(self.supported_cryptos[symbol]['name'])
            crypto_names.append(symbol)
        
        search_query = ' OR '.join(crypto_names[:10])  # Limit query length
        
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": search_query,
                "sortBy": "publishedAt",
                "pageSize": limit,
                "language": "en",
                "domains": "coindesk.com,cointelegraph.com,decrypt.co,theblock.co"
            }
            headers = {"X-API-Key": self.newsapi_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        articles = []
                        for article in data.get("articles", []):
                            if article.get("title"):
                                # Determine which crypto this article is about
                                relevant_cryptos = []
                                title_desc = (article.get("title", "") + " " + article.get("description", "")).lower()
                                
                                for symbol, info in self.supported_cryptos.items():
                                    if symbol.lower() in title_desc or info['name'].lower() in title_desc:
                                        relevant_cryptos.append(symbol)
                                
                                articles.append({
                                    "title": article.get("title", ""),
                                    "description": article.get("description", ""),
                                    "url": article.get("url", ""),
                                    "published_at": article.get("publishedAt", ""),
                                    "source": article.get("source", {}).get("name", "Unknown") if article.get("source") else "Unknown",
                                    "sentiment": self._analyze_sentiment(title_desc),
                                    "relevant_cryptos": relevant_cryptos if relevant_cryptos else ["CRYPTO"]
                                })
                        return articles
                    else:
                        print(f"NewsAPI error: {response.status}")
                        return self._mock_crypto_news()
                        
        except Exception as e:
            print(f"NewsAPI error: {e}")
            return self._mock_crypto_news()
    
    def _mock_crypto_news(self) -> List[Dict]:
        """Return mock news data for testing"""
        return [
            {
                "title": "Bitcoin Reaches New All-Time High as Institutional Adoption Grows",
                "description": "Major corporations continue to add Bitcoin to their treasury reserves",
                "url": "https://example.com/btc-news-1",
                "published_at": datetime.now().isoformat(),
                "source": "Mock Crypto News",
                "sentiment": "positive",
                "relevant_cryptos": ["BTC"]
            },
            {
                "title": "Ethereum 2.0 Staking Rewards Attract More Validators",
                "description": "The transition to proof-of-stake continues to show promising results",
                "url": "https://example.com/eth-news-1",
                "published_at": datetime.now().isoformat(),
                "source": "Mock Blockchain Times",
                "sentiment": "positive",
                "relevant_cryptos": ["ETH"]
            },
            {
                "title": "Solana Network Experiences Brief Outage, Recovery Underway",
                "description": "Technical issues cause temporary disruption to the Solana blockchain",
                "url": "https://example.com/sol-news-1",
                "published_at": datetime.now().isoformat(),
                "source": "Mock DeFi Daily",
                "sentiment": "negative",
                "relevant_cryptos": ["SOL"]
            },
            {
                "title": "Regulatory Clarity Boosts Cryptocurrency Market Confidence",
                "description": "New guidelines provide clearer framework for digital asset operations",
                "url": "https://example.com/crypto-news-1",
                "published_at": datetime.now().isoformat(),
                "source": "Mock Regulatory Watch",
                "sentiment": "positive",
                "relevant_cryptos": ["BTC", "ETH", "ADA"]
            }
        ]
    
    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis"""
        positive_words = ["surge", "bull", "rally", "gain", "rise", "up", "positive", "growth", "strong", "adoption", "breakthrough"]
        negative_words = ["crash", "bear", "drop", "fall", "decline", "down", "negative", "loss", "volatility", "uncertainty", "outage", "hack"]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        return "neutral"
    
    async def get_market_overview(self) -> Dict:
        """Get comprehensive market overview"""
        prices = await self.get_crypto_prices()
        news = await self.get_crypto_news(limit=10)
        
        # Calculate market metrics
        total_market_cap = sum(crypto.get("market_cap", 0) for crypto in prices.values())
        
        # Sentiment analysis
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        for article in news:
            sentiment_counts[article["sentiment"]] += 1
        
        overall_sentiment = max(sentiment_counts, key=sentiment_counts.get)
        
        return {
            "prices": prices,
            "news": news,
            "market_metrics": {
                "total_market_cap": total_market_cap,
                "tracked_assets": len(prices),
                "news_sentiment": overall_sentiment,
                "sentiment_breakdown": sentiment_counts
            },
            "timestamp": datetime.now().isoformat(),
            "supported_cryptos": list(self.supported_cryptos.keys())
        }

# Example usage
async def main():
    fetcher = MultiCryptoDataFetcher()
    
    print("🚀 Multi-Crypto Market Data")
    print("=" * 50)
    
    # Get market overview
    market_data = await fetcher.get_market_overview()
    
    print(f"📊 Prices for {len(market_data['prices'])} cryptocurrencies:")
    for symbol, data in market_data['prices'].items():
        change_color = "🟢" if data['change_24h'] >= 0 else "🔴"
        print(f"  {change_color} {symbol}: ${data['price']:,.2f} ({data['change_24h']:+.2f}%)")
    
    print(f"\n📰 Latest {len(market_data['news'])} news articles:")
    for article in market_data['news'][:5]:
        sentiment_emoji = "🟢" if article['sentiment'] == 'positive' else "🔴" if article['sentiment'] == 'negative' else "🟡"
        cryptos = ", ".join(article['relevant_cryptos'])
        print(f"  {sentiment_emoji} {article['title']} [{cryptos}]")
    
    print(f"\n📈 Market Overview:")
    print(f"  Total Market Cap: ${market_data['market_metrics']['total_market_cap']:,.0f}")
    print(f"  Overall Sentiment: {market_data['market_metrics']['news_sentiment']}")
    print(f"  Supported Assets: {', '.join(market_data['supported_cryptos'])}")

if __name__ == "__main__":
    asyncio.run(main())
