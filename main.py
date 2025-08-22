import os
from http.cookiejar import MozillaCookieJar
from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

# -------------------------
# Load cookies if present
# -------------------------
cookies_file = 'cookies.txt'
if os.path.exists(cookies_file):
    cookie_jar = MozillaCookieJar(cookies_file)
    cookie_jar.load(ignore_discard=True, ignore_expires=True)

ydl_opts_full = {
    'quiet': True,
    'skip_download': True,
    'format': 'bestaudio/best',
    'cookiefile': cookies_file if os.path.exists(cookies_file) else None
}

def extract_info(url):
    with yt_dlp.YoutubeDL(ydl_opts_full) as ydl:
        return ydl.extract_info(url, download=False)

def build_formats_list(info):
    fmts = []
    for f in info.get('formats', []):
        url_f = f.get('url')
        if not url_f:
            continue
        has_audio = f.get('acodec') != 'none'
        if not has_audio:
            continue
        fmts.append({
            'format_id': f.get('format_id'),
            'ext': f.get('ext'),
            'kind': 'audio-only',
            'abr': f.get('abr'),
            'url': url_f,
            'filesize': f.get('filesize') or f.get('filesize_approx')
        })
    return fmts

# -------------------------
# /audio Endpoint
# -------------------------
@app.route('/audio')
def api_signed_audio():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Provide "url"'}), 400
    try:
        info = extract_info(url)
        audio_formats = [f for f in build_formats_list(info) if f['ext'] == 'webm']
        if not audio_formats:
            return jsonify({'error': 'No audio-only webm formats found'}), 404

        # Pick worst quality (lowest bitrate)
        audio_formats.sort(key=lambda f: f.get('abr') or 0)
        worst_audio = audio_formats[0]

        return jsonify({
            'title': info.get('title'),
            'audio_url': worst_audio['url'],
            'bitrate': worst_audio.get('abr'),
            'ext': worst_audio.get('ext'),
            'filesize': worst_audio.get('filesize')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

