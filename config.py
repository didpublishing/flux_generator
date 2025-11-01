import os
from dotenv import load_dotenv
import openai
import logging

logger = logging.getLogger("flux_prompt")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    # Console handler
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    # File handler (writes to project root or container workdir)
    try:
        os.makedirs('logs', exist_ok=True)
        fh = logging.FileHandler('logs/app.log', encoding='utf-8')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except Exception:
        # Fallback silently if file handler cannot be created
        pass

class Config:
    def __init__(self):
        self.api_key = None
        self.load_config()
    
    def load_config(self):
        """Load configuration from .env file"""
        load_dotenv()
        self.api_key = os.getenv('OPENAI_API_KEY')
        
        if not self.api_key:
            raise ValueError("OpenAI API key not found in .env file")
    
    def validate_api_key(self):
        """Validate the API key by making a simple request"""
        try:
            # Simple validation - try to list models
            client = openai.OpenAI(api_key=self.api_key)
            _ = client.models.list()
            return True, ""
        except Exception as e:
            return False, str(e)
    
    def get_api_key(self):
        return self.api_key
