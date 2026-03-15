"""
配置文件
"""

import json
import os

# 基础路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ollama 配置
OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen3:0.6b"

# Flask 配置
SECRET_KEY = "ollama-chat-secret-key"
HOST = "0.0.0.0"
PORT = 8000

# 对话历史
MAX_HISTORY = 20


class Config:
    """配置管理类"""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or os.path.join(BASE_DIR, 'config.json')
        self._config = self._load()
    
    def _load(self) -> dict:
        """加载配置"""
        default_config = {
            'llm': {
                'base_url': OLLAMA_BASE_URL,
                'default_model': DEFAULT_MODEL,
                'temperature': 0.7,
                'top_p': 0.9,
                'max_tokens': 2048,
                'system_prompt': '',
                'use_langchain': False,
                'host': HOST,
                'port': PORT
            },
            'stt': {
                'mode': 'whisper',  # websocket, whisper
                'language': 'zh',
                'whisper_model': 'base',  # tiny, base, small, medium, large
                'whisper_device': 'cpu'
            },
            'tts': {
                'provider': 'browser',  # browser, elevenlabs
                'voice': 'default',
                'speed': 1.0
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 合并配置
                    for key in default_config:
                        if key in user_config:
                            default_config[key].update(user_config[key])
            except:
                pass
        
        return default_config
    
    def get(self, key: str, default=None):
        """获取配置"""
        return self._config.get(key, default)
    
    def set(self, key: str, value):
        """设置配置"""
        self._config[key] = value
    
    def save(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")
