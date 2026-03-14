"""
配置文件
"""

# Ollama 配置
OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama2"

# Flask 配置
SECRET_KEY = "ollama-chat-secret-key"
HOST = "0.0.0.0"
PORT = 5000

# 对话历史
MAX_HISTORY = 20
