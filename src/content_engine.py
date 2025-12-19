import os
import json
import requests
import urllib.parse
from typing import Dict, List, Optional

class ContentEngine:
    def __init__(self, api_key: Optional[str] = None):
        # Pollinations.ai is free, no key needed
        pass

    def generate_script(self, topic: str) -> Dict:
        """
        Generates a script for a YouTube Short via Pollinations.ai (Free).
        Returns a dictionary with title, script_segments, and keywords.
        """
        print(f"Generating script for topic: {topic}...")
        
        # We need to be very explicit about JSON for Pollinations/OpenAI-compat models
        system_instruction = "You are a helpful assistant that outputs ONLY valid JSON."
        # Viral Shorts Structure Prompt
        prompt = f"""
        You are a YouTube Shorts Master Scriptwriter. Your goal is to write a script for "{topic}" that goes VIRAL.
        
        STRICTLY OUTPUT VALID JSON ONLY. NO MARKDOWN. NO COMMENTS.
        
        Guidelines:
        1. **The Hook (0-3s)**: The first segment MUST be a strong visual and verbal hook. Shocking, controversial, or extremely curious.
        2. **Pacing**: Fast-paced. No filler words.
        3. **Tone**: Energetic, storytelling, factual but dramatic.
        4. **Visuals**: PROMPTS MUST BE PHOTOREALISTIC. Use keywords like: "Cinematic 4k", "Hyper-realistic", "Dramatic Lighting", "Unreal Engine 5 Render". Avoid "cartoon" or "illustration" unless specified.
        
        Structure:
        {{
            "title": "Clickbait Title (under 50 chars)",
            "script_segments": [
                {{
                    "text": "Hook sentence here. (Keep it punchy)",
                    "visual_prompt": "Hyper-realistic close-up of [Subject], dramatic rim lighting, 8k resolution, cinematic depth of field"
                }},
                {{
                    "text": "Body content... fast facts... story progression",
                    "visual_prompt": "Wide shot, action-filled, [Scene Description], 8k render"
                }},
                ... (aim for 5-7 segments total for 60s)
            ],
            "keywords": ["tag1", "#shorts", "viral"]
        }}
        """
        
        # Pollinations text API: https://text.pollinations.ai/{prompt}?model=openai
        # We combine system and user prompt for better adherence
        full_prompt = f"{system_instruction}\n\n{prompt}"
        safe_prompt = urllib.parse.quote(full_prompt)
        url = f"https://text.pollinations.ai/{safe_prompt}?model=openai" 
        
        for attempt in range(3):
            try:
                response = requests.get(url, timeout=90) # Increased timeout
                if response.status_code != 200:
                    print(f"Error: API returned status {response.status_code}. Retrying...")
                    time.sleep(2)
                    continue
                    
                text = response.text.strip()
                data = self._clean_and_parse_json(text)
                if data:
                    return data
            except Exception as e:
                print(f"Error generating script (Attempt {attempt+1}): {e}")
                time.sleep(2)
                
        return {}

    def generate_viral_topics(self, category: str, count: int = 5) -> List[str]:
        """
        Asks the AI to brainstorm viral topics for a given category.
        """
        print(f"🧠 Brainstorming {count} viral topics for category: {category}...")
        prompt = f"""
        List {count} highly viral, clickbaity YouTube Shorts topics about "{category}".
        Output strictly a JSON list of strings. No markdown.
        Example: ["The Day AI Took Over", "Why Mars is a Trap"]
        """
        
        full_prompt = f"You are a viral content strategist. Output ONLY valid JSON.\n\n{prompt}"
        safe_prompt = urllib.parse.quote(full_prompt)
        url = f"https://text.pollinations.ai/{safe_prompt}?model=openai"
        
        for attempt in range(3):
            try:
                response = requests.get(url, timeout=60)
                text = response.text.strip()
                data = self._clean_and_parse_json(text)
                if isinstance(data, list):
                    return data
            except Exception as e:
                print(f"Error generating topics: {e}")
                
        return []

    def _clean_and_parse_json(self, text: str):
        """
        Robustly extracts and parses JSON from potentially dirty AI output.
        """
        try:
            # 1. Try direct parse
            return json.loads(text)
        except:
            pass
            
        try:
            # 2. Extract code block
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            
            # 3. Aggressive finding of { } or [ ]
            text = text.strip()
            if not (text.startswith("{") or text.startswith("[")):
                # Try to find first bracket
                start_curly = text.find("{")
                start_square = text.find("[")
                
                if start_curly != -1 and (start_square == -1 or start_curly < start_square):
                    text = text[start_curly:]
                    end = text.rfind("}")
                    if end != -1: text = text[:end+1]
                elif start_square != -1:
                    text = text[start_square:]
                    end = text.rfind("]")
                    if end != -1: text = text[:end+1]
            
            return json.loads(text)
        except Exception as e:
             # print(f"JSON Parse Error: {e}\nText: {text[:100]}...")
             return None
