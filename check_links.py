import requests
import sys
from datetime import datetime
import time
import re

INPUT_FILE = "playlist.m3u"
OUTPUT_FILE = "playlist.m3u"

def is_youtube_url(url):
    """YouTube URL'sini tespit eder"""
    return 'youtube.com' in url or 'youtu.be' in url or 'googlevideo.com' in url

def is_working(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # YouTube URL'leri için daha toleranslı yaklaşım
        if is_youtube_url(url):
            # YouTube URL'leri için daha kısa timeout ve basit kontrol
            r = requests.head(url, timeout=10, headers=headers, allow_redirects=True)
            # YouTube için 200 veya 302/301 (redirect) kabul edilebilir
            return r.status_code in [200, 301, 302, 404] # 404 bile geçici olabilir YouTube'da
        
        # Normal URL'ler için standart kontrol
        r = requests.get(url, timeout=15, stream=True, headers=headers, allow_redirects=True)
        return r.status_code == 200
    except Exception as e:
        print(f"⚠️  Hata ({url}): {str(e)[:50]}...")
        # YouTube URL'leri için daha toleranslı - sadece çok ciddi hatalar için False dön
        if is_youtube_url(url):
            return "timeout" not in str(e).lower()  # Timeout hariç kabul et
        return False

def main():
    print(f"🚀 IPTV Playlist Kontrolü Başlıyor... {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"❌ {INPUT_FILE} dosyası bulunamadı!")
        sys.exit(1)

    new_lines = []
    broken_urls = []
    working_urls = []
    total_urls = 0
    youtube_urls = 0
    
    for i, line in enumerate(lines):
        if line.startswith("http"):
            total_urls += 1
            url = line.strip()
            
            if is_youtube_url(url):
                youtube_urls += 1
                print(f"🎬 YouTube URL ({total_urls}): {url[:50]}...")
            else:
                print(f"🔍 Kontrol ediliyor ({total_urls}): {url[:50]}...")
            
            if is_working(url):
                new_lines.append(line)
                working_urls.append(url)
                print(f"✅ Çalışıyor")
            else:
                # Sadece gerçekten bozuk olanları sil
                print(f"❌ Çalışmıyor - silinecek")
                broken_urls.append(url)
            
            # Rate limiting - YouTube için daha uzun bekle
            if is_youtube_url(url):
                time.sleep(1.0)  # YouTube için daha uzun bekle
            else:
                time.sleep(0.5)
        else:
            new_lines.append(line)

    # Sadece değişiklik varsa dosyayı güncelle
    if broken_urls:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        
        print("\n" + "=" * 60)
        print(f"📊 SONUÇ RAPORU:")
        print(f"📈 Toplam URL: {total_urls}")
        print(f"🎬 YouTube URL: {youtube_urls}")
        print(f"✅ Çalışan: {len(working_urls)}")
        print(f"❌ Bozuk: {len(broken_urls)}")
        print(f"🔄 {len(broken_urls)} bozuk link temizlendi!")
        
        if broken_urls:
            print(f"\n🗑️  Temizlenen linkler:")
            for url in broken_urls[:10]:  # İlk 10 tanesini göster
                print(f"   - {url}")
            if len(broken_urls) > 10:
                print(f"   ... ve {len(broken_urls) - 10} tane daha")
                
        print("✅ Playlist başarıyla güncellendi!")
    else:
        print("\n" + "=" * 60)
        print("🎉 Harika! Tüm linkler çalışıyor, güncelleme gerekmiyor.")
        print(f"📈 Toplam {total_urls} link kontrol edildi.")
        print(f"🎬 YouTube URL: {youtube_urls}")

if __name__ == "__main__":
    main()
