import logging
import asyncio
import random
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    # Rotating User-Agent Pool (Modern desktop browsers across different OS platforms)
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
    ]

    def __init__(self, source_name: str, base_url: str):
        self.source_name = source_name
        self.base_url = base_url
        self.headers_template = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive"
        }

    async def fetch_html(self, url: str, apply_delay: bool = True) -> Optional[str]:
        """Asynchronously fetches the HTML content of the given URL.
        Applies a random delay and rotates User-Agent to prevent bot detection.
        """
        if apply_delay:
            # Random delay between 0.5 and 2.0 seconds to prevent rate-limiting/blocking
            delay = random.uniform(0.5, 2.0)
            logger.info(f"Applying rate limit delay of {delay:.2f}s before fetching {url}...")
            await asyncio.sleep(delay)

        # Set up headers with a random User-Agent from the pool
        headers = self.headers_template.copy()
        headers["User-Agent"] = random.choice(self.USER_AGENTS)

        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15.0) as client:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    return response.text
                else:
                    logger.error(f"Failed to fetch {url}. Status code: {response.status_code}")
                    return None
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                return None

    @abstractmethod
    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrapes the target website and returns a list of dictionaries with thread details."""
        pass
