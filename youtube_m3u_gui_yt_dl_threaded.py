import sys
import os
import logging
import re
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QFileDialog, QHeaderView, QAbstractItemView, QCheckBox
)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from yt_dlp import YoutubeDL

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

DEFAULT_DIR = os.path.join(os.path.expanduser("~"), "you_to")
DEFAULT_TXT = os.path.join(DEFAULT_DIR, "channels.txt")
DEFAULT_M3U = os.path.join(DEFAULT_DIR, "output.m3u")


# ---------- Yardımcı Fonksiyonlar ----------
def extract_youtube_id(url: str) -> str | None:
    """Verilen URL'den YouTube video ID'sini çıkarır."""
    if not url:
        return None

    match = re.search(r'[?&]v=([^&]+)', url)
    if match:
        return match.group(1)

    if 'youtu.be/' in url:
        return url.split('youtu.be/')[-1].split('?')[0]

    if '/live/' in url or '/embed/' in url:
        parts = url.split('/')
        return parts[-1].split('?')[0]

    return None


# ---------- Worker Thread ----------
class YTConvertThread(QThread):
    update_signal = Signal(int, str)
    finished_signal = Signal()
    error_signal = Signal(int, str)

    def __init__(self, rows_to_convert):
        super().__init__()
        self.rows_to_convert = list(rows_to_convert)

    def clean_url(self, url: str) -> str:
        if not url or len(url) < 500:
            return url

        if "googlevideo.com" in url:
            try:
                # URL'yi parçalara ayır
                base_url = url.split('?')[0]
                query_part = url.split('?', 1)[1] if '?' in url else ''
                
                # Temel parametreleri koru
                essential_params = []
                for param in query_part.split('&'):
                    if '=' in param:
                        key = param.split('=')[0]
                        # Sadece gerekli parametreleri koru
                        if key in ['id', 'itag', 'source', 'live', 'requiressl', 'playlist_type']:
                            essential_params.append(param)
                
                # Temizlenmiş URL'yi oluştur
                clean_url = base_url + ('?' + '&'.join(essential_params) if essential_params else '')
                
                # Eğer hala çok uzunsa, daha agresif temizle
                if len(clean_url) > 300:
                    # Sadece en temel parametreleri bırak
                    minimal_params = []
                    for param in query_part.split('&'):
                        if '=' in param:
                            key = param.split('=')[0]
                            if key in ['id', 'itag']:
                                minimal_params.append(param)
                    clean_url = base_url + ('?' + '&'.join(minimal_params) if minimal_params else '')
                
                return clean_url
                
            except Exception as e:
                logging.warning(f"URL temizlenirken hata: {e}")
        
        return url

    def pick_stream_url(self, info: dict, fallback: str) -> str:
        formats = info.get("formats") or []

        # 1. Canlı yayın HLS formatları (m3u8)
        hls_formats = [f for f in formats if f.get("protocol", "").startswith("m3u8") and f.get("url")]
        if hls_formats:
            # En iyi HLS formatını seç
            best_hls = max(hls_formats, key=lambda f: (f.get("height", 0), f.get("tbr", 0)), default=None)
            if best_hls and best_hls.get("url"):
                hls_url = best_hls["url"]
                # Çok uzun URL'leri kısalt
                if len(hls_url) > 800:
                    cleaned = self.clean_url(hls_url)
                    # Hala uzunsa, video ID'si ile basit format oluştur
                    if len(cleaned) > 400:
                        video_id = info.get("id", "")
                        if video_id:
                            return f"https://www.youtube.com/watch?v={video_id}"
                    return cleaned
                return hls_url

        # 2. MP4 formatları
        mp4_formats = [f for f in formats if f.get("ext") == "mp4" and f.get("url") and len(f.get("url", "")) < 500]
        if mp4_formats:
            best_mp4 = max(mp4_formats, key=lambda f: (f.get("height", 0), f.get("tbr", 0)), default=None)
            if best_mp4:
                return best_mp4["url"]

        # 3. Ana URL kontrol
        main_url = info.get("url")
        if main_url and len(main_url) < 500:
            return main_url

        # 4. Requested formats
        for fmt in info.get("requested_formats", []):
            if fmt.get("url") and len(fmt.get("url", "")) < 500:
                return fmt["url"]

        # 5. Herhangi bir kısa format
        for fmt in formats:
            if fmt.get("url") and len(fmt.get("url", "")) < 400:
                return fmt["url"]

        # 6. Son çare: YouTube watch URL'si
        video_id = info.get("id")
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"

        return fallback

    def run(self):
        ydl_opts = {
            "quiet": True,
            "noplaylist": True,
            "skip_download": True,
            "format": "best[protocol^=m3u8]/best[ext=mp4]/best",
            "socket_timeout": 45,
            "retries": 8,
            "fragment_retries": 8,
            "geo_bypass": True,
            "hls_prefer_native": True,
            "nocheckcertificate": True,
            "ignoreerrors": True,
            "no_warnings": True,
            "extract_flat": False,
            "writesubtitles": False,
            "writeautomaticsub": False,
            "prefer_free_formats": False,
            "live_from_start": True,
            "http_headers": {
                "User-Agent": "com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip",
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate",
                "X-YouTube-Client-Name": "3",
                "X-YouTube-Client-Version": "19.09.37"
            },
            "extractor_args": {
                "youtube": {
                    "player_client": ["android_creator", "android_music", "android", "web_creator", "web_music", "web"],
                    "include_hls_manifest": True,
                    "skip": ["dash"],
                    "lang": ["en"],
                    "max_comments": [0],
                    "comment_sort": ["top"],
                    "player_skip": ["configs"],
                    "innertube_host": ["youtubei.googleapis.com"],
                    "innertube_key": ["AIzaSyA8eiZmM1FaDVjRy-df2KTyQ_vz_yYM39w"]
                }
            }
        }

        for row, url in self.rows_to_convert:
            if self.isInterruptionRequested():
                break
            if not url.startswith("http"):
                self.error_signal.emit(row, "Geçersiz URL")
                continue
            
            # URL'nin YouTube olup olmadığını kontrol et
            if not ("youtube.com" in url or "youtu.be" in url):
                self.error_signal.emit(row, "❌ Sadece YouTube desteklenir")
                continue
            
            # Video ID'sini çıkar
            video_id = extract_youtube_id(url)
            if not video_id:
                self.error_signal.emit(row, "❌ Video ID bulunamadı")
                continue
                
            try:
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False) or {}
                    converted = self.pick_stream_url(info, url)
                    if converted != url:  # Dönüşüm başarılı
                        self.update_signal.emit(row, converted)
                    else:
                        # yt-dlp başarısız oldu, alternatif URL'ler dene
                        alternative_url = self.get_alternative_url(video_id)
                        self.update_signal.emit(row, alternative_url)
                        
            except Exception as e:
                error_msg = str(e).lower()
                if "no video formats found" in error_msg or "format" in error_msg:
                    # Alternatif URL kullan
                    alternative_url = self.get_alternative_url(video_id)
                    self.update_signal.emit(row, alternative_url)
                elif "403" in error_msg or "forbidden" in error_msg:
                    self.error_signal.emit(row, "❌ Erişim engellendi")
                elif "404" in error_msg or "not found" in error_msg:
                    self.error_signal.emit(row, "❌ Video bulunamadı")
                elif "ssl" in error_msg or "certificate" in error_msg:
                    self.error_signal.emit(row, "❌ SSL hatası")
                elif "connection" in error_msg or "timeout" in error_msg:
                    self.error_signal.emit(row, "❌ Bağlantı hatası")
                elif "sign in" in error_msg or "login" in error_msg:
                    self.error_signal.emit(row, "❌ Giriş gerekli")
                elif "private" in error_msg or "unavailable" in error_msg:
                    self.error_signal.emit(row, "❌ Özel/Kullanılamaz")
                else:
                    # Son çare olarak alternatif URL
                    alternative_url = self.get_alternative_url(video_id)
                    self.update_signal.emit(row, alternative_url)

        self.finished_signal.emit()
        
    def get_alternative_url(self, video_id):
        """yt-dlp başarısız olduğunda alternatif URL'ler döndürür"""
        alternatives = [
            f"https://www.youtube.com/embed/{video_id}",
            f"https://youtu.be/{video_id}",
            f"https://www.youtube.com/watch?v={video_id}",
            f"https://m.youtube.com/watch?v={video_id}"
        ]
        # İlk alternatifi döndür
        return alternatives[0]


# ---------- Main GUI ----------
class M3UGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("M3U GUI YouTube Dönüştürücü")
        self.categories = ["Radyo", "YouTube", "Kamera", "TV", "Diğer"]
        self._build_ui()
        os.makedirs(DEFAULT_DIR, exist_ok=True)
        if os.path.exists(DEFAULT_TXT):
            self._load_txt(DEFAULT_TXT)
        self.thread: YTConvertThread | None = None

    def _build_ui(self):
        form = QHBoxLayout()
        self.name_in, self.url_in, self.logo_in, self.real_in = [QLineEdit() for _ in range(4)]
        self.name_in.setPlaceholderText("Kanal Adı")
        self.url_in.setPlaceholderText("Kanal Linki")
        self.logo_in.setPlaceholderText("Logo URL (opsiyonel)")
        self.real_in.setPlaceholderText("Gerçek Link (YouTube)")

        self.cat_in = QComboBox(); self.cat_in.setEditable(True); self.cat_in.addItems(self.categories)
        self.cat_in.setCurrentText("YouTube")

        add_btn = QPushButton("Ekle"); add_btn.clicked.connect(self.add_row)
        upd_btn = QPushButton("Seçiliyi Güncelle"); upd_btn.clicked.connect(self.update_selected)
        del_btn = QPushButton("Seçiliyi Sil"); del_btn.clicked.connect(self.delete_selected)

        for lbl, widget, stretch in [
            ("Ad:", self.name_in, 2),
            ("Kategori:", self.cat_in, 1),
            ("Link:", self.url_in, 3),
            ("Logo:", self.logo_in, 2),
            ("Gerçek Link:", self.real_in, 3)
        ]:
            form.addWidget(QLabel(lbl)); form.addWidget(widget, stretch)

        form.addWidget(add_btn); form.addWidget(upd_btn); form.addWidget(del_btn)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Kanal Adı", "Kategori", "Link", "Logo", "Gerçek Link", "Durum"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.handle_double_click)

        settings = QHBoxLayout()
        self.use_simple_urls_cb = QCheckBox("M3U'da Basit YouTube URL'leri Kullan")
        self.use_simple_urls_cb.setChecked(True)
        settings.addWidget(self.use_simple_urls_cb); settings.addStretch()

        bottom = QHBoxLayout()
        for txt, func in [
            ("Dosyadan Yükle", self.load_from_file),
            ("Listeyi Kaydet (.txt)", self.save_list_txt),
            ("Farklı Kaydet", self.save_list_as),
            ("Temizle", self.clear_list),
            ("Benzerleri Sil", self.remove_duplicates),
            ("yt-dlp Güncelle", self.update_ytdlp),
        ]:
            btn = QPushButton(txt); btn.clicked.connect(func); bottom.addWidget(btn)

        self.simple_btn = QPushButton("🔗 Basit URL"); self.simple_btn.clicked.connect(self.convert_to_simple_urls)
        self.convert_btn = QPushButton("🎥 Stream URL"); self.convert_btn.clicked.connect(self.convert_youtube_all)
        self.clean_btn = QPushButton("🧹 YouTube'a Çevir"); self.clean_btn.clicked.connect(self.clean_long_urls)
        export_btn = QPushButton("📁 M3U Oluştur"); export_btn.clicked.connect(self.export_m3u)

        bottom.addStretch(); bottom.addWidget(self.simple_btn); bottom.addWidget(self.convert_btn); bottom.addWidget(self.clean_btn); bottom.addWidget(export_btn)

        root = QVBoxLayout(self)
        root.addLayout(form); root.addWidget(self.table); root.addLayout(settings); root.addLayout(bottom)

    def get_row_data(self, row):
        return tuple(self.table.item(row, col).text().strip() if self.table.item(row, col) else "" for col in range(6))

    def _insert_row(self, name, cat, url, logo, real):
        r = self.table.rowCount(); self.table.insertRow(r)
        for c, v in enumerate((name, cat, url, logo, real)): self.table.setItem(r, c, QTableWidgetItem(v))
        self.table.setItem(r, 5, QTableWidgetItem(""))

    def _clear_inputs(self):
        for w in (self.name_in, self.url_in, self.logo_in, self.real_in): w.clear()

    def add_row(self):
        name, cat, url, logo, real = self.name_in.text().strip(), self.cat_in.currentText().strip() or "Diğer", self.url_in.text().strip(), self.logo_in.text().strip(), self.real_in.text().strip()
        if not name or (not url and not real):
            QMessageBox.warning(self, "Hata", "Kanal adı ve en az bir link girilmeli."); return
        self._insert_row(name, cat, url, logo, real); self._clear_inputs()

    def delete_selected(self):
        rows = sorted({idx.row() for idx in self.table.selectedIndexes()}, reverse=True)
        if not rows: QMessageBox.warning(self, "Hata", "Silmek için bir satır seçin."); return
        for r in rows: self.table.removeRow(r)

    def handle_double_click(self, row, col):
        name, cat, url, logo, real, _ = self.get_row_data(row)
        self.name_in.setText(name); self.cat_in.setCurrentText(cat)
        self.url_in.setText(url); self.logo_in.setText(logo); self.real_in.setText(real)

    def update_selected(self):
        r = self.table.currentRow()
        if r < 0: QMessageBox.warning(self, "Hata", "Güncellemek için satır seçin."); return
        for c, v in enumerate((self.name_in.text().strip() or self.table.item(r, 0).text(),
                               self.cat_in.currentText().strip() or self.table.item(r, 1).text(),
                               self.url_in.text().strip() or self.table.item(r, 2).text(),
                               self.logo_in.text().strip() or self.table.item(r, 3).text(),
                               self.real_in.text().strip() or self.table.item(r, 4).text())):
            self.table.setItem(r, c, QTableWidgetItem(v))
        self.table.setItem(r, 5, QTableWidgetItem("")); self._clear_inputs()

    def clear_list(self): self.table.setRowCount(0)

    def _load_txt(self, path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip() or line.startswith("#"): continue
                parts = [p.strip() for p in line.split("|")]
                while len(parts) < 5: parts.append("")
                self._insert_row(*parts[:5])

    def _load_m3u(self, path):
        ext_re = re.compile(r'#EXTINF:-1.*?group-title="([^"]*)".*?tvg-logo="([^"]*)".*?,(.*)$')
        with open(path, encoding="utf-8", errors="ignore") as f:
            name, cat, logo = "", "Diğer", ""
            for l in f:
                l = l.strip()
                if l.startswith("#EXTINF"):
                    m = ext_re.match(l)
                    if m: cat, logo, name = m.groups()
                elif l and not l.startswith("#"):
                    self._insert_row(name, cat, l, logo, "")

    def load_from_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Yükle", DEFAULT_DIR, "Metin/M3U (*.txt *.m3u)")
        if not path: return
        try:
            self._load_m3u(path) if path.lower().endswith(".m3u") else self._load_txt(path)
            QMessageBox.information(self, "Tamam", f"Dosya yüklendi: {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Dosya okunamadı:\n{e}")

    def _save_list(self, path, m3u=False):
        lines = []
        if m3u:
            lines.append("#EXTM3U")
            use_simple = self.use_simple_urls_cb.isChecked()
            for r in range(self.table.rowCount()):
                name, cat, url, logo, real, _ = self.get_row_data(r)

                # Gerçek stream linkini kullan
                if use_simple:
                    # Eğer dönüştürülmüş stream URL'si varsa onu kullan
                    url_use = url if "googlevideo.com" in url or url.endswith(".m3u8") else real
                else:
                    url_use = real if real.startswith("http") else url

                logo_str = f' tvg-logo="{logo}"' if logo else ""
                lines.append(f'#EXTINF:-1 group-title="{cat}"{logo_str},{name}')
                lines.append(url_use)
        else:
            for r in range(self.table.rowCount()):
                name, cat, url, logo, real, _ = self.get_row_data(r)
                lines.append("|".join((name, cat, url, logo, real)))
        with open(path, "w", encoding="utf-8") as f: f.write("\n".join(lines))

    def save_list_txt(self):
        path, _ = QFileDialog.getSaveFileName(self, "Kaydet (.txt)", DEFAULT_DIR, "Metin (*.txt)")
        if path: self._save_list(path, m3u=False)

    def save_list_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Kaydet", DEFAULT_DIR, "TXT (*.txt);;M3U (*.m3u)")
        if path: self._save_list(path, m3u=path.lower().endswith(".m3u"))

    def export_m3u(self):
        path, _ = QFileDialog.getSaveFileName(self, "M3U Oluştur", DEFAULT_DIR, "M3U (*.m3u)")
        if path: self._save_list(path, m3u=True)

    def remove_duplicates(self):
        seen, removed = set(), 0
        for row in reversed(range(self.table.rowCount())):
            real = self.table.item(row, 4).text().strip() if self.table.item(row, 4) else ""
            orig = self.table.item(row, 2).text().strip() if self.table.item(row, 2) else ""
            key = real if real.startswith("http") else orig
            if key:
                if key in seen: self.table.removeRow(row); removed += 1
                else: seen.add(key)
        QMessageBox.information(self, "Tamam", f"{removed} adet tekrar eden bağlantı silindi.")

    def convert_to_simple_urls(self):
        converted = 0
        for r in range(self.table.rowCount()):
            url = self.table.item(r, 4).text().strip() or self.table.item(r, 2).text().strip()
            if not url:
                continue
                
            # Sadece YouTube URL'lerini işle
            if not ("youtube.com" in url or "youtu.be" in url):
                self.table.setItem(r, 5, QTableWidgetItem("⚠️ YouTube değil"))
                continue
                
            video_id = extract_youtube_id(url)
            if video_id:
                simple_url = f"https://www.youtube.com/watch?v={video_id}"
                self.table.setItem(r, 2, QTableWidgetItem(simple_url))
                if not self.table.item(r, 4) or not self.table.item(r, 4).text().startswith("http"):
                    self.table.setItem(r, 4, QTableWidgetItem(simple_url))
                self.table.setItem(r, 5, QTableWidgetItem("📺 Basitleştirildi"))
                converted += 1
            else:
                self.table.setItem(r, 5, QTableWidgetItem("❌ Geçersiz YouTube URL"))
                
        QMessageBox.information(self, "Tamam", f"{converted} adet URL basitleştirildi.")

    def clean_long_urls(self):
        """Uzun googlevideo URL'lerini temizler"""
        cleaned = 0
        for r in range(self.table.rowCount()):
            url = self.table.item(r, 2).text().strip() if self.table.item(r, 2) else ""
            
            if "googlevideo.com" in url and len(url) > 200:
                try:
                    # Video ID'sini URL'den çıkar
                    video_id = None
                    itag = None
                    
                    # Query parametrelerinden video ID ve itag bul
                    if '?' in url:
                        query_part = url.split('?', 1)[1]
                        for param in query_part.split('&'):
                            if '=' in param:
                                key, value = param.split('=', 1)
                                if key == 'id':
                                    video_id = value.split('.')[0]  # .7 gibi ekleri temizle
                                elif key == 'itag':
                                    itag = value
                    
                    if video_id:
                        # YouTube'un basit HLS URL formatını kullan
                        if itag:
                            clean_url = f"https://www.youtube.com/watch?v={video_id}"
                        else:
                            clean_url = f"https://www.youtube.com/watch?v={video_id}"
                            
                        # Alternatif olarak direkt HLS manifest
                        # clean_url = f"https://manifest.googlevideo.com/api/manifest/hls_playlist/id/{video_id}.m3u8"
                        
                        self.table.setItem(r, 2, QTableWidgetItem(clean_url))
                        self.table.setItem(r, 5, QTableWidgetItem("🧹 YouTube URL'ye çevrildi"))
                        cleaned += 1
                    else:
                        self.table.setItem(r, 5, QTableWidgetItem("❌ Video ID bulunamadı"))
                        
                except Exception as e:
                    self.table.setItem(r, 5, QTableWidgetItem("❌ Temizlenemedi"))
                    
        if cleaned > 0:
            QMessageBox.information(self, "Tamam", f"{cleaned} adet URL YouTube linkine çevrildi.\nArtık '🎥 Stream URL' butonuna basarak yeni stream linklerini alabilirsiniz.")
        else:
            QMessageBox.information(self, "Bilgi", "Temizlenecek uzun googlevideo URL'si bulunamadı.")

    def update_ytdlp(self):
        """yt-dlp'yi günceller"""
        try:
            import subprocess
            import sys
            
            # yt-dlp'yi güncelle
            result = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"], 
                                  capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                QMessageBox.information(self, "Başarılı", "yt-dlp başarıyla güncellendi!\nProgram yeniden başlatılması önerilir.")
            else:
                QMessageBox.warning(self, "Hata", f"Güncelleme başarısız:\n{result.stderr}")
                
        except subprocess.TimeoutExpired:
            QMessageBox.warning(self, "Hata", "Güncelleme zaman aşımına uğradı.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Güncelleme hatası:\n{str(e)}")

    def convert_youtube_all(self):
        # Sadece YouTube URL'lerini seç
        rows = []
        for r in range(self.table.rowCount()):
            url = self.table.item(r, 2).text().strip() if self.table.item(r, 2) else ""
            if url and ("youtube.com" in url or "youtu.be" in url):
                rows.append((r, url))
                
        if not rows:
            QMessageBox.warning(self, "Hata", "Dönüştürülecek YouTube bağlantısı bulunamadı.")
            return
            
        # YouTube olmayan satırları işaretle
        for r in range(self.table.rowCount()):
            url = self.table.item(r, 2).text().strip() if self.table.item(r, 2) else ""
            if url and not ("youtube.com" in url or "youtu.be" in url):
                self.table.setItem(r, 5, QTableWidgetItem("⚠️ YouTube değil"))
                
        self.thread = YTConvertThread(rows)
        self.thread.update_signal.connect(self._update_row_url)
        self.thread.error_signal.connect(self._update_row_error)
        self.thread.finished_signal.connect(lambda: QMessageBox.information(self, "Tamam", f"{len(rows)} YouTube bağlantısı işlendi."))
        self.thread.start()

    @Slot(int, str)
    def _update_row_url(self, row, url):
        self.table.setItem(row, 2, QTableWidgetItem(url))
        if "embed" in url:
            self.table.setItem(row, 5, QTableWidgetItem("🔄 Embed URL"))
        elif "googlevideo.com" in url:
            self.table.setItem(row, 5, QTableWidgetItem("✅ Stream URL"))
        else:
            self.table.setItem(row, 5, QTableWidgetItem("✅ Alternatif URL"))

    @Slot(int, str)
    def _update_row_error(self, row, msg):
        self.table.setItem(row, 5, QTableWidgetItem(msg))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = M3UGUI()
    window.resize(1000, 600)
    window.show()
    sys.exit(app.exec())
