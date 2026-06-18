import logging
import re
import asyncio
from database.db import Database
from scrapers.donanim_arsivi import DonanimArsiviScraper
from services.nlp_helper import local_keyword_match, clean_word
from services.gemini_service import GeminiService
from services.telegram_service import TelegramService
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_price_locally(title: str, content: str) -> float:
    """Parses Turkish pricing formats (e.g., '4.099 TL', '4099,50 TL', '150₺') from text."""
    text_to_search = (title + " " + content[:200]).lower().replace("₺", "tl")
    
    # Matches patterns like 4.099, 4099, 4099.50, 4099,50 followed by tl
    matches = re.findall(r'(\d+[\d.,]*)\s*(?:tl|lira)', text_to_search)
    for match in matches:
        cleaned = match
        # Handle decimal vs thousands formatting in Turkish
        if "," in cleaned and "." in cleaned:
            # Format: 4.099,50 -> 4099.50
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif "," in cleaned:
            parts = cleaned.split(",")
            # If exactly 2 digits after comma, it's decimal (e.g., 4099,50)
            if len(parts[-1]) == 2:
                cleaned = cleaned.replace(".", "").replace(",", ".")
            else:
                cleaned = cleaned.replace(",", "")
        elif "." in cleaned:
            parts = cleaned.split(".")
            # If exactly 2 digits after dot, it's decimal (e.g., 4099.50)
            if len(parts[-1]) == 2:
                pass
            else:
                cleaned = cleaned.replace(".", "")
                
        try:
            val = float(cleaned)
            if val > 0:
                return val
        except ValueError:
            continue
            
    return 0.0

async def run_pipeline():
    """Runs the full scrape-process-verify-notify loop in either AI Mode or Local Mode."""
    logger.info("--- Starting Pipeline Run ---")
    
    # 1. Initialize DB
    await Database.initialize()
    
    # 2. Get active keywords
    active_keywords = await Database.get_active_keywords()
    logger.info(f"Loaded {len(active_keywords)} active tracking keywords: {active_keywords}")
    
    # 3. Scrape new threads
    scrapers = [DonanimArsiviScraper()]
    new_threads_count = 0
    for scraper in scrapers:
        try:
            threads = await scraper.scrape()
            new_threads_count += len(threads)
        except Exception as e:
            logger.error(f"Error running scraper {scraper.source_name}: {e}", exc_info=True)

    logger.info(f"Scraper runs completed. Found {new_threads_count} new threads in this execution.")
    
    # 4. Fetch unprocessed threads from DB
    unprocessed = await Database.get_unprocessed_threads(limit=30)
    if not unprocessed:
        logger.info("No unprocessed threads in DB. Pipeline finished.")
        return
        
    # Check if AI mode is unlocked
    has_api_key = bool(Config.GEMINI_API_KEY)
    mode_name = "AI MODU (Gemini)" if has_api_key else "YEREL MOD (API-less)"
    logger.info(f"Pipeline running in: {mode_name}")
    
    for thread in unprocessed:
        thread_db_id = thread["id"]
        title = thread["title"]
        content = thread["content"]
        url = thread["url"]
        
        logger.info(f"Processing thread [{thread_db_id}]: {title[:50]}...")
        
        # Skip dummy expired placeholder content
        if "[İndirim Bitti - Detay Çekilmedi]" in content:
            await Database.mark_thread_as_processed(thread_db_id)
            continue
            
        try:
            if has_api_key:
                # --- AI MODE PATHWAY ---
                parsed = await GeminiService.extract_product_details(title, content)
                if not parsed:
                    logger.warning(f"Gemini failed to parse thread {thread_db_id}.")
                    await Database.mark_thread_as_processed(thread_db_id)
                    continue
                    
                if parsed.is_deal and parsed.product_name:
                    is_match = await GeminiService.check_keyword_match(
                        parsed.product_name, 
                        parsed.category, 
                        active_keywords
                    )
                    
                    if is_match and parsed.price is not None and parsed.price > 0:
                        logger.info(f"Verifying market price for '{parsed.product_name}' (Forum Price: {parsed.price} TL)...")
                        verification = await GeminiService.verify_discount(parsed.product_name, parsed.price)
                        
                        if verification:
                            deal_id = await Database.add_deal(
                                thread_id=thread_db_id,
                                product_name=parsed.product_name,
                                forum_price=parsed.price,
                                market_price=verification.lowest_market_price,
                                discount_percentage=verification.discount_percentage,
                                category=parsed.category,
                                google_search_summary=verification.search_summary,
                                is_verified=verification.is_real_discount,
                                deal_score=verification.discount_percentage
                            )
                            
                            if verification.is_real_discount:
                                deal_data = {
                                    "product_name": parsed.product_name,
                                    "category": parsed.category,
                                    "forum_price": parsed.price,
                                    "market_price": verification.lowest_market_price,
                                    "discount_percentage": verification.discount_percentage,
                                    "source_store": verification.source_store,
                                    "google_search_summary": verification.search_summary,
                                    "thread_url": url
                                }
                                sent = await TelegramService.send_deal_notification(deal_data)
                                if sent:
                                    await Database.mark_deal_as_sent(deal_id)
            else:
                # --- LOCAL MODE PATHWAY (API-less) ---
                # Check keyword match using local Turkish NLP stemming & yumuşama rules
                is_match = local_keyword_match(title, active_keywords)
                
                if is_match:
                    logger.info(f"Local Match found in title: '{title}'")
                    # Extract price using local regex helper
                    price = extract_price_locally(title, content)
                    
                    # Store as verified deal in database (since it matched local keywords)
                    deal_id = await Database.add_deal(
                        thread_id=thread_db_id,
                        product_name=title,
                        forum_price=price if price > 0 else None,
                        market_price=None, # No market price in local mode
                        discount_percentage=0.0,
                        category="Yerel Eşleşme",
                        google_search_summary="Yerel Mod (Gemini API anahtarı olmadan yerel kök ve ek eşleştirmesi ile süzüldü).",
                        is_verified=True,
                        deal_score=0.0
                    )
                    
                    # Format a simple local Telegram card
                    price_str = f"{price:,.2f} TL" if price > 0 else "Belirtilmemiş"
                    local_msg = (
                        "ℹ️ <b>YEREL FİLTRE EŞLEŞMESİ</b>\n\n"
                        f"📦 <b>Ürün:</b> {title}\n"
                        f"💰 <b>Fiyat:</b> {price_str}\n"
                        f"🔍 <b>Açıklama:</b> Kelime eşleşmesi ile tespit edildi.\n\n"
                        f"🔗 <a href='{url}'>Forum Konusuna Git &gt;&gt;</a>"
                    )
                    
                    sent = await TelegramService.send_message(local_msg)
                    if sent:
                        await Database.mark_deal_as_sent(deal_id)
                else:
                    logger.info(f"Thread '{title}' did not match local keywords.")
            
            # Mark processed
            await Database.mark_thread_as_processed(thread_db_id)
            
        except Exception as ex:
            logger.error(f"Error processing thread {thread_db_id}: {ex}", exc_info=True)
            await Database.mark_thread_as_processed(thread_db_id)
            
    logger.info("--- Pipeline Run Finished ---")
