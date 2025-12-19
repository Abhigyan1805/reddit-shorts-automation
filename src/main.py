import os
import json
import argparse
from dotenv import load_dotenv
from content_engine import ContentEngine
from media_gen import MediaGen
from video_editor import VideoEditor

import re
import shutil

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).replace(" ", "_").lower()

def setup_directories(base_dir):
    if os.path.exists(base_dir):
        # Optional: cleanup or just warn?
        # For a clean run, let's remove it if it exists to strictly avoid overlapping media from same topic re-runs
        shutil.rmtree(base_dir)
    os.makedirs(f"{base_dir}/images", exist_ok=True)
    os.makedirs(f"{base_dir}/audio", exist_ok=True)

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Shorts Automation")
    parser.add_argument("--topic", type=str, help="Topic for the short", required=False)
    parser.add_argument("--upload", action="store_true", help="Upload to YouTube after generation")
    parser.add_argument("--test", action="store_true", help="Generate only 1 segment for testing")
    args = parser.parse_args()
    
    topic = args.topic or input("Enter a topic for the Short: ")
    safe_topic = sanitize_filename(topic)
    run_dir = f"output/{safe_topic}"
    
    print(f"--- Initializing Engines (Run Dir: {run_dir}) ---")
    content_engine = ContentEngine()
    media_gen = MediaGen()
    editor = VideoEditor()
    
    setup_directories(run_dir)
    
    # 1. Generate Script
    print("\n--- Step 1: Generating Script ---")
    script_data = content_engine.generate_script(topic)
    if not script_data:
        print("Failed to generate script. Exiting.")
        return

    print(f"Title: {script_data.get('title')}")
    with open(f"{run_dir}/script.json", "w") as f:
        json.dump(script_data, f, indent=2)
        
    # 2. Generate Media
    print("\n--- Step 2: Generating Media (Parallel) ---")
    
    segments = script_data.get("script_segments", [])
    if args.test and segments:
        print("TEST MODE: Processing only the first segment.")
        segments = segments[:1]
        
    image_paths = [f"{run_dir}/images/segment_{i}.png" for i in range(len(segments))]
    audio_paths = [f"{run_dir}/audio/segment_{i}.mp3" for i in range(len(segments))]
    
    import concurrent.futures
    
    def process_segment_media(idx, segment):
        # Image
        img_path = image_paths[idx]
        if not os.path.exists(img_path):
            try:
                media_gen.generate_image(segment['visual_prompt'], img_path)
            except Exception as e:
                print(f"Error generating image {idx}: {e}")

        # Audio
        audio_path = audio_paths[idx]
        if not os.path.exists(audio_path):
            try:
                media_gen.generate_audio(segment['text'], audio_path)
            except Exception as e:
                print(f"Error generating audio {idx}: {e}")
                
        print(f"Completed Media for Segment {idx+1}")

    # Use ThreadPool to run I/O bound tasks in parallel
    # We limit to 2 workers to avoid hitting free API rate limits too hard (timeouts)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(process_segment_media, i, seg) for i, seg in enumerate(segments)]
        for future in concurrent.futures.as_completed(futures):
            # Just retrieve result to bubble up exceptions if needed
            try:
                future.result()
            except Exception as e:
                print(f"Thread Error: {e}")
        
    # Check for failures and validate media integrity
    missing_files = []
    for i in range(len(segments)):
        # Check Image Existence
        if not os.path.exists(image_paths[i]): 
            missing_files.append(f"Image {i} (Missing)")
        else:
            # Check Image Integrity
            try:
                with Image.open(image_paths[i]) as img:
                    img.verify()
            except Exception as e:
                print(f"⚠️ Detected corrupt image at segment {i}: {e}")
                missing_files.append(f"Image {i} (Corrupt)")
                try: os.remove(image_paths[i]) # Clean up bad file
                except: pass

        # Check Audio Existence (EdgeTTS usually reliable but good to check size)
        if not os.path.exists(audio_paths[i]): 
            missing_files.append(f"Audio {i} (Missing)")
        elif os.path.getsize(audio_paths[i]) == 0:
             missing_files.append(f"Audio {i} (Empty)")
        
    if missing_files:
        raise Exception(f"Critical Media Generation Failure. Missing/Corrupt: {missing_files}")

    # 3. Create Video
    print("\n--- Step 3: Editing Video ---")
    output_video = f"{run_dir}/final_{safe_topic}.mp4"
    
    # Filter out missing media
    valid_segments = []
    valid_imgs = []
    valid_audios = []
    
    for i in range(len(segments)):
        if os.path.exists(image_paths[i]) and os.path.exists(audio_paths[i]):
            valid_segments.append(segments[i])
            valid_imgs.append(image_paths[i])
            valid_audios.append(audio_paths[i])
        else:
            print(f"Skipping segment {i} due to missing media.")
            
    if valid_segments:
        editor.create_video(valid_segments, valid_imgs, valid_audios, output_video)
        print(f"\nSUCCESS! Video generated at: {os.path.abspath(output_video)}")
        
        # 4. Upload (Optional)
        if args.upload:
            print("\n--- Step 4: Uploading to YouTube ---")
            from uploader import YouTubeUploader
            uploader = YouTubeUploader()
            
            # Construct metadata
            title = script_data.get("title", f"AI Generated Short - {topic}")
            description = f"Short about {topic}\n\nTags: {', '.join(script_data.get('keywords', []))}\n#shorts"
            tags = script_data.get("keywords", [])
            
            uploader.upload_video(output_video, title=title, description=description, tags=tags)
            
    else:
        print("No valid segments to create video.")

if __name__ == "__main__":
    main()
