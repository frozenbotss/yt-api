import os
from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

# Cookies for restricted videos
cookies_file = 'cookies.txt'
cookie_path = os.path.abspath(cookies_file) if os.path.exists(cookies_file) else None

# YT-DLP options
ydl_opts = {
    'quiet': True,
    'skip_download': True,
    'cookiefile': cookie_path,
    'noplaylist': True,
    'geo_bypass': True,
    'format': '249',  # Force lowest webm/opus audio
}

def extract_forced_audio(url):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        # Find itag 249
        for f in info.get('formats', []):
            if f.get('format_id') == '249':
                return info.get('title'), f['url'], f.get('abr'), f.get('ext')
        raise Exception("Audio format 249 not available")

@app.route('/audio')
def api_audio():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Provide "url" query param'}), 400
    try:
        title, audio_url, abr, ext = extract_forced_audio(url)
        return jsonify({
            'title': title,
            'audio_url': audio_url,
            'bitrate': abr,
            'ext': ext
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)


