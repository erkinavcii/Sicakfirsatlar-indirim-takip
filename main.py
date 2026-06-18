import uvicorn
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dashboard.app import app
from scheduler import setup_scheduler
from database.db import Database

# Configure system logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    # 1. Startup Actions
    logger.info("Initializing system database...")
    await Database.initialize()
    
    logger.info("Starting background scheduler...")
    scheduler = setup_scheduler()
    scheduler.start()
    
    yield  # Runs the application
    
    # 2. Shutdown Actions
    logger.info("Stopping background scheduler...")
    scheduler.shutdown()

# Register the lifespan handler
app.router.lifespan_context = lifespan

if __name__ == "__main__":
    logger.info("Launching Sıcak Fırsatlar Takip Web Dashboard & Scraper...")
    # Run server on localhost port 8000. Reload is disabled to prevent duplicate scheduler starts.
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
