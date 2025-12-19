import requests
import urllib.parse

prompt = "Write a one sentence fact about space."
safe_prompt = urllib.parse.quote(prompt)

models = ["", "openai", "searchgpt", "mistral", "turbo"]

for m in models:
    url = f"https://text.pollinations.ai/{safe_prompt}"
    if m:
        url += f"?model={m}"
    
    print(f"Testing Model '{m}': {url}")
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Content: {response.text[:50]}...")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 20)
