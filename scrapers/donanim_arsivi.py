import re
import time
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
        """Scrapes multiple forum thread pages, filters duplicates against the DB,
        and halts parsing when encountering threads older than 24 hours.
        """
        logger.info(f"Starting pagination scrape for {self.source_name}...")
        
        new_threads = []
        page = 1
        max_pages = 3
        stop_scraping = False
        
        while page <= max_pages and not stop_scraping:
            # Construct page URL (XenForo pagination style: /page-N)
            url = self.forum_url if page == 1 else f"{self.forum_url}page-{page}"
            
            logger.info(f"Scraping {self.source_name} page {page}: {url}...")
            # We don't apply rate limit delay on page 1, but apply it on pages 2+
            html = await self.fetch_html(url, apply_delay=(page > 1))
            if not html:
                logger.error(f"Could not fetch page {page}.")
                break

            soup = BeautifulSoup(html, "html.parser")
            thread_items = soup.select(".structItem.structItem--thread")
            
            if not thread_items:
                logger.info("No threads found on this page. Stopping.")
                break

            page_new_count = 0
            for item in thread_items:
                try:
                    # 1. Check if thread is sticky/pinned
                    classes = item.get("class", [])
                    is_sticky = "structItem--sticky" in classes or "is-sticky" in classes
                    
                    # 2. Check thread age using data-timestamp
                    time_el = item.select_one(".structItem-startDate time")
                    if time_el:
                        timestamp_str = time_el.get("data-timestamp", "")
                        if timestamp_str.isdigit():
                            thread_time = int(timestamp_str)
                            current_time = int(time.time())
                            # Stop scraping if thread is not pinned and is older than 24 hours (86400 seconds)
                            if not is_sticky and (current_time - thread_time > 86400):
                                age_hours = (current_time - thread_time) / 3600
                                logger.info(f"Encountered thread older than 24 hours (Age: {age_hours:.1f} hours). Stopping pagination.")
                                stop_scraping = True
                                break

                    # 3. Parse thread ID from class list
                    thread_id = None
                    for cls in classes:
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

                    # 4. Extract basic details
                    title = title_el.text.strip()
                    thread_url = href if href.startswith("http") else f"{self.base_url}{href}"
                    
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
                    
                    # 5. Handle expired threads immediately without detail fetch
                    if is_expired:
                        logger.info(f"Thread {thread_id} is expired. Skipping detail fetch and marking processed.")
                        await Database.add_thread(
                            source=self.source_name,
                            thread_id=thread_id,
                            title=title,
                            url=thread_url,
                            content="[İndirim Bitti - Detay Çekilmedi]",
                            author=author
                        )
                        async with Database.session() as db:
                            async with db.execute("SELECT id FROM threads WHERE thread_id = ?", (thread_id,)) as cursor:
                                row = await cursor.fetchone()
                                if row:
                                    await Database.mark_thread_as_processed(row['id'])
                        page_new_count += 1
                        continue

                    # 6. Fetch details for active threads
                    content = ""
                    detail_html = await self.fetch_html(thread_url)
                    if detail_html:
                        detail_soup = BeautifulSoup(detail_html, "html.parser")
                        body_el = detail_soup.select_one(".message-body")
                        if body_el:
                            content = body_el.text.strip()
                            content = re.sub(r"\n+", "\n", content)
                    
                    # Save active thread to DB
                    await Database.add_thread(
                        source=self.source_name,
                        thread_id=thread_id,
                        title=title,
                        url=thread_url,
                        content=content,
                        author=author
                    )
                    
                    new_threads.append({
                        "thread_id": thread_id,
                        "title": title,
                        "url": thread_url,
                        "content": content,
                        "author": author,
                        "prefix": prefix,
                        "is_expired": is_expired
                    })
                    page_new_count += 1
                    
                except Exception as e:
                    logger.error(f"Error parsing thread item: {e}", exc_info=True)
                    continue
            
            logger.info(f"Page {page} parsed. Found {page_new_count} new threads on this page.")
            page += 1

        logger.info(f"Multi-page scrape completed. Total active new threads found: {len(new_threads)}")
        return new_threads
