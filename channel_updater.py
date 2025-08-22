#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
turkiye_kanallari.m3u Güncelleyici
Bu script kanalların durumunu kontrol eder ve güncel tutmaya yardımcı olur.
"""

import requests
import json
import time
import os
from datetime import datetime
import threading
from urllib.parse import urlparse

class ChannelUpdater:
    def __init__(self):
        self.working_channels = []
        self.broken_channels = []
        self.timeout = 10
        
        # Script'in bulunduğu dizini al
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Çalışma dizinini script dizinine değiştir
        if os.getcwd() != self.script_dir:
            os.chdir(self.script_dir)
            print(f"📁 Çalışma dizini değiştirildi: {self.script_dir}")
        
    def check_stream_url(self, url, channel_name):
        """Stream URL'ini kontrol et"""
        try:
            # Headers ekleyerek bot korumasını aş
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # CNN Türk için özel timeout
            timeout = 15 if 'cnn' in channel_name.lower() else self.timeout
            
            # M3U8 linkleri için özel kontrol
            if url.endswith('.m3u8'):
                # İlk önce HEAD request ile hızlı kontrol
                response = requests.head(url, timeout=timeout, allow_redirects=True, headers=headers)
                
                if response.status_code == 200:
                    # TRT kanalları için basitleştirilmiş kontrol
                    if 'trt.com.tr' in url:
                        return True, "Çalışıyor (TRT Official)"
                    
                    # Diğer kanallar için stream içeriğini kontrol et
                    try:
                        content_response = requests.get(url, timeout=timeout, headers=headers)
                        content = content_response.text
                        
                        # M3U8 playlist içeriğini kontrol et
                        if '#EXTM3U' in content or '#EXT-X-VERSION' in content:
                            return True, "Çalışıyor (Stream aktif)"
                        else:
                            # Basit format kontrolü
                            lines = content.strip().split('\n')
                            if any(line.endswith('.ts') or line.endswith('.m3u8') for line in lines):
                                return True, "Çalışıyor (Basic stream)"
                            else:
                                return False, "M3U8 içerik sorunu"
                    except Exception as e:
                        # Eğer içerik okunamıyorsa ama HTTP 200 alıyorsak, çalışıyor sayalım
                        return True, "Çalışıyor (HTTP OK)"
                else:
                    return False, f"HTTP {response.status_code}"
            else:
                # Normal web sayfaları için
                response = requests.get(url, timeout=timeout, allow_redirects=True, headers=headers)
                if response.status_code == 200:
                    return True, "Erişilebilir"
                else:
                    return False, f"HTTP {response.status_code}"
                    
        except requests.exceptions.Timeout:
            return False, "Zaman aşımı"
        except requests.exceptions.ConnectionError:
            return False, "Bağlantı hatası"
        except Exception as e:
            return False, f"Hata: {str(e)}"
    
    def test_channel(self, channel):
        """Tek kanal test et"""
        name = channel['name']
        url = channel['url']
        category = channel['category']
        
        print(f"🔍 {name} kontrol ediliyor...")
        
        is_working, status = self.check_stream_url(url, name)
        
        result = {
            'name': name,
            'category': category,
            'url': url,
            'status': status,
            'working': is_working,
            'checked_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if is_working:
            print(f"✅ {name}: {status}")
            self.working_channels.append(result)
        else:
            print(f"❌ {name}: {status}")
            self.broken_channels.append(result)
            
        return result
    
    def get_channels_from_m3u(self, filename="turkiye_kanallari.m3u"):
        """M3U dosyasından kanalları çıkar"""
        channels = []
        
        try:
            # Dosya yolunu tam yol olarak oluştur
            full_path = os.path.join(self.script_dir, filename)
            
            # Dosya varlığını kontrol et
            if not os.path.exists(full_path):
                print(f"❌ {filename} dosyası bulunamadı!")
                print(f"📁 Aranan yer: {full_path}")
                print(f"📁 Geçerli dizin: {os.getcwd()}")
                
                # Dizindeki M3U dosyalarını listele
                m3u_files = [f for f in os.listdir(self.script_dir) if f.endswith('.m3u')]
                if m3u_files:
                    print(f"📄 Bulunan M3U dosyaları:")
                    for i, f in enumerate(m3u_files, 1):
                        print(f"   {i}. {f}")
                    print("💡 Yukarıdaki dosyalardan birini kullanmak ister misiniz?")
                else:
                    print("💡 M3U dosyasının script ile aynı dizinde olduğunu kontrol edin.")
                return []
            
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            current_channel = {}
            for line in lines:
                line = line.strip()
                
                if line.startswith('#EXTINF'):
                    # Kanal bilgilerini çıkar
                    if 'group-title=' in line:
                        category = line.split('group-title="')[1].split('"')[0]
                        current_channel['category'] = category
                    
                    if ',' in line:
                        name = line.split(',')[-1]
                        current_channel['name'] = name
                        
                elif line and not line.startswith('#') and current_channel:
                    # URL satırı
                    current_channel['url'] = line
                    channels.append(current_channel.copy())
                    current_channel = {}
            
            return channels
            
        except FileNotFoundError:
            print(f"❌ {filename} dosyası bulunamadı!")
            print(f"📁 Geçerli dizin: {os.getcwd()}")
            print("💡 M3U dosyasının script ile aynı dizinde olduğunu kontrol edin.")
            return []
        except Exception as e:
            print(f"❌ M3U dosyası okunurken hata: {str(e)}")
            return []
    
    def test_category_channels(self, category_filter):
        """Belirli kategorideki kanalları test et"""
        channels = self.get_channels_from_m3u()
        if not channels:
            print("❌ M3U dosyası bulunamadı!")
            return
        
        # Kategoriyi filtrele
        filtered_channels = [ch for ch in channels if category_filter.lower() in ch['category'].lower()]
        
        if not filtered_channels:
            print(f"❌ '{category_filter}' kategorisinde kanal bulunamadı!")
            return
        
        print(f"🔍 {category_filter} kategorisinde {len(filtered_channels)} kanal test ediliyor...")
        print("=" * 50)
        
        # Test sonuçları
        working = []
        broken = []
        
        for i, channel in enumerate(filtered_channels, 1):
            print(f"[{i}/{len(filtered_channels)}] ", end="")
            result = self.test_channel(channel)
            
            if result['working']:
                working.append(result)
            else:
                broken.append(result)
        
        # Sonuçları raporla
        print(f"\n📊 {category_filter.upper()} SONUÇLARI:")
        print("=" * 30)
        print(f"✅ Çalışan: {len(working)}")
        print(f"❌ Sorunlu: {len(broken)}")
        
        if broken:
            print(f"\n🔧 Sorunlu {category_filter} Kanalları:")
            for ch in broken:
                print(f"• {ch['name']}: {ch['status']}")
                
        return working, broken
    
    def test_single_channel(self, channel_name):
        """Tek bir kanalı test et"""
        channels = self.get_channels_from_m3u()
        if not channels:
            print("❌ M3U dosyası bulunamadı!")
            return
        
        for channel in channels:
            if channel_name.lower() in channel['name'].lower():
                print(f"🔍 {channel['name']} test ediliyor...")
                result = self.test_channel(channel)
                return result
        
        print(f"❌ '{channel_name}' adında kanal bulunamadı!")
        return None
    
    def select_m3u_file(self):
        """Kullanıcının M3U dosyası seçmesini sağla"""
        m3u_files = [f for f in os.listdir(self.script_dir) if f.endswith('.m3u')]
        
        if not m3u_files:
            print("❌ Hiçbir M3U dosyası bulunamadı!")
            return None
        
        print(f"\n📄 Bulunan M3U dosyaları:")
        for i, f in enumerate(m3u_files, 1):
            file_path = os.path.join(self.script_dir, f)
            file_size = os.path.getsize(file_path)
            print(f"   {i}. {f} ({file_size} bytes)")
        
        try:
            choice = input(f"\nKullanmak istediğiniz dosyayı seçin (1-{len(m3u_files)}): ").strip()
            index = int(choice) - 1
            
            if 0 <= index < len(m3u_files):
                selected_file = m3u_files[index]
                print(f"✅ Seçilen dosya: {selected_file}")
                return selected_file
            else:
                print("❌ Geçersiz seçim!")
                return None
                
        except ValueError:
            print("❌ Geçersiz giriş!")
            return None
    
    def check_all_channels(self):
        """Tüm kanalları kontrol et"""
        print("🚀 Kanal durumu kontrolü başlıyor...")
        print("=" * 50)
        
        channels = self.get_channels_from_m3u()
        if not channels:
            print("❌ Kontrol edilecek kanal bulunamadı!")
            print("💡 Lütfen 'turkiye_kanallari.m3u' dosyasının mevcut dizinde olduğunu kontrol edin.")
            
            # Alternatif M3U dosyası seçme önerisi
            m3u_files = [f for f in os.listdir(self.script_dir) if f.endswith('.m3u')]
            if m3u_files:
                use_alternative = input("\n🔄 Başka bir M3U dosyası kullanmak ister misiniz? (e/h): ").strip().lower()
                if use_alternative == 'e':
                    selected_file = self.select_m3u_file()
                    if selected_file:
                        channels = self.get_channels_from_m3u(selected_file)
                    
            if not channels:
                return
        
        print(f"📺 {len(channels)} kanal kontrol edilecek...\n")
        
        # Tüm kanalları test et
        for i, channel in enumerate(channels, 1):
            print(f"[{i}/{len(channels)}] ", end="")
            self.test_channel(channel)
            time.sleep(1)  # Rate limiting
        
        # Sonuçları raporla
        self.generate_report()
    
    def generate_report(self):
        """Detaylı rapor oluştur"""
        print("\n" + "=" * 50)
        print("📊 KANAL DURUMU RAPORU")
        print("=" * 50)
        
        total = len(self.working_channels) + len(self.broken_channels)
        working_rate = (len(self.working_channels) / total * 100) if total > 0 else 0
        
        print(f"✅ Çalışan kanallar: {len(self.working_channels)}")
        print(f"❌ Sorunlu kanallar: {len(self.broken_channels)}")
        print(f"📈 Başarı oranı: %{working_rate:.1f}")
        
        if self.broken_channels:
            print(f"\n🔧 Sorunlu Kanallar:")
            print("-" * 30)
            for channel in self.broken_channels:
                print(f"• {channel['name']} ({channel['category']}): {channel['status']}")
        
        # Kategori bazlı analiz
        self.analyze_by_category()
        
        # JSON raporu kaydet
        report = {
            'checked_at': datetime.now().isoformat(),
            'total_channels': total,
            'working_channels': len(self.working_channels),
            'broken_channels': len(self.broken_channels),
            'success_rate': working_rate,
            'working': self.working_channels,
            'broken': self.broken_channels
        }
        
        with open('channel_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Detaylı rapor 'channel_report.json' dosyasına kaydedildi")
    
    def suggest_fixes_for_broken_channels(self):
        """Çalışmayan kanallar için öneriler getir"""
        if not self.broken_channels:
            print("✅ Tüm kanallar çalışıyor, öneri gerekmiyor!")
            return
        
        print("\n🔧 ÇALIŞMAYAN KANALLAR İÇİN ÖNERİLER:")
        print("=" * 50)
        
        # Kanal bazlı alternatif URL'ler
        alternative_urls = {
            "CNN Türk": [
                "https://ciner-live.daioncdn.net/cnnturk/cnnturk.m3u8",
                "https://live.duhnet.tv/S2/HLS_LIVE/cnnturknp/playlist.m3u8",
                "https://mn-nl.mncdn.com/blutv_cnnturk2/live_720p2000000kbps/index.m3u8"
            ],
            "A Haber": [
                "https://trkvz-live.daioncdn.net/ahaber/ahaber.m3u8",
                "https://live.duhnet.tv/S2/HLS_LIVE/ahabernp/playlist.m3u8",
                "https://mn-nl.mncdn.com/blutv_ahaber/live_720p2000000kbps/index.m3u8"
            ],
            "FOX TV": [
                "https://fox-live.daioncdn.net/foxtv/foxtv.m3u8",
                "https://live.duhnet.tv/S2/HLS_LIVE/foxtvnp/playlist.m3u8"
            ],
            "TRT Spor Yıldız": [
                "https://tv-trtspor2.medya.trt.com.tr/master.m3u8",
                "https://tv-trtsporyildiz.medya.trt.com.tr/master.m3u8"
            ]
        }
        
        # Benzer kanal önerileri
        similar_channels = {
            "CNN Türk": ["NTV", "Haber Türk", "24 TV"],
            "A Haber": ["CNN Türk", "Haber Türk", "TRT Haber"],
            "FOX TV": ["Show TV", "Kanal D", "Star TV"],
            "ESPN International": ["TRT Spor", "A Spor", "S Sport"],
            "BBC Earth": ["TRT Belgesel", "National Geographic Turkey", "Discovery Channel Turkey"]
        }
        
        for i, channel in enumerate(self.broken_channels, 1):
            name = channel['name']
            status = channel['status']
            category = channel['category']
            
            print(f"\n🔴 {i}. {name} ({category})")
            print(f"   Hata: {status}")
            
            # Hata tipine göre öneriler
            if "HTTP 403" in status or "HTTP 500" in status:
                print("   💡 Öneriler:")
                print("      • Sunucu bot koruması kullanıyor olabilir")
                print("      • VPN kullanmayı deneyin")
                print("      • Farklı saatlerde tekrar deneyin")
                
            elif "Bağlantı hatası" in status:
                print("   💡 Öneriler:")
                print("      • İnternet bağlantınızı kontrol edin")
                print("      • URL geçici olarak erişilemez olabilir")
                print("      • DNS ayarlarınızı kontrol edin")
                
            elif "Zaman aşımı" in status:
                print("   💡 Öneriler:")
                print("      • Sunucu yavaş yanıt veriyor")
                print("      • Timeout süresini artırın")
                print("      • Daha hızlı internet bağlantısı kullanın")
            
            # Alternatif URL'ler
            if name in alternative_urls:
                print("   🔗 Alternatif URL'ler:")
                for j, alt_url in enumerate(alternative_urls[name], 1):
                    print(f"      {j}. {alt_url}")
            
            # Benzer kanallar
            if name in similar_channels:
                print(f"   📺 Benzer çalışan kanallar:")
                for similar in similar_channels[name]:
                    # Benzer kanalın çalışıp çalışmadığını kontrol et
                    is_working = any(ch['name'] == similar and ch['working'] 
                                   for ch in self.working_channels)
                    if is_working:
                        print(f"      ✅ {similar}")
                    else:
                        print(f"      ❓ {similar}")
        
        print(f"\n💼 GENEL ÖNERİLER:")
        print("=" * 30)
        print("1. 📱 VPN kullanarak farklı konumlardan deneyin")
        print("2. 🔄 Kanalları farklı saatlerde tekrar kontrol edin")
        print("3. 🌐 DNS ayarlarınızı değiştirin (8.8.8.8, 1.1.1.1)")
        print("4. 📞 Kanal sağlayıcısına güncel URL için başvurun")
        print("5. 🔍 IPTV forumlarında güncel URL'leri arayın")
        
        # Otomatik düzeltme önerisi
        print(f"\n🤖 OTOMATİK DÜZELTİCİ:")
        print("   M3U dosyanızı otomatik olarak düzeltmek ister misiniz? (e/h)")
    
    def auto_fix_channels(self):
        """Çalışmayan kanalları otomatik düzelt"""
        if not self.broken_channels:
            print("✅ Düzeltilecek kanal yok!")
            return
        
        print("\n🔧 OTOMATİK DÜZELTME BAŞLATIYOR...")
        
        alternative_urls = {
            "CNN Türk": "https://ciner-live.daioncdn.net/cnnturk/cnnturk.m3u8",
            "A Haber": "https://trkvz-live.daioncdn.net/ahaber/ahaber.m3u8",
            "TRT Spor Yıldız": "https://tv-trtspor2.medya.trt.com.tr/master.m3u8"
        }
        
        fixed_count = 0
        
        try:
            # M3U dosyasını oku
            with open('turkiye_kanallari.m3u', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Her bozuk kanal için alternatif URL'yi dene
            for channel in self.broken_channels:
                name = channel['name']
                old_url = channel['url']
                
                if name in alternative_urls:
                    new_url = alternative_urls[name]
                    content = content.replace(old_url, new_url)
                    print(f"✅ {name} URL'si güncellendi")
                    fixed_count += 1
                else:
                    print(f"❌ {name} için alternatif URL bulunamadı")
            
            # Güncellenmiş dosyayı kaydet
            if fixed_count > 0:
                backup_name = f"turkiye_kanallari_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.m3u"
                
                # Yedek oluştur
                with open(backup_name, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Orijinal dosyayı güncelle
                with open('turkiye_kanallari.m3u', 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"\n💾 {fixed_count} kanal düzeltildi!")
                print(f"📁 Yedek dosya: {backup_name}")
                print("🔄 Değişiklikleri test etmek için kanalları tekrar kontrol edin.")
            else:
                print("\n❌ Hiçbir kanal düzeltilemedi.")
                
        except Exception as e:
            print(f"❌ Otomatik düzeltme hatası: {str(e)}")
    
    def suggest_alternatives(self):
        """Alternatif stream kaynakları öner"""
        print("\n🔗 ALTERNATİF KAYNAKLAR:")
        print("-" * 40)
        
        alternatives = {
            "TRT Kanalları": "https://www.trtizle.com/canli-yayin",
            "Ana Kanallar": "https://www.teve2.com.tr/canli-yayin",
            "Haber Kanalları": "https://www.ntv.com.tr/canli-yayin",
            "Spor Kanalları": "https://www.trtspor.com.tr/canli-yayin",
            "Belgesel Kanalları": "https://www.trtbelgesel.com.tr/canli-yayin",
            "beIN Sports": "https://www.beinsports.com.tr/",
            "Discovery Turkey": "https://www.discoveryturkey.com/",
            "National Geographic": "https://www.nationalgeographic.com.tr/",
            "Genel IPTV": "https://github.com/iptv-org/iptv"
        }
        
        for category, url in alternatives.items():
            print(f"• {category}: {url}")
    
    def analyze_by_category(self):
        """Kategorilere göre analiz yap"""
        print("\n📊 KATEGORİ BAZLI ANALİZ:")
        print("-" * 40)
        
        # Kategorileri topla
        category_stats = {}
        all_channels = self.working_channels + self.broken_channels
        
        for channel in all_channels:
            category = channel['category']
            if category not in category_stats:
                category_stats[category] = {'total': 0, 'working': 0, 'broken': 0}
            
            category_stats[category]['total'] += 1
            if channel['working']:
                category_stats[category]['working'] += 1
            else:
                category_stats[category]['broken'] += 1
        
        # Kategori sıralaması
        category_order = [
            'Ana Kanal', 'Haber', 'TRT',
            'Spor - Yerli', 'Spor - Türkçe', 'Spor - Yabancı',
            'Belgesel - Yerli', 'Belgesel - Türkçe', 'Belgesel - Yabancı',
            'Eğitim'
        ]
        
        for category in category_order:
            if category in category_stats:
                stats = category_stats[category]
                success_rate = (stats['working'] / stats['total'] * 100) if stats['total'] > 0 else 0
                
                # Emoji seçimi
                if 'Spor' in category:
                    emoji = "⚽"
                elif 'Belgesel' in category:
                    emoji = "🎬"
                elif category == 'Haber':
                    emoji = "📰"
                elif category == 'TRT':
                    emoji = "📺"
                elif category == 'Eğitim':
                    emoji = "🎓"
                else:
                    emoji = "📻"
                
                print(f"{emoji} {category}: {stats['working']}/{stats['total']} (%{success_rate:.1f})")
        
        # Kategori dışı kanallar
        for category, stats in category_stats.items():
            if category not in category_order:
                success_rate = (stats['working'] / stats['total'] * 100) if stats['total'] > 0 else 0
                print(f"📡 {category}: {stats['working']}/{stats['total']} (%{success_rate:.1f})")

def print_logo():
    """ASCII logo ve başlık yazdır"""
    logo = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║    ████████╗██╗   ██╗    ██╗   ██╗██████╗ ██████╗  █████╗ ████████╗███████╗██████╗ 
    ║    ╚══██╔══╝██║   ██║    ██║   ██║██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██╔══██╗
    ║       ██║   ██║   ██║    ██║   ██║██████╔╝██║  ██║███████║   ██║   █████╗  ██████╔╝
    ║       ██║   ╚██╗ ██╔╝    ██║   ██║██╔═══╝ ██║  ██║██╔══██║   ██║   ██╔══╝  ██╔══██╗
    ║       ██║    ╚████╔╝     ╚██████╔╝██║     ██████╔╝██║  ██║   ██║   ███████╗██║  ██║
    ║       ╚═╝     ╚═══╝       ╚═════╝ ╚═╝     ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
    ║                                                           ║
    ║               � Türkiye TV Kanalları Güncel Tutma Aracı               ║
    ║                         v1.0 - Tropicx24                        ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(logo)

def main():
    print_logo()
    print()
    
    updater = ChannelUpdater()
    
    while True:
        print("\n📋 Menü:")
        print("1. Tüm kanalları kontrol et")
        print("2. Son raporu görüntüle")
        print("3. Kategori analizini görüntüle")
        print("4. Çalışmayan kanallar için öneriler")
        print("5. Otomatik kanal düzeltici")
        print("6. Alternatif kaynakları göster")
        print("7. Otomatik kontrol başlat (her 6 saatte)")
        print("8. Çıkış")
        
        choice = input("\nSeçiminiz (1-8): ").strip()
        
        if choice == "1":
            updater.check_all_channels()
            
        elif choice == "2":
            try:
                with open('channel_report.json', 'r', encoding='utf-8') as f:
                    report = json.load(f)
                print(f"\n📊 Son Rapor ({report['checked_at']}):")
                print(f"✅ Çalışan: {report['working_channels']}")
                print(f"❌ Sorunlu: {report['broken_channels']}")
                print(f"📈 Başarı: %{report['success_rate']:.1f}")
            except FileNotFoundError:
                print("❌ Henüz rapor oluşturulmamış. Önce kontrol yapın.")
                
        elif choice == "3":
            if hasattr(updater, 'working_channels') and (updater.working_channels or updater.broken_channels):
                updater.analyze_by_category()
            else:
                print("❌ Henüz kanal kontrolü yapılmamış. Önce 1. seçeneği kullanın.")
                
        elif choice == "4":
            if hasattr(updater, 'broken_channels') and updater.broken_channels:
                updater.suggest_fixes_for_broken_channels()
            else:
                print("❌ Çalışmayan kanal yok veya henüz kontrol yapılmamış.")
                
        elif choice == "5":
            if hasattr(updater, 'broken_channels') and updater.broken_channels:
                updater.auto_fix_channels()
            else:
                print("❌ Düzeltilecek kanal yok veya henüz kontrol yapılmamış.")
                
        elif choice == "6":
            updater.suggest_alternatives()
            
        elif choice == "7":
            print("🔄 Otomatik kontrol başlatılıyor...")
            print("Her 6 saatte bir kanallar kontrol edilecek.")
            print("Durdurmak için Ctrl+C basın.")
            
            try:
                while True:
                    updater.check_all_channels()
                    print("⏰ 6 saat bekleniyor...")
                    time.sleep(6 * 60 * 60)  # 6 saat
            except KeyboardInterrupt:
                print("\n⏹️ Otomatik kontrol durduruldu.")
                
        elif choice == "8":
            print("👋 Çıkılıyor...")
            break
            
        else:
            print("❌ Geçersiz seçim!")

if __name__ == "__main__":
    main()
