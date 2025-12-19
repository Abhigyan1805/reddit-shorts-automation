# 🎬 Reddit Shorts Automation

A fully automated Python tool that creates viral "Reddit Shorts" style videos. It scrapes popular threads, generates AI voiceovers, and overlays them onto gameplay footage with dynamic subtitles.

## ✨ Features

- **Automated Content Sourcing**: Scrapes threads from `r/AskReddit`, `r/Showerthoughts`, `r/NoStupidQuestions`, and more.
- **Smart Filtering**: Avoids sticky posts, videos, and duplicates.
- **AI Voiceover**: Uses `edge-tts` for high-quality, TikTok-style speech.
- **Dynamic Video Editing**:
  - Overlays audio on random Minecraft/gameplay clips.
  - Generates synchronized chunked subtitles (2-3 words).
  - "Big Font" styling (YouTuber style).
- **Batch Mode**: Can generate 20+ videos in a single run.

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/shorts-automation.git
   cd shorts-automation
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup Environment Variables**
   Create a `.env` file (copy from `.env.example`) and add your Reddit API keys (optional but recommended):
   ```
   REDDIT_CLIENT_ID=your_id
   REDDIT_CLIENT_SECRET=your_secret
   REDDIT_USER_AGENT=your_agent
   ```
   *Note: The script works without keys using the public JSON API, but more slowly.*

4. **Add Gameplay Footage**
   Place your `.mp4` background videos in:
   `assets/gameplay/`

## 🚀 Usage

### Generate a Single Video
```bash
python src/main_reddit.py
```
This will create a video in `output_reddit/` based on a random viral thread.

### Generate a Batch (The "Farm")
```bash
python src/batch_generate.py
```
This generates 20 unique videos in a sequence, handling rate limits and duplicate checks.

## 📂 Project Structure

- `src/main_reddit.py`: Main entry point for single generation.
- `src/batch_generate.py`: Script for bulk generation.
- `src/reddit_client.py`: Handles Reddit scraping (PRAW + JSON fallback).
- `src/video_editor.py`: MoviePy logic for composition and subtitles.
- `src/tts_engine.py`: Text-to-Speech wrapper.

## 🤝 Contributing

Feel free to open issues or submit PRs if you want to add more features like different background types or new subtitle styles!
