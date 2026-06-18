import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import Config
from pipeline import run_pipeline

logger = logging.getLogger(__name__)

def setup_scheduler() -> AsyncIOScheduler:
    """Creates and configures an AsyncIO scheduler for periodic scraping runs."""
    scheduler = AsyncIOScheduler()
    
    interval = Config.SCRAPE_INTERVAL_MINUTES
    
    # Schedule the scrape-verify pipeline
    scheduler.add_job(
        run_pipeline,
        trigger="interval",
        minutes=interval,
        id="discount_scraper_pipeline",
        name="Scrape & Verify Sıcak Fırsatlar",
        replace_existing=True
    )
    
    logger.info(f"Scheduler setup: Pipeline scheduled to run every {interval} minutes.")
    return scheduler
