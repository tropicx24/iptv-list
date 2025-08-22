# 📺 IPTV Playlist Otomatik Güncelleme

Bu proje IPTV playlist'inizdeki linkleri otomatik olarak kontrol eder ve çalışmayan linkleri temizler.

## 🚀 Özellikler

- ✅ Otomatik link kontrolü
- 🔄 Günde 2 kez çalışma (06:00 ve 18:00)
- 🤖 GitHub Actions ile tam otomatik
- 📊 Detaylı raporlama
- 🗑️ Bozuk linkleri otomatik temizleme

## 📋 Çalışma Mantığı

1. **Günlük Kontrol**: Her gün belirlenen saatlerde çalışır
2. **Link Testi**: Her URL'ye HTTP isteği gönderir
3. **Temizleme**: Çalışmayan linkleri playlist'ten çıkarır
4. **Güncelleme**: Değişiklikleri otomatik commit eder

## 🛠️ Kurulum

1. Bu repository'yi fork edin
2. \playlist.m3u\ dosyanızı yükleyin
3. GitHub Actions otomatik olarak çalışmaya başlar

## 📊 Durum

[![🔄 IPTV Playlist Otomatik Güncelleme](https://github.com/tropicx24/iptv-playlist/actions/workflows/update_playlist.yml/badge.svg)](https://github.com/tropicx24/iptv-playlist/actions/workflows/update_playlist.yml)

Son güncelleme: $(Get-Date -Format "dd.MM.yyyy HH:mm")

## 📝 Kullanım

### Manuel Çalıştırma
`ash
python check_links.py
`

### GitHub Actions üzerinden
- Repository > Actions > "Update IPTV Playlist" > "Run workflow"

## ⚙️ Yapılandırma

\.github/workflows/update_playlist.yml\ dosyasında zamanlama ayarlarını değiştirebilirsiniz:

`yaml
schedule:
  - cron: '0 3 * * *'   # Her gün 06:00 (UTC+3)
  - cron: '0 15 * * *'  # Her gün 18:00 (UTC+3)
`

## 📈 Özelleştirme

- **Timeout Süresi**: \check_links.py\ içinde \	imeout=15\
- **Rate Limiting**: stekler arası 0.5 saniye bekleme
- **User Agent**: Gerçek tarayıcı benzeri header

## 🤝 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (\git checkout -b feature/amazing-feature\)
3. Commit edin (\git commit -m 'Add amazing feature'\)
4. Push edin (\git push origin feature/amazing-feature\)
5. Pull Request oluşturun

## 📄 Lisans

Bu proje MIT lisansı altındadır.

---

🤖 **Bu repository GitHub Actions tarafından otomatik olarak güncellenmektedir.**
