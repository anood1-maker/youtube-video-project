
import yt_dlp
import speech_recognition as sr
from pydub import AudioSegment
import pandas as pd
import os
import tempfile
from googleapiclient.discovery import build
import re

class YouTubeArabicProcessor:
    def __init__(self, youtube_api_key=None):
        self.youtube_api_key = youtube_api_key
        self.recognizer = sr.Recognizer()

    def clean_filename(self, name):
        invalid = r'\/:*?"<>|｜'
        return ''.join(c for c in name if c not in invalid)

    def extract_video_id(self, url):
        video_id_match = re.search(r'(?:v=|\\/)([0-9A-Za-z_-]{11})', url)
        if video_id_match:
            return video_id_match.group(1)
        return None

    def download_audio(self, youtube_url, output_path):
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
            raw_title = info.get('title', 'Unknown')
            clean_title = self.clean_filename(raw_title)

            # ابحث عن أول ملف .wav في مجلد الإخراج وأعد تسميته
            for filename in os.listdir(output_path):
                if filename.lower().endswith(".wav"):
                    original_path = os.path.join(output_path, filename)
                    new_path = os.path.join(output_path, f"{clean_title}.wav")
                    os.rename(original_path, new_path)
                    return new_path, clean_title

            print("❌ لم يتم العثور على ملف الصوت بصيغة WAV.")
            return None, clean_title

    def transcribe_audio_chunks(self, audio_file, chunk_duration=30):
        audio = AudioSegment.from_wav(audio_file)
        chunks = []
        chunk_length_ms = chunk_duration * 1000
        for i in range(0, len(audio), chunk_length_ms):
            chunk = audio[i:i + chunk_length_ms]
            chunks.append(chunk)

        transcriptions = []
        for i, chunk in enumerate(chunks):
            try:
                temp_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
                chunk.export(temp_path, format="wav")
                with sr.AudioFile(temp_path) as source:
                    audio_data = self.recognizer.record(source)
                    try:
                        text = self.recognizer.recognize_google(audio_data, language='ar-SA')
                        start_time = i * chunk_duration
                        end_time = min((i + 1) * chunk_duration, len(audio) / 1000)
                        transcriptions.append({
                            'start_time': start_time,
                            'end_time': end_time,
                            'text': text
                        })
                        print(f"✅ تم تفريغ المقطع {i+1} بنجاح")
                    except sr.UnknownValueError:
                        print(f"⚠️ لم يتم فهم الصوت في المقطع {i+1}")
                    except sr.RequestError as e:
                        print(f"❌ خطأ في خدمة التعرف على الصوت: {e}")
                os.unlink(temp_path)
            except Exception as e:
                print(f"❌ خطأ في معالجة المقطع {i+1}: {e}")
        return transcriptions

    def get_video_comments(self, video_id, max_results=100):
        if not self.youtube_api_key:
            print("❌ لم يتم توفير مفتاح YouTube API")
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
            print(f"❌ خطأ أثناء جلب التعليقات: {e}")
            return []

    def save_to_excel(self, data, filename, columns):
        df = pd.DataFrame(data)
        if not df.empty and columns:
            df = df[columns]
        df.to_excel(filename, index=False)
        print(f"💾 تم حفظ البيانات في: {filename}")

    def process_video(self, youtube_url, output_dir="output"):
        os.makedirs(output_dir, exist_ok=True)
        video_id = self.extract_video_id(youtube_url)
        if not video_id:
            print("❌ رابط يوتيوب غير صالح")
            return
        print(f"🎬 جاري معالجة الفيديو ID: {video_id}")
        try:
            print("📥 تحميل الصوت...")
            audio_file, title = self.download_audio(youtube_url, output_dir)
            if audio_file is None:
                print("❌ لم يتم تحميل ملف الصوت بنجاح.")
                return

            print(f"🎵 تم تحميل الصوت: {title}")

            print("📝 تفريغ الصوت إلى نص (عربي)...")
            transcriptions = self.transcribe_audio_chunks(audio_file)
            transcription_filename = os.path.join(output_dir, f"{title}_transcription.xlsx")
            self.save_to_excel(transcriptions, transcription_filename, ['start_time', 'end_time', 'text'])

            print("💬 جلب التعليقات...")
            comments = self.get_video_comments(video_id)
            comments_filename = os.path.join(output_dir, f"{title}_comments.xlsx")
            self.save_to_excel(comments, comments_filename, ['author', 'comment', 'likes', 'published_at'])

            if os.path.exists(audio_file):
                os.remove(audio_file)
            print("✅ تمت المعالجة بنجاح!")
        except Exception as e:
            print(f"❌ فشل المعالجة: {e}")

def main():
    youtube_api_key = "AIzaSyDS9f46i4aKcqUL90cWMNSu5e5ung4BErc"
    youtube_url = "https://www.youtube.com/watch?v=g8w-XMxsLP8"
    processor = YouTubeArabicProcessor(youtube_api_key)
    processor.process_video(youtube_url)

if __name__ == "__main__":
    main()
