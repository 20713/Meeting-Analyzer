from openai import OpenAI
from core.config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        """Initialize the OpenAI client with configuration."""
        if not Config.API_KEY:
            logger.warning("API Key is missing. LLM calls will fail.")
        
        self.client = OpenAI(
            api_key=Config.API_KEY,
            base_url=Config.API_BASE_URL
        )

    def chat_stream(self, messages):
        """
        Stream chat completions from the LLM.
        
        Args:
            messages (list): A list of message dictionaries (role, content).
            
        Yields:
            str: The content chunks from the stream.
        """
        try:
            logger.info(f"Sending request to LLM with {len(messages)} messages")
            response = self.client.chat.completions.create(
                model=Config.MODEL_NAME,
                messages=messages,
                temperature=Config.TEMPERATURE,
                max_tokens=Config.MAX_TOKENS,
                stream=True
            )
            
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            error_msg = f"Error calling LLM API: {str(e)}"
            logger.error(error_msg)
            yield f"⚠️ **系统提示**: {error_msg}\n\n请检查 API Key 配置或网络连接。"
