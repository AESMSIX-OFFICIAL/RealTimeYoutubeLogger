import asyncio
import websockets
import json
from urllib.parse import urlparse, parse_qs
import threading
import os
import logging
from yt_dlp import YoutubeDL

# Konfigurasi logging ke file logging.txt
logging.basicConfig(
    filename="logging.txt",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

LOG_FILE = "tab_log.txt"
logged_links = set()

# Fungsi untuk mengambil judul URL menggunakan yt-dlp
def get_url_title(url):
    try:
        with YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('title', 'Unknown Title')
    except Exception as e:
        logger.error(f"Failed to fetch title: {e}")
        return "Unknown Title"

# Muat URL yang sudah tercatat dari file LOG_FILE
def load_logged_links():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            for line in f:
                logged_links.add(line.strip())

load_logged_links()

# Fungsi untuk menormalisasi URL YouTube
def canonicalize_youtube_url(url):
    if "www.youtube.com/watch?v=" not in url:
        return None
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    if 'v' not in query_params:
        return None
    video_id = query_params['v'][0]
    canonical_url = f"https://www.youtube.com/watch?v={video_id}"
    return canonical_url

# Fungsi untuk memeriksa apakah URL adalah video musik
def is_music_video(url):
    try:
        with YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            categories = info.get('categories', [])
            tags = info.get('tags', [])
            genre = info.get('genre', '')
            title = info.get('title', '')

            if 'Music' in categories or genre.lower() == 'music':
                return True
            music_keywords = ['music', 'official video', 'lyrics', 'mv', 'audio']
            if any(keyword in title.lower() for keyword in music_keywords):
                return True
            if any(keyword in tag.lower() for tag in tags for keyword in music_keywords):
                return True
    except Exception as e:
        logger.warning(f"Failed to check video category: {e}")
    return False

# Fungsi handler untuk WebSocket
async def handler(websocket):
    client_addr = websocket.remote_address
    logger.info(f"Client connected: {client_addr}")
    print(f"Client connected: {client_addr}")

    try:
        await websocket.send(json.dumps({"message": "Connection established with server."}))
    except Exception as e:
        logger.error(f"Error sending handshake: {e}")

    async for message in websocket:
        try:
            data = json.loads(message)
            url = data.get("url")
            canonical_url = canonicalize_youtube_url(url)

            if canonical_url:
                if is_music_video(canonical_url):
                    if canonical_url not in logged_links:
                        with open(LOG_FILE, "a") as f:
                            f.write(f"{canonical_url}\n")
                        logged_links.add(canonical_url)
                        title = get_url_title(canonical_url)
                        logger.info(f"Logged URL: {canonical_url} | Title: {title}")
                        print(f"Logged: {canonical_url}")
                    else:
                        logger.info(f"Duplicate music URL received, ({canonical_url}) will not be logged.")
                        print(f"Duplicate music URL received, ({canonical_url}) will not be logged.")
                else:
                    logger.info(f"URL is not a music video: {canonical_url}")
                    print(f"URL is not a music video: {canonical_url}")

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            print(f"Error processing message: {e}")

# Fungsi untuk mendengarkan input keyboard (shortcut 'q' untuk keluar)
def listen_for_quit(loop):
    while True:
        inp = input()
        if inp.strip().lower() == 'q':
            logger.info("Shortcut Q pressed. Shutting down server...")
            print("Shortcut Q pressed. Shutting down server...")
            loop.call_soon_threadsafe(loop.stop)
            break

# Fungsi main untuk menjalankan server WebSocket
async def main():
    loop = asyncio.get_running_loop()
    threading.Thread(target=listen_for_quit, args=(loop,), daemon=True).start()
    async with websockets.serve(handler, "localhost", 8765):
        logger.info("WebSocket server running on ws://localhost:8765")
        print("WebSocket server running on ws://localhost:8765")
        await asyncio.Future()  # Menjalankan server tanpa henti

if __name__ == "__main__":
    asyncio.run(main())