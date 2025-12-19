import asyncio
import edge_tts
import os

class TTSEngine:
    def __init__(self, output_dir="temp_audio"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        # Voices: en-US-ChristopherNeural (Male), en-US-AriaNeural (Female), etc.
        self.voice = "en-US-ChristopherNeural" 

    async def generate_audio(self, text: str, filename: str) -> str:
        """
        Generates audio file from text. Returns absolute path.
        """
        output_path = os.path.join(self.output_dir, filename)
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(output_path)
        return os.path.abspath(output_path)

    def run_generate(self, text: str, filename: str) -> str:
        """
        Synchronous wrapper for the async generate function.
        """
        return asyncio.run(self.generate_audio(text, filename))
