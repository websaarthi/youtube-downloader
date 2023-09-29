from flask import Flask, render_template, request
from pytube import YouTube
import os
from moviepy.editor import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from mutagen.id3 import ID3, APIC

app = Flask(__name__)

# Mapping of quality options to resolution values
QUALITY_OPTIONS = {
    "Auto": "highest",
    "Low": "144p",
    "Medium": "360p",
    "High": "720p",
}

# Function to add album artwork to audio file
def add_album_artwork(audio_file, artwork_path):
    audio = ID3(audio_file)
    
    # Load the album cover image
    with open(artwork_path, 'rb') as album_cover_file:
        album_cover_data = album_cover_file.read()
    
    # Add the album cover as artwork
    audio.add(APIC(3, 'image/jpeg', 3, 'Front cover', album_cover_data))
    
    # Save the updated audio file
    audio.save()

# Function to download a YouTube video or audio based on user's selection
def download_media(url, output_path, selected_quality, download_type):
    try:
        yt = YouTube(url)
        
        if download_type == "audio":
            # Download the audio stream in the best quality available
            stream = yt.streams.filter(only_audio=True, file_extension='mp4').first()
            stream.download(output_path)
            
            # Convert MP4 audio to MP3
            mp4_file = os.path.join(output_path, f"{yt.title}.mp4")
            mp3_file = os.path.join(output_path, f"{yt.title}.mp3")

            try:
                video = VideoFileClip(mp4_file)
                audio = video.audio
                audio.write_audiofile(mp3_file)
                video.close()
                audio.close()
            except Exception as e:
                # If video properties couldn't be accessed, try audio-only conversion
                audio_clip = AudioFileClip(mp4_file)
                audio_clip.write_audiofile(mp3_file)
                audio_clip.close()

            # Remove the original MP4 file
            os.remove(mp4_file)

            # Add album artwork to the audio file
            add_album_artwork(mp3_file, os.path.join(output_path, 'image.jpg'))

        else:
            # Download video stream with the selected quality
            stream = yt.streams.filter(res=QUALITY_OPTIONS.get(selected_quality, "highest")).first()

        if stream:
            stream.download(output_path)
            return True, yt.title  # Return the media title on success
        else:
            return False, "Selected quality not available for this media type."

    except Exception as e:
        return False, f"Error: {e}"

@app.route('/')
def index():
    return render_template('index.html', quality_options=QUALITY_OPTIONS.keys())

@app.route('/download', methods=['POST'])
def download():
    video_url = request.form['video_url']
    selected_quality = request.form['quality']  # Get selected quality from the form
    download_type = request.form['download_type']  # Get selected download type (video or audio)
    output_path = 'C:\\Users\\Akhilesh\\Downloads'  # Update this with your custom directory path

    success, message = download_media(video_url, output_path, selected_quality, download_type)

    if success:
        media_type = "Video" if download_type == "video" else "Audio"
        return f"{media_type} '{message}' downloaded successfully!"
    else:
        return f"{download_type.capitalize()} download failed. {message}"

if __name__ == '__main__':
    app.run(debug=True)
