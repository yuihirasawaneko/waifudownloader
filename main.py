import sys
import os
import subprocess
import threading
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QLineEdit, QFileDialog,
    QVBoxLayout, QHBoxLayout, QProgressBar, QMessageBox, QListWidget
)
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt

class WifeeDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WifeeDownloader — выдра качает музыку 🦦🎶")
        self.setFixedSize(700, 500)
        self.output_path = ""
        self.download_queue = []

        self.init_ui()
        self.ffmpeg_path = self.detect_ffmpeg()

    def init_ui(self):
        # Основной вертикальный layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # ---------------- ЛОГО ВЫДРЫ ----------------
        self.otter_label = QLabel("🦦")
        self.otter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.otter_label.setFont(QFont("Segoe UI", 60))
        main_layout.addWidget(self.otter_label)

        # ---------------- URL ----------------
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Вставьте URL ролика или плейлиста")
        self.url_input.setFont(QFont("Segoe UI", 11))
        main_layout.addWidget(self.url_input)

        # ---------------- ПАПКА ----------------
        folder_layout = QHBoxLayout()
        self.folder_btn = QPushButton("Выбрать папку")
        self.folder_btn.clicked.connect(self.pick_folder)
        folder_layout.addWidget(self.folder_btn)

        self.folder_label = QLabel("Папка не выбрана")
        folder_layout.addWidget(self.folder_label)
        main_layout.addLayout(folder_layout)

        # ---------------- КНОПКА СКАЧАТЬ ----------------
        self.download_btn = QPushButton("Добавить в очередь")
        self.download_btn.clicked.connect(self.add_to_queue)
        main_layout.addWidget(self.download_btn)

        # ---------------- СПИСОК ОЧЕРЕДИ ----------------
        self.queue_list = QListWidget()
        main_layout.addWidget(self.queue_list)

        # ---------------- ПРОГРЕСС ----------------
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.progress)

        # ---------------- КНОПКА ВЫДРА ДОВОЛЬНА ----------------
        self.happy_btn = QPushButton("Выдра довольна! 🦦")
        self.happy_btn.clicked.connect(self.happy_animation)
        main_layout.addWidget(self.happy_btn)

    # ---------------- ПАПКА ----------------
    def pick_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выбрать папку для загрузки")
        if folder:
            self.output_path = folder
            self.folder_label.setText(folder)

    # ---------------- FFmpeg ----------------
    def detect_ffmpeg(self):
        possible = [
            r"C:/ProgramData/chocolatey/lib/ffmpeg/tools/ffmpeg/bin",
            r"C:/ffmpeg/bin",
            r"C:/Program Files/ffmpeg/bin",
            r"C:/ProgramData/chocolatey/bin"
        ]
        for p in possible:
            if os.path.exists(p):
                return p
        return None

    # ---------------- ДОБАВИТЬ В ОЧЕРЕДЬ ----------------
    def add_to_queue(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Ошибка", "Введите URL!")
            return
        if not self.output_path:
            QMessageBox.warning(self, "Ошибка", "Выберите папку для загрузки!")
            return

        self.download_queue.append(url)
        self.queue_list.addItem(url)
        self.url_input.clear()
        if len(self.download_queue) == 1:
            self.start_download(self.download_queue[0])

    # ---------------- ЗАПУСК ЗАГРУЗКИ ----------------
    def start_download(self, url):
        thread = threading.Thread(target=self.download_thread, args=(url,))
        thread.start()

    # ---------------- ПОТОК ЗАГРУЗКИ ----------------
    def download_thread(self, url):
        self.progress.setValue(0)
        self.download_btn.setEnabled(False)

        cmd = [
            "yt-dlp",
            url,
            "-x", "--audio-format", "mp3",
            "--audio-quality", "0",
            "--embed-thumbnail",
            "--embed-metadata",
            "--add-metadata",
            "--convert-thumbnails", "jpg",
            "-o", f"{self.output_path}/%(title)s.%(ext)s"
        ]
        if self.ffmpeg_path:
            cmd.extend(["--ffmpeg-location", self.ffmpeg_path])

        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in process.stdout:
                if "[download]" in line and "%" in line:
                    try:
                        percent = int(line.split('%')[0].split()[-1])
                        self.progress.setValue(percent)
                    except:
                        pass
            process.wait()
            if process.returncode == 0:
                QMessageBox.information(self, "Готово!", "Выдра скачала ваш трек! 🦦✔")
            else:
                QMessageBox.critical(self, "Ошибка", "Произошла ошибка при скачивании.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

        # Удаляем из очереди и запускаем следующий
        self.download_queue.pop(0)
        self.queue_list.takeItem(0)
        if self.download_queue:
            self.start_download(self.download_queue[0])
        else:
            self.download_btn.setEnabled(True)
            self.progress.setValue(0)

    # ---------------- АНИМАЦИЯ ВЫДРЫ ----------------
    def happy_animation(self):
        # простая временная анимация текста
        original = self.otter_label.text()
        self.otter_label.setText("🦦✨")
        threading.Timer(0.5, lambda: self.otter_label.setText(original)).start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WifeeDownloader()
    window.show()
    sys.exit(app.exec())
