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

async def run_trading_system():
    print("Starting FinTech Trading Agent System...")
    print("=" * 50)
    
    user_id = 1
    instrument = "XBX-USD"
    
    print(f"User ID: {user_id}")
    print(f"Instrument: {instrument}")
    print(f"Mode: Paper Trading")
    print("=" * 50)
    
    try:
        agent = LangGraphTradingAgent(user_id=user_id, instrument=instrument)
        print("✓ LangGraph Trading Agent initialized")
        
        print("\nRunning trading cycles...")
        print("Press Ctrl+C to stop")
        print("-" * 30)
        
        cycle_count = 0
        while True:
            cycle_count += 1
            print(f"\n[Cycle {cycle_count}] Starting...")
            
            try:
                result = await agent.execute_cycle()
                
                if result.get('success'):
                    print(f"[Cycle {cycle_count}] ✓ Completed successfully")
                    action = result.get('state', {}).get('action', {})
                    if action.get('executed'):
                        print(f"[Cycle {cycle_count}] 🎯 Trade executed!")
                        fills = action.get('fills', [])
                        if fills:
                            fill = fills[0]
                            print(f"[Cycle {cycle_count}] Price: ${fill.get('price', 0):.2f}")
                            print(f"[Cycle {cycle_count}] Quantity: {fill.get('quantity', 0):.6f}")
                else:
                    print(f"[Cycle {cycle_count}] ⚠ Completed with issues")
                
                state = result.get('state', {})
                decision = state.get('decision', {})
                print(f"[Cycle {cycle_count}] Decision: {decision.get('action', 'hold')}")
                print(f"[Cycle {cycle_count}] Confidence: {decision.get('confidence', 0):.2f}")
                
                portfolio = state.get('portfolio', {})
                if portfolio:
                    print(f"[Cycle {cycle_count}] Cash: ${portfolio.get('cash_balance', 0):.2f}")
                    print(f"[Cycle {cycle_count}] Total Value: ${portfolio.get('total_value', 0):.2f}")
                    print(f"[Cycle {cycle_count}] P&L: {portfolio.get('pnl_pct', 0):.2f}%")
                
            except Exception as e:
                print(f"[Cycle {cycle_count}] ✗ Error: {e}")
            
            print(f"[Cycle {cycle_count}] Waiting 5 minutes...")
            await asyncio.sleep(300)
            
    except KeyboardInterrupt:
        print("\n\nTrading system stopped by user")
    except Exception as e:
        print(f"\n✗ System error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_trading_system())
