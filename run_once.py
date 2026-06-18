import asyncio
import logging
from pipeline import run_pipeline

# Configure system logging for script execution
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("run_once")

async def main():
    logger.info("Initializing Sıcak Fırsatlar Takip (Single Run Mode)...")
    await run_pipeline()
    logger.info("Single run process completed successfully.")

if __name__ == "__main__":
    asyncio.run(main())
