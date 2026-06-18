import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
    
    # SQLite Database settings
    DB_PATH = os.getenv("DB_PATH", "database.db")
    
    SCRAPE_INTERVAL_MINUTES = int(os.getenv("SCRAPE_INTERVAL_MINUTES", "10"))
    MIN_DISCOUNT_PERCENTAGE = float(os.getenv("MIN_DISCOUNT_PERCENTAGE", "15"))
    
    # Domains to check during market price validation
    DEFAULT_DOMAINS = [
        "amazon.com.tr",
        "hepsiburada.com",
        "trendyol.com",
        "n11.com",
        "teknosa.com",
        "vatanbilgisayar.com"
    ]
    domains_str = os.getenv("GOOGLE_SEARCH_DOMAINS", "")
    GOOGLE_SEARCH_DOMAINS = [d.strip() for d in domains_str.split(",") if d.strip()] if domains_str else DEFAULT_DOMAINS

    @classmethod
    def validate(cls):
        """Validate if the required configurations are set."""
        warnings = []
        if not cls.GEMINI_API_KEY:
            warnings.append("GEMINI_API_KEY is not set. AI extraction and price validation will not work.")
        if not cls.TELEGRAM_BOT_TOKEN or not cls.TELEGRAM_CHAT_ID:
            warnings.append("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not set. Telegram notifications will be disabled.")
        return warnings
