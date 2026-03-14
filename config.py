"""
配置文件
"""

# Ollama 配置
OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama2"

# 可用模型列表
AVAILABLE_MODELS = [
    "llama2",
    "llama2:13b",
    "mistral",
    "codellama",
    "neural-chat",
]

# Flask 配置
SECRET_KEY = "ollama-chat-secret-key"
HOST = "0.0.0.0"
PORT = 5000

# 语音配置
# STT: "websocket" (浏览器Web Speech API) 或 "whisper"
STT_MODE = "websocket"
# TTS: "pyttsx3" (本地) 或 "gtts" (Google API)
TTS_MODE = "pyttsx3"

# 对话历史
MAX_HISTORY = 20
