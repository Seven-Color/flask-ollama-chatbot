"""
Flask + Ollama 聊天应用
使用 Router 协调各服务模块
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask

# 导入模块
from services import LLMService, STTService, TTSService
from router import Router
from config import Config

# 加载配置
config = Config()

# 从配置获取
SECRET_KEY = "ollama-chat-secret-key"
HOST = "127.0.0.1"
PORT = 8000

# 创建 Flask 应用
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# 初始化服务配置
llm_config = config.get('llm', {})
stt_config = config.get('stt', {})
tts_config = config.get('tts', {})

# 初始化服务
llm_service = LLMService(llm_config)
stt_service = STTService(stt_config)
tts_service = TTSService(tts_config)

# 初始化 Router 并注册路由
router = Router(app, llm_service, stt_service, tts_service)

# ==================== 主程序 ====================

if __name__ == '__main__':
    print(f"""
==========================================
  Flask + Ollama Chatbot
  使用 Router 协调服务
  访问 http://localhost:{PORT}
==========================================
    """)
    
    app.run(host=HOST, port=PORT, debug=True, threaded=True)
