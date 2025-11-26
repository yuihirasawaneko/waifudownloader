# 🇷🇺 WifeeDownloader — красивый GUI для yt-dlp  
*A simple GUI for yt-dlp created with love ❤️ and PyQt6 🦦*

WifeeDownloader — это современное приложение для быстрой, удобной и красивой загрузки музыки и плейлистов с YouTube.  
Поддерживает параллельные загрузки, прогрессбар для каждого файла, многопоточность, анимацию выдры и отличный UX.

---

## Особенности

- Милый и дружелюбный интерфейс (PyQt6)
- Параллельная загрузка множества файлов
- Поддержка плейлистов и отдельных роликов
- Автоматическая конвертация в MP3
  - embed-thumbnail  
  - add-metadata  
  - convert-thumbnails jpg
- Прогрессбар, скорость, ETA, лог для каждого файла
- Выбор папки загрузки
- Два режима: Threads / Processes
- Легко кастомизируется под свои темы и стили

---

## Установка зависимостей

```bash
pip install pyqt6 yt-dlp pillow
```

*(Не забудьте установить FFmpeg и добавить его в PATH)*

---

## Запуск

```bash
python main.py
```

---

## Сборка EXE через Nuitka

```bash
python -m nuitka main.py ^
 --standalone ^
 --onefile ^
 --enable-plugin=pyqt6 ^
 --lto=yes ^
 --clang ^
 --assume-yes-for-downloads ^
 --windows-icon-from-ico=icon.ico ^
 --windows-disable-console ^
 --include-data-file=otter.png=otter.png ^
 --output-dir=build
```

---

# 🇺🇸 WifeeDownloader — beautiful GUI for yt-dlp  
*A simple GUI for yt-dlp created with love ❤️ and PyQt6 🦦*

WifeeDownloader is a modern application for fast, convenient and visually pleasing music and playlist downloading from YouTube.  
Supports parallel downloads, per-item progress bars, multiprocessing, otter animations and great UX.

## Features

- Cute and friendly interface (PyQt6)
- Parallel downloading of multiple files
- Playlist and single video support
- Auto MP3 conversion:
  - embed-thumbnail  
  - add-metadata  
  - convert-thumbnails jpg
- Per-item progress bar, speed, ETA and log
- Choose download directory
- Two modes: Threads / Processes
- Fully theme‑ready and customizable

## Install dependencies

```bash
pip install pyqt6 yt-dlp pillow
```

(FFmpeg must be installed and added to PATH)

## Run

```bash
python main.py
```

## Build EXE via Nuitka

```bash
python -m nuitka main.py ^
 --standalone ^
 --onefile ^
 --enable-plugin=pyqt6 ^
 --lto=yes ^
 --clang ^
 --assume-yes-for-downloads ^
 --windows-icon-from-ico=icon.ico ^
 --windows-disable-console ^
 --include-data-file=otter.png=otter.png ^
 --output-dir=build
```
