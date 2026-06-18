import re
import logging
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper
from database.db import Database
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class DonanimArsiviScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            source_name="donanimarsivi",
            base_url="https://forum.donanimarsivi.com"
        )
        self.forum_url = f"{self.base_url}/forumlar/Sicakfirsatlar/"

    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrapes the thread list, filters duplicates against the DB, 
        and fetches post details for new active threads.
        """
        logger.info(f"Starting scrape for {self.source_name}...")
        html = await self.fetch_html(self.forum_url)
        if not html:
            logger.error("Could not fetch forum main page.")
            return []

        soup = BeautifulSoup(html, "html.parser")
        thread_items = soup.select(".structItem.structItem--thread")
        
        new_threads = []
        for item in thread_items:
            try:
                # 1. Parse thread ID from class list
                thread_id = None
                for cls in item.get("class", []):
                    match = re.match(r"js-threadListItem-(\d+)", cls)
                    if match:
                        thread_id = match.group(1)
                        break
                
                title_el = item.select_one(".structItem-title a[data-tp-primary='on']")
                if not title_el:
                    title_el = item.select_one(".structItem-title a")
                
                if not title_el:
                    continue
                
                href = title_el.get("href", "")
                if not thread_id and href:
                    match = re.search(r"\.(\d+)/?$", href)
                    if match:
                        thread_id = match.group(1)
                
                if not thread_id:
                    continue

                # 2. Extract title, prefix, and check expiration
                title = title_el.text.strip()
                url = href if href.startswith("http") else f"{self.base_url}{href}"
                
                prefix_el = item.select_one(".structItem-title .label, .structItem-title [class*='label']")
                prefix = prefix_el.text.strip() if prefix_el else ""
                
                is_expired = "bitti" in prefix.lower() or "sonlandı" in prefix.lower() or "❌" in prefix
                
                author_el = item.select_one(".username")
                author = author_el.text.strip() if author_el else item.get("data-author", "Unknown")
                
                # Check database to see if we already have this thread
                async with Database.session() as db:
                    async with db.execute("SELECT id FROM threads WHERE thread_id = ?", (thread_id,)) as cursor:
                        if await cursor.fetchone():
                            # Thread already scraped, skip to next
                            continue

                logger.info(f"Found new thread: '{title}' (ID: {thread_id}), Prefix: '{prefix}'")
                
                # 3. Handle expired threads: save as processed immediately without fetching details
                if is_expired:
                    logger.info(f"Thread {thread_id} is expired. Skipping detail fetch and marking as processed.")
                    async with Database.session() as db:
                        now_str = re.sub(r'T.*', '', re.sub(r'\.\d+', '', re.sub(r'\+.*', '', re.sub(r'T', ' ', re.sub(r' ', ' ', ''))))) 
                        # We will let Database handle scraped_at
                        await Database.add_thread(
                            source=self.source_name,
                            thread_id=thread_id,
                            title=title,
                            url=url,
                            content="[İndirim Bitti - Detay Çekilmedi]",
                            author=author
                        )
                        # Mark it processed immediately
                        async with db.execute("SELECT id FROM threads WHERE thread_id = ?", (thread_id,)) as cursor:
                            row = await cursor.fetchone()
                            if row:
                                await Database.mark_thread_as_processed(row['id'])
                    continue

                # 4. For active new threads, fetch the first post body
                content = ""
                detail_html = await self.fetch_html(url)
                if detail_html:
                    detail_soup = BeautifulSoup(detail_html, "html.parser")
                    body_el = detail_soup.select_one(".message-body")
                    if body_el:
                        content = body_el.text.strip()
                        content = re.sub(r"\n+", "\n", content)
                
                # Save active thread to database (processed = 0)
                await Database.add_thread(
                    source=self.source_name,
                    thread_id=thread_id,
                    title=title,
                    url=url,
                    content=content,
                    author=author
                )
                
                new_threads.append({
                    "thread_id": thread_id,
                    "title": title,
                    "url": url,
                    "content": content,
                    "author": author,
                    "prefix": prefix,
                    "is_expired": is_expired
                })
                
            except Exception as e:
                logger.error(f"Error parsing thread item: {e}", exc_info=True)
                continue

        logger.info(f"Scrape completed. Found {len(new_threads)} new active threads.")
        return new_threads
