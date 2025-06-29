from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/fumck')
def extract_info():
    url = request.args.get('url')
    search_query = request.args.get('search')

    if not url and not search_query:
        return jsonify({'error': 'Provide either "url" or "search" parameter'}), 400

    # You can put your cookies.txt file path here
    cookies_file = "cookies.txt"

    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'format': 'bestvideo+bestaudio/best',
        'cookiefile': cookies_file  # <-- added for using cookies.txt
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if search_query:
                search_result = ydl.extract_info(f"ytsearch:{search_query}", download=False)
                if not search_result.get('entries'):
                    return jsonify({'error': 'No search results found'}), 404
                info = search_result['entries'][0]
            else:
                info = ydl.extract_info(url, download=False)
    except Exception as e:
        return jsonify({'error': f'Failed to extract info: {str(e)}'}), 500

    def get_size_bytes(fmt):
        return fmt.get('filesize') or fmt.get('filesize_approx') or 0

    def format_size(bytes_val):
        if bytes_val >= 1e9:
            return f"{bytes_val/1e9:.2f} GB"
        if bytes_val >= 1e6:
            return f"{bytes_val/1e6:.2f} MB"
        if bytes_val >= 1e3:
            return f"{bytes_val/1e3:.2f} KB"
        return f"{bytes_val} B"

    # Audio formats
    audio_formats = [
        {
            'format_id': f.get('format_id'),
            'abr': f.get('abr'),
            'ext': f.get('ext'),
            'filesize_bytes': get_size_bytes(f),
            'filesize': format_size(get_size_bytes(f)),
            'url': f.get('url')
        }
        for f in info.get('formats', [])
        if f.get('vcodec') == 'none' and f.get('acodec') != 'none' and f.get('url') and 'videoplayback' in f['url']
    ]

    # Video formats
    video_formats = [
        {
            'format_id': f.get('format_id'),
            'height': f.get('height'),
            'width': f.get('width'),
            'fps': f.get('fps'),
            'ext': f.get('ext'),
            'filesize_bytes': get_size_bytes(f),
            'filesize': format_size(get_size_bytes(f)),
            'url': f.get('url')
        }
        for f in info.get('formats', [])
        if f.get('vcodec') != 'none' and f.get('url') and 'videoplayback' in f['url']
    ]

    # Suggestions (related videos)
    suggestions = []
    if 'related' in info:
        for entry in info['related']:
            suggestions.append({
                'id': entry.get('id'),
                'title': entry.get('title'),
                'url': f"https://www.youtube.com/watch?v={entry.get('id')}" if entry.get('id') else None,
                'thumbnail': entry.get('thumbnails')[0]['url'] if entry.get('thumbnails') else None
            })

    # Final response
    result = {
        'title': info.get('title'),
        'video_url': f"https://www.youtube.com/watch?v={info.get('id')}" if info.get('id') else None,
        'duration': info.get('duration'),
        'upload_date': info.get('upload_date'),
        'view_count': info.get('view_count'),
        'like_count': info.get('like_count'),
        'thumbnail': info.get('thumbnail'),
        'description': info.get('description'),
        'tags': info.get('tags'),
        'is_live': info.get('is_live'),
        'age_limit': info.get('age_limit'),
        'average_rating': info.get('average_rating'),
        'channel': {
            'name': info.get('uploader'),
            'url': f"https://www.youtube.com/channel/{info.get('channel_id')}" if info.get('channel_id') else None,
            'id': info.get('uploader_id')
        },
        'audio_formats': audio_formats,
        'video_formats': video_formats,
        'suggestions': suggestions
    }

    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
