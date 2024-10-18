from flask import Flask, jsonify, request, session
import requests
import yt_dlp
from collections import deque
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a strong secret key
CORS(app)  # Enable CORS for all routes

YOUTUBE_API_KEY = 'AIzaSyAoPxOO-JRJEl7Q_86MZkQViqdHAQ0ZdBw'
YOUTUBE_SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search'
recent_searches = deque(maxlen=5)  # Store last 5 searches

@app.route('/')
def index():
    with open('index.html', 'r') as f:
        return f.read()

# Search YouTube for songs
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if query:
        params = {
            'part': 'snippet',
            'q': query,
            'key': YOUTUBE_API_KEY,
            'type': 'video',
            'maxResults': 5,
            'regionCode': 'US'
        }
        response = requests.get(YOUTUBE_SEARCH_URL, params=params)
        results = response.json().get('items', [])
        songs = []

        for result in results:
            video_id = result['id']['videoId']
            title = result['snippet']['title']
            thumbnail = result['snippet']['thumbnails']['default']['url']
            description = result['snippet']['description']
            songs.append({
                'title': title,
                'videoId': video_id,
                'thumbnail': thumbnail,
                'description': description
            })

        # Add the search query to recent searches
        recent_searches.append(query)

        return jsonify({
            'songs': songs,
            'recent_searches': list(recent_searches)
        })
    return jsonify({'songs': [], 'recent_searches': []})

# Stream song using yt-dlp
@app.route('/play', methods=['GET'])
def play():
    video_id = request.args.get('videoId')
    if video_id:
        url = f'https://www.youtube.com/watch?v={video_id}'
        ydl_opts = {
            'format': 'bestaudio',
            'noplaylist': True,
            'quiet': True,
            'nocheckcertificate': True,
            'extract_flat': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                audio_url = info.get('url')
                duration = info.get('duration')  # Get song duration in seconds
                return jsonify({
                    'stream_url': audio_url,
                    'duration': duration  # Return duration
                })
            except Exception as e:
                return jsonify({'error': f'Failed to retrieve audio stream: {str(e)}'}), 500

    return jsonify({'error': 'Invalid video ID'}), 400

@app.route('/favorites', methods=['POST'])
def add_favorite():
    video_id = request.json.get('videoId')
    if 'favorites' not in session:
        session['favorites'] = []  # Initialize favorites in the session
    if video_id and video_id not in session['favorites']:
        session['favorites'].append(video_id)  # Add to favorites
        session.modified = True  # Mark session as modified
        return jsonify({'message': 'Added to favorites'}), 200
    return jsonify({'error': 'Invalid video ID or already in favorites'}), 400

@app.route('/favorites', methods=['GET'])
def list_favorites():
    if 'favorites' in session:
        favorite_songs = []
        for video_id in session['favorites']:
            url = f'https://www.youtube.com/watch?v={video_id}'
            ydl_opts = {
                'format': 'bestaudio',
                'noplaylist': True,
                'quiet': True,
                'nocheckcertificate': True,
                'extract_flat': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title')
                thumbnail = info.get('thumbnail')
                favorite_songs.append({'title': title, 'videoId': video_id, 'thumbnail': thumbnail})

        return jsonify(favorite_songs)
    return jsonify([])  # Return empty if no favorites

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)  # Replit uses port 3000
