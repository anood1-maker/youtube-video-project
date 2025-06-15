import yt_dlp
import speech_recognition as sr
from pydub import AudioSegment
import pandas as pd
import os
import tempfile
from googleapiclient.discovery import build
import re
import json

class YouTubeArabicProcessor:
    def __init__(self, youtube_api_key=None):
        self.youtube_api_key = youtube_api_key
        self.recognizer = sr.Recognizer()
        
    def extract_video_id(self, url):
        """Extract video ID from YouTube URL"""
        video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
        if video_id_match:
            return video_id_match.group(1)
        return None
    
    def download_audio(self, youtube_url, output_path):
        """Download audio from YouTube video"""
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            title = info.get('title', 'Unknown')
            audio_file = os.path.join(output_path, f"{title}.wav")
            return audio_file, title
    
    def transcribe_audio_chunks(self, audio_file, chunk_duration=30):
        """Transcribe audio in chunks for better accuracy"""
        audio = AudioSegment.from_wav(audio_file)
        chunks = []
        
        # Split audio into chunks
        chunk_length_ms = chunk_duration * 1000
        for i in range(0, len(audio), chunk_length_ms):
            chunk = audio[i:i + chunk_length_ms]
            chunks.append(chunk)
        
        transcriptions = []
        
        for i, chunk in enumerate(chunks):
            try:
                # Export chunk to temporary file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    chunk.export(temp_file.name, format="wav")
                    
                    # Transcribe chunk
                    with sr.AudioFile(temp_file.name) as source:
                        audio_data = self.recognizer.record(source)
                        try:
                            # Use Google's speech recognition for Arabic
                            text = self.recognizer.recognize_google(audio_data, language='ar-SA')
                            start_time = i * chunk_duration
                            end_time = min((i + 1) * chunk_duration, len(audio) / 1000)
                            
                            transcriptions.append({
                                'start_time': start_time,
                                'end_time': end_time,
                                'text': text
                            })
                            print(f"Chunk {i+1}/{len(chunks)} transcribed successfully")
                        except sr.UnknownValueError:
                            print(f"Could not understand audio in chunk {i+1}")
                        except sr.RequestError as e:
                            print(f"Error with speech recognition service for chunk {i+1}: {e}")
                    
                    # Clean up temporary file
                    os.unlink(temp_file.name)
                    
            except Exception as e:
                print(f"Error processing chunk {i+1}: {e}")
        
        return transcriptions
    
    def get_video_comments(self, video_id, max_results=100):
        """Get comments from YouTube video using YouTube API"""
        if not self.youtube_api_key:
            print("YouTube API key not provided. Cannot fetch comments.")
            return []
        
        try:
            youtube = build('youtube', 'v3', developerKey=self.youtube_api_key)
            
            comments = []
            next_page_token = None
            
            while len(comments) < max_results:
                request = youtube.commentThreads().list(
                    part='snippet',
                    videoId=video_id,
                    maxResults=min(100, max_results - len(comments)),
                    pageToken=next_page_token,
                    order='relevance'
                )
                
                response = request.execute()
                
                for item in response['items']:
                    comment = item['snippet']['topLevelComment']['snippet']
                    comments.append({
                        'author': comment['authorDisplayName'],
                        'comment': comment['textOriginal'],
                        'likes': comment['likeCount'],
                        'published_at': comment['publishedAt']
                    })
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            
            return comments
            
        except Exception as e:
            print(f"Error fetching comments: {e}")
            return []
    
    def save_to_csv(self, data, filename, columns):
        """Save data to CSV file"""
        df = pd.DataFrame(data)
        if not df.empty:
            df = df[columns] if columns else df
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"Data saved to {filename}")
    
    def process_video(self, youtube_url, output_dir="output"):
        """Main function to process YouTube video"""
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract video ID
        video_id = self.extract_video_id(youtube_url)
        if not video_id:
            print("Invalid YouTube URL")
            return
        
        print(f"Processing video ID: {video_id}")
        
        try:
            # Download audio
            print("Downloading audio...")
            audio_file, title = self.download_audio(youtube_url, output_dir)
            print(f"Audio downloaded: {title}")
            
            # Transcribe audio
            print("Transcribing audio...")
            transcriptions = self.transcribe_audio_chunks(audio_file)
            
            # Save transcriptions to CSV
            transcription_filename = os.path.join(output_dir, f"{title}_transcription.csv")
            self.save_to_csv(
                transcriptions, 
                transcription_filename,
                ['start_time', 'end_time', 'text']
            )
            
            # Get comments
            print("Fetching comments...")
            comments = self.get_video_comments(video_id)
            
            # Save comments to CSV
            comments_filename = os.path.join(output_dir, f"{title}_comments.csv")
            self.save_to_csv(
                comments, 
                comments_filename,
                ['author', 'comment', 'likes', 'published_at']
            )
            
            # Clean up audio file
            if os.path.exists(audio_file):
                os.remove(audio_file)
            
            print("Processing completed successfully!")
            print(f"Files created:")
            print(f"- Transcription: {transcription_filename}")
            print(f"- Comments: {comments_filename}")
            
        except Exception as e:
            print(f"Error processing video: {e}")

def main():
    # You can set your YouTube API key here or as an environment variable
    youtube_api_key = os.environ.get('YOUTUBE_API_KEY')
    
    processor = YouTubeArabicProcessor(youtube_api_key)
    
    # Get YouTube URL from user
    youtube_url = input("Enter the YouTube video URL: ")
    
    if not youtube_url:
        print("Please provide a valid YouTube URL")
        return
    
    # Process the video
    processor.process_video(youtube_url)

if __name__ == "__main__":
    main()
