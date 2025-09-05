import asyncio
import uvicorn
from src.api import app
from src.database import init_database, create_tables


async def main():
    await init_database()
    await create_tables()
    print("Database initialized successfully")
    
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
