#!/usr/bin/env python3

import sys
import os
sys.path.append('/Users/kousthubhveturi/fintech-agent')
sys.path.append('/Users/kousthubhveturi/fintech-agent/python')

os.chdir('/Users/kousthubhveturi/fintech-agent/python')

from dotenv import load_dotenv
load_dotenv()

import asyncio
from src.database import init_database, create_tables

async def setup_database():
    print("Setting up database...")
    try:
        await init_database()
        print("✓ Database initialized")
        
        await create_tables()
        print("✓ Tables created")
        
        print("\nDatabase setup complete!")
        
    except Exception as e:
        print(f"✗ Database setup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(setup_database())
