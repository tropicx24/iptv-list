import requests
from bs4 import BeautifulSoup
import re
import json

def get_cnn_turk_stream():
    """CNN Türk canlı yayın linkini bul"""
    try:
        url = "https://www.cnnturk.com/canli-yayin"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Video player script'lerini ara
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'stream' in script.string.lower():
                # M3U8 link'lerini ara
                m3u8_links = re.findall(r'https?://[^"\']*\.m3u8[^"\']*', script.string)
                if m3u8_links:
                    return m3u8_links[0]
                    
                # MP4 link'lerini ara
                mp4_links = re.findall(r'https?://[^"\']*\.mp4[^"\']*', script.string)
                if mp4_links:
                    return mp4_links[0]
        
        # Alternatif: Embed player'ı kontrol et
        iframe = soup.find('iframe')
        if iframe and iframe.get('src'):
            return iframe.get('src')
            
        return None
        
    except Exception as e:
        print(f"CNN Türk stream alınamadı: {e}")
        return None

def create_news_m3u():
    """Haber kanalları M3U listesi oluştur"""
    
    # Haber kanalları stream linkleri
    news_channels = [
        {
            "name": "CNN Türk",
            "category": "Haber",
            "logo": "https://upload.wikimedia.org/wikipedia/commons/6/68/CNN_T%C3%BCrk_logosu.png",
            "url": "auto"  # Otomatik bulunacak
        },
        {
            "name": "NTV",
            "category": "Haber", 
            "logo": "https://upload.wikimedia.org/wikipedia/tr/9/9e/NTV_logosu.png",
            "url": "https://dogus-live.daioncdn.net/ntv/ntv.m3u8"
        },
        {
            "name": "Haber Türk",
            "category": "Haber",
            "logo": "https://upload.wikimedia.org/wikipedia/tr/2/23/Habert%C3%BCrk_logosu.png", 
            "url": "https://tv.ensonhaber.com/haberturk/haberturk.m3u8"
        },
        {
            "name": "24 TV",
            "category": "Haber",
            "logo": "https://upload.wikimedia.org/wikipedia/tr/e/e4/24_TV_logosu.png",
            "url": "https://turkmedya-live.ercdn.net/tv24/tv24.m3u8"
        },
        {
            "name": "A Haber",
            "category": "Haber",
            "logo": "https://upload.wikimedia.org/wikipedia/tr/e/e9/A_Haber_logosu.png",
            "url": "https://tv.ensonhaber.com/ahaber/ahaber.m3u8"
        },
        {
            "name": "Halk TV",
            "category": "Haber",
            "logo": "https://upload.wikimedia.org/wikipedia/tr/1/1c/HalkTV_logosu.png",
            "url": "https://halktv-live.ercdn.net/halktv/halktv.m3u8"
        }
    ]
    
    # Ana TV Kanalları
    main_tv_channels = [
        {
            "name": "Show TV",
            "category": "Ana Kanal",
            "logo": "https://upload.wikimedia.org/wikipedia/tr/f/f1/Show_TV.png",
            "url": "https://ciner-live.daioncdn.net/showtv/showtv.m3u8"
        },
        {
            "name": "ATV",
            "category": "Ana Kanal",
            "logo": "https://upload.wikimedia.org/wikipedia/tr/6/68/Atv_logosu.png",
            "url": "https://trkvz-live.daioncdn.net/atv/atv.m3u8"
        },
        {
            "name": "Star TV",
            "category": "Ana Kanal",
            "logo": "https://upload.wikimedia.org/wikipedia/tr/6/68/Star_TV_logosu.png",
            "url": "https://dogus-live.daioncdn.net/startv/startv.m3u8"
        },
        {
            "name": "FOX TV",
            "category": "Ana Kanal",
            "logo": "https://upload.wikimedia.org/wikipedia/commons/0/0d/Fox-tv-tr.png",
            "url": "https://fox-live.daioncdn.net/foxtv/foxtv.m3u8"
        },
        {
            "name": "Kanal D",
            "category": "Ana Kanal",
            "logo": "https://upload.wikimedia.org/wikipedia/tr/9/9d/Kanal_D.png",
            "url": "https://demiroren-live.daioncdn.net/kanald/kanald.m3u8"
        },
        {
            "name": "TV8",
            "category": "Ana Kanal",
            "logo": "https://upload.wikimedia.org/wikipedia/tr/9/95/TV8_yeni_logosu.png",
            "url": "https://tv8-live.daioncdn.net/tv8/tv8.m3u8"
        },
        {
            "name": "Kanal 7",
            "category": "Ana Kanal",
            "logo": "https://upload.wikimedia.org/wikipedia/tr/8/85/Kanal_7.png",
            "url": "https://kanal7-live.daioncdn.net/kanal7/kanal7.m3u8"
        },
        {
            "name": "Beyaz TV",
            "category": "Ana Kanal",
            "logo": "https://upload.wikimedia.org/wikipedia/tr/b/b9/Beyaz_TV_logosu.png",
            "url": "https://beyaztv-live.daioncdn.net/beyaztv/beyaztv.m3u8"
        }
    ]
    
    # TRT Kanalları
    trt_channels = [
        {
            "name": "TRT 1",
            "category": "TRT",
            "logo": "https://upload.wikimedia.org/wikipedia/tr/9/9b/TRT_1_logosu.png",
            "url": "https://tv-trt1.medya.trt.com.tr/master.m3u8"
        },
        {
            "name": "TRT Haber",
            "category": "TRT",
            "logo": "https://upload.wikimedia.org/wikipedia/tr/a/a5/TRT_Haber_logosu.png",
            "url": "https://tv-trthaber.medya.trt.com.tr/master.m3u8"
        },
        {
            "name": "TRT World",
            "category": "TRT",
            "logo": "https://upload.wikimedia.org/wikipedia/commons/2/27/TRT_World.png",
            "url": "https://tv-trtworld.medya.trt.com.tr/master.m3u8"
        },
        {
            "name": "TRT Spor",
            "category": "TRT",
            "logo": "https://upload.wikimedia.org/wikipedia/tr/6/61/TRT_Spor_logosu.png",
            "url": "https://tv-trtspor1.medya.trt.com.tr/master.m3u8"
        },
        {
            "name": "TRT Çocuk",
            "category": "TRT",
            "logo": "https://upload.wikimedia.org/wikipedia/tr/9/9c/TRT_%C3%87ocuk_logosu.png",
            "url": "https://tv-trtcocuk.medya.trt.com.tr/master.m3u8"
        },
        {
            "name": "TRT Belgesel",
            "category": "TRT",
            "logo": "https://upload.wikimedia.org/wikipedia/tr/4/4a/TRT_Belgesel_logosu.png",
            "url": "https://tv-trtbelgesel.medya.trt.com.tr/master.m3u8"
        },
        {
            "name": "TRT Müzik",
            "category": "TRT",
            "logo": "https://upload.wikimedia.org/wikipedia/tr/9/94/TRT_M%C3%BCzik_logosu.png",
            "url": "https://tv-trtmuzik.medya.trt.com.tr/master.m3u8"
        },
        {
            "name": "TRT Türk",
            "category": "TRT",
            "logo": "https://upload.wikimedia.org/wikipedia/tr/d/dd/TRT_T%C3%BCrk_logosu.png",
            "url": "https://tv-trtturk.medya.trt.com.tr/master.m3u8"
        },
        {
            "name": "TRT Avaz",
            "category": "TRT",
            "logo": "https://upload.wikimedia.org/wikipedia/tr/8/8a/TRT_Avaz_logosu.png",
            "url": "https://tv-trtavaz.medya.trt.com.tr/master.m3u8"
        },
        {
            "name": "TRT Kurdî",
            "category": "TRT",
            "logo": "https://upload.wikimedia.org/wikipedia/commons/8/8e/TRT_Kurd%C3%AE.png",
            "url": "https://tv-trtkurdi.medya.trt.com.tr/master.m3u8"
        },
        {
            "name": "TRT Arabi",
            "category": "TRT",
            "logo": "https://upload.wikimedia.org/wikipedia/commons/9/9a/TRT_ARABI.png",
            "url": "https://tv-trtarabi.medya.trt.com.tr/master.m3u8"
        },
        {
            "name": "TRT EBA TV İlkokul",
            "category": "TRT",
            "logo": "https://upload.wikimedia.org/wikipedia/tr/4/47/TRT_EBA_TV_%C4%B0lkokul_logosu.png",
            "url": "https://tv-e-okul00.medya.trt.com.tr/master.m3u8"
        },
        {
            "name": "TRT EBA TV Ortaokul",
            "category": "TRT",
            "logo": "https://upload.wikimedia.org/wikipedia/tr/b/bf/TRT_EBA_TV_Ortaokul_logosu.png",
            "url": "https://tv-e-okul01.medya.trt.com.tr/master.m3u8"
        },
        {
            "name": "TRT EBA TV Lise",
            "category": "TRT",
            "logo": "https://upload.wikimedia.org/wikipedia/tr/1/19/TRT_EBA_TV_Lise_logosu.png",
            "url": "https://tv-e-okul02.medya.trt.com.tr/master.m3u8"
        }
    ]
    
    # Tüm kanalları birleştir
    all_channels = news_channels + main_tv_channels + trt_channels
    
    # CNN Türk stream'ini otomatik bul
    print("CNN Türk canlı yayın linki aranıyor...")
    cnn_stream = get_cnn_turk_stream()
    
    # M3U dosyası oluştur
    m3u_content = "#EXTM3U\n"
    
    for channel in all_channels:
        name = channel["name"]
        category = channel["category"]
        logo = channel["logo"]
        
        if channel["url"] == "auto" and name == "CNN Türk":
            url = cnn_stream if cnn_stream else "https://www.cnnturk.com/canli-yayin"
        else:
            url = channel["url"]
            
        # M3U formatında ekle
        m3u_content += f'#EXTINF:-1 group-title="{category}" tvg-logo="{logo}",{name}\n'
        m3u_content += f'{url}\n'
    
    # Dosyaya kaydet
    with open("turkiye_kanallari.m3u", "w", encoding="utf-8") as f:
        f.write(m3u_content)
    
    print("✅ turkiye_kanallari.m3u dosyası oluşturuldu!")
    print(f"📺 {len(news_channels)} haber + {len(main_tv_channels)} ana kanal + {len(trt_channels)} TRT = {len(all_channels)} toplam kanal")
    
    if cnn_stream:
        print(f"🔗 CNN Türk stream: {cnn_stream}")
    else:
        print("⚠️ CNN Türk stream otomatik bulunamadı, web sayfası linki kullanıldı")
    
    return m3u_content

if __name__ == "__main__":
    # Türkiye kanalları M3U'sunu oluştur
    create_news_m3u()
    
    # İçeriği göster
    print("\n📄 M3U İçeriği:")
    with open("turkiye_kanallari.m3u", "r", encoding="utf-8") as f:
        print(f.read())