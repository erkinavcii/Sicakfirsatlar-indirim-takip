# GitHub Actions Kurulum ve Çalıştırma Rehberi

Bu proje, 7/24 kesintisiz çalışması ve Telegram bildirimleri göndermesi için **GitHub Actions** ile tam uyumlu hale getirilmiştir. GitHub Actions tamamen ücretsizdir ve herhangi bir VPS/Sunucu kurulumu gerektirmez.

---

## ⚙️ Sistem Nasıl Çalışır?

### 1. SQLite Veri Kalıcılığı (Database Persistence)
GitHub Actions her tetiklendiğinde temiz ve sıfırlanmış bir sanal makinede çalışır. Verilerin (kaydedilen konular, eşleşen indirimler, kelimeler) kaybolmaması için **Dynamic Cache Rolling** (Dinamik Önbellek) yöntemi kullanılmıştır:
* Her çalıştırmada, bir önceki başarılı çalışmanın `database.db` önbelleği indirilir.
* Tarama işlemi gerçekleştirilir ve yeni konular veritabanına eklenir.
* İşlem bitiminde güncel `database.db` dosyası yeni bir sürüm anahtarı (`database-${{ github.run_id }}`) ile GitHub önbelleğine geri yüklenir.
* **Yedekleme:** Her çalışmanın sonucundaki veritabanı, Actions sekmesinde 14 gün boyunca saklanacak bir **Artifact (Dosya Yedek)** olarak yüklenir. Dilediğiniz zaman indirip yerel bilgisayarınızda açabilirsiniz.

### 2. İki Modlu Çalışma Desteği (Dual-Mode)
* **Yapay Zeka (AI) Modu:** `GEMINI_API_KEY` tanımlıysa Gemini modeli indirimleri analiz eder, gerçek fiyat karşılaştırması yapar ve Telegram'dan gönderir.
* **Yerel (Local) Mod:** `GEMINI_API_KEY` tanımlı değilse, hiçbir API anahtarına gerek duymadan Türkçe ek ve yumuşama kurallarını kullanarak forum konularını filtreler ve Telegram bildirimlerini gönderir.

---

## 🚀 Kurulum Adımları

### Adım 1: Projeyi Kendi GitHub Hesabınıza Yükleyin
Projeyi kendi GitHub hesabınızda bir depoya (repository) push edin veya fork edin.
> [!IMPORTANT]
> Güvenliğiniz için `database.db` ve `.env` dosyaları `.gitignore` içinde engellenmiştir. Bunları kesinlikle deponuza commit etmeyin.

### Adım 2: Telegram Botu ve Sohbet ID Alımı
Eğer Telegram bildirimleri almak istiyorsanız:
1. [@BotFather](https://t.me/BotFather) botu aracılığıyla yeni bir bot oluşturun ve **API Token** değerini alın.
2. [@userinfobot](https://t.me/userinfobot) botuna mesaj atarak kendi Telegram **Sohbet ID (Chat ID)** değerinizi öğrenin.
3. Botunuza Telegram üzerinden `/start` komutunu göndererek mesaj gönderimini aktifleştirin.

### Adım 3: GitHub Secrets Tanımlama
Deponuzun GitHub sayfasına gidin:
1. **Settings** (Ayarlar) > **Secrets and variables** > **Actions** menüsünü açın.
2. **New repository secret** butonuna basarak aşağıdaki değişkenleri ekleyin:

| Secret Adı | Değer | Açıklama |
| :--- | :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | `123456789:ABCDefGh...` | Telegram botunuzun API tokenı |
| `TELEGRAM_CHAT_ID` | `987654321` | Bildirim alacağınız Telegram kullanıcı veya grup ID'niz |
| `GEMINI_API_KEY` | *(İsteğe Bağlı)* | Yapay Zeka modu için Google Gemini API anahtarı |

---

## 🏃 Workflow Tetikleme Yöntemleri

### 1. Zamanlanmış Cron (Otomatik)
* `.github/workflows/scrape.yml` dosyası, sistemi her **30 dakikada bir** otomatik olarak tetikler.
* *Not:* GitHub'ın ücretsiz sunucularındaki yoğunluğa bağlı olarak 30 dakikalık cron'lar bazen 5-15 dakika gecikmeli çalışabilir.

### 2. Manuel Tetikleme (Workflow Dispatch)
İstediğiniz zaman tarayıcıyı anlık olarak tetikleyebilirsiniz:
1. GitHub deponuzda **Actions** sekmesine gidin.
2. Sol menüden **Manual Scraper Trigger** veya **Scheduled Scraper**'ı seçin.
3. **Run workflow** butonuna basarak işlemi anında başlatın.

---

## 🖥️ Yerel Bilgisayarla Senkronizasyon (Opsiyonel)

GitHub Actions üzerinde çalışan veritabanını kendi bilgisayarınızdaki Web Arayüzünde (Dashboard) görmek isterseniz:
1. Son başarılı GitHub Action çalışmasının sayfasına gidin.
2. Sayfanın en altındaki **Artifacts** kısmından `database-backup` dosyasını indirin.
3. İndirdiğiniz zip içindeki `database.db` dosyasını bilgisayarınızdaki proje klasörüne çıkartın.
4. `python main.py` komutuyla yerel sunucuyu çalıştırıp tarayıcınızdan `http://localhost:8000` adresine girerek tüm geçmiş taramaları ve eşleşmeleri premium arayüzden inceleyin.
