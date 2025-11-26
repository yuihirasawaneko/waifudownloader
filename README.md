🇷🇺 README (Русский)
WifeeDownloader — красивый GUI для yt-dl 🦦🎶

A simple and lovely GUI for yt-dlp, built with PyQt6 and love ❤️

WifeeDownloader — это современное приложение для быстрой, удобной и красивой загрузки музыки и плейлистов с YouTube.
Поддерживает параллельные загрузки, прогрессбар для каждого файла, многопоточность/многопроцессность, анимацию выдры 🦦 и лучший UX для простых и больших загрузок.

✨ Особенности

🦦 Милый и отзывчивый интерфейс
Дружелюбная атмосфера, кастомная анимированная выдра.

🚀 Параллельная загрузка множества файлов
Поддержка ThreadPool и Multiprocessing.

📥 Поддержка плейлистов и отдельных роликов

🎧 Автоматическая конвертация в MP3

встроенная поддержка:

--embed-thumbnail

--add-metadata

--convert-thumbnails jpg

📊 Прогрессбар и статус для каждого файла

процент загрузки

текущая скорость

ETA

лог активности

📂 Выбор папки и гибкие настройки

🧵 Режимы загрузки

Thread Mode (рекомендуется)

Process Mode (каждая загрузка в отдельном процессе)

🎨 Готово для кастомизации
Легко встроить свои темы, blur, анимации, стили.

📦 Установка зависимостей
pip install pyqt6 yt-dlp pillow


(FFmpeg должен быть установлен и добавлен в PATH)

▶️ Запуск
python main.py

🛠 Сборка EXE через Nuitka

PowerShell:

python -m nuitka main.py `
 --standalone `
 --onefile `
 --enable-plugin=pyqt6 `
 --lto=yes `
 --clang `
 --assume-yes-for-downloads `
 --windows-icon-from-ico=icon.ico `
 --windows-disable-console `
 --include-data-file=otter.png=otter.png `
 --output-dir=build

❤️ Создано с любовью, PyQt6 и выдрами

Если вы улыбнулись, значит проект работает 🦦💗

🇺🇸 README (English)
WifeeDownloader — a beautiful GUI for yt-dl 🦦🎶

A simple and lovely GUI for yt-dlp, built with PyQt6 and love ❤️

WifeeDownloader is a modern desktop application for fast, easy and beautiful music downloading from YouTube.
It supports multi-downloads, per-item progress bars, threads/processes, otter animations 🦦 and clean UX for both small and huge tasks.

✨ Features

🦦 Cute, responsive UI
Friendly interface with animated otter support.

🚀 Parallel download of multiple files
Supports ThreadPool and Multiprocessing.

📥 Downloads playlists and individual videos

🎧 Automatic MP3 conversion
Includes:

--embed-thumbnail

--add-metadata

--convert-thumbnails jpg

📊 Per-item progress and status

progress percent

download speed

ETA

activity logs

📂 Folder selection + flexible runtime settings

🧵 Multiple modes

Thread Mode (recommended)

Process Mode (each task in a separate process)

🎨 Customizable UI
Easy to extend with blur, themes, animations, shiny UI.

📦 Install dependencies
pip install pyqt6 yt-dlp pillow


(FFmpeg must be installed and available in PATH)

▶️ Run
python main.py

🛠 Build EXE via Nuitka

PowerShell:

python -m nuitka main.py `
 --standalone `
 --onefile `
 --enable-plugin=pyqt6 `
 --lto=yes `
 --clang `
 --assume-yes-for-downloads `
 --windows-icon-from-ico=icon.ico `
 --windows-disable-console `
 --include-data-file=otter.png=otter.png `
 --output-dir=build

❤️ Made with love, PyQt6, and otters

If it made you smile — the project works 🦦✨