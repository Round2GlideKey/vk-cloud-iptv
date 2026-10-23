from flask import Flask, Response, redirect, request
import yt_dlp

app = Flask(__name__)

# Ваши официальные каналы VK Видео
STREAM_URL = "https://live.vkvideo.ru/btvrestored"
CHANNEL_URL = "https://vkvideo.ru/@btv_restored"

def get_vk_stream_url(url):
    """Получает прямую .m3u8 ссылку на поток через yt-dlp"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'playlist_items': '1' # Для канала берем только последнее видео
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Если это плейлист/канал, проваливаемся в первое видео
            if 'entries' in info:
                entries = list(info['entries'])
                if entries:
                    info = ydl.extract_info(entries[0]['url'], download=False)
                else:
                    return None
                    
            # Ищем прямую ссылку на hls поток (.m3u8)
            return info.get('url') or info.get('formats', [{}])[-1].get('url')
    except Exception as e:
        print(f"Ошибка парсинга {url}: {e}")
        return None

@app.route('/playlist.m3u')
def get_playlist():
    host = request.host_url.rstrip('/')
    
    m3u = "#EXTM3U\n"
    # 1. Ссылка на ваш живой стрим
    m3u += f'#EXTINF:-1 tvg-logo="https://vk.com", BTV Live Стрим\n{host}/live\n'
    # 2. Ссылка на последнее видео с канала
    m3u += f'#EXTINF:-1 tvg-logo="https://vk.com", BTV Последнее Видео\n{host}/latest\n'
    
    return Response(m3u, mimetype='text/plain')

@app.route('/live')
def route_live():
    stream_url = get_vk_stream_url(STREAM_URL)
    if stream_url:
        return redirect(stream_url)
    return "Стрим сейчас оффлайн или недоступен", 404

@app.route('/latest')
def route_latest():
    video_url = get_vk_stream_url(CHANNEL_URL)
    if video_url:
        return redirect(video_url)
    return "Видео на канале не найдены", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
