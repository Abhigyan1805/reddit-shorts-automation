import os
import random
from reddit_client import RedditClient
from tts_engine import TTSEngine
from video_editor import VideoEditor
import shutil

class RedditShortsMaker:
    def __init__(self):
        self.reddit = RedditClient()
        self.tts = TTSEngine(output_dir="temp_assets")
        self.editor = VideoEditor()
        self.assets_dir = os.path.join(os.getcwd(), "assets", "gameplay")
        self.output_dir = "output_reddit"
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.assets_dir, exist_ok=True)

    def run(self, subreddit="AskReddit", ignore_ids=None):
        if ignore_ids is None: ignore_ids = []
        
        # 1. Get Content
        print(f"🔍 Fetching viral thread from r/{subreddit}...")
        post = self.reddit.get_viral_thread(subreddit, limit=30, ignore_ids=ignore_ids) # Increased limit for batch
        if not post:
            print("❌ No suitable threads found.")
            return None

        print(f"✅ Found Thread: {post['title']}")
        
        # 2. Generate Audio
        print("🎙️ Generating Voiceover...")
        segments = []
        audio_paths = []
        image_paths = [] # We use black/transparent images or just reuse background logic

        # Title
        title_audio = self.tts.run_generate(post['title'], "title.mp3")
        segments.append({'text': post['title']})
        audio_paths.append(title_audio)

        # Body (if exists)
        if post['body']:
            # Split body if too long
            body_text = post['body'][:500] 
            body_audio = self.tts.run_generate(body_text, "body.mp3")
            segments.append({'text': body_text})
            audio_paths.append(body_audio)

        # Comments
        for i, comment in enumerate(post['comments']):
            comment_audio = self.tts.run_generate(comment, f"comment_{i}.mp3")
            segments.append({'text': comment})
            audio_paths.append(comment_audio)

        # 3. Background Video
        bg_video = self._get_random_gameplay()
        if not bg_video:
            print("❌ No gameplay video found in 'assets/gameplay'. Please add one!")
            return

        # 4. Assemble
        # We need to adapt the VideoEditor to accept a SINGLE video file and overlay audio/text
        # The existing VideoEditor expects list of IMAGES. We need to modify it or create a new method.
        # Let's use a new method specifically for Reddit Shorts style.
        
        # Sanitize title for filename
        safe_title = "".join([c for c in post['title'] if c.isalnum() or c in (' ', '-', '_')]).strip()
        safe_title = safe_title.replace(" ", "_")[:50] # Limit length
        
        output_filename = os.path.join(self.output_dir, f"{safe_title}.mp4")
        self._assemble_reddit_video(bg_video, audio_paths, segments, output_filename)
        return post['id']

    def _get_random_gameplay(self):
        files = [f for f in os.listdir(self.assets_dir) if f.endswith(('.mp4', '.mkv'))]
        if not files: return None
        return os.path.join(self.assets_dir, random.choice(files))

    def _assemble_reddit_video(self, video_path, audio_paths, segments, output_path):
        from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips, CompositeVideoClip, TextClip
        from moviepy.video.tools.subtitles import SubtitlesClip
        
        print("🎬 Assembling Video...")
        
        # 1. Pre-render combined audio to avoid mixing hangs
        print("   - Mixing Audio...")
        audios = [AudioFileClip(p) for p in audio_paths]
        final_audio_mem = concatenate_audioclips(audios)
        
        temp_audio_path = os.path.join(self.output_dir, "temp_combined_audio.mp3")
        final_audio_mem.write_audiofile(temp_audio_path, bitrate="192k")
        
        # Reload as single file
        final_audio = AudioFileClip(temp_audio_path)
        total_duration = final_audio.duration
        
        # 2. Load Video and Loop/Cut
        print("   - Preparing Video...")
        video = VideoFileClip(video_path)
        if video.duration < total_duration:
            # Loop video if too short
            video = video.loop(duration=total_duration)
        else:
            # Pick random start point
            max_start = video.duration - total_duration
            start = random.uniform(0, max_start)
            video = video.subclip(start, start + total_duration)
            
        video = video.resize(height=1920) # Ensure vertical 9:16 roughly
        video = video.crop(x1=video.w//2 - 540, width=1080, height=1920)
        video = video.set_audio(final_audio)

        # 3. Generate Subtitles
        print("   - Generating Subtitles...")
        clips = [video]
        current_time = 0
        
        # We need the original durations for timing, which we can get from the audios list before we close them
        # Re-using 'audios' list for duration reference is fine
        
        for i, segment in enumerate(segments):
            text = segment['text']
            duration = audios[i].duration 
            
            # Create chunked captions (2-3 words max)
            words = text.split()
            if not words:
                current_time += duration
                continue
            
            chunk_size = 2 # User requested 2-3 words. 2 is safer for "Big Fonts"
            chunks = [' '.join(words[j:j+chunk_size]) for j in range(0, len(words), chunk_size)]
            
            if not chunks: 
                 current_time += duration
                 continue

            time_per_chunk = duration / len(chunks)
            
            for chunk_idx, chunk in enumerate(chunks):
                chunk_start = current_time + (chunk_idx * time_per_chunk)
                txt_clip = self.editor.create_caption_clip(chunk.upper(), time_per_chunk, chunk_start)
                if txt_clip:
                    clips.append(txt_clip)
            
            current_time += duration
            audios[i].close() # Cleanup original handles

        # 4. Write Final Video
        print("   - Rendering Final Output...")
        final = CompositeVideoClip(clips)
        # Using ultra-fast preset and threads
        final.write_videofile(
            output_path, 
            fps=24, 
            codec='libx264', 
            audio_codec='aac', 
            preset='ultrafast', 
            threads=4,
            logger='bar'
        )
        
        final.close()
        final_audio.close()
        video.close()
        # Clean up temp audio
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
            
        print(f"✨ Video Created: {output_path}")

if __name__ == "__main__":
    bot = RedditShortsMaker()
    
    # List of text-heavy subreddits good for shorts
    subreddits = [
        "AskReddit", 
        "NoStupidQuestions", 
        "Showerthoughts", 
        "confessions", 
        "TrueOffMyChest", 
        "explainlikeimfive",
        "AmItheAsshole"
    ]
    selected_sub = random.choice(subreddits)
    
    bot.run(selected_sub)
