import os
from pydantic_settings import BaseSettings
from typing import Dict, List


class Settings(BaseSettings):
    app_mode: str = "paper"
    coindesk_api_key: str
    neon_database_url: str
    redis_url: str = "redis://localhost:6379/0"
    starting_cash_usd: float = 10000.0
    
    news_secondary: str = "NewsAPI"
    newsapi_key: str = ""
    gnews_key: str = ""
    mediastack_key: str = ""
    
    news_recency_half_life_min: int = 90
    news_credibility_table: str = "marketwatch:1.0,newsapi:0.8,gnews:0.7"
    news_halt_window_min: int = 20
    max_position_pct: float = 0.2
    daily_loss_halt_pct: float = 0.02
    
    slippage_bps: int = 5
    fee_bps: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def credibility_weights(self) -> Dict[str, float]:
        weights = {}
        for pair in self.news_credibility_table.split(','):
            source, weight = pair.split(':')
            weights[source.strip()] = float(weight.strip())
        return weights


settings = Settings()
