"""
Flask + Ollama 聊天应用 (服务化架构)
使用 Router + Service 模式

架构说明：
- Router: 信息流控制中心，协调各服务
- LLMService: 大语言模型服务 (LangChain + Ollama)
- STTService: 语音识别服务
- TTSService: 语音合成服务
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_socketio import SocketIO

from config import *
from services import LLMService, STTService, TTSService
from router import Router

# 创建 Flask 应用
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# 创建 SocketIO - Windows 兼容模式
try:
    import eventlet
    socketio = SocketIO(
        app, 
        cors_allowed_origins="*", 
        async_mode='eventlet',
        ping_timeout=30,
        ping_interval=25
    )
except ImportError:
    # 没有 eventlet 使用 threading
    socketio = SocketIO(
        app, 
        cors_allowed_origins="*", 
        async_mode='threading',
        ping_timeout=30,
        ping_interval=25
    )

# 初始化服务
print("初始化服务...")

llm_service = LLMService({
    'base_url': OLLAMA_BASE_URL,
    'default_model': DEFAULT_MODEL,
    'use_langchain': False,  # 设置为 True 启用 LangChain
    'temperature': 0.7,
    'top_p': 0.9,
    'max_tokens': 2048,
    'system_prompt': '你是一个有用的 AI 助手。'
})

stt_service = STTService({
    'mode': 'websocket',  # websocket / whisper
    'language': 'zh-CN'
})

tts_service = TTSService({
    'mode': 'pyttsx3',  # pyttsx3 / gtts / edge
    'language': 'zh',
    'rate': 150,
    'volume': 1.0
})

print(f"  LLM: {llm_service.base_url} / {llm_service.default_model}")
print(f"  STT: {stt_service.mode}")
print(f"  TTS: {tts_service.mode}")

# 初始化路由器
router = Router(app, llm_service, stt_service, tts_service)

# WebSocket 事件处理
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('message')
def handle_message(data):
    """处理实时聊天消息"""
    session_id = data.get('session_id', 'default')
    message = data.get('message', '')
    model = data.get('model', llm_service.default_model)
    
    if session_id not in router.conversations:
        router.conversations[session_id] = []
    
    history = router.conversations[session_id]
    
    from flask_socketio import emit
    
    full_response = ""
    for token in llm_service.chat_stream(message, history, model):
        full_response += token
        emit('response', {'token': token})
    
    history.append({'role': 'user', 'content': message})
    history.append({'role': 'assistant', 'content': full_response})
    emit('response', {'done': True})


# ==================== 主程序 ====================

if __name__ == '__main__':
    print(f"""
==========================================
  Flask + Ollama Chatbot (服务化架构)
  
  架构: Router + Service Pattern
  - LLM Service: 大语言模型
  - STT Service: 语音识别  
  - TTS Service: 语音合成
  
  访问 http://localhost:{PORT}
==========================================
    """)
    
    # 使用 127.0.0.1 确保本机可访问
    socketio.run(app, host="127.0.0.1", port=PORT, debug=False)
