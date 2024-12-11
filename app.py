from flask import Flask, render_template, request, Response
from yt_dlp import YoutubeDL
import os
import urllib.parse
import tempfile

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_video():
    try:
        # Get the video URL from the form
        video_url = request.form['url']

        # Options for yt_dlp to stream directly
        ydl_opts = {
            'format': 'best',  # Choose the best video and audio quality
            'noplaylist': True,  # Don't download playlists if the URL is for a playlist
            'outtmpl': 'downloads/%(id)s.%(ext)s',  # Temporary location (can be omitted)
            'cookiefile': None  # Default, if no cookie is provided
        }

        # Pass cookies from the environment variable (if available)
        cookies_content = os.getenv('YOUTUBE_COOKIES')
        if cookies_content:
            # Create a temporary file for cookies
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as cookies_file:
                cookies_file.write(cookies_content)
                ydl_opts['cookiefile'] = cookies_file.name

        with YoutubeDL(ydl_opts) as ydl:
            # Extract video information without downloading to the server
            info = ydl.extract_info(video_url, download=False)
            video_title = info.get('title', 'video')
            file_extension = info.get('ext', 'mp4')
            video_url = info['url']  # The direct URL for the video stream

        # Create a Response object to stream the video to the client
        def generate_video():
            # Now stream the video by using the extracted video URL
            with YoutubeDL(ydl_opts) as ydl:
                video_data = ydl.extract_info(video_url, download=False)
                # Stream the video by fetching the URL of the best stream
                response = ydl.urlopen(video_data['url'])
                for chunk in response:
                    yield chunk

        # URL encode the filename to safely handle special characters
        encoded_filename = urllib.parse.quote(f'{video_title}.{file_extension}')

        return Response(
            generate_video(),
            mimetype=f'video/{file_extension}',
            headers={
                'Content-Disposition': f'attachment; filename="{encoded_filename}"'
            }
        )

    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
