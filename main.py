from flask import Flask, Response, redirect, request
import yt_dlp

app = Flask(__name__)

# Ваши официальные каналы VK Видео
STREAM_URL = "https://vkvideo.ru"
CHANNEL_URL = "https://vkvideo.ru"

def get_archive_videos(channel_url, count=10):
    """Получает список последних видео из архива канала"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': 'in_playlist',  # Быстро собирает только названия и ID без тяжелого парсинга
        'playlist_items': f'1-{count}'  # Задаем количество видео из архива
    }
    videos = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
            if 'entries' in info:
                for entry in info['entries']:
                    if entry:
                        # Формируем прямую ссылку на ролик из его ID
                        video_id = entry.get('id')
                        title = entry.get('title', 'Архивное видео')
                        if video_id:
                            # Корректный URL для VK Видео
                            full_url = f"https://vkvideo.ru{video_id}"
                            videos.append({"name": title, "url": full_url})
    except Exception as e:
        print(f"Ошибка при получении архива: {e}")
    return videos

def get_single_stream_url(url):
    """Получает прямую .m3u8 ссылку на поток конкретного видео или стрима"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('url') or info.get('formats', [{}])[-1].get('url')
    except Exception as e:
        print(f"Ошибка парсинга потока {url}: {e}")
        return None

@app.route('/playlist.m3u')
def get_playlist():
    host = request.host_url.rstrip('/')
    
    m3u = "#EXTM3U\n"
    # 1. Добавляем живой стрим (всегда на первой строчке)
    m3u += f'#EXTINF:-1 tvg-logo="https://vk.com" group-title="Прямой эфир", BTV Live Стрим\n{host}/live\n'
    
    # 2. Динамически подтягиваем архивные ролики
    archive_videos = get_archive_videos(CHANNEL_URL, count=10)
    
    for i, video in enumerate(archive_videos):
        # Передаем URL видео в параметре запроса, чтобы не создавать под каждый ролик свой роут
        m3u += f'#EXTINF:-1 tvg-logo="https://vk.com" group-title="Архив передач", {video["name"]}\n{host}/stream?url={video["url"]}\n'
        
    return Response(m3u, mimetype='text/plain')

@app.route('/live')
def route_live():
    stream_url = get_single_stream_url(STREAM_URL)
    if stream_url:
        return redirect(stream_url)
    return "Стрим сейчас оффлайн или недоступен", 404

@app.route('/stream')
def route_stream():
    video_url = request.args.get('url')
    if not video_url:
        return "Missing url parameter", 400
        
    stream_url = get_single_stream_url(video_url)
    if stream_url:
        return redirect(stream_url)
    return "Видео не найдено или недоступно", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
