import asyncio
import edge_tts
from typing import Optional
import time
import os
from dotenv import load_dotenv

load_dotenv()

class MediaGen:
    def __init__(self):
        # No API keys needed for these free tools!
        pass

    def generate_image(self, prompt: str, output_path: str):
        """
        Generates an image via Pollinations.ai (Free) and saves to output_path.
        """
        print(f"Generating image for prompt: {prompt[:50]}...")
        try:
            # Pollinations.ai URL format: https://image.pollinations.ai/prompt/{prompt}
            # Enhance prompt with quality boosters
            enhanced_prompt = f"{prompt}, cinematic lighting, award winning photography, 8k, highly detailed, photorealistic"
            safe_prompt = requests.utils.quote(enhanced_prompt)
            image_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1080&height=1920&model=flux&nologo=true"
            
            for attempt in range(3):
                try:
                     response = requests.get(image_url, timeout=120)
                     if response.status_code == 200:
                         with open(output_path, 'wb') as handler:
                             handler.write(response.content)
                         return # Success
                     else:
                         print(f"Image API Status: {response.status_code}. Retrying...")
                         time.sleep(2)
                except Exception as e:
                     print(f"Image Gen Error (Attempt {attempt+1}): {e}")
                     time.sleep(2)
                     
                     time.sleep(2)
            
            # --- BACKUP: Hugging Face ---
            print("⚠️ Pollinations failed. Attempting Backup (Hugging Face)...")
            if self._generate_image_hf(prompt, output_path):
                print("✅ Backup Successful (Hugging Face)")
                return

            raise Exception("Failed to generate image (All providers failed)")
            
        except Exception as e:
            print(f"Error generating image: {e}")

    def _generate_image_hf(self, prompt: str, output_path: str) -> bool:
        """
        Backup: Generates image using Hugging Face Inference API (SDXL).
        Requires HF_TOKEN in .env
        """
        token = os.getenv("HF_TOKEN")
        if not token:
            print("❌ No HF_TOKEN found in .env. Skipping backup.")
            return False
            
        API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        headers = {"Authorization": f"Bearer {token}"}
        
        # Enhanced prompt for HF too
        payload = {
            "inputs": f"{prompt}, cinematic lighting, 8k, photorealistic",
            "parameters": {"negative_prompt": "blurry, cartoon, illustration, low quality"}
        }

        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return True
            else:
                print(f"HF API Error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"HF Backup Error: {e}")
            return False

    async def _generate_audio_async(self, text: str, output_path: str):
        """
        Async helper for edge-tts
        """
        communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
        await communicate.save(output_path)

    def generate_audio(self, text: str, output_path: str):
        """
        Generates TTS audio via Edge TTS (Free) and saves to output_path.
        """
        print(f"Generating audio for text: {text[:30]}...")
        try:
            asyncio.run(self._generate_audio_async(text, output_path))
        except Exception as e:
            print(f"Error generating audio: {e}")
