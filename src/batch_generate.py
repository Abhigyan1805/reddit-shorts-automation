from main_reddit import RedditShortsMaker
import random
import time

def batch_generate(count=20):
    bot = RedditShortsMaker()
    used_ids = []
    
    # List of text-heavy subreddits
    subreddits = [
        "AskReddit", "NoStupidQuestions", "Showerthoughts", 
        "confessions", "TrueOffMyChest", "explainlikeimfive", "AmItheAsshole"
    ]
    
    print(f"🚀 Starting Batch Generation of {count} videos...")
    
    for i in range(count):
        print(f"\n=================================")
        print(f"🎬 Generating Video {i+1}/{count}")
        print(f"=================================\n")
        
        selected_sub = random.choice(subreddits)
        
        try:
            # We track used IDs to avoid duplicates in this run
            post_id = bot.run(selected_sub, ignore_ids=used_ids)
            
            if post_id:
                used_ids.append(post_id)
                print(f"✅ Finished Video {i+1}. Sleeping for 5s to cool down...")
            else:
                print(f"⚠️ Failed to generate video {i+1}. Retrying different sub...")
                # Simple retry logic
                selected_sub = random.choice(subreddits)
                post_id = bot.run(selected_sub, ignore_ids=used_ids)
                if post_id: used_ids.append(post_id)
                
            time.sleep(5) # Cool down
            
        except Exception as e:
            print(f"❌ Critical Error in Batch {i+1}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    batch_generate(20)
