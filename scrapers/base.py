import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    def __init__(self, source_name: str, base_url: str):
        self.source_name = source_name
        self.base_url = base_url
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive"
        }

    async def fetch_html(self, url: str) -> Optional[str]:
        """Asynchronously fetches the HTML content of the given URL."""
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=15.0) as client:
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
        """Scrapes the target website and returns a list of dictionaries with thread details:
        
        [
            {
                'thread_id': str,
                'title': str,
                'url': str,
                'content': str,
                'author': str
            },
            ...
        ]
        """
        pass
