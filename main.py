from flask import Flask, Response, redirect, request
import xml.etree.ElementTree as ET
import urllib.request
import yt_dlp

app = Flask(__name__)

# Ссылка на ваш стрим
STREAM_URL = "https://live.vkvideo.ru/btvrestored"

# RSS-лента вашего канала для мгновенного получения архива видео без блокировок
# (VK автоматически транслирует сюда все новые ролики)
RSS_URL = "https://vk.com"

CHROME_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def get_archive_from_rss(rss_url, count=10):
    """Быстро и надежно вытягивает последние видео через RSS-фид ВКонтакте"""
    videos = []
    try:
        req = urllib.request.Request(
            rss_url, 
            headers={'User-Agent': CHROME_USER_AGENT}
        )
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        # Ищем все элементы <item> (это и есть видеоролики)
        items = root.findall('.//item')
        
        for item in items[:count]:
            title = item.find('title').text if item.find('title') is not None else "Архивное видео"
            link = item.find('link').text if item.find('link') is not None else None
            
            if link:
                # Очищаем ссылку от лишних параметров, если они есть
                clean_url = link.split('?')[0]
                videos.append({"name": title, "url": clean_url})
    except Exception as e:
        print(f"Ошибка чтения RSS: {e}")
    return videos

def get_single_stream_url(url):
    """Получает прямую .m3u8 ссылку на поток конкретного видео или стрима"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'http_headers': {
            'User-Agent': CHROME_USER_AGENT
        }
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
    # Принудительно делаем ссылки внутри плейлиста безопасными (https)
    host = request.host_url.rstrip('/').replace('http://', 'https://')
    
    m3u = "#EXTM3U\n"
    # 1. Добавляем живой стрим
    m3u += f'#EXTINF:-1 tvg-logo="https://vk.com" group-title="Прямой эфир", BTV Live Стрим\n{host}/live\n'
    
    # 2. Подтягиваем архивные ролики из RSS
    archive_videos = get_archive_from_rss(RSS_URL, count=10)
    
    for video in archive_videos:
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
