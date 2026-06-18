import os
import aiosqlite
from datetime import datetime
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
from config import Config

class Database:
    @classmethod
    @asynccontextmanager
    async def session(cls) -> aiosqlite.Connection:
        """Asynchronous context manager that yields a configured SQLite connection and closes it on exit."""
        db = await aiosqlite.connect(Config.DB_PATH)
        db.row_factory = aiosqlite.Row
        try:
            yield db
        finally:
            await db.close()

    @classmethod
    async def initialize(cls):
        """Initializes database tables if they do not exist."""
        async with cls.session() as db:
            # Table 1: Scraped Threads
            await db.execute("""
                CREATE TABLE IF NOT EXISTS threads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    thread_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    content TEXT,
                    author TEXT,
                    scraped_at TEXT NOT NULL,
                    processed INTEGER DEFAULT 0
                )
            """)
            
            # Table 2: Verified Deals
            await db.execute("""
                CREATE TABLE IF NOT EXISTS deals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id INTEGER NOT NULL,
                    product_name TEXT NOT NULL,
                    forum_price REAL,
                    market_price REAL,
                    discount_percentage REAL,
                    category TEXT,
                    google_search_summary TEXT,
                    is_verified INTEGER DEFAULT 0,
                    deal_score REAL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    notification_sent INTEGER DEFAULT 0,
                    FOREIGN KEY (thread_id) REFERENCES threads (id) ON DELETE CASCADE
                )
            """)
            
            # Table 3: Tracking Keywords/Categories
            await db.execute("""
                CREATE TABLE IF NOT EXISTS keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT UNIQUE NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL
                )
            """)
            
            # Insert default keywords if the table is empty
            async with db.execute("SELECT COUNT(*) as count FROM keywords") as cursor:
                row = await cursor.fetchone()
                if row and row['count'] == 0:
                    default_keywords = [
                        "laptop", "macbook", "ssd", "monitör", "iphone", "bilgisayar", "kulaklık",
                        "bebek bezi", "deterjan", "kahve", "mouse", "klavye", "telefon", "ekran kartı"
                    ]
                    now_str = datetime.now().isoformat()
                    for kw in default_keywords:
                        await db.execute(
                            "INSERT INTO keywords (keyword, is_active, created_at) VALUES (?, 1, ?)",
                            (kw, now_str)
                        )
            
            await db.commit()

    # --- Threads CRUD ---
    @classmethod
    async def add_thread(cls, source: str, thread_id: str, title: str, url: str, content: str, author: str) -> bool:
        """Inserts a thread if it doesn't already exist. Returns True if inserted, False if duplicate."""
        now_str = datetime.now().isoformat()
        async with cls.session() as db:
            try:
                await db.execute(
                    """INSERT INTO threads (source, thread_id, title, url, content, author, scraped_at, processed) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, 0)""",
                    (source, thread_id, title, url, content, author, now_str)
                )
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                # Already exists
                return False

    @classmethod
    async def get_unprocessed_threads(cls, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieves threads that haven't been processed by the LLM yet."""
        async with cls.session() as db:
            async with db.execute(
                "SELECT * FROM threads WHERE processed = 0 ORDER BY scraped_at DESC LIMIT ?", (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    @classmethod
    async def mark_thread_as_processed(cls, thread_id: int):
        """Marks a thread as processed."""
        async with cls.session() as db:
            await db.execute("UPDATE threads SET processed = 1 WHERE id = ?", (thread_id,))
            await db.commit()

    # --- Deals CRUD ---
    @classmethod
    async def add_deal(cls, thread_id: int, product_name: str, forum_price: Optional[float], 
                       market_price: Optional[float], discount_percentage: Optional[float], 
                       category: Optional[str], google_search_summary: Optional[str], 
                       is_verified: bool, deal_score: float) -> int:
        """Inserts a verified deal. Returns the new deal ID."""
        now_str = datetime.now().isoformat()
        async with cls.session() as db:
            cursor = await db.execute(
                """INSERT INTO deals (thread_id, product_name, forum_price, market_price, 
                                      discount_percentage, category, google_search_summary, 
                                      is_verified, deal_score, created_at, notification_sent) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
                (thread_id, product_name, forum_price, market_price, discount_percentage, 
                 category, google_search_summary, 1 if is_verified else 0, deal_score, now_str)
            )
            await db.commit()
            return cursor.lastrowid

    @classmethod
    async def get_deals(cls, limit: int = 50, only_verified: bool = True) -> List[Dict[str, Any]]:
        """Retrieves deals with associated thread details."""
        query = """
            SELECT d.*, t.title as thread_title, t.url as thread_url, t.source as thread_source
            FROM deals d
            JOIN threads t ON d.thread_id = t.id
        """
        if only_verified:
            query += " WHERE d.is_verified = 1"
        query += " ORDER BY d.created_at DESC LIMIT ?"
        
        async with cls.session() as db:
            async with db.execute(query, (limit,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    @classmethod
    async def get_unsent_deals(cls) -> List[Dict[str, Any]]:
        """Retrieves deals that have not yet been sent via Telegram."""
        query = """
            SELECT d.*, t.title as thread_title, t.url as thread_url, t.source as thread_source
            FROM deals d
            JOIN threads t ON d.thread_id = t.id
            WHERE d.notification_sent = 0 AND d.is_verified = 1
            ORDER BY d.created_at ASC
        """
        async with cls.session() as db:
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    @classmethod
    async def mark_deal_as_sent(cls, deal_id: int):
        """Marks a deal as notified."""
        async with cls.session() as db:
            await db.execute("UPDATE deals SET notification_sent = 1 WHERE id = ?", (deal_id,))
            await db.commit()

    # --- Keywords CRUD ---
    @classmethod
    async def get_active_keywords(cls) -> List[str]:
        """Retrieves all active keyword strings."""
        async with cls.session() as db:
            async with db.execute("SELECT keyword FROM keywords WHERE is_active = 1") as cursor:
                rows = await cursor.fetchall()
                return [r['keyword'] for r in rows]

    @classmethod
    async def get_all_keywords(cls) -> List[Dict[str, Any]]:
        """Retrieves all keywords with metadata."""
        async with cls.session() as db:
            async with db.execute("SELECT * FROM keywords ORDER BY keyword ASC") as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    @classmethod
    async def add_keyword(cls, keyword: str) -> bool:
        """Adds a tracking keyword."""
        keyword = keyword.strip().lower()
        if not keyword:
            return False
        now_str = datetime.now().isoformat()
        async with cls.session() as db:
            try:
                await db.execute(
                    "INSERT INTO keywords (keyword, is_active, created_at) VALUES (?, 1, ?)",
                    (keyword, now_str)
                )
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                # Already exists
                return False

    @classmethod
    async def delete_keyword(cls, keyword_id: int):
        """Deletes a tracking keyword."""
        async with cls.session() as db:
            await db.execute("DELETE FROM keywords WHERE id = ?", (keyword_id,))
            await db.commit()

    @classmethod
    async def toggle_keyword_status(cls, keyword_id: int, is_active: bool):
        """Enables or disables a tracking keyword."""
        async with cls.session() as db:
            await db.execute(
                "UPDATE keywords SET is_active = ? WHERE id = ?",
                (1 if is_active else 0, keyword_id)
            )
            await db.commit()
