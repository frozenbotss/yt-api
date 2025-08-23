import os
from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

# -------------------------
# Cookies for restricted videos
# -------------------------
cookies_file = 'cookies.txt'
cookie_path = os.path.abspath(cookies_file)
cookies_used = os.path.exists(cookies_file)

print(f"[INFO] Cookies file path: {cookie_path}")
print(f"[INFO] Cookies file exists: {cookies_used}")

# -------------------------
# YT-DLP options
# -------------------------
ydl_opts = {
    'quiet': True,
    'skip_download': True,
    'cookiefile': cookie_path if cookies_used else None,
    'noplaylist': True,
    'geo_bypass': True,
    'format': '249',  # lowest webm/opus audio
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
    }
}

def extract_forced_audio(url):
    print(f"[INFO] Extracting audio for URL: {url}")
    print(f"[INFO] Using cookies: {cookies_used}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        print(f"[INFO] Video title: {info.get('title')}")
        # Try to find itag 249
        for f in info.get('formats', []):
            if f.get('format_id') == '249':
                filesize = f.get('filesize') or f.get('filesize_approx') or None
                print(f"[INFO] Selected format: {f.get('format_id')} {f.get('ext')} {f.get('abr')}k | size: {filesize}")
                return info.get('title'), f['url'], f.get('abr'), f.get('ext'), filesize
        raise Exception("Audio format 249 not available")

# -------------------------
# /audio Endpoint
# -------------------------
@app.route('/audio')
def api_audio():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Provide \"url\" query param'}), 400
    try:
        title, audio_url, abr, ext, filesize = extract_forced_audio(url)
        return jsonify({
            'title': title,
            'audio_url': audio_url,
            'bitrate': abr,
            'ext': ext,
            'filesize': filesize
        })
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"[INFO] Starting Flask server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)



