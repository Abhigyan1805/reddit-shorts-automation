import subprocess
import sys
import time
import os
import re

# Curated Viral Topics (Initial Seed)
TOPICS = [
    # Tech / AI
    "The Dead Internet Theory: Are You Talking to Bots?",
    "2025: The Year Smartphones Die (AI Pins)",
    "Roko's Basilisk: The Most Dangerous Thought Experiment",
    
    # Space / Horror
    "The Dark Forest Theory: Why We Should STOP Looking for Aliens",
    "The Great Attractor: Something is Pulling Our Galaxy",
    "Vacuum Decay: The Universe Could End in a Second",
    
    # History / Mystery
    "The Library of Alexandria: What Did We REALLY Lose?",
    "The Dancing Plague of 1518",
    
    # Paradoxes
    "The Mandela Effect: False Memory or Parallel Universe?",
    "The Ship of Theseus: Am I The Same Person?",
    
    # Nature
    "The Zombie Fungus is Real (Last of Us)"
]

CATEGORIES = [
    "Futuristic Tech & AI dangers",
    "Scary Space Facts",
    "Unsolved Historical Mysteries",
    "Psychological Paradoxes",
    "Crazy Biology Facts",
    "Deep Ocean Mysteries",
    "Simulation Theory",
    "Ancient Civilizations",
    "Future Predictions 2030",
    "Quantum Physics for Dummies"
]

import json
import webbrowser
from datetime import datetime

PROGRESS_FILE = "progress.json"

def update_progress(completed, total, current_topic, status, logs=[]):
    data = {
        "completed": completed,
        "total": total,
        "current_topic": current_topic,
        "status": status,
        "logs": logs
    }
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f)

LOGS = []
def add_log(msg, type="info"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    LOGS.append({"time": timestamp, "message": msg, "type": type})
    # Keep log history manageable
    if len(LOGS) > 50:
        LOGS.pop(0)

def run_farm():
    print(f"🚜 STARTING FARM MODE: Target 50 Videos...")
    
    # Init Progress
    update_progress(0, 50, "Initializing", "Warming up engines...", [])
    
    # Open Dashboard
    dashboard_path = os.path.abspath("frontend/dashboard.html")
    print(f"Opening Dashboard: {dashboard_path}")
    webbrowser.open(f"file://{dashboard_path}")
    
    # Dynamic expansion
    from content_engine import ContentEngine
    engine = ContentEngine()
    
    target_count = 50
    current_count = len(TOPICS)
    
    if current_count < target_count:
        msg = f"📉 Only have {current_count} topics. Generating {target_count - current_count} more..."
        print(msg)
        add_log(msg)
        update_progress(0, target_count, "Brainstorming", "Generating new viral topics...", LOGS)
        
        cat_idx = 0
        while len(TOPICS) < target_count:
            cat = CATEGORIES[cat_idx % len(CATEGORIES)]
            new_topics = engine.generate_viral_topics(cat, count=5)
            for t in new_topics:
                if t not in TOPICS:
                    TOPICS.append(t)
            cat_idx += 1
            time.sleep(2) # rate limit politeness
            
            update_progress(0, target_count, "Brainstorming", f"Topics Found: {len(TOPICS)}/{target_count}", LOGS)
            print(f"   ... Total Topics: {len(TOPICS)}")
            
    # Slice to exact 50 if verified overflow
    final_topics = TOPICS[:target_count]
    
    print("="*60)
    print(f"🚜 CULTIVATING {len(final_topics)} VIDEOS")
    print("="*60)
    
    stats = {"success": 0, "fail": 0}
    
    for i, topic in enumerate(final_topics):
        print(f"\n🌱 [{i+1}/{len(final_topics)}] Planted Topic: {topic}")
        
        # --- RESUME LOGIC ---
        safe_topic = re.sub(r'[\\/*?:"<>|]', "", topic).replace(" ", "_").lower()
        expected_output = f"output/{safe_topic}/final_{safe_topic}.mp4"
        
        if os.path.exists(expected_output):
             msg = f"⏭️ Skipping '{topic}': Video already exists at {expected_output}"
             print(msg)
             add_log(msg, "info")
             update_progress(i + 1, target_count, topic, "Skipped (Exists)", LOGS)
             stats["success"] += 1 # Count as success for progress bar
             continue
        # --------------------

        add_log(f"Starting: {topic}")
        update_progress(i, target_count, topic, "Generating Video...", LOGS)
        
        print("-" * 30)
        
        start_time = time.time()
        try:
            # Using sys.executable ensures we use the active venv
            cmd = [sys.executable, "src/main.py", "--topic", topic]
            
            # Run usage: subprocess.run(cmd, check=True)
            result = subprocess.run(cmd)
            
            if result.returncode == 0:
                duration = int(time.time() - start_time)
                msg = f"✅ Harvested '{topic}' in {duration}s"
                print(msg)
                add_log(msg, "success")
                stats["success"] += 1
            else:
                msg = f"🥀 Failed '{topic}'"
                print(msg)
                add_log(msg, "error")
                stats["fail"] += 1
                
        except KeyboardInterrupt:
            print("\n🛑 Farm Stopped by User.")
            add_log("Farm stopped by user", "error")
            break
        except Exception as e:
            msg = f"❌ Error: {e}"
            print(msg)
            add_log(msg, "error")
            stats["fail"] += 1
            
        # Update progress after each video
        update_progress(i + 1, target_count, topic, "Cooling down...", LOGS)
            
        # Cool-down to be nice to free APIs
        print("💤 Resting soil (10s)...")
        time.sleep(10)
        
    final_msg = f"🚜 FARM COMPLETE: {stats['success']} Harvested, {stats['fail']} Withered."
    print("\n" + "="*60)
    print(final_msg)
    print("="*60)
    add_log(final_msg, "success")
    update_progress(target_count, target_count, "Done", "Farm Cycle Complete", LOGS)

if __name__ == "__main__":
    run_farm()
