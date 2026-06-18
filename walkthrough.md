# 🌌 Akıllı İndirim Takip ve Doğrulama Sistemi - Kullanım Kılavuzu

Bu kılavuz, projenin nasıl yapılandırılacağını, lokalde nasıl çalıştırılacağını ve gelecekte nasıl genişletileceğini (yeni siteler ekleme) adım adım açıklamaktadır.

---

## 1. Hızlı Başlangıç (Gereksinimler & Çalıştırma)

Uygulamanın çalışması için gerekli bağımlılıklar kuruludur. Depoyu başka bir makinede ayağa kaldırmak için aşağıdaki adımları izleyebilirsiniz.

### Depoyu Klonlama ve Kurulum
```bash
# 1. Depoyu klonlayın
git clone https://github.com/erkinavcii/Sicakfirsatlar-indirim-takip.git
cd SıcakFırsatlarTakip

# 2. Gerekli kütüphaneleri yükleyin
pip install -r requirements.txt
```

### Sunucuyu Başlatma
Uygulama sunucusunu çalıştırmak için terminalde şu komutu çalıştırabilirsiniz:
```bash
python main.py
```
Bu komut:
1. SQLite veritabanını (`database.db`) başlatır ve tabloları oluşturur.
2. 10 dakikada bir otomatik çalışacak asenkron Tarama Zamanlayıcısını (Scheduler) başlatır.
3. Kontrol panelini (FastAPI Web Dashboard) `http://127.0.0.1:8000` adresinde ayağa kaldırır.

---

## 2. Yapılandırma Ayarları (.env)

Kök dizinde bulunan `.env.example` dosyasını kopyalayarak `.env` adında yeni bir dosya oluşturun ve içini kendi bilgilerinizle doldurun:

```env
# Gemini API Anahtarınız (İndirim Analizi & Google Fiyat Doğrulaması için)
GEMINI_API_KEY=AIzaSy...

# Telegram Bot Token ve Kanal/Grup ID (İndirim Bildirimleri için)
TELEGRAM_BOT_TOKEN=1234567890:ABCdef...
TELEGRAM_CHAT_ID=-100XXXXXXXXXX

# SQLite Veritabanı Dosya Yolu
DB_PATH=database.db

# Taramalar Arasındaki Süre (Dakika)
SCRAPE_INTERVAL_MINUTES=10

# Minimum İndirim Oranı (Bu orandan daha az indirimli ürünler Telegram'a atılmaz)
MIN_DISCOUNT_PERCENTAGE=15
```

> [!TIP]
> Gemini API anahtarınızı ücretsiz olarak [Google AI Studio](https://aistudio.google.com/) üzerinden alabilirsiniz. Google Search Grounding özelliği Gemini API'ye gömülü olduğu için ek arama motoru API'si kurmanıza gerek kalmaz.

---

## 3. Web Dashboard Kullanımı

Kontrol paneline `http://127.0.0.1:8000` adresinden erişebilirsiniz. Arayüz tamamen **Vanilla CSS** ile premium koyu tema (glassmorphism detayları ve mikro animasyonlar) şeklinde tasarlanmıştır:

- **Şimdi Tara Butonu**: Taramayı beklemeden hemen el ile tetikleyebilirsiniz. Buton "Taranıyor..." moduna geçip taramayı arka planda asenkron çalıştırır ve tamamlandığında sayfayı yeniler.
- **Fırsat Rozetleri**:
  - 🔮 **Yerel Filtre**: API anahtarı olmadan, `nlp_helper.py` içindeki Türkçe ek/yumuşama eşleştirmeleriyle yakalanan fırsatları temsil eder.
  - 🔥 **%X İndirim**: Gemini API + Google Search ile internette canlı piyasa fiyat araştırması yapılmış ve haksız indirim olmadığı doğrulanmış fırsatları temsil eder.
- **Takip Edilen Kelimeler**: Sistem varsayılan olarak `monitör`, `laptop`, `telefon`, `bebek bezi` gibi anahtar kelimelerle kurulur. Yeni kelimeler ekleyebilir, mevcut kelimelerin aktif/pasif durumunu değiştirebilir veya silebilirsiniz.

---

## 4. Yeni Bir Site Eklemek (Modüler Kazıma)

Sistem modüler tasarlandığı için yeni bir indirim sitesi (örneğin *X Forumu* veya bir e-ticaret indirim sayfası) eklemek oldukça basittir:

1. `scrapers/` dizini altında yeni bir Python dosyası oluşturun (örn: `scrapers/yeni_forum.py`).
2. Sınıfınızı `BaseScraper` sınıfından türetin ve asenkron `scrape()` metodunu doldurun:

```python
from scrapers.base import BaseScraper
from database.db import Database
from typing import List, Dict, Any

class YeniForumScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            source_name="yeniforum",
            base_url="https://yeniforum.com"
        )
        self.forum_url = "https://yeniforum.com/indirimler"

    async def scrape(self) -> List[Dict[str, Any]]:
        # Sayfa HTML'ini BaseScraper içindeki fetch_html ile çekin
        html = await self.fetch_html(self.forum_url)
        
        new_threads = []
        # BeautifulSoup ile parse edip başlık, url, yazar vb. ayıklayın
        # ...
        
        # Tekrarlanan konuları veritabanından sorgulayarak filtreleyin
        # ...
        
        # Yeni konuları veritabanına ekleyin
        await Database.add_thread(
            source=self.source_name,
            thread_id=thread_id,
            title=title,
            url=url,
            content=content,
            author=author
        )
        
        return new_threads
```

3. `pipeline.py` dosyasını açıp oluşturduğunuz yeni tarayıcıyı listeye ekleyin:
```diff
- scrapers = [DonanimArsiviScraper()]
+ scrapers = [DonanimArsiviScraper(), YeniForumScraper()]
```
