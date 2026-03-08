import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # API Configuration
    API_KEY = os.getenv("DASHSCOPE_API_KEY")
    API_BASE_URL = os.getenv("API_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    MODEL_NAME = os.getenv("QWEN_MODEL_NAME", "qwen3.5-plus")

    # Gradio Configuration
    GRADIO_PORT = int(os.getenv("GRADIO_PORT", "7860"))
    GRADIO_SERVER_NAME = os.getenv("GRADIO_SERVER_NAME", "0.0.0.0")

    # LLM Parameters
    TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))

    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
    DEMO_DOCS_DIR = os.path.join(BASE_DIR, "demo_docs")

    @classmethod
    def check_env(cls):
        """Ensure necessary directories exist and check for critical environment variables."""
        os.makedirs(cls.UPLOADS_DIR, exist_ok=True)
        os.makedirs(cls.DEMO_DOCS_DIR, exist_ok=True)
        
        if not cls.API_KEY:
            print("Warning: DASHSCOPE_API_KEY not found in environment variables. Please set it in .env file.")
            return False
        return True
