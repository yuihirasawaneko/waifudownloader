# main.py (fixed: use item_id keys instead of QListWidgetItem)
import sys
import os
import subprocess
import threading
import time
from functools import partial
from concurrent.futures import ThreadPoolExecutor
from queue import Empty
import multiprocessing as mp

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QLineEdit, QFileDialog,
    QVBoxLayout, QHBoxLayout, QProgressBar, QMessageBox, QListWidget, QListWidgetItem,
    QSpinBox, QComboBox
)
from PyQt6.QtGui import QPixmap, QMovie, QFont
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QTimer

# -------------------- Helper: detect ffmpeg --------------------
def detect_ffmpeg():
    possible = [
        r"C:/ProgramData/chocolatey/lib/ffmpeg/tools/ffmpeg/bin",
        r"C:/ffmpeg/bin",
        r"C:/Program Files/ffmpeg/bin",
        r"C:/ProgramData/chocolatey/bin"
    ]
    for p in possible:
        if os.path.exists(p) and os.path.exists(os.path.join(p, "ffmpeg.exe")):
            return p
    # fallback: assume in PATH
    for exe in ("ffmpeg", "ffprobe"):
        try:
            subprocess.run([exe, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            return None
    return ""  # empty means use PATH

# -------------------- Worker signals (for QThread-like behavior) --------------------
class WorkerSignals(QObject):
    progress = pyqtSignal(int)           # percent
    status = pyqtSignal(str)             # text status
    finished = pyqtSignal(bool, str)     # success, message

# -------------------- Thread-based worker (recommended) --------------------
class DownloadThreadWorker(QObject):
    def __init__(self, url, outdir, ffmpeg_location=None):
        super().__init__()
        self.url = url
        self.outdir = outdir
        self.ffmpeg_location = ffmpeg_location
        self.signals = WorkerSignals()
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        """Run yt-dlp in a subprocess and parse progress lines."""
        cmd = [
            "yt-dlp", self.url,
            "-x", "--audio-format", "mp3",
            "--audio-quality", "0",
            "--embed-thumbnail", "--embed-metadata", "--add-metadata",
            "--convert-thumbnails", "jpg",
            "-o", os.path.join(self.outdir, "%(title)s.%(ext)s"),
            "--newline"  # important: force newline progress output
        ]
        if self.ffmpeg_location:
            cmd.extend(["--ffmpeg-location", self.ffmpeg_location])

        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
        except Exception as e:
            self.signals.status.emit(f"Ошибка запуска: {e}")
            self.signals.finished.emit(False, str(e))
            return

        self.signals.status.emit("Запущено")
        try:
            for raw_line in proc.stdout:
                if self._cancel:
                    try:
                        proc.kill()
                    except:
                        pass
                    self.signals.status.emit("Отменено")
                    self.signals.finished.emit(False, "Canceled")
                    return
                line = raw_line.strip()
                # yt-dlp prints progress lines like: [download]  42.3% of ...
                if line.startswith("[download]") and "%" in line:
                    # try to extract percent
                    try:
                        # take first occurrence of NN.N%
                        before_percent = line.split("%")[0]
                        perc_text = before_percent.strip().split()[-1]
                        perc = int(float(perc_text.replace("%","")))
                        percent = max(0, min(100, perc))
                        self.signals.progress.emit(percent)
                        self.signals.status.emit(line)
                    except Exception:
                        self.signals.status.emit(line)
                else:
                    # other informative lines
                    self.signals.status.emit(line)
            proc.wait()
            if proc.returncode == 0:
                self.signals.progress.emit(100)
                self.signals.status.emit("Готово")
                self.signals.finished.emit(True, "OK")
            else:
                self.signals.status.emit(f"Ошибка процесса ({proc.returncode})")
                self.signals.finished.emit(False, f"Return code {proc.returncode}")
        except Exception as e:
            try:
                proc.kill()
            except:
                pass
            self.signals.status.emit(f"Ошибка: {e}")
            self.signals.finished.emit(False, str(e))


# -------------------- Process-based worker (alternative mode) --------------------
def process_worker_entry(url, outdir, ffmpeg_location, progress_queue):
    """
    Запускается в отдельном процессе. Посылает строки прогресса в progress_queue.
    """
    cmd = [
        "yt-dlp", url,
        "-x", "--audio-format", "mp3",
        "--audio-quality", "0",
        "--embed-thumbnail", "--embed-metadata", "--add-metadata",
        "--convert-thumbnails", "jpg",
        "-o", os.path.join(outdir, "%(title)s.%(ext)s"),
        "--newline"
    ]
    if ffmpeg_location:
        cmd.extend(["--ffmpeg-location", ffmpeg_location])

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
    except Exception as e:
        progress_queue.put(("status", f"Ошибка старта: {e}"))
        progress_queue.put(("finished", (False, str(e))))
        return

    for raw_line in proc.stdout:
        line = raw_line.strip()
        progress_queue.put(("status", line))
        if line.startswith("[download]") and "%" in line:
            try:
                before_percent = line.split("%")[0]
                perc_text = before_percent.strip().split()[-1]
                perc = int(float(perc_text.replace("%","")))
                progress_queue.put(("progress", perc))
            except Exception:
                pass
    proc.wait()
    if proc.returncode == 0:
        progress_queue.put(("progress", 100))
        progress_queue.put(("status", "Готово"))
        progress_queue.put(("finished", (True, "OK")))
    else:
        progress_queue.put(("status", f"Ошибка процесса ({proc.returncode})"))
        progress_queue.put(("finished", (False, f"Return code {proc.returncode}")))


# -------------------- UI: item widget for each download --------------------
class DownloadItemWidget(QWidget):
    cancel_requested = pyqtSignal()

    def __init__(self, url):
        super().__init__()
        self.url = url
        h = QHBoxLayout()
        self.setLayout(h)
        self.label = QLabel(url)
        self.label.setFixedWidth(360)
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.status = QLabel("Ожидает")
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(lambda: self.cancel_requested.emit())
        h.addWidget(self.label)
        h.addWidget(self.progress)
        h.addWidget(self.status)
        h.addWidget(self.cancel_btn)

    def set_progress(self, val):
        self.progress.setValue(val)

    def set_status(self, text):
        self.status.setText(text)

    def set_done(self, ok, msg):
        if ok:
            self.status.setText("Готово")
            self.cancel_btn.setEnabled(False)
        else:
            self.status.setText("Ошибка")
            self.cancel_btn.setEnabled(False)


# -------------------- MainWindow --------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WifeeDownloader — Multimode")
        self.setFixedSize(900, 600)
        self.ffmpeg_path = detect_ffmpeg()
        self.executor = ThreadPoolExecutor(max_workers=3)  # default
        self.processes = {}  # map item_id -> (Process, Queue)
        self.init_ui()
        # now items maps item_id -> meta dict (meta contains 'lw_item')
        self.items = {}

        # Poll timer for process queues
        self.poll_timer = QTimer()
        self.poll_timer.setInterval(200)
        self.poll_timer.timeout.connect(self.poll_process_queues)
        self.poll_timer.start()

    def init_ui(self):
        v = QVBoxLayout(self)

        top_h = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Вставьте URL (или плейлист) тут")
        self.add_btn = QPushButton("Добавить")
        self.add_btn.clicked.connect(self.on_add)
        self.folder_btn = QPushButton("Папка")
        self.folder_btn.clicked.connect(self.on_pick_folder)
        self.folder_label = QLabel("Папка не выбрана")

        top_h.addWidget(self.url_input)
        top_h.addWidget(self.add_btn)
        top_h.addWidget(self.folder_btn)
        top_h.addWidget(self.folder_label)
        v.addLayout(top_h)

        opts_h = QHBoxLayout()
        opts_h.addWidget(QLabel("Параллельных задач:"))
        self.spin_workers = QSpinBox()
        self.spin_workers.setMinimum(1)
        self.spin_workers.setMaximum(16)
        self.spin_workers.setValue(3)
        self.spin_workers.valueChanged.connect(self.on_workers_changed)
        opts_h.addWidget(self.spin_workers)

        opts_h.addWidget(QLabel("Режим:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Thread (рекомендуется)", "Process (отдельные процессы)"])
        opts_h.addWidget(self.mode_combo)

        # animation toggle
        self.anim_btn = QPushButton("Показать выдру")
        self.anim_btn.clicked.connect(self.toggle_otter)
        opts_h.addWidget(self.anim_btn)

        v.addLayout(opts_h)

        # list
        self.list_widget = QListWidget()
        v.addWidget(self.list_widget)

        # bottom bar
        bottom_h = QHBoxLayout()
        self.start_all_btn = QPushButton("Старт всех")
        self.start_all_btn.clicked.connect(self.start_all)
        self.cancel_all_btn = QPushButton("Отмена всех")
        self.cancel_all_btn.clicked.connect(self.cancel_all)
        bottom_h.addWidget(self.start_all_btn)
        bottom_h.addWidget(self.cancel_all_btn)
        v.addLayout(bottom_h)

        # otter gif placeholder
        self.otter_label = QLabel("🦦")
        self.otter_label.setFont(QFont("Segoe UI", 32))
        v.addWidget(self.otter_label, alignment=Qt.AlignmentFlag.AlignCenter)

    def on_workers_changed(self, n):
        # adjust threadpool by recreating executor
        try:
            self.executor._max_workers = n
        except Exception:
            pass

    def on_pick_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if folder:
            self.output_path = folder
            self.folder_label.setText(folder)

    def _get_item_id(self, lw_item: QListWidgetItem) -> str:
        """Return item_id stored in lw_item UserRole (or None)."""
        data = lw_item.data(Qt.ItemDataRole.UserRole)
        return data if isinstance(data, str) else None

    def _get_lw_item_by_id(self, item_id: str) -> QListWidgetItem:
        """Return the QListWidgetItem reference for stored item_id (or None)."""
        meta = self.items.get(item_id)
        if not meta:
            return None
        return meta.get("lw_item")

    def on_add(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Ошибка", "Введите URL")
            return
        if not hasattr(self, "output_path") or not self.output_path:
            QMessageBox.warning(self, "Ошибка", "Выберите папку загрузки")
            return

        item_widget = DownloadItemWidget(url)
        lw_item = QListWidgetItem()
        lw_item.setSizeHint(item_widget.sizeHint())
        self.list_widget.addItem(lw_item)
        self.list_widget.setItemWidget(lw_item, item_widget)

        # attach cancel handler later. we bind lw_item reference in lambda via closure
        item_widget.cancel_requested.connect(partial(self.cancel_item_by_lw, lw_item))

        # create unique id for this lw_item (use id() for simplicity)
        item_id = str(id(lw_item))
        lw_item.setData(Qt.ItemDataRole.UserRole, item_id)

        # store controller info keyed by item_id
        self.items[item_id] = {"lw_item": lw_item, "widget": item_widget, "state": "pending", "worker": None}
        self.url_input.clear()

    def start_all(self):
        # iterate over item_ids
        for item_id, meta in list(self.items.items()):
            if meta["state"] == "pending":
                self.start_item_by_id(item_id)

    def start_item_by_id(self, item_id: str):
        meta = self.items.get(item_id)
        if not meta:
            return
        widget = meta["widget"]
        url = widget.url
        widget.set_status("Запускается")
        widget.set_progress(0)
        meta["state"] = "running"

        mode = self.mode_combo.currentIndex()  # 0 thread, 1 process
        if mode == 0:
            # thread mode: use DownloadThreadWorker run() in a real thread
            worker = DownloadThreadWorker(url, self.output_path, self.ffmpeg_path)
            # connect signals
            worker.signals.progress.connect(widget.set_progress)
            worker.signals.status.connect(widget.set_status)
            worker.signals.finished.connect(lambda ok, msg, iid=item_id: self.on_item_finished_by_id(iid, ok, msg))
            meta["worker"] = worker
            # run in thread via ThreadPoolExecutor to avoid blocking main loop
            self.executor.submit(worker.run)
        else:
            # process mode: create mp.Queue and mp.Process
            q = mp.Queue()
            p = mp.Process(target=process_worker_entry, args=(url, self.output_path, self.ffmpeg_path, q), daemon=True)
            # store by item_id
            self.processes[item_id] = (p, q)
            p.start()
            meta["worker"] = ("process", p, q)
            # update status
            widget.set_status("Запущен (process)")

    def poll_process_queues(self):
        # poll each running process queue and update UI
        for item_id, procinfo in list(self.processes.items()):
            p, q = procinfo
            meta = self.items.get(item_id)
            if meta is None:
                continue
            widget = meta["widget"]
            try:
                while True:
                    typ, payload = q.get_nowait()
                    if typ == "status":
                        widget.set_status(payload)
                    elif typ == "progress":
                        widget.set_progress(payload)
                    elif typ == "finished":
                        ok, msg = payload
                        widget.set_done(ok, msg)
                        # cleanup
                        try:
                            p.join(timeout=0.1)
                        except:
                            pass
                        # remove process entry
                        if item_id in self.processes:
                            del self.processes[item_id]
                        meta["state"] = "done"
            except Empty:
                pass

    def on_item_finished_by_id(self, item_id: str, ok: bool, msg: str):
        meta = self.items.get(item_id)
        if not meta:
            return
        widget = meta["widget"]
        widget.set_done(ok, msg)
        meta["state"] = "done"

    def cancel_item_by_lw(self, lw_item: QListWidgetItem):
        """Called from item_widget.cancel_requested; lw_item is the QListWidgetItem reference."""
        item_id = self._get_item_id(lw_item)
        if not item_id:
            return
        self.cancel_item_by_id(item_id)

    def cancel_item_by_id(self, item_id: str):
        meta = self.items.get(item_id)
        if not meta:
            return
        widget = meta["widget"]
        w = meta.get("worker")
        # thread worker
        if isinstance(w, DownloadThreadWorker):
            w.cancel()
            widget.set_status("Отмена...")
            meta["state"] = "cancelled"
        elif isinstance(w, tuple) and w[0] == "process":
            # process mode stored as ("process", proc, q)
            proc = w[1]
            try:
                proc.terminate()
            except:
                pass
            widget.set_status("Отменён")
            meta["state"] = "cancelled"
            # cleanup processes dict if exists
            if item_id in self.processes:
                try:
                    self.processes[item_id][0].terminate()
                except:
                    pass
                del self.processes[item_id]

    def cancel_all(self):
        for item_id in list(self.items.keys()):
            self.cancel_item_by_id(item_id)

    def start_worker_for_item_if_pending(self):
        # optional helper to auto-start pending items if pool has free slots
        running = sum(1 for m in self.items.values() if m["state"] == "running")
        limit = self.spin_workers.value()
        for item_id, meta in self.items.items():
            if running >= limit:
                break
            if meta["state"] == "pending":
                self.start_item_by_id(item_id)
                running += 1

    def toggle_otter(self):
        # simple GIF show/hide if file exists
        gif_path = os.path.join(os.path.dirname(__file__), "otter_happy.gif")
        png_path = os.path.join(os.path.dirname(__file__), "otter.png")
        if os.path.exists(gif_path):
            movie = QMovie(gif_path)
            self.otter_label.setMovie(movie)
            movie.start()
            # stop after 3s
            QTimer.singleShot(3000, lambda: self.restore_otter(png_path))
        elif os.path.exists(png_path):
            self.otter_label.setPixmap(QPixmap(png_path).scaledToHeight(120, Qt.TransformationMode.SmoothTransformation))
        else:
            QMessageBox.information(self, "Выдра", "Положи otter.png или otter_happy.gif рядом с main.py")

    def restore_otter(self, png_path):
        if os.path.exists(png_path):
            self.otter_label.setPixmap(QPixmap(png_path).scaledToHeight(120, Qt.TransformationMode.SmoothTransformation))
        else:
            self.otter_label.setText("🦦")

# -------------------- Entrypoint --------------------
def main():
    mp.set_start_method("spawn", force=True)  # safe on Windows
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
