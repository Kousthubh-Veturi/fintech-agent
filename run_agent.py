#!/usr/bin/env python3

import asyncio
import sys
import argparse
from src.agent_nodes import TradingAgent
from src.database import init_database, create_tables


async def run_agent(user_id: int, instrument: str = "XBX-USD", interval: int = 300):
    print(f"Starting trading agent for user {user_id}")
    print(f"Instrument: {instrument}")
    print(f"Interval: {interval} seconds")
    print("Press Ctrl+C to stop")
    
    try:
        await init_database()
        await create_tables()
        print("Database initialized")
        
        agent = TradingAgent(user_id, instrument)
        await agent.run_continuous(interval)
        
    except KeyboardInterrupt:
        print("\nAgent stopped by user")
    except Exception as e:
        print(f"Agent error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Run the trading agent")
    parser.add_argument("user_id", type=int, help="User ID for the agent")
    parser.add_argument("--instrument", default="XBX-USD", help="Trading instrument (default: XBX-USD)")
    parser.add_argument("--interval", type=int, default=300, help="Execution interval in seconds (default: 300)")
    
    args = parser.parse_args()
    
    asyncio.run(run_agent(args.user_id, args.instrument, args.interval))


if __name__ == "__main__":
    main()
