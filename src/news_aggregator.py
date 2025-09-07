import aiohttp
import feedparser
import asyncio
import time
import hashlib
from typing import Dict, List, Optional, Protocol
from datetime import datetime, timedelta
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from .config import settings
from .redis_client import redis_client


class NewsProvider(Protocol):
    async def fetch(self, symbols: List[str]) -> List[Dict]: ...


class MarketWatchProvider:
    def __init__(self):
        self.base_url = "https://feeds.marketwatch.com/marketwatch/cryptocurrency"
        self.name = "marketwatch"
    
    async def fetch(self, symbols: List[str]) -> List[Dict]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)
                        
                        news_items = []
                        for entry in feed.entries[:20]:
                            news_items.append({
                                "source": self.name,
                                "title": entry.get("title", ""),
                                "url": entry.get("link", ""),
                                "published_at": self._parse_date(entry.get("published", "")),
                                "content": entry.get("summary", ""),
                                "symbols": self._extract_symbols(entry.get("title", "") + " " + entry.get("summary", ""))
                            })
                        
                        return news_items
        except Exception as e:
            print(f"MarketWatch fetch error: {e}")
            return []
    
    def _parse_date(self, date_str: str) -> datetime:
        try:
            from datetime import timezone
            dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
            return dt.replace(tzinfo=timezone.utc)
        except:
            from datetime import timezone
            return datetime.now(timezone.utc)
    
    def _extract_symbols(self, text: str) -> List[str]:
        symbols = []
        text_upper = text.upper()
        crypto_symbols = ["BTC", "ETH", "XRP", "ADA", "SOL", "DOGE", "MATIC", "DOT", "AVAX", "LINK"]
        for symbol in crypto_symbols:
            if symbol in text_upper:
                symbols.append(symbol)
        return symbols


class NewsAPIProvider:
    def __init__(self):
        self.api_key = settings.newsapi_key
        self.base_url = "https://newsapi.org/v2/everything"
        self.name = "newsapi"
    
    async def fetch(self, symbols: List[str]) -> List[Dict]:
        if not self.api_key:
            return []
        
        try:
            query = " OR ".join([f'"{symbol}"' for symbol in symbols])
            params = {
                "q": f"cryptocurrency OR crypto OR {query}",
                "apiKey": self.api_key,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 20
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        news_items = []
                        for article in data.get("articles", []):
                            news_items.append({
                                "source": self.name,
                                "title": article.get("title", ""),
                                "url": article.get("url", ""),
                                "published_at": self._parse_date(article.get("publishedAt", "")),
                                "content": article.get("description", ""),
                                "symbols": self._extract_symbols(article.get("title", "") + " " + article.get("description", ""))
                            })
                        
                        return news_items
        except Exception as e:
            print(f"NewsAPI fetch error: {e}")
            return []
    
    def _parse_date(self, date_str: str) -> datetime:
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            from datetime import timezone
            return datetime.now(timezone.utc)
    
    def _extract_symbols(self, text: str) -> List[str]:
        symbols = []
        text_upper = text.upper()
        crypto_symbols = ["BTC", "ETH", "XRP", "ADA", "SOL", "DOGE", "MATIC", "DOT", "AVAX", "LINK"]
        for symbol in crypto_symbols:
            if symbol in text_upper:
                symbols.append(symbol)
        return symbols


class GNewsProvider:
    def __init__(self):
        self.api_key = settings.gnews_key
        self.base_url = "https://gnews.io/api/v4/search"
        self.name = "gnews"
    
    async def fetch(self, symbols: List[str]) -> List[Dict]:
        if not self.api_key:
            return []
        
        try:
            query = " OR ".join([f'"{symbol}"' for symbol in symbols])
            params = {
                "q": f"cryptocurrency OR crypto OR {query}",
                "token": self.api_key,
                "lang": "en",
                "max": 20
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        news_items = []
                        for article in data.get("articles", []):
                            news_items.append({
                                "source": self.name,
                                "title": article.get("title", ""),
                                "url": article.get("url", ""),
                                "published_at": self._parse_date(article.get("publishedAt", "")),
                                "content": article.get("content", ""),
                                "symbols": self._extract_symbols(article.get("title", "") + " " + article.get("content", ""))
                            })
                        
                        return news_items
        except Exception as e:
            print(f"GNews fetch error: {e}")
            return []
    
    def _parse_date(self, date_str: str) -> datetime:
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            from datetime import timezone
            return datetime.now(timezone.utc)
    
    def _extract_symbols(self, text: str) -> List[str]:
        symbols = []
        text_upper = text.upper()
        crypto_symbols = ["BTC", "ETH", "XRP", "ADA", "SOL", "DOGE", "MATIC", "DOT", "AVAX", "LINK"]
        for symbol in crypto_symbols:
            if symbol in text_upper:
                symbols.append(symbol)
        return symbols


class NewsAggregator:
    def __init__(self):
        self.providers = [MarketWatchProvider()]
        
        if settings.news_secondary == "NewsAPI" and settings.newsapi_key:
            self.providers.append(NewsAPIProvider())
        elif settings.news_secondary == "GNews" and settings.gnews_key:
            self.providers.append(GNewsProvider())
        
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.credibility_weights = settings.credibility_weights
    
    def _calculate_sentiment(self, text: str) -> float:
        if not text:
            return 0.0
        
        scores = self.sentiment_analyzer.polarity_scores(text)
        return scores["compound"]
    
    def _calculate_recency_decay(self, published_at: datetime) -> float:
        from datetime import timezone
        now = datetime.now(timezone.utc)
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        age_minutes = (now - published_at).total_seconds() / 60
        half_life = settings.news_recency_half_life_min
        return 2 ** (-age_minutes / half_life)
    
    def _calculate_credibility(self, source: str) -> float:
        return self.credibility_weights.get(source, 0.5)
    
    def _deduplicate_news(self, news_items: List[Dict]) -> List[Dict]:
        seen_urls = set()
        seen_hashes = set()
        unique_items = []
        
        for item in news_items:
            url = item.get("url", "")
            content_hash = hashlib.md5(
                (item.get("title", "") + item.get("content", "")).encode()
            ).hexdigest()
            
            if url not in seen_urls and content_hash not in seen_hashes:
                seen_urls.add(url)
                seen_hashes.add(content_hash)
                unique_items.append(item)
        
        return unique_items
    
    async def fetch_news(self, symbols: List[str]) -> List[Dict]:
        all_news = []
        
        for provider in self.providers:
            try:
                if redis_client.is_rate_limited(f"news_{provider.name}", 10, 60):
                    print(f"Rate limited for {provider.name}")
                    continue
                
                news_items = await provider.fetch(symbols)
                all_news.extend(news_items)
                
                for symbol in symbols:
                    symbol_news = [item for item in news_items if symbol in item.get("symbols", [])]
                    redis_client.set_news_data(provider.name, symbol, symbol_news, ttl=1800)
                
            except Exception as e:
                print(f"Error fetching from {provider.name}: {e}")
        
        unique_news = self._deduplicate_news(all_news)
        
        for item in unique_news:
            item["sentiment"] = self._calculate_sentiment(
                item.get("title", "") + " " + item.get("content", "")
            )
            item["recency_score"] = self._calculate_recency_decay(item["published_at"])
            item["credibility_score"] = self._calculate_credibility(item["source"])
            item["weight"] = (
                abs(item["sentiment"]) * 
                item["recency_score"] * 
                item["credibility_score"]
            )
        
        return sorted(unique_news, key=lambda x: x["weight"], reverse=True)
    
    async def get_news_for_symbol(self, symbol: str, limit: int = 10) -> List[Dict]:
        cached_news = []
        for provider in self.providers:
            cached = redis_client.get_news_data(provider.name, symbol)
            if cached:
                cached_news.extend(cached)
        
        if cached_news:
            return sorted(cached_news, key=lambda x: x.get("weight", 0), reverse=True)[:limit]
        
        fresh_news = await self.fetch_news([symbol])
        return fresh_news[:limit]
    
    def get_news_summary(self, news_items: List[Dict], top_k: int = 5) -> Dict:
        if not news_items:
            return {
                "items": [],
                "avg_sentiment": 0.0,
                "negative_news_count": 0,
                "positive_news_count": 0,
                "high_impact_news": []
            }
        
        top_news = news_items[:top_k]
        sentiments = [item.get("sentiment", 0) for item in news_items]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
        
        negative_count = sum(1 for s in sentiments if s < -0.1)
        positive_count = sum(1 for s in sentiments if s > 0.1)
        
        high_impact = [
            item for item in news_items 
            if item.get("weight", 0) > 0.7 and abs(item.get("sentiment", 0)) > 0.3
        ]
        
        return {
            "items": [
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "sentiment": item.get("sentiment", 0),
                    "weight": item.get("weight", 0),
                    "source": item.get("source", ""),
                    "published_at": item["published_at"].isoformat()
                }
                for item in top_news
            ],
            "avg_sentiment": avg_sentiment,
            "negative_news_count": negative_count,
            "positive_news_count": positive_count,
            "high_impact_news": [
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "sentiment": item.get("sentiment", 0),
                    "weight": item.get("weight", 0)
                }
                for item in high_impact[:3]
            ]
        }


news_aggregator = NewsAggregator()
