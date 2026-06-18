import logging
import json
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from config import Config
from database.db import Database

logger = logging.getLogger(__name__)

# Model 1: Structure to extract from a forum post
class ParsedProduct(BaseModel):
    product_name: str = Field(
        description="Clean, brand-included standard product name (e.g., 'Apple MacBook Air M2 8GB/256GB' or 'Fairy Platinum Bulaşık Makinesi Kapsülü 120 Yıkama')"
    )
    price: Optional[float] = Field(
        default=None,
        description="Numeric price of the product mentioned in the thread in Turkish Lira (TL). Null if no specific price is mentioned."
    )
    category: str = Field(
        description="Category of the product. E.g., 'Elektronik', 'Gıda', 'Moda', 'Kişisel Bakım', 'Ev & Yaşam', 'Diğer'"
    )
    is_deal: bool = Field(
        description="True if this thread is an advertisement/post about a specific discounted product. False if it is a general thread, request, question, chat, or doesn't represent a specific product deal."
    )
    confidence: float = Field(
        description="Confidence score between 0.0 and 1.0 of the extraction."
    )

# Model 2: Structure for Google Search market price validation
class MarketVerification(BaseModel):
    lowest_market_price: Optional[float] = Field(
        default=None,
        description="Lowest price (in TL) found on major Turkish e-commerce sites (Amazon, Trendyol, Hepsiburada, N11, Vatan, Teknosa etc.). Null if not found."
    )
    source_store: Optional[str] = Field(
        default=None,
        description="Name of the store having the lowest market price (e.g. 'Amazon.com.tr', 'Hepsiburada')"
    )
    search_summary: str = Field(
        description="A 1-2 sentence summary of what was found in the search results (e.g., 'Product is sold on Amazon for 25.000 TL and Hepsiburada for 26.500 TL')."
    )
    is_real_discount: bool = Field(
        description="True if the forum price is at least 10% lower than the lowest market price found."
    )
    discount_percentage: float = Field(
        description="Calculated discount percentage based on: ((lowest_market_price - forum_price) / lowest_market_price) * 100. 0.0 if not applicable."
    )

class GeminiService:
    _client = None

    @classmethod
    def get_client(cls) -> genai.Client:
        """Lazily instantiates the Gemini API Client."""
        if cls._client is None:
            if not Config.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is not configured in settings/environment.")
            cls._client = genai.Client(api_key=Config.GEMINI_API_KEY)
        return cls._client

    @classmethod
    async def extract_product_details(cls, title: str, content: str) -> Optional[ParsedProduct]:
        """Uses Gemini structured outputs to extract product details from forum post title and body."""
        try:
            client = cls.get_client()
            prompt = f"""
            Aşağıdaki forum başlığını ve içeriğini analiz et. Bu başlık bir indirim/fırsat paylaşımı mı karar ver.
            Eğer bir indirim paylaşımıysa, paylaşılan ürünün temiz ismini, fiyatını ve kategorisini çıkar.
            
            Forum Başlığı: {title}
            Forum İçeriği: {content}
            """
            
            # Using Gemini 2.5 Flash as standard model for quick structured tasks
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ParsedProduct,
                    temperature=0.1
                )
            )
            
            parsed: ParsedProduct = response.parsed
            return parsed
        except Exception as e:
            logger.error(f"Error in extract_product_details: {e}", exc_info=True)
            return None

    @classmethod
    async def verify_discount(cls, product_name: str, forum_price: float) -> Optional[MarketVerification]:
        """Uses Gemini Google Search Grounding to verify market prices and calculate real discounts."""
        try:
            client = cls.get_client()
            prompt = f"""
            Türkiye'deki popüler e-ticaret sitelerinde (Amazon.com.tr, Hepsiburada, Trendyol, N11, Vatan Bilgisayar, Teknosa vb.)
            '{product_name}' ürününün güncel satış fiyatını araştır.
            Bulduğun en düşük güvenilir piyasa fiyatını belirle.
            Bu fiyatı, forumda paylaşılan indirimli fiyat olan {forum_price} TL ile karşılaştır.
            
            Matematiksel olarak indirim oranını hesapla:
            indirim_orani = ((piyasa_fiyati - {forum_price}) / piyasa_fiyati) * 100
            
            Eğer indirim oranı %10 veya daha fazla ise bunu 'gerçek indirim' (is_real_discount = true) olarak işaretle.
            """
            
            # Using Gemini 2.5 Flash with search tools enabled
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=MarketVerification,
                    tools=[{"google_search_retrieval": {}}],
                    temperature=0.1
                )
            )
            
            parsed: MarketVerification = response.parsed
            return parsed
        except Exception as e:
            logger.error(f"Error in verify_discount: {e}", exc_info=True)
            return None

    @classmethod
    async def check_keyword_match(cls, product_name: str, category: str, keywords: List[str]) -> bool:
        """Checks if the product name or category matches the user's tracking list.
        First attempts simple substring matches, then falls back to semantic LLM evaluation.
        """
        # 1. Direct lowercase string matching
        name_lower = product_name.lower()
        cat_lower = category.lower()
        
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in name_lower or kw_lower in cat_lower:
                return True
                
        # 2. Semantic matching with Gemini for close variations (e.g. 'mac' matching 'macbook', 'bebek' matching 'baby wipes')
        try:
            client = cls.get_client()
            prompt = f"""
            Ürün Adı: {product_name}
            Kategori: {category}
            Takip Listesi: {", ".join(keywords)}
            
            Yukarıdaki ürünün, takip listesindeki kelimelerden biriyle alakalı veya eşdeğer olup olmadığını kontrol et. 
            Cevabını sadece JSON olarak ver: {{"matches": true/false}}
            """
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            
            res_json = json.loads(response.text)
            return res_json.get("matches", False)
        except Exception as e:
            logger.error(f"Error in check_keyword_match (semantic fallback): {e}")
            return False
