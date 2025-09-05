import numpy as np
import pandas as pd
from typing import List, Dict, Optional
import ta


class TechnicalIndicators:
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> List[float]:
        if len(prices) < period:
            return [np.nan] * len(prices)
        
        df = pd.DataFrame({"close": prices})
        ema = ta.trend.EMAIndicator(df["close"], window=period).ema_indicator()
        return ema.fillna(method="bfill").tolist()
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
        if len(prices) < period + 1:
            return [np.nan] * len(prices)
        
        df = pd.DataFrame({"close": prices})
        rsi = ta.momentum.RSIIndicator(df["close"], window=period).rsi()
        return rsi.fillna(50).tolist()
    
    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, List[float]]:
        if len(prices) < slow:
            return {"macd": [np.nan] * len(prices), "signal": [np.nan] * len(prices), "histogram": [np.nan] * len(prices)}
        
        df = pd.DataFrame({"close": prices})
        macd_indicator = ta.trend.MACD(df["close"], window_fast=fast, window_slow=slow, window_sign=signal)
        
        return {
            "macd": macd_indicator.macd().fillna(0).tolist(),
            "signal": macd_indicator.macd_signal().fillna(0).tolist(),
            "histogram": macd_indicator.macd_diff().fillna(0).tolist()
        }
    
    @staticmethod
    def calculate_atr(high: List[float], low: List[float], close: List[float], period: int = 14) -> List[float]:
        if len(high) < period or len(low) < period or len(close) < period:
            return [np.nan] * len(close)
        
        df = pd.DataFrame({"high": high, "low": low, "close": close})
        atr = ta.volatility.AverageTrueRange(df["high"], df["low"], df["close"], window=period).average_true_range()
        return atr.fillna(method="bfill").tolist()
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2) -> Dict[str, List[float]]:
        if len(prices) < period:
            return {"upper": [np.nan] * len(prices), "middle": [np.nan] * len(prices), "lower": [np.nan] * len(prices)}
        
        df = pd.DataFrame({"close": prices})
        bb_indicator = ta.volatility.BollingerBands(df["close"], window=period, window_dev=std_dev)
        
        return {
            "upper": bb_indicator.bollinger_hband().fillna(method="bfill").tolist(),
            "middle": bb_indicator.bollinger_mavg().fillna(method="bfill").tolist(),
            "lower": bb_indicator.bollinger_lband().fillna(method="bfill").tolist()
        }
    
    @staticmethod
    def calculate_stochastic(high: List[float], low: List[float], close: List[float], 
                           k_period: int = 14, d_period: int = 3) -> Dict[str, List[float]]:
        if len(high) < k_period or len(low) < k_period or len(close) < k_period:
            return {"k": [np.nan] * len(close), "d": [np.nan] * len(close)}
        
        df = pd.DataFrame({"high": high, "low": low, "close": close})
        stoch_indicator = ta.momentum.StochasticOscillator(df["high"], df["low"], df["close"], 
                                                          window=k_period, smooth_window=d_period)
        
        return {
            "k": stoch_indicator.stoch().fillna(50).tolist(),
            "d": stoch_indicator.stoch_signal().fillna(50).tolist()
        }
    
    @staticmethod
    def calculate_volume_indicators(close: List[float], volume: List[float]) -> Dict[str, List[float]]:
        if len(close) < 20 or len(volume) < 20:
            return {"obv": [0] * len(close), "volume_sma": [0] * len(close)}
        
        df = pd.DataFrame({"close": close, "volume": volume})
        
        obv = ta.volume.OnBalanceVolumeIndicator(df["close"], df["volume"]).on_balance_volume()
        volume_sma = ta.volume.VolumeSMAIndicator(df["volume"], window=20).volume_sma()
        
        return {
            "obv": obv.fillna(0).tolist(),
            "volume_sma": volume_sma.fillna(0).tolist()
        }
    
    @staticmethod
    def calculate_trend_strength(prices: List[float], period: int = 20) -> List[float]:
        if len(prices) < period:
            return [0] * len(prices)
        
        df = pd.DataFrame({"close": prices})
        adx = ta.trend.ADXIndicator(df["close"], df["close"], df["close"], window=period).adx()
        return adx.fillna(0).tolist()
    
    @staticmethod
    def calculate_support_resistance(prices: List[float], window: int = 20) -> Dict[str, List[float]]:
        if len(prices) < window:
            return {"support": [np.nan] * len(prices), "resistance": [np.nan] * len(prices)}
        
        support = []
        resistance = []
        
        for i in range(len(prices)):
            start_idx = max(0, i - window + 1)
            window_prices = prices[start_idx:i+1]
            
            if len(window_prices) < 3:
                support.append(np.nan)
                resistance.append(np.nan)
                continue
            
            local_min = min(window_prices)
            local_max = max(window_prices)
            
            support.append(local_min)
            resistance.append(local_max)
        
        return {
            "support": support,
            "resistance": resistance
        }
    
    @staticmethod
    def calculate_all_indicators(ohlc_data: List[Dict]) -> Dict[str, any]:
        if not ohlc_data or len(ohlc_data) < 20:
            return {}
        
        closes = [float(candle["close"]) for candle in ohlc_data]
        highs = [float(candle["high"]) for candle in ohlc_data]
        lows = [float(candle["low"]) for candle in ohlc_data]
        volumes = [float(candle.get("volume", 0)) for candle in ohlc_data]
        
        indicators = {}
        
        try:
            indicators["ema_12"] = TechnicalIndicators.calculate_ema(closes, 12)
            indicators["ema_26"] = TechnicalIndicators.calculate_ema(closes, 26)
            indicators["ema_50"] = TechnicalIndicators.calculate_ema(closes, 50)
            indicators["ema_200"] = TechnicalIndicators.calculate_ema(closes, 200)
            
            indicators["rsi"] = TechnicalIndicators.calculate_rsi(closes, 14)
            
            macd = TechnicalIndicators.calculate_macd(closes)
            indicators["macd"] = macd["macd"]
            indicators["macd_signal"] = macd["signal"]
            indicators["macd_histogram"] = macd["histogram"]
            
            indicators["atr"] = TechnicalIndicators.calculate_atr(highs, lows, closes, 14)
            
            bb = TechnicalIndicators.calculate_bollinger_bands(closes, 20, 2)
            indicators["bb_upper"] = bb["upper"]
            indicators["bb_middle"] = bb["middle"]
            indicators["bb_lower"] = bb["lower"]
            
            stoch = TechnicalIndicators.calculate_stochastic(highs, lows, closes)
            indicators["stoch_k"] = stoch["k"]
            indicators["stoch_d"] = stoch["d"]
            
            volume_indicators = TechnicalIndicators.calculate_volume_indicators(closes, volumes)
            indicators["obv"] = volume_indicators["obv"]
            indicators["volume_sma"] = volume_indicators["volume_sma"]
            
            indicators["adx"] = TechnicalIndicators.calculate_trend_strength(closes, 20)
            
            sr = TechnicalIndicators.calculate_support_resistance(closes, 20)
            indicators["support"] = sr["support"]
            indicators["resistance"] = sr["resistance"]
            
            current_price = closes[-1]
            indicators["current_price"] = current_price
            
            indicators["price_change_1h"] = ((current_price - closes[-60]) / closes[-60] * 100) if len(closes) >= 60 else 0
            indicators["price_change_24h"] = ((current_price - closes[0]) / closes[0] * 100) if len(closes) > 0 else 0
            
        except Exception as e:
            print(f"Error calculating indicators: {e}")
            return {}
        
        return indicators
