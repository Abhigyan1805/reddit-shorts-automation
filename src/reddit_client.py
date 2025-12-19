import praw
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class RedditClient:
    def __init__(self):
        self.client_id = os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = os.getenv("REDDIT_USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.use_praw = False
        if self.client_id and self.client_secret and "your_" not in self.client_id:
            print("✅ Logged in to Reddit API (Authenticated)")
            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )
            self.use_praw = True
        else:
            print("⚠️ access keys missing or default. Switching to Public JSON API (Read-Only).")

    def get_viral_thread(self, subreddit_name: str = "AskReddit", limit: int = 10, ignore_ids: List[str] = []) -> Optional[Dict]:
        """
        Fetches a hot thread. Uses PRAW if available, else requests the JSON URL.
        """
        if self.use_praw:
            return self._get_viral_thread_praw(subreddit_name, limit, ignore_ids)
        else:
            return self._get_viral_thread_json(subreddit_name, limit, ignore_ids)

    def _get_viral_thread_json(self, subreddit_name: str, limit: int, ignore_ids: List[str]) -> Optional[Dict]:
        import requests
        import random
        import time
        
        try:
            url = f"https://www.reddit.com/r/{subreddit_name}/hot.json?limit={limit}"
            headers = {"User-Agent": self.user_agent}
            
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                print(f"Failed to fetch public JSON: {response.status_code}")
                return None
                
            data = response.json()
            posts = data['data']['children']
            
            # Shuffle to get different results each run
            random.shuffle(posts)
            
            for post in posts:
                post_data = post['data']
                if post_data.get('stickied') or post_data.get('is_video'):
                    continue
                
                if post_data['id'] in ignore_ids:
                    print(f"Skipping used thread: {post_data['id']}")
                    continue
                    
                # Need comments - this only gives us the post. We need a specific call for comments.
                # public URL for post: https://www.reddit.com{permalink}.json
                if post_data['num_comments'] < 10:
                    continue
                    
                print(f"Inspecting thread: {post_data['title'][:50]}...")
                
                # Fetch comments
                try:
                    permalink = post_data['permalink']
                    comments_url = f"https://www.reddit.com{permalink}.json?sort=top"
                    time.sleep(1) # Be polite to public API
                    c_resp = requests.get(comments_url, headers=headers)
                    if c_resp.status_code != 200: continue
                    
                    c_data = c_resp.json()
                    # c_data is list: [0] is post object, [1] is comments listing
                    comments_list = c_data[1]['data']['children']
                    
                    top_comments = []
                    for comment in comments_list[:5]:
                        c_body = comment['data'].get('body')
                        if c_body and c_body != "[removed]" and len(c_body) < 300:
                            top_comments.append(c_body)
                    
                    if not top_comments:
                        continue
                        
                    return {
                        "title": post_data['title'],
                        "body": post_data.get('selftext', '')[:1000],
                        "comments": top_comments,
                        "url": post_data['url'],
                        "id": post_data['id']
                    }
                    
                except Exception as e:
                    print(f"Error fetching comments for thread: {e}")
                    continue
                    
            return None
        except Exception as e:
            print(f"Error in JSON fallback: {e}")
            return None

    def _get_viral_thread_praw(self, subreddit_name: str, limit: int, ignore_ids: List[str]) -> Optional[Dict]:
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            # Fetch hot posts
            threads = subreddit.hot(limit=limit)
             
            for submission in threads:
                if submission.stickied:
                    continue

                if submission.id in ignore_ids:
                    print(f"Skipping used thread: {submission.id}")
                    continue
                 
                if submission.num_comments < 10:
                    continue
 
                # Load comments
                submission.comments.replace_more(limit=0) # Remove "load more comments"
                top_comments = []
                 
                for comment in submission.comments[:3]: # Top 3 comments
                    if comment.body == "[removed]" or len(comment.body) > 300: 
                        continue
                    top_comments.append(comment.body)
                 
                if not top_comments:
                    continue
                
                return {
                    "title": submission.title,
                    "body": submission.selftext if len(submission.selftext) < 500 else "",
                    "comments": top_comments,
                    "url": submission.url,
                    "id": submission.id
                }
                 
            return None
             
        except Exception as e:
            print(f"Error fetching from Reddit (PRAW): {e}")
            return None

# Test
if __name__ == "__main__":
    client = RedditClient()
    thread = client.get_viral_thread()
    if thread:
        print(f"Title: {thread['title']}")
        print(f"Comments: {len(thread['comments'])}")
