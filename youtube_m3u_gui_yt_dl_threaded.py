# youtube_m3u_gui_yt_dl_threaded_m3u.py
import sys, os, requests
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QFileDialog, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap
from yt_dlp import YoutubeDL

DEFAULT_DIR = r"C:\Users\ersan\OneDrive\Masaüstü\you_to"
DEFAULT_TXT = os.path.join(DEFAULT_DIR, "channels.txt")
DEFAULT_M3U = os.path.join(DEFAULT_DIR, "output.m3u")

# ---------- Worker Thread ----------
class YTConvertThread(QThread):
    update_signal = Signal(int, str)  # row, converted URL

    def __init__(self, table):
        super().__init__()
        self.table = table

    def run(self):
        ydl_opts = {'format':'best[ext=mp4]/best', 'quiet':True, 'noplaylist':True}
        with YoutubeDL(ydl_opts) as ydl:
            for r in range(self.table.rowCount()):
                url_item = self.table.item(r,2)
                real_item = self.table.item(r,4)
                if url_item and "youtu" in url_item.text() and (not real_item or not real_item.text()):
                    url = url_item.text().strip()
                    try:
                        info = ydl.extract_info(url, download=False)
                        direct_url = info.get('url', url)
                    except:
                        direct_url = url
                    self.update_signal.emit(r, direct_url)

# ---------- Main GUI ----------
class M3UGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.categories = ["Radyo", "YouTube", "Kamera", "TV", "Diğer"]
        # --- Form Üst ---
        form = QHBoxLayout()
        self.name_in = QLineEdit(); self.name_in.setPlaceholderText("Kanal Adı")
        self.url_in  = QLineEdit(); self.url_in.setPlaceholderText("Kanal Linki")
        self.logo_in = QLineEdit(); self.logo_in.setPlaceholderText("Logo URL (opsiyonel)")
        self.cat_in  = QComboBox(); self.cat_in.setEditable(True)
        self.cat_in.addItems(self.categories)
        self.cat_in.setCurrentText("YouTube")

        add_btn = QPushButton("Ekle"); add_btn.clicked.connect(self.add_row)
        upd_btn = QPushButton("Düzenle"); upd_btn.clicked.connect(self.update_selected)
        del_btn = QPushButton("Seçiliyi Sil"); del_btn.clicked.connect(self.delete_selected)

        form.addWidget(QLabel("Ad:")); form.addWidget(self.name_in, 2)
        form.addWidget(QLabel("Kategori:")); form.addWidget(self.cat_in, 1)
        form.addWidget(QLabel("Link:")); form.addWidget(self.url_in, 3)
        form.addWidget(QLabel("Logo:")); form.addWidget(self.logo_in, 2)
        form.addWidget(add_btn); form.addWidget(upd_btn); form.addWidget(del_btn)

        # --- Tablo ---
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Kanal Adı", "Kategori", "Link", "Logo", "Gerçek Link"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.handle_double_click)

        # --- Alt Butonlar ---
        bottom = QHBoxLayout()
        load_btn = QPushButton("Dosyadan Yükle"); load_btn.clicked.connect(self.load_from_file)
        save_list_btn = QPushButton("Listeyi Kaydet (.txt)"); save_list_btn.clicked.connect(self.save_list_txt)
        save_as_btn = QPushButton("Listeyi Farklı Kaydet"); save_as_btn.clicked.connect(self.save_list_as)
        clear_btn = QPushButton("Listeyi Temizle"); clear_btn.clicked.connect(self.clear_list)
        export_btn = QPushButton("M3U Oluştur (.m3u)"); export_btn.clicked.connect(self.export_m3u)
        convert_btn = QPushButton("YouTube Linklerini Dönüştür"); convert_btn.clicked.connect(self.convert_youtube_all)
        append_btn = QPushButton("Mevcut M3U'ya Ekle"); append_btn.clicked.connect(self.append_to_existing_m3u)

        bottom.addWidget(load_btn)
        bottom.addWidget(save_list_btn)
        bottom.addWidget(save_as_btn)
        bottom.addWidget(clear_btn)
        bottom.addStretch(1)
        bottom.addWidget(convert_btn)
        bottom.addWidget(export_btn)
        bottom.addWidget(append_btn)

        # --- Ana Yerleşim ---
        root = QVBoxLayout(self)
        root.addLayout(form)
        root.addWidget(self.table)
        root.addLayout(bottom)

        os.makedirs(DEFAULT_DIR, exist_ok=True)
        if os.path.exists(DEFAULT_TXT):
            self.load_txt(DEFAULT_TXT)

    # ---------- Yardımcı Fonksiyonlar ----------
    def add_row_to_table(self, name, category, url, logo, real_link=""):
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setItem(r, 0, QTableWidgetItem(name))
        self.table.setItem(r, 1, QTableWidgetItem(category))
        self.table.setItem(r, 2, QTableWidgetItem(url))

        # Logo için QLabel kullanımı
        if logo:
            label = QLabel()
            pixmap = QPixmap()
            try:
                pixmap.loadFromData(requests.get(logo).content)  # URL'den görseli indir
                label.setPixmap(pixmap.scaled(50, 50, Qt.KeepAspectRatio))  # Görseli ölçekle
            except Exception as e:
                label.setText("Hata")  # Görsel yüklenemezse hata mesajı göster
            self.table.setCellWidget(r, 3, label)
        else:
            self.table.setItem(r, 3, QTableWidgetItem(""))

        self.table.setItem(r, 4, QTableWidgetItem(real_link))

    def get_row_data(self, r):
        def g(c): 
            it = self.table.item(r, c)
            return it.text().strip() if it else ""
        return g(0), g(1), g(2), g(3), g(4)

    def clear_inputs(self):
        self.name_in.clear(); self.url_in.clear(); self.logo_in.clear()

    # ---------- Ekle / Düzenle / Sil ----------
    def add_row(self):
        name = self.name_in.text().strip()
        category = self.cat_in.currentText().strip() or "Diğer"
        url = self.url_in.text().strip()
        logo = self.logo_in.text().strip()
        if not name or not url:
            QMessageBox.warning(self, "Hata", "Kanal adı ve link boş olamaz!")
            return
        self.add_row_to_table(name, category, url, logo)
        self.clear_inputs()

    def update_selected(self):
        r = self.table.currentRow()
        if r < 0:
            QMessageBox.warning(self, "Hata", "Düzenlenecek satırı seçin.")
            return
        name = self.name_in.text().strip() or self.table.item(r,0).text()
        category = self.cat_in.currentText().strip() or self.table.item(r,1).text()
        url = self.url_in.text().strip() or self.table.item(r,2).text()
        logo = self.logo_in.text().strip() or self.table.item(r,3).text()
        self.table.setItem(r, 0, QTableWidgetItem(name))
        self.table.setItem(r, 1, QTableWidgetItem(category))
        self.table.setItem(r, 2, QTableWidgetItem(url))
        self.table.setItem(r, 3, QTableWidgetItem(logo))
        self.clear_inputs()

    def delete_selected(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        if not rows:
            QMessageBox.warning(self, "Hata", "Silmek için bir satır seçin.")
            return
        for r in rows:
            self.table.removeRow(r)

    # ---------- Çift tıkla kategori değiştirme ----------
    def handle_double_click(self, row, col):
        if col != 1:
            name, cat, url, logo, rl = self.get_row_data(row)
            self.name_in.setText(name); self.cat_in.setCurrentText(cat)
            self.url_in.setText(url);   self.logo_in.setText(logo)
            return
        combo = QComboBox(self.table)
        existing = set(self.categories)
        current_text = (self.table.item(row, col).text() if self.table.item(row, col) else "").strip()
        combo.setEditable(True)
        combo.addItems(self.categories)
        if current_text and current_text not in existing:
            combo.addItem(current_text)
        combo.setCurrentText(current_text or "Diğer")
        combo.activated.connect(lambda *_: self.apply_inline_category(row, col, combo))
        self.table.setCellWidget(row, col, combo)
        combo.showPopup()

    def apply_inline_category(self, row, col, combo):
        val = combo.currentText().strip() or "Diğer"
        self.table.removeCellWidget(row, col)
        self.table.setItem(row, col, QTableWidgetItem(val))
        if val not in self.categories:
            self.categories.append(val)
            self.cat_in.addItem(val)

    # ---------- Dosyadan yükleme ----------
    def load_from_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Liste Yükle", DEFAULT_DIR,
                                              "Metin/M3U (*.txt *.m3u);;Tüm Dosyalar (*)")
        if not path:
            return
        if path.lower().endswith(".m3u"):
            self.load_m3u(path)
        else:
            self.load_txt(path)

    def load_txt(self, path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line=line.strip()
                if not line or line.startswith("#"): 
                    continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 3:
                    name, category, url = parts[:3]
                    logo = parts[3] if len(parts) >= 4 else ""
                    self.add_row_to_table(name, category or "Diğer", url, logo)
        QMessageBox.information(self, "Bilgi", f"Yüklendi: {os.path.basename(path)}")

    def load_m3u(self, path):
        import re
        ext_re = re.compile(r'#EXTINF:-1.*?(?:group-title="(?P<grp>[^"]*)")?.*?(?:tvg-logo="(?P<logo>[^"]*)")?.*?,(?P<name>.*)$')
        pending = None
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                s = line.strip()
                if not s:
                    continue
                if s.startswith("#EXTINF"):
                    m = ext_re.match(s)
                    if m:
                        pending = {
                            "name": m.group("name") or "Kanal",
                            "cat": (m.group("grp") or "Diğer").strip(),
                            "logo": (m.group("logo") or "").strip()
                        }
                elif not s.startswith("#") and pending:
                    self.add_row_to_table(pending["name"], pending["cat"], s, pending["logo"])
                    pending = None
        QMessageBox.information(self, "Bilgi", f"M3U Yüklendi: {os.path.basename(path)}")

    # ---------- Kaydetme ----------
    def _save_list(self, path, as_m3u=False):
        lines = []
        if as_m3u:
            lines.append("#EXTM3U")
            for r in range(self.table.rowCount()):
                name, cat, url, logo, real = self.get_row_data(r)
                url_use = real if "youtu" in url and real else url
                logo_str = f' tvg-logo="{logo}"' if logo else ""
                lines.append(f'#EXTINF:-1 group-title="{cat}"{logo_str},{name}')
                lines.append(url_use)
        else:
            for r in range(self.table.rowCount()):
                name, cat, url, logo, real = self.get_row_data(r)
                lines.append(f"{name}|{cat}|{url}|{logo}")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        QMessageBox.information(self, "Tamam", f"Liste kaydedildi:\n{path}")

    def save_list_txt(self):
        path, _ = QFileDialog.getSaveFileName(self, "Listeyi Kaydet (.txt)", DEFAULT_DIR,
                                              "Metin (*.txt)")
        if path:
            self._save_list(path, as_m3u=False)

    def save_list_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Listeyi Farklı Kaydet (.txt/.m3u)", DEFAULT_DIR,
                                              "Metin (*.txt);;M3U (*.m3u)")
        if path:
            as_m3u = path.lower().endswith(".m3u")
            self._save_list(path, as_m3u)

    def export_m3u(self):
        path, _ = QFileDialog.getSaveFileName(self, "M3U Kaydet", DEFAULT_DIR,
                                              "M3U (*.m3u)")
        if path:
            self._save_list(path, as_m3u=True)

    def clear_list(self):
        self.table.setRowCount(0)

    # ---------- YouTube Dönüştürme ----------
    def convert_youtube_all(self):
        self.thread = YTConvertThread(self.table)
        self.thread.update_signal.connect(self.update_real_link)
        self.thread.start()

    def update_real_link(self, row, url):
        self.table.setItem(row, 4, QTableWidgetItem(url))

    # ---------- Mevcut M3U'ya Ekleme ----------
    def append_to_existing_m3u(self):
        # Seçili satır(lar)ı mevcut bir M3U dosyasının sonuna ekle
        selected_rows = sorted({i.row() for i in self.table.selectedIndexes()})
        if not selected_rows:
            QMessageBox.warning(self, "Hata", "Eklemek için en az bir satır seçin.")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Mevcut M3U Dosyasını Seç", DEFAULT_DIR, "M3U (*.m3u)")
        if not path:
            return
        try:
            with open(path, "a", encoding="utf-8") as f:
                for r in selected_rows:
                    name, cat, url, logo, real = self.get_row_data(r)
                    url_use = real if "youtu" in url and real else url
                    logo_str = f' tvg-logo="{logo}"' if logo else ""
                    f.write(f'\n#EXTINF:-1 group-title="{cat}"{logo_str},{name}\n{url_use}')
            QMessageBox.information(self, "Başarılı", f"Seçili kanallar mevcut M3U dosyasına eklendi:\n{os.path.basename(path)}")
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Dosyaya eklenemedi:\n{e}")

# ---------- Program Başlat ----------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = M3UGUI()
    window.show()
    sys.exit(app.exec())
