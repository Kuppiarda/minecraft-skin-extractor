# Copyright (C) 2026 Kuppiarda
# This file is part of Minecraft Skin Extractor.
# Licensed under the GNU GPL v3.0.

import json
import base64
import shutil
from pathlib import Path
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWidgets import QApplication, QCheckBox, QMainWindow, QSlider, QWidget, QHBoxLayout, QFrame, QLabel, QLineEdit, QVBoxLayout, QFileDialog, QPushButton, QColorDialog, QListWidget, QListWidgetItem
from PySide6.QtCore import Qt, QUrl, QSize
from PySide6.QtGui import QFontMetrics, QPixmap, QImage, QIcon
from PIL import Image


def main():

    # Uygulamanın oluşturulması
    app = QApplication()

    # Genel pencere ayarları
    window = QMainWindow()
    window.setWindowTitle("Minecraft Skin Extractor")
    window.resize(1000, 600)

    # Ana widget/layout oluşturulma kısmı
    central = QWidget()
    window.setCentralWidget(central)

    layout = QHBoxLayout(central)
    layout.setContentsMargins(15, 15, 15, 15)
    layout.setSpacing(15)    

    # Gallery ve Skin gösterici bölümlerinin oluşturulması
    viewer, web_view = show_viewer()

    layout.addWidget(show_gallery(web_view)) # fix genişlik olacak
    layout.addWidget(viewer, 1) # bu da kendini genişletecek

    # Uygulama-pencerenin gösterilmesi  
    window.show()
    app.exec()


def show_gallery(web_view):
    gallery = QFrame()
    gallery.setObjectName("gallery")
    gallery.setStyleSheet(
        """
        QPushButton {
            background-color: #222;
        }
        QPushButton:hover {
            background-color: #333;
        }
        QPushButton:pressed {
            background-color: #444;
        }
        QLineEdit {
            background-color: #222;
        }
        QLineEdit:hover {
            background-color: #333;
        }
        #gallery {
            background-color: #222;
            border-radius: 8px;
        }
        QListWidget {
            background-color: #222;
            border: none;
            outline: none;
        }
        QListWidget::item {
            background-color: #333;
            border: 2px solid transparent;
            border-radius: 8px;
            padding: 4px;
        }
        QListWidget::item:hover {
            background-color: #444;
        }
        QListWidget::item:selected {
            color: #4da3ff;
            background-color: #333;
            border: 2px solid #4da3ff;
        }
        """
    )
    gallery.setFixedWidth(500)

    gallery_layout = QVBoxLayout(gallery)

    # Title kısmı
    title_layout = QHBoxLayout()

    gallery_title = QLabel("Skins")
    skin_count_label = QLabel("0 files")

    title_layout.addWidget(gallery_title)
    title_layout.addStretch() # Arada boşluk olsun, sağ tarafta olsun diye sayı dosya şeyi
    title_layout.addWidget(skin_count_label)

    gallery_layout.addLayout(title_layout)

    # Skin listesi
    skin_list = QListWidget()
    skin_list.setViewMode(QListWidget.ViewMode.IconMode)
    skin_list.setFlow(QListWidget.Flow.LeftToRight)
    skin_list.setWrapping(True)
    skin_list.setResizeMode(QListWidget.ResizeMode.Adjust)
    skin_list.setMovement(QListWidget.Movement.Static) # Yer dğeiştirilmesin
    skin_list.setIconSize(QSize(94, 94))
    skin_list.setGridSize(QSize(116, 130))
    skin_list.setSpacing(0)
    skin_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection) # Çoklu seçim

    gallery_layout.addWidget(skin_list)

    # Seçilenleri indirme
    download_button = QPushButton("Download selected (0)")

    def update_selection_count():
        count = len(skin_list.selectedItems())
        download_button.setText(f"Download selected ({count})")

    skin_list.itemSelectionChanged.connect(update_selection_count)

    # Skine tıklayınca viewerda gösterme kısmı
    def on_skin_clicked(item):
        skin_path = Path(item.data(Qt.ItemDataRole.UserRole))
        web_view.setProperty("selectedSkinPath", str(skin_path)) # Seçili skini web veiwda saklıyoruz daha sonra indirmek için

        skin_data = ("data:image/png;base64," + base64.b64encode(skin_path.read_bytes()).decode("ascii"))
        web_view.page().runJavaScript(f"changeSkin({json.dumps(skin_data)})") # Skini viewera yolluyoruz

    skin_list.currentItemChanged.connect(
        lambda current, previous: on_skin_clicked(current)
        if current else None
    )

    # Renk/isim filtresi işleri
    target_color = None
    color_cache = {}

    # Arama
    search_input = QLineEdit()
    search_input.setPlaceholderText("Search skins by filename...")
    gallery_layout.addWidget(search_input)

    # Renk seçme
    color_layout = QHBoxLayout()

    color_button = QPushButton("Filter by color")
    color_filter_checkbox = QCheckBox("Use color filter")

    color_layout.addWidget(color_button, 1)
    color_layout.addWidget(color_filter_checkbox, 0, Qt.AlignmentFlag.AlignRight) # Sağa dayalı checkbox

    gallery_layout.addLayout(color_layout)

    # Threshold
    threshold_label = QLabel("Threshold: 50")

    threshold_slider = QSlider(Qt.Orientation.Horizontal)
    threshold_slider.setRange(0, 440)
    threshold_slider.setSingleStep(5)
    threshold_slider.setValue(50)

    threshold_layout = QHBoxLayout()
    threshold_layout.addWidget(threshold_label)
    threshold_layout.addWidget(threshold_slider)

    gallery_layout.addLayout(threshold_layout)

    # Filtreleme
    def apply_filters():
        filter_skins(
            skin_list,
            search_input.text(),
            target_color=(
                target_color
                if color_filter_checkbox.isChecked()
                else None
            ),
            threshold=threshold_slider.value(),
            color_cache=color_cache
        )

        visible_count = sum(
            not skin_list.item(i).isHidden()
            for i in range(skin_list.count())
        )        

        total_count = skin_list.count()

        skin_count_label.setText(
            f"{visible_count}/{total_count} files"
        )

    search_input.textChanged.connect(lambda _: apply_filters())
    color_filter_checkbox.toggled.connect(lambda _: apply_filters()) # Filtreleri uygulama tek bölgede daha düzenli oldu

    def on_threshold_changed(value):
        threshold_label.setText(f"Threshold: {value}")
        apply_filters()

    threshold_slider.valueChanged.connect(on_threshold_changed)

    def select_color(): # Renk seçici
        nonlocal target_color # Bu da kara büyü

        color = QColorDialog.getColor()

        if color.isValid():
            target_color = (color.red(), color.green(), color.blue())
            apply_filters()

    color_button.clicked.connect(select_color)

    # Kaynak klasörü  seçimi
    folder_button = QPushButton("Select skin source folder")
    folder_button.clicked.connect(
        lambda: reload_gallery(
            select_folder(),
            skin_list,
            skin_count_label,
            color_cache,
            apply_filters
        )
    )

    gallery_layout.addWidget(folder_button)

    # İndirme
    download_button.clicked.connect(
        lambda: download_skin([
            item.data(Qt.ItemDataRole.UserRole)
            for item in skin_list.selectedItems()
        ])
    )

    gallery_layout.addWidget(download_button)

    # İlk yükleme
    reload_gallery(None, skin_list, skin_count_label, color_cache, apply_filters)

    return gallery

def show_viewer():
    viewer = QFrame()
    viewer.setObjectName("viewer")
    viewer.setStyleSheet(
        """
        QPushButton {
            background-color: #222;
        }
        QPushButton:hover {
            background-color: #333;
        }
        QPushButton:pressed {
            background-color: #444;
        }
        #viewer {
            background-color: #252525;
            border-radius: 8px;
        }
        """
    )

    viewer_layout = QVBoxLayout(viewer)

    # Htmlden gösterilecek çünkü skinview3d
    web_view = QWebEngineView()
    web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)    

    html_path = Path(__file__).parent / "viewer" /"viewer.html"
    web_view.load(QUrl.fromLocalFile(str(html_path)))

    viewer_layout.addWidget(web_view)

    # Buton kısmı

    auto_rotate = True
    walking = False

    download_current_button = QPushButton("Download skin")
    auto_rotate_button = QPushButton("Auto rotate: on")
    walking_button = QPushButton("Walking: off")
    viewer_layout.addWidget(download_current_button)
    viewer_layout.addWidget(auto_rotate_button)
    viewer_layout.addWidget(walking_button)

    def toggle_auto_rotate():
        nonlocal auto_rotate

        auto_rotate = not auto_rotate

        web_view.page().runJavaScript(
            f"toggleAutoRotate({str(auto_rotate).lower()})"
        )

        status = "on" if auto_rotate else "off"
        auto_rotate_button.setText(f"Auto rotate: {status}")

    auto_rotate_button.clicked.connect(toggle_auto_rotate)

    def toggle_walking():
        nonlocal walking

        walking = not walking

        web_view.page().runJavaScript(
            f"toggleWalking({str(walking).lower()})"
        )

        status = "on" if walking else "off"
        walking_button.setText(f"Walking: {status}")

    walking_button.clicked.connect(toggle_walking)

    download_current_button.clicked.connect(
        lambda: download_skin([
            web_view.property("selectedSkinPath")
        ])
    )

    return viewer, web_view

def filter_skins(skin_list, search_text, target_color=None, threshold=0, color_cache=None):
    search_text = search_text.casefold() # Büyük küçük önemsiz kalsın

    if color_cache is None: # İlk filtrelemede renklere cache olsun
        color_cache = {}

    for index in range(skin_list.count()):

        # Tanımlamalar
        item = skin_list.item(index)
        skin_path = Path(item.data(Qt.ItemDataRole.UserRole))

        # İsim filtrelemesi
        name_match = search_text in skin_path.name.casefold()

        # Renk filtresi kısmı

        color_match = True
        if target_color is not None:
            _skin_path = str(skin_path)

            if _skin_path not in color_cache:
                color_cache[_skin_path] = get_average_color(skin_path)

            average_color = color_cache[_skin_path]

            distance = sum(
                (average_color[i] - target_color[i]) ** 2
                for i in range(3)
            ) ** 0.5 # 3d uzaydaki yakınlığı, öklid

            color_match = distance <= threshold

        item.setHidden(not (name_match and color_match)) # isim ve renk eşleşmesi birlikte yoksa gizle

def make_thumbnail(skin_path):
    try:
        image = Image.open(skin_path).convert("RGBA")
        image.thumbnail((96, 96), Image.Resampling.NEAREST) # 96x96 thumbnail oluşturuyor, büyütme yapmıyor

        canvas = Image.new("RGBA", (112, 112), (0, 0, 0, 0))

        x = (112 - image.width) // 2 # Tam ortası
        y = (112 - image.height) // 2 # ^

        canvas.alpha_composite(image, (x, y))

        image_data = canvas.tobytes("raw", "RGBA")
        qimage = QImage(image_data, 112, 112, QImage.Format.Format_RGBA8888).copy()

        return QPixmap.fromImage(qimage)

    except Exception:
        return None

def display_skins(skin_list, skin_directory=None):
    skin_list.clear()

    skin_paths = load_skin_paths(skin_directory)

    font_metrics = QFontMetrics(skin_list.font())

    for skin_path in skin_paths:
        thumbnail = make_thumbnail(skin_path) # Hızlı olması için thumbnail, gerçek fotonun kendisi değil

        if thumbnail is None:
            continue

        text = font_metrics.elidedText(skin_path.name, Qt.TextElideMode.ElideRight, 80) # x pikselden fazlaysa kırp
        item = QListWidgetItem(QIcon(thumbnail), text)

        item.setData(Qt.ItemDataRole.UserRole, str(skin_path))
        item.setToolTip(str(skin_path)) # Fareyle gelince full path görünmesi için

        skin_list.addItem(item) # Fonksiyon dışına ekleniyor

    return skin_list.count()

def select_folder():
    return QFileDialog.getExistingDirectory(None, "Choose skin source/assets folder")    

def reload_gallery(folder, skin_list, skin_count_label, color_cache, apply_filters):
    if folder is None:
        count = display_skins(skin_list)
    else:
        if not folder:
            return

        count = display_skins(skin_list, folder)

    color_cache.clear()
    skin_count_label.setText(f"{count}/{count} files")

    apply_filters()

def download_skin(skin_paths):
    if not skin_paths:
        return

    destination = QFileDialog.getExistingDirectory(None, "Select download folder")

    if not destination:
        return

    for skin_path in skin_paths:
        shutil.copy2(skin_path, destination)

def load_skin_paths(skin_directory=None):
    if skin_directory is None:
        skin_directory = (Path.home() / "AppData" / "Roaming" / ".minecraft" / "assets" / "skins")
    else:
        skin_directory = Path(skin_directory)

    skin_paths = []

    for file_path in skin_directory.rglob("*"):
        if file_path.is_file():
            skin_paths.append(file_path)

    return skin_paths

#########################################

def get_average_color(skin_path):
    image = Image.open(skin_path).convert("RGBA")
    pixels = list(image.getdata())

    visible_pixels = [
        (r, g, b)
        for r, g, b, a in pixels
        if a > 0 # Sadece görünürler olcak diğerleri dahil değil
    ]

    if not visible_pixels:
        return (0, 0, 0)

    count = len(visible_pixels)

    average = tuple(
        sum(pixel[channel] for pixel in visible_pixels) // count
        for channel in range(3)
    )

    return average






if __name__ == "__main__":
    main()