import logging
import httpx
from typing import Dict, Any
from config import Config

logger = logging.getLogger(__name__)

class TelegramService:
    @staticmethod
    async def send_message(text: str) -> bool:
        """Sends a raw message to the configured Telegram chat."""
        if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
            logger.warning("Telegram Bot Token or Chat ID is missing. Skipping notification.")
            return False

        url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": Config.TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    logger.info("Telegram notification sent successfully.")
                    return True
                else:
                    logger.error(f"Failed to send Telegram message: {response.status_code} - {response.text}")
                    return False
            except Exception as e:
                logger.error(f"Exception during sending Telegram message: {e}")
                return False

    @classmethod
    async def send_deal_notification(cls, deal: Dict[str, Any]) -> bool:
        """Formats and sends a detailed HTML alert for a verified discount deal."""
        prod_name = deal.get("product_name", "Bilinmeyen Ürün")
        cat = deal.get("category", "Diğer")
        f_price = deal.get("forum_price")
        m_price = deal.get("market_price")
        disc_pct = deal.get("discount_percentage", 0)
        source = deal.get("source_store", "Piyasa")
        summary = deal.get("google_search_summary", "Fiyat doğrulaması yapıldı.")
        url = deal.get("thread_url", "https://forum.donanimarsivi.com")
        
        # Select emoji based on discount intensity
        if disc_pct >= 40:
            emoji = "🚨🚨🚨 ULTRA SICAK FIRSAT"
        elif disc_pct >= 25:
            emoji = "💥💥 SICAK FIRSAT"
        else:
            emoji = "🔥 FIRSAT"

        # Safe formatting of floats
        f_price_str = f"{f_price:,.2f} TL" if f_price is not None else "Belirtilmemiş"
        m_price_str = f"{m_price:,.2f} TL" if m_price is not None else "Bulunamadı"

        message = (
            f"<b>{emoji}</b>\n\n"
            f"📦 <b>Ürün:</b> {prod_name}\n"
            f"🏷️ <b>Kategori:</b> {cat}\n\n"
            f"💰 <b>Forum Fiyatı:</b> {f_price_str}\n"
            f"📉 <b>En Ucuz Piyasa Fiyatı:</b> {m_price_str} ({source})\n"
            f"💸 <b>Net İndirim:</b> %{disc_pct:.0f} daha ucuz!\n\n"
            f"🔍 <b>Piyasa Analizi:</b> <i>{summary}</i>\n\n"
            f"🔗 <a href='{url}'>Forum Konusuna Git &gt;&gt;</a>"
        )

        return await cls.send_message(message)
