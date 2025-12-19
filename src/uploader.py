import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

class YouTubeUploader:
    def __init__(self, client_secrets_file="client_secret.json"):
        self.scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        self.api_service_name = "youtube"
        self.api_version = "v3"
        self.client_secrets_file = client_secrets_file
        self.youtube = None

    def authenticate(self):
        """
        Authenticates the user and creates a YouTube API client.
        """
        creds = None
        # The file token.json stores the user's access and refresh tokens.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', self.scopes)
            
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.client_secrets_file):
                    print(f"Error: {self.client_secrets_file} not found. Cannot authenticate with YouTube.")
                    return False
                    
                flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, self.scopes)
                creds = flow.run_local_server(port=0)
                
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
                
        self.youtube = googleapiclient.discovery.build(
            self.api_service_name, self.api_version, credentials=creds)
        return True

    def upload_video(self, file_path, title, description, tags, category_id="22", privacy_status="private"):
        """
        Uploads a video to YouTube.
        """
        if not self.youtube:
            if not self.authenticate():
                return

        print(f"Uploading {file_path}...")
        
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": category_id
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            }
        }

        request = self.youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=googleapiclient.http.MediaFileUpload(file_path, chunksize=-1, resumable=True)
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Uploaded {int(status.progress() * 100)}%")
        
        print(f"Upload Complete! Video ID: {response.get('id')}")
        return response.get('id')
