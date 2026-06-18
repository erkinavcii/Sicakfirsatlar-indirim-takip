# 🚀 Gelecek Geliştirmeler & Yol Haritası (Futures & Roadmap)

Bu dosya, **Akıllı İndirim Takip ve Doğrulama Sistemi**'nin gelecek geliştirme adımlarını, önceliklerini ve genişletilme planlarını içermektedir. Proje, bu yol haritasına uygun şekilde tamamen modüler bir yapıda kurgulanmıştır.

---

## 📅 Geliştirme Fazları (Phases & Priorities)

### Faz 1 — Scraper Güvenilirliği & Dayanıklılık 
*   **Öncelik**: Çok Yüksek | **Durum**: Tamamlandı ✅
*   **Hedef**: Forum HTML yapısındaki değişikliklere karşı dayanıklılık kazanmak ve bot tespiti engellerini aşmak.
*   **Görevler**:
    *   [x] **Rate Limiting & Random Delay**: İstekler arasına asenkron rastgele gecikmeler (`asyncio.sleep(random.uniform(0.5, 2.0))`) eklenerek insan benzeri tarama profili oluşturulması.
    *   [x] **Rotating User-Agent Pool**: [base.py](scrapers/base.py) dosyasında 10-15 adet güncel tarayıcı User-Agent'ından oluşan bir havuz tanımlanıp her istekte rastgele seçilmesi.
    *   [x] **Çoklu Sayfa Desteği (Pagination)**: Sadece ilk sayfayı değil, son 24 saat içinde açılan tüm konuları yakalamak için geriye doğru sayfalama desteği.
    *   [ ] **İleti Bazlı Tekilleştirme**: Aynı indirim konusunu veya iletisini tekrar işlememek için `thread_id` ve `post_id` veritabanı kontrollerinin doğrulanması.

### Faz 2 — NLP & Yerel Filtreleme Kalitesi
*   **Öncelik**: Yüksek | **Durum**: Kısmen Tamamlandı (Temel NLP + Fuzzy Eşleşme Aktif) ✅
*   **Hedef**: Yerel filtreleme kalitesini artırarak hatalı eşleşmeleri sıfıra indirmek.
*   **Görevler**:
    *   [ ] **Keyword Yönetimi**: Takip kelimelerinin doğrudan [config.py](config.py) içerisindeki `TRACKED_KEYWORDS` listesinden de yüklenebilir/yönetilebilir hale getirilmesi.
    *   [x] **Fuzzy Matching (Bulanık Eşleşme)**: "samsung" yerine "samsun" veya "sansung" gibi yazım hatalarını yakalamak için `rapidfuzz` kütüphanesi entegrasyonu (Levenshtein benzerlik skoru > %85).
    *   [ ] **Minimum İndirim Eşiği**: Yapay zeka modunda minimum indirim oranını filtreleyen parametre (örn: `MIN_DISCOUNT_PERCENTAGE = 10`).
    *   [ ] **Karaliste (Blacklist) Desteği**: "satılık", "aranıyor", "referans", "ikinci el" gibi indirim olmayan veya spam ilanların yerelde doğrudan elenmesi.

### Faz 3 — Fiyat Doğrulama Stratejileri
*   **Öncelik**: Orta | **Durum**: Kısmen Tamamlandı (Gemini Grounding Aktif) ✅
*   **Hedef**: Fiyat doğrulama katmanını daha hızlı ve yedekli hale getirmek.
*   **Görevler**:
    *   [x] **Gemini Search Grounding**: Gemini API ile canlı internet araması yaparak fiyat doğrulaması yapılması.
    *   [ ] **Google Custom Search Fallback**: Gemini aramasının başarısız veya limit aşımında olduğu durumlarda yedek arama katmanı olarak Google Search API entegrasyonu.
    *   [ ] **E-Ticaret API Sorgulamaları**: Trendyol, Hepsiburada gibi sitelerin unofficial arama API'leri kullanılarak doğrudan ve hızlı ürün/fiyat teyidi.

### Faz 4 — Bildirim & Dashboard Geliştirmeleri
*   **Öncelik**: Orta | **Durum**: Kısmen Tamamlandı (Telegram & Manual Trigger Aktif) ✅
*   **Hedef**: Kullanıcı etkileşimini ve bildirim kanallarını zenginleştirmek.
*   **Görevler**:
    *   [x] **Telegram Bot Entegrasyonu**: HTML kart formatında anlık bildirim gönderilmesi.
    *   [x] **Dashboard Manuel Tetikleme**: Kontrol paneline "Şimdi Tara" butonuyla anlık asenkron tarama desteği.
    *   [ ] **Aynı Fırsat Tekrar Bildirim Engelleyici (24 Saat Cooldown)**: Aynı ürünün farklı başlıklarla tekrar paylaşılması durumunda, 24 saat içinde sadece 1 kez bildirim atılmasını sağlayan ürün ismi bazlı akıllı tekilleştirme.
    *   [ ] **Discord Webhook Entegrasyonu**: Telegram'a alternatif olarak Discord kanallarına webhook ile kolay indirim kartları gönderilmesi.

### Faz 5 — Çoklu Site Desteği
*   **Öncelik**: Düşük | **Durum**: Planlanıyor ⏳
*   **Hedef**: Sistemi farklı forum ve indirim sitelerine genişletmek.
*   **Görevler**:
    *   [ ] **Donanım Haber Sıcak Fırsatlar**: `DonanimHaberScraper` yazılması.
    *   [ ] **Technopat Sosyal İndirim Köşesi**: `TechnopatScraper` yazılması.
    *   [ ] **Ekşi Sözlük / Fırsat Başlıkları**: Popüler indirim başlıklarının taranması.

### Faz 6 — GitHub Actions Bulut Entegrasyonu & Veri Kalıcılığı
*   **Öncelik**: Yüksek | **Durum**: Tamamlandı ✅
*   **Hedef**: Sunucu/VPS maliyeti olmadan sistemi 7/24 bulut üzerinde ücretsiz çalıştırmak.
*   **Görevler**:
    *   [x] **Tekli Çalışma Scripti (run_once.py)**: Web sunucusu ayağa kaldırmadan tek adımda tarama ve Telegram bildirim işlemini gerçekleştirip sonlanan script.
    *   [x] **Dinamik Önbellekleme (Dynamic Cache Rolling)**: GitHub Actions her çalıştığında SQLite veri dosyasını (`database.db`) kaybetmemek için dinamik önbellek yönetimi.
    *   [x] **Manuel ve Zamanlanmış Tetikleyiciler**: Her 30 dakikada bir otomatik çalışan cron ve GitHub Actions panelinden anlık tetiklenebilen manuel buton desteği.
    *   [x] **Kurulum Dokümantasyonu**: Adım adım kurulum yönergelerinin [docs/github-actions-setup.md](docs/github-actions-setup.md) olarak yazılması.

### Faz 7 — Veritabanı Ölçekleme (Hosted Database)
*   **Öncelik**: Düşük | **Durum**: Planlanıyor (Gelecek Yol Haritası) ⏳
*   **Hedef**: SQLite dosya önbellekleme yerine, buluttaki bir PostgreSQL (Supabase / Neon / CockroachDB) veritabanına doğrudan bağlanma seçeneği eklemek.
*   **Görevler**:
    *   [ ] **SQLAlchemy / SQLModel Geçişi**: Farklı SQL lehçeleriyle (SQLite ve PostgreSQL) uyumlu çalışacak ORM katmanı.
    *   [ ] **Bulut DB Yapılandırması**: `.env` dosyasına `DATABASE_URL` parametresi eklenerek canlı veritabanı desteği sağlanması.

---

## 📝 Temiz Proje Promptu (GitHub ve Geliştiriciler İçin)

Aşağıdaki prompt, projenin tüm mimari detaylarını ve vizyonunu başka bir yapay zekaya veya geliştiriciye aktarmak için şablon olarak kullanılabilir:

```markdown
## Proje: Sıcak Fırsatlar İndirim Takip Otomasyonu (Smart Deal Tracker)

### Amaç
Donanimarsivi.com Sıcak Fırsatlar forumunu asenkron olarak tarayan, kullanıcı tanımlı anahtar kelimelerle eşleşen indirimleri tespit eden, yapay zeka ile piyasa fiyatını doğrulayan ve Telegram/Discord üzerinden bildirim gönderen çift modlu bir indirim takip otomasyonu geliştir.

### Teknik Stack
- Backend: Python 3.10+, FastAPI, aiosqlite
- Scraping: httpx + BeautifulSoup4 (asenkron), Rotating User-Agent, Rate Limiting
- NLP: Özel Türkçe Lemmatizer/Stemmer (çekim ekleri + ünsüz yumuşaması yumuşatıcı)
- AI Doğrulama: Google Gemini API (Pydantic Structured Output + Google Search Grounding)
- Bildirim: Telegram Bot API, Discord Webhook
- Zamanlama: APScheduler (10 dakikalık zamanlayıcı + manuel tetikleme)
- Dashboard: FastAPI + Jinja2 HTML/CSS (Curated space colors, glassmorphism, animated statuses)

### Çift Mod Mimarisi (Dual-Mode)
1. Yerel Mod (Zero-Setup): API anahtarı gerekmez. XenForo ön eklerinden (🔥 İndirim / ❌ İndirim Bitti) ve yerel Türkçe NLP motoruyla filtreleme.
2. Gemini Modu: GEMINI_API_KEY tanımlandığında aktif. Ürün adı ve fiyatı yapılandırılmış veri olarak çıkarılır, Google Search Grounding ile e-ticaret sitelerindeki (Amazon, Hepsiburada vb.) en ucuz fiyatlar aranır, indirim oranı doğrulanıp Telegram'a atılır.

### Temel Gereksinimler
- Thread ID bazlı duplicate kontrolü (aynı konuyu tekrar işleme)
- config.py'den yönetilebilir TRACKED_KEYWORDS ve MIN_DISCOUNT_PERCENTAGE parametreleri
- 24 saatlik bildirim cooldown penceresi (aynı ürün için mükerrer bildirim engelleme)
- Yeni site eklemeyi kolaylaştıran modüler BaseScraper abstract sınıf mimarisi
```
