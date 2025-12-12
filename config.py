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
        self.openai_api_key = None
        self.flux_api_key = None
        self.flux_host = None
        self.black_forest_labs_api_key = None
        self.load_config()
    
    def load_config(self):
        """Load configuration from .env file"""
        load_dotenv()
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Flux API - support both old FLUX_API_KEY and new BLACK_FOREST_LABS_API_KEY
        # Prefer Black Forest Labs direct API if available
        self.black_forest_labs_api_key = os.getenv('BLACK_FOREST_LABS_API_KEY')
        if self.black_forest_labs_api_key:
            self.flux_api_key = self.black_forest_labs_api_key
            self.flux_host = 'bfl'  # Black Forest Labs direct API
        else:
            self.flux_api_key = os.getenv('FLUX_API_KEY')
            self.flux_host = os.getenv('FLUX_HOST', 'fal')  # fal, together, fireworks, replicate, bfl
        
        # OpenAI is required for prompt generation
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not found in .env file")
    
    def validate_api_key(self):
        """Validate the API key by making a simple request"""
        try:
            # Simple validation - try to list models
            client = openai.OpenAI(api_key=self.openai_api_key)
            _ = client.models.list()
            return True, ""
        except Exception as e:
            return False, str(e)
    
    def get_openai_api_key(self):
        return self.openai_api_key
    
    def get_flux_api_key(self):
        return self.flux_api_key
    
    def get_flux_host(self):
        return self.flux_host
    
    def get_black_forest_labs_api_key(self):
        """Get Black Forest Labs API key (direct API access)"""
        return self.black_forest_labs_api_key
    
    def get_comfyui_server_address(self) -> str:
        """Get ComfyUI server address"""
        return os.getenv('COMFYUI_SERVER_ADDRESS', '127.0.0.1:8188')
    
    def get_comfyui_workflow_dir(self) -> str:
        """Get ComfyUI workflow directory"""
        return os.getenv('COMFYUI_WORKFLOW_DIR', 'workflows/comfyui')
    
    def get_comfyui_temp_dir(self) -> str:
        """Get ComfyUI temporary upload directory"""
        return os.getenv('COMFYUI_TEMP_DIR', 'temp_uploads')
    
    # Backward compatibility
    def get_api_key(self):
        return self.openai_api_key
