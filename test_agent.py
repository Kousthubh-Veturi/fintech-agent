#!/usr/bin/env python3

import sys
import os
sys.path.append('/Users/kousthubhveturi/fintech-agent')
sys.path.append('/Users/kousthubhveturi/fintech-agent/python')

os.chdir('/Users/kousthubhveturi/fintech-agent/python')

from dotenv import load_dotenv
load_dotenv()

import asyncio
from src.langgraph_agent import LangGraphTradingAgent
from src.redis_client import redis_client

async def test_components():
    print("Testing FinTech Trading Agent Components...")
    
    print("\n1. Testing Redis Connection...")
    try:
        redis_result = await redis_client.ping()
        print(f"   Redis: {'✓ Connected' if redis_result else '✗ Failed'}")
    except Exception as e:
        print(f"   Redis: ✗ Error - {e}")
    
    print("\n2. Testing Environment Variables...")
    coindesk_key = os.getenv('COINDESK_API_KEY')
    neon_url = os.getenv('NEON_DATABASE_URL')
    news_key = os.getenv('NEWSAPI_KEY')
    
    print(f"   CoinDesk API: {'✓ Found' if coindesk_key else '✗ Missing'}")
    print(f"   Neon DB: {'✓ Found' if neon_url else '✗ Missing'}")
    print(f"   NewsAPI: {'✓ Found' if news_key else '✗ Missing'}")
    
    print("\n3. Testing LangGraph Agent...")
    try:
        agent = LangGraphTradingAgent(user_id=1, instrument='XBX-USD')
        print("   ✓ Agent created successfully")
        
        print("   Running single trading cycle...")
        result = await agent.execute_cycle()
        
        if result.get('success'):
            print("   ✓ Trading cycle completed successfully")
        else:
            print("   ⚠ Trading cycle completed with issues")
            if result.get('error'):
                print(f"   Error: {result['error']}")
        
        state = result.get('state', {})
        print(f"   Market data: {'✓ Found' if state.get('market_data') else '✗ Missing'}")
        print(f"   Portfolio: {'✓ Found' if state.get('portfolio') else '✗ Missing'}")
        print(f"   News research: {'✓ Found' if state.get('research') else '✗ Missing'}")
        print(f"   Technical indicators: {'✓ Found' if state.get('indicators') else '✗ Missing'}")
        print(f"   Risk checks: {'✓ Found' if state.get('risk_checks') else '✗ Missing'}")
        print(f"   Decision: {state.get('decision', {}).get('action', 'hold')}")
        print(f"   Action executed: {'✓ Yes' if state.get('action', {}).get('executed') else '✗ No'}")
        
    except Exception as e:
        print(f"   ✗ Agent test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n4. Testing API Components...")
    try:
        from src.coindesk_client import CoinDeskClient
        async with CoinDeskClient() as client:
            price = await client.get_latest_price('XBX-USD')
            print(f"   CoinDesk API: {'✓ Working' if price else '⚠ No data'}")
    except Exception as e:
        print(f"   CoinDesk API: ✗ Error - {e}")
    
    try:
        from src.paper_broker import paper_broker
        portfolio = await paper_broker.get_portfolio_summary(1)
        print(f"   Paper Broker: {'✓ Working' if portfolio else '✗ Failed'}")
    except Exception as e:
        print(f"   Paper Broker: ✗ Error - {e}")
    
    try:
        from src.news_aggregator import news_aggregator
        news = await news_aggregator.get_news_for_symbol('BTC', limit=5)
        print(f"   News Aggregator: {'✓ Working' if news else '⚠ No data'}")
    except Exception as e:
        print(f"   News Aggregator: ✗ Error - {e}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_components())
