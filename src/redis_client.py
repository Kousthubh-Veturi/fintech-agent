import redis
import json
import time
from typing import Any, Optional, Dict, List
from .config import settings


class RedisClient:
    def __init__(self):
        self.redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        self.rate_limit_prefix = "rate_limit:"
        self.cache_prefix = "cache:"
        self.news_prefix = "news:"
        self.ohlc_prefix = "ohlc:"
    
    async def ping(self) -> bool:
        try:
            return self.redis.ping()
        except Exception:
            return False
    
    def cache_set(self, key: str, value: Any, ttl: int = 300) -> bool:
        try:
            serialized = json.dumps(value) if not isinstance(value, str) else value
            return self.redis.setex(f"{self.cache_prefix}{key}", ttl, serialized)
        except Exception as e:
            print(f"Redis cache_set error: {e}")
            return False
    
    def cache_get(self, key: str) -> Optional[Any]:
        try:
            value = self.redis.get(f"{self.cache_prefix}{key}")
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            print(f"Redis cache_get error: {e}")
            return None
    
    def cache_delete(self, key: str) -> bool:
        try:
            return bool(self.redis.delete(f"{self.cache_prefix}{key}"))
        except Exception as e:
            print(f"Redis cache_delete error: {e}")
            return False
    
    def set_ohlc_data(self, symbol: str, timeframe: str, data: List[Dict], ttl: int = 300) -> bool:
        key = f"{self.ohlc_prefix}{symbol}:{timeframe}"
        return self.cache_set(key, data, ttl)
    
    def get_ohlc_data(self, symbol: str, timeframe: str) -> Optional[List[Dict]]:
        key = f"{self.ohlc_prefix}{symbol}:{timeframe}"
        return self.cache_get(key)
    
    def set_latest_price(self, symbol: str, price: float, ttl: int = 60) -> bool:
        key = f"price:{symbol}:latest"
        return self.cache_set(key, price, ttl)
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        key = f"price:{symbol}:latest"
        return self.cache_get(key)
    
    def set_news_data(self, source: str, symbol: str, data: List[Dict], ttl: int = 1800) -> bool:
        key = f"{self.news_prefix}{source}:{symbol}"
        return self.cache_set(key, data, ttl)
    
    def get_news_data(self, source: str, symbol: str) -> Optional[List[Dict]]:
        key = f"{self.news_prefix}{source}:{symbol}"
        return self.cache_get(key)
    
    def is_rate_limited(self, client_id: str, max_requests: int, window_seconds: int) -> bool:
        try:
            key = f"{self.rate_limit_prefix}{client_id}"
            current_time = int(time.time())
            window_start = current_time - window_seconds
            
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {current_time: current_time})
            pipe.expire(key, window_seconds)
            
            results = pipe.execute()
            current_requests = results[1]
            
            return current_requests >= max_requests
        except Exception as e:
            print(f"Redis rate limit error: {e}")
            return True
    
    def get_rate_limit_remaining(self, client_id: str, max_requests: int, window_seconds: int) -> int:
        try:
            key = f"{self.rate_limit_prefix}{client_id}"
            current_time = int(time.time())
            window_start = current_time - window_seconds
            
            self.redis.zremrangebyscore(key, 0, window_start)
            current_requests = self.redis.zcard(key)
            
            return max(0, max_requests - current_requests)
        except Exception as e:
            print(f"Redis rate limit check error: {e}")
            return 0
    
    def set_market_data(self, symbol: str, data: Dict, ttl: int = 60) -> bool:
        key = f"market:{symbol}"
        return self.cache_set(key, data, ttl)
    
    def get_market_data(self, symbol: str) -> Optional[Dict]:
        key = f"market:{symbol}"
        return self.cache_get(key)
    
    def set_portfolio_data(self, user_id: str, data: Dict, ttl: int = 30) -> bool:
        key = f"portfolio:{user_id}"
        return self.cache_set(key, data, ttl)
    
    def get_portfolio_data(self, user_id: str) -> Optional[Dict]:
        key = f"portfolio:{user_id}"
        return self.cache_get(key)
    
    def invalidate_portfolio_cache(self, user_id: str) -> bool:
        key = f"portfolio:{user_id}"
        return self.cache_delete(key)
    
    def get_all_keys(self, pattern: str = "*") -> List[str]:
        try:
            return self.redis.keys(pattern)
        except Exception as e:
            print(f"Redis keys error: {e}")
            return []
    
    def flush_all(self) -> bool:
        try:
            return self.redis.flushall()
        except Exception as e:
            print(f"Redis flush error: {e}")
            return False


redis_client = RedisClient()
