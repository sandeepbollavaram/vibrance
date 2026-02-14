import sys
import os
import cv2
import numpy as np
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QListWidget,
    QTextEdit, QSlider, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage, QPainter


# ================= ZOOMABLE VIEW =================

from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QPainter


class ZoomableImageView(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)

        # Better rendering quality
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

    def set_image(self, pixmap):
        self.pixmap_item.setPixmap(pixmap)

        # FIX: convert QRect → QRectF
        rect = QRectF(pixmap.rect())
        self.setSceneRect(rect)

        self.resetTransform()

    def wheelEvent(self, event):
        zoom_factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        self.scale(zoom_factor, zoom_factor)


# ================= SPLIT COMPARISON VIEW =================

class SplitCompareWidget(QWidget):
    def __init__(self, before_pixmap, after_pixmap):
        super().__init__()
        self.before = before_pixmap
        self.after = after_pixmap
        self.slider_pos = 0.5
        self.setMinimumSize(1000, 600)

    def paintEvent(self, event):
        painter = QPainter(self)

        w = self.width()
        h = self.height()

        before_scaled = self.before.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        after_scaled = self.after.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        split_x = int(w * self.slider_pos)

        painter.drawPixmap(0, 0, after_scaled)
        painter.setClipRect(0, 0, split_x, h)
        painter.drawPixmap(0, 0, before_scaled)
        painter.setClipping(False)

        painter.setPen(Qt.red)
        painter.drawLine(split_x, 0, split_x, h)

    def mouseMoveEvent(self, event):
        self.slider_pos = event.x() / self.width()
        self.update()

    def mousePressEvent(self, event):
        self.slider_pos = event.x() / self.width()
        self.update()


# ================= MAIN APP =================

class ImageEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Advanced Image Editor Pro")
        self.setGeometry(100, 100, 1600, 850)

        self.current_folder = ""
        self.log_file = "logs.txt"

        self.initUI()
        self.load_previous_logs()

    # ================= UI =================

    def initUI(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)

        # LEFT PANEL
        left_layout = QVBoxLayout()

        self.path_input = QLineEdit()
        self.browse_button = QPushButton("Browse Folder")
        self.browse_button.clicked.connect(self.browse_folder)

        self.extension_input = QLineEdit()
        self.extension_input.setPlaceholderText("jpg / png")

        self.load_button = QPushButton("Load Files")
        self.load_button.clicked.connect(self.load_files)

        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.MultiSelection)
        self.file_list.itemClicked.connect(self.preview_input)

        self.input_preview = ZoomableImageView()

        left_layout.addWidget(QLabel("Folder Path"))
        left_layout.addWidget(self.path_input)
        left_layout.addWidget(self.browse_button)
        left_layout.addWidget(QLabel("Extension"))
        left_layout.addWidget(self.extension_input)
        left_layout.addWidget(self.load_button)
        left_layout.addWidget(self.file_list)
        left_layout.addWidget(self.input_preview)

        # CENTER PANEL
        center_layout = QVBoxLayout()

        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(-100, 100)

        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(-100, 100)

        self.exposure_slider = QSlider(Qt.Horizontal)
        self.exposure_slider.setRange(-100, 100)

        self.highlights_slider = QSlider(Qt.Horizontal)
        self.highlights_slider.setRange(-100, 100)

        self.blur_slider = QSlider(Qt.Horizontal)
        self.blur_slider.setRange(0, 50)

        self.crop_button = QPushButton("Crop Selected")
        self.crop_button.clicked.connect(self.crop_images)

        self.apply_button = QPushButton("APPLY EDITS")
        self.apply_button.clicked.connect(self.apply_edits)

        center_layout.addWidget(QLabel("Brightness"))
        center_layout.addWidget(self.brightness_slider)
        center_layout.addWidget(QLabel("Contrast"))
        center_layout.addWidget(self.contrast_slider)
        center_layout.addWidget(QLabel("Exposure"))
        center_layout.addWidget(self.exposure_slider)
        center_layout.addWidget(QLabel("Highlights"))
        center_layout.addWidget(self.highlights_slider)
        center_layout.addWidget(QLabel("Blur"))
        center_layout.addWidget(self.blur_slider)
        center_layout.addWidget(self.crop_button)
        center_layout.addStretch()
        center_layout.addWidget(self.apply_button)

        # RIGHT PANEL
        right_layout = QVBoxLayout()

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        self.output_list = QListWidget()
        self.output_list.itemClicked.connect(self.preview_output)

        self.output_preview = ZoomableImageView()

        self.compare_button = QPushButton("Compare Before / After")
        self.compare_button.clicked.connect(self.open_split_compare)

        right_layout.addWidget(QLabel("Log History"))
        right_layout.addWidget(self.log_box)
        right_layout.addWidget(QLabel("Output Files"))
        right_layout.addWidget(self.output_list)
        right_layout.addWidget(self.output_preview)
        right_layout.addWidget(self.compare_button)

        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(center_layout, 2)
        main_layout.addLayout(right_layout, 3)

    # ================= LOG =================

    def log(self, msg):
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{time}] {msg}"
        self.log_box.append(entry)

        with open(self.log_file, "a") as f:
            f.write(entry + "\n")

    def load_previous_logs(self):
        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as f:
                self.log_box.setText(f.read())

    # ================= FILES =================

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.path_input.setText(folder)
            self.current_folder = folder
            self.log("Folder Selected")

    def load_files(self):
        folder = self.path_input.text().strip()
        ext = self.extension_input.text().strip().lower()

        if not os.path.isdir(folder):
            self.log("Invalid Folder Path")
            return

        if not ext.startswith("."):
            ext = "." + ext

        self.current_folder = folder
        self.file_list.clear()

        for file in os.listdir(folder):
            if file.lower().endswith(ext):
                self.file_list.addItem(file)

        self.log("Files Loaded")

    # ================= PREVIEW =================

    def display_image(self, path, view):
        image = cv2.imread(path)
        if image is None:
            return

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, ch = image.shape
        bytes_per_line = ch * w
        qt_image = QImage(image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)

        view.set_image(pixmap)

    def preview_input(self, item):
        path = os.path.join(self.current_folder, item.text())
        self.display_image(path, self.input_preview)

    def preview_output(self, item):
        path = os.path.join(self.current_folder, item.text())
        self.display_image(path, self.output_preview)

    # ================= EDIT =================

    def apply_edits(self):
        selected = self.file_list.selectedItems()
        if not selected:
            self.log("No files selected")
            return

        for item in selected:
            filename = item.text()
            path = os.path.join(self.current_folder, filename)
            image = cv2.imread(path)

            image = cv2.convertScaleAbs(
                image,
                alpha=1 + self.contrast_slider.value() / 100,
                beta=self.brightness_slider.value()
            )

            # Exposure
            gamma = 1.0 + (self.exposure_slider.value() / 100)
            invGamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
            image = cv2.LUT(image, table)

            # Highlights
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            h, s, v = cv2.split(hsv)
            v = np.clip(v + self.highlights_slider.value(), 0, 255).astype(np.uint8)
            hsv = cv2.merge([h, s, v])
            image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

            # Blur
            blur = self.blur_slider.value()
            if blur > 0:
                k = blur * 2 + 1
                image = cv2.GaussianBlur(image, (k, k), 0)

            # Sharpen
            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
            image = cv2.filter2D(image, -1, kernel)

            output_name = "edited_" + filename
            output_path = os.path.join(self.current_folder, output_name)

            cv2.imwrite(output_path, image)
            self.output_list.addItem(output_name)
            self.log(f"Edited {filename}")

    # ================= CROP =================

    def crop_images(self):
        selected = self.file_list.selectedItems()
        if not selected:
            self.log("No files selected for crop")
            return

        for item in selected:
            filename = item.text()
            path = os.path.join(self.current_folder, filename)
            image = cv2.imread(path)

            r = cv2.selectROI("Select Area & Press ENTER", image, False)
            cv2.destroyAllWindows()

            x, y, w, h = r
            cropped = image[int(y):int(y+h), int(x):int(x+w)]

            output_name = "cropped_" + filename
            output_path = os.path.join(self.current_folder, output_name)

            cv2.imwrite(output_path, cropped)
            self.output_list.addItem(output_name)
            self.log(f"Cropped {filename}")

    # ================= SPLIT COMPARE =================

    def open_split_compare(self):
        selected_output = self.output_list.selectedItems()
        selected_input = self.file_list.selectedItems()

        if not selected_output or not selected_input:
            self.log("Select one input and one output image")
            return

        input_path = os.path.join(self.current_folder, selected_input[0].text())
        output_path = os.path.join(self.current_folder, selected_output[0].text())

        before_img = cv2.imread(input_path)
        after_img = cv2.imread(output_path)

        before_img = cv2.cvtColor(before_img, cv2.COLOR_BGR2RGB)
        after_img = cv2.cvtColor(after_img, cv2.COLOR_BGR2RGB)

        h, w, ch = before_img.shape
        qt_before = QImage(before_img.data, w, h, ch*w, QImage.Format_RGB888)
        qt_after = QImage(after_img.data, w, h, ch*w, QImage.Format_RGB888)

        before_pixmap = QPixmap.fromImage(qt_before)
        after_pixmap = QPixmap.fromImage(qt_after)

        self.compare_window = SplitCompareWidget(before_pixmap, after_pixmap)
        self.compare_window.setWindowTitle("Drag to Compare Before / After")
        self.compare_window.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageEditorApp()
    window.show()
    sys.exit(app.exec_())
