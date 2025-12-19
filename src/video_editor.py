import os
from typing import List, Dict
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np

class VideoEditor:
    def __init__(self):
        # Default shorts resolution
        self.width = 1080
        self.height = 1920

    def create_caption_clip(self, text, duration, start_time):
        """
        Creates a moviepy clip for a short burst of text (2 words).
        Style: Big, Bold, Yellow/White with Black Outline.
        """
        # Canvas size - Increased height for safety
        img = Image.new('RGBA', (self.width, 500), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Load Font - Try Arial Bold for that "YouTuber" look
        fontsize = 150 # Increased for "Big Fonts" request
        font_name = "arialbd.ttf"
        try:
            font = ImageFont.truetype(font_name, fontsize)
        except:
            try:
                font_name = "arial.ttf"
                font = ImageFont.truetype(font_name, fontsize)
            except:
                font = ImageFont.load_default()
                
        # --- Shrink to Fit Logic ---
        # Max width with padding (90% of screen)
        max_width = self.width * 0.9
        
        # We need to measure text. Pillow's getlength is useful.
        # If unavailable, we catch error and skip (fallback).
        try:
            while fontsize > 50:
                length = draw.textlength(text, font=font)
                if length > max_width:
                    fontsize -= 5
                    font = ImageFont.truetype(font_name, fontsize)
                else:
                    break
        except Exception as e:
            print(f"Warning: Could not resize text: {e}")

        # Text Handling
        # Center position
        w, h = img.size
        
        # Draw Outline (Stroke)
        stroke_width = int(fontsize / 15) # Dynamic stroke
        x, y = w / 2, h / 2
        
        # Draw black outline by drawing text in black at multiple offsets
        for adj_x in range(-stroke_width, stroke_width+1):
            for adj_y in range(-stroke_width, stroke_width+1):
                 draw.text((x+adj_x, y+adj_y), text, font=font, fill='black', anchor='mm')
        
        # Draw Main Text (Yellow)
        text_color = '#FFD700' # Gold/Yellow
        
        draw.text((x, y), text, font=font, fill=text_color, anchor='mm')
        
        # Convert to clip
        img_np = np.array(img)
        clip = ImageClip(img_np, duration=duration)
        clip = clip.set_position(('center', 1100)).set_start(start_time) # Raised position slightly
        return clip

    def create_video(self, segments: List[Dict], image_paths: List[str], audio_paths: List[str], output_file: str):
        """
        Assembles the video via Concatenation (Safer for audio).
        """
        print(f"Assembling video with {len(segments)} segments...")
        segment_clips = []
        
        for i, segment in enumerate(segments):
            if i >= len(image_paths) or i >= len(audio_paths):
                break
                
            # Load Audio
            audio_clip = AudioFileClip(audio_paths[i])
            duration = audio_clip.duration
            
            # Load Image
            img_clip = ImageClip(image_paths[i])
            
            # Crop/Resize Logic
            img_w, img_h = img_clip.size
            target_ratio = self.width / self.height
            current_ratio = img_w / img_h
            
            if current_ratio > target_ratio:
                 new_width = int(img_h * target_ratio)
                 center_x = img_w // 2
                 img_clip = img_clip.crop(x1=center_x - new_width//2, width=new_width, height=img_h)
            else:
                 new_height = int(img_w / target_ratio)
                 center_y = img_h // 2
                 img_clip = img_clip.crop(y1=center_y - new_height//2, width=img_w, height=new_height)
                 
            img_clip = img_clip.resize(newsize=(self.width, self.height))
            img_clip = img_clip.set_duration(duration)
            img_clip = img_clip.set_audio(audio_clip)
            
            # --- Dynamic Captions (Per Segment) ---
            full_text = segment.get('text', '')
            words = full_text.split()
            
            # Group words into chunks of 2
            chunk_size = 2
            chunks = [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
            
            txt_clips = []
            if chunks:
                time_per_chunk = duration / len(chunks)
                
                for idx, chunk in enumerate(chunks):
                    # Relative start time for this segment (starts at 0)
                    start = idx * time_per_chunk
                    txt_clip = self.create_caption_clip(chunk.upper(), time_per_chunk, start)
                    txt_clips.append(txt_clip)
            
            # Compose this segment (Image + Audio + Text Overlays)
            # The base clip is img_clip. The text clips overlay on top.
            segment_composite = CompositeVideoClip([img_clip] + txt_clips).set_duration(duration)
            segment_clips.append(segment_composite)
            
        # Concatenate all segments sequentially
        final_video = concatenate_videoclips(segment_clips, method="compose")
        try:
            final_video.write_videofile(output_file, fps=24, codec='libx264', audio_codec='aac')
        finally:
            # Cleanup to prevent file locks
            final_video.close()
            for clip in segment_clips:
                clip.close()
        
        print(f"Video saved to {output_file}")
