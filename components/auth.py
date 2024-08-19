from authlib.integrations.requests_client import OAuth2Session
from config.config import GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, REDIRECT_URI

class Auth:
    def __init__(self):
        self.oauth = OAuth2Session(
            client_id=GITHUB_CLIENT_ID,
            client_secret=GITHUB_CLIENT_SECRET,
            redirect_uri=REDIRECT_URI
        )
    
    def get_auth_url(self):
        return self.oauth.create_authorization_url("https://github.com/login/oauth/authorize")
    
    def fetch_token(self, authorization_response, code):
        return self.oauth.fetch_token(
            "https://github.com/login/oauth/access_token",
            authorization_response=authorization_response,
            code=code
        )
