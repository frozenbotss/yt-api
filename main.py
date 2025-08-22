import os
from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

# -------------------------
# Cookies file for restricted videos
# -------------------------
cookies_file = 'cookies.txt'
cookie_path = os.path.abspath(cookies_file) if os.path.exists(cookies_file) else None

# -------------------------
# YT-DLP Options
# -------------------------
ydl_opts = {
    'quiet': True,
    'skip_download': True,
    'format': 'bestaudio/best',  # best audio fallback
    'cookiefile': cookie_path,
    'noplaylist': True,
    'geo_bypass': True,
}

# -------------------------
# Extract info
# -------------------------
def extract_audio_url(url):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        # Build list of audio formats
        audio_formats = []
        for f in info.get('formats', []):
            if f.get('acodec') == 'none':
                continue
            url_f = f.get('url')
            if not url_f:
                continue
            audio_formats.append({
                'format_id': f.get('format_id'),
                'ext': f.get('ext'),
                'abr': f.get('abr'),
                'url': url_f,
                'filesize': f.get('filesize') or f.get('filesize_approx')
            })

        if not audio_formats:
            raise Exception("No audio formats available")

        # Pick lowest bitrate (lightweight for PyTgCalls)
        audio_formats.sort(key=lambda f: f.get('abr') or 0)
        return info.get('title'), audio_formats[0]['url'], audio_formats[0].get('abr')

# -------------------------
# /audio Endpoint
# -------------------------
@app.route('/audio')
def api_audio():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Provide "url" query param'}), 400
    try:
        title, audio_url, abr = extract_audio_url(url)
        return jsonify({
            'title': title,
            'audio_url': audio_url,
            'bitrate': abr
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

