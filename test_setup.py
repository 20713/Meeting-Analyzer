import os
import sys

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config import Config
from core.llm_client import LLMClient
from core.analyzer import AnalyzerPrompts

def test_config():
    print("Testing Config...")
    # Basic checks
    assert Config.GRADIO_PORT == 7860 or Config.GRADIO_PORT is not None
    assert Config.UPLOADS_DIR.endswith("uploads")
    
    # Ensure directories are created
    Config.check_env()
    assert os.path.exists(Config.UPLOADS_DIR)
    assert os.path.exists(Config.DEMO_DOCS_DIR)
    print("Config OK.")

def test_prompts():
    print("Testing Prompts...")
    content = "Test meeting content"
    
    # Initial report prompt
    initial_prompt = AnalyzerPrompts.get_initial_report_prompt(content)
    assert len(initial_prompt) == 2
    assert initial_prompt[0]['role'] == 'system'
    assert "Test meeting content" in initial_prompt[1]['content']
    
    # Chat prompt
    history = [("Q1", "A1")]
    chat_prompt = AnalyzerPrompts.get_chat_prompt(content, history)
    # Expected: System + User(Q1) + Assistant(A1)
    assert len(chat_prompt) == 3 
    assert chat_prompt[1]['role'] == 'user'
    assert chat_prompt[1]['content'] == 'Q1'
    assert chat_prompt[2]['role'] == 'assistant'
    assert chat_prompt[2]['content'] == 'A1'
    print("Prompts OK.")

if __name__ == "__main__":
    try:
        test_config()
        test_prompts()
        print("All basic tests passed!")
    except AssertionError as e:
        print(f"Test failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
