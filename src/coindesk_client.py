import aiohttp
import asyncio
import websockets
import json
import time
from typing import Dict, List, Optional, Any
from .config import settings
from .redis_client import redis_client


class CoinDeskClient:
    def __init__(self):
        self.base_url = "https://data-api.coindesk.com"
        self.ws_url = "wss://data-streamer.coindesk.com"
        self.api_key = settings.coindesk_api_key
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict]:
        if not self.session:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(f"{self.base_url}{endpoint}", params=params, timeout=10) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"CoinDesk API error: {response.status} - {await response.text()}")
                        return None
        else:
            async with self.session.get(f"{self.base_url}{endpoint}", params=params, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"CoinDesk API error: {response.status} - {await response.text()}")
                    return None
    
    async def get_historical_ohlc(self, instrument: str = "XBX-USD", timeframe: str = "minutes", 
                                 limit: int = 120, market: str = "sda") -> Optional[List[Dict]]:
        cache_key = f"{instrument}:{timeframe}:{limit}"
        cached_data = redis_client.get_ohlc_data(cache_key, timeframe)
        if cached_data:
            return cached_data
        
        if redis_client.is_rate_limited("coindesk_ohlc", 100, 60):
            print("Rate limited for OHLC data")
            return None
        
        endpoint = f"/index/cc/v1/historical/{timeframe}"
        params = {
            "market": market,
            "instrument": instrument,
            "limit": limit,
            "groups": "OHLC,VOLUME"
        }
        
        data = await self._make_request(endpoint, params)
        if data and "Data" in data:
            ohlc_data = data["Data"]
            redis_client.set_ohlc_data(cache_key, timeframe, ohlc_data, ttl=300)
            return ohlc_data
        
        return None
    
    async def get_latest_tick(self, instrument: str = "XBX-USD", market: str = "sda") -> Optional[Dict]:
        cache_key = f"tick:{instrument}"
        cached_tick = redis_client.cache_get(cache_key)
        if cached_tick:
            return cached_tick
        
        if redis_client.is_rate_limited("coindesk_tick", 200, 60):
            print("Rate limited for tick data")
            return None
        
        endpoint = "/index/cc/v2/historical/messages"
        current_time = int(time.time())
        params = {
            "market": market,
            "instrument": instrument,
            "after_ts": current_time - 60,
            "limit": 1,
            "groups": "MESSAGE"
        }
        
        data = await self._make_request(endpoint, params)
        if data and "Data" in data and data["Data"]:
            latest_tick = data["Data"][-1]
            redis_client.cache_set(cache_key, latest_tick, ttl=30)
            return latest_tick
        
        return None
    
    async def get_latest_price(self, instrument: str = "XBX-USD") -> Optional[float]:
        cached_price = redis_client.get_latest_price(instrument)
        if cached_price:
            return cached_price
        
        tick_data = await self.get_latest_tick(instrument)
        if tick_data and "VALUE" in tick_data:
            price = float(tick_data["VALUE"])
            redis_client.set_latest_price(instrument, price, ttl=30)
            return price
        
        return None
    
    async def get_ohlc_daily(self, instrument: str = "XBX-USD", days: int = 30) -> Optional[List[Dict]]:
        return await self.get_historical_ohlc(instrument, "days", days)
    
    async def get_ohlc_hourly(self, instrument: str = "XBX-USD", hours: int = 24) -> Optional[List[Dict]]:
        return await self.get_historical_ohlc(instrument, "hours", hours)
    
    async def get_ohlc_minutes(self, instrument: str = "XBX-USD", minutes: int = 120) -> Optional[List[Dict]]:
        return await self.get_historical_ohlc(instrument, "minutes", minutes)
    
    async def stream_ticks(self, instruments: List[str] = None, callback=None):
        if not instruments:
            instruments = ["XBX-USD"]
        
        ws_url = f"{self.ws_url}?api_key={self.api_key}"
        
        try:
            async with websockets.connect(ws_url, ping_interval=15, ping_timeout=60) as websocket:
                subscribe_message = {
                    "action": "SUBSCRIBE",
                    "type": "index_cc_v1_latest_tick",
                    "groups": ["VALUE", "LAST_UPDATE"],
                    "market": "sda",
                    "instruments": instruments
                }
                
                await websocket.send(json.dumps(subscribe_message))
                print(f"Subscribed to tick stream for {instruments}")
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        if callback:
                            await callback(data)
                        else:
                            print(f"Tick data: {data}")
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                    except Exception as e:
                        print(f"Message processing error: {e}")
                        
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed")
        except Exception as e:
            print(f"WebSocket error: {e}")
    
    async def get_market_summary(self, instruments: List[str] = None) -> Dict[str, Any]:
        if not instruments:
            instruments = ["XBX-USD"]
        
        market_data = {}
        
        for instrument in instruments:
            try:
                price = await self.get_latest_price(instrument)
                ohlc_1h = await self.get_ohlc_hourly(instrument, 1)
                ohlc_1d = await self.get_ohlc_daily(instrument, 1)
                
                market_data[instrument] = {
                    "price": price,
                    "ohlc_1h": ohlc_1h[0] if ohlc_1h else None,
                    "ohlc_1d": ohlc_1d[0] if ohlc_1d else None,
                    "timestamp": time.time()
                }
                
                redis_client.set_market_data(instrument, market_data[instrument], ttl=60)
                
            except Exception as e:
                print(f"Error getting market data for {instrument}: {e}")
                market_data[instrument] = None
        
        return market_data


async def get_coindesk_client() -> CoinDeskClient:
    return CoinDeskClient()
