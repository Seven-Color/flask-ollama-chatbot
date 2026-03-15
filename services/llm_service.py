"""
LLM Service - 大语言模型服务
使用原生 Ollama API (兼容 LangChain 接口)
"""

import requests
import json
from typing import List, Dict, Any, Optional, Generator


class LLMService:
    """
    大语言模型服务
    使用原生 Ollama API，兼容 LangChain 接口
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        # 默认配置
        self.config = config or {}
        self.base_url = self.config.get('base_url', 'http://localhost:11434')
        self.default_model = self.config.get('default_model', 'qwen3')
        self.temperature = self.config.get('temperature', 0.7)
        self.top_p = self.config.get('top_p', 0.9)
        self.max_tokens = self.config.get('max_tokens', 2048)
        self.system_prompt = self.config.get('system_prompt', '')
        
        # 对话历史 (每个 session_id 对应一个消息列表)
        self._message_histories: Dict[str, List[Dict]] = {}
    
    def _get_history(self, session_id: str) -> List[Dict]:
        """获取或创建会话历史"""
        if session_id not in self._message_histories:
            self._message_histories[session_id] = []
        return self._message_histories[session_id]
    
    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [m['name'] for m in models]
        except Exception as e:
            print(f"获取模型列表失败: {e}")
        return [self.default_model]
    
    def _build_messages(self, message: str, history: List[Dict] = None) -> List[Dict]:
        """构建 Ollama 消息格式"""
        messages = []
        
        # 添加系统提示
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        
        # 添加历史消息
        if history:
            for h in history:
                role = h.get('role', 'user')
                content = h.get('content', '')
                if role in ['user', 'assistant', 'system']:
                    messages.append({"role": role, "content": content})
        
        # 添加当前消息
        messages.append({"role": "user", "content": message})
        
        return messages
    
    def chat(self, message: str, history: List[Dict] = None, 
             model: Optional[str] = None) -> str:
        """
        聊天（同步）
        """
        model = model or self.default_model
        messages = self._build_messages(message, history)
        
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "num_ctx": self.max_tokens
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")
        except Exception as e:
            return f"Error: {str(e)}"
    
    def chat_stream(self, message: str, history: List[Dict] = None,
                    model: Optional[str] = None) -> Generator[str, None]:
        """
        聊天（流式）
        """
        model = model or self.default_model
        messages = self._build_messages(message, history)
        
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "num_ctx": self.max_tokens
            }
        }
        
        try:
            response = requests.post(url, json=payload, stream=True, timeout=120)
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "message" in data:
                            token = data["message"].get("content", "")
                            if token:
                                yield token
                    except:
                        continue
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return {
            'base_url': self.base_url,
            'default_model': self.default_model,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'max_tokens': self.max_tokens,
            'system_prompt': self.system_prompt,
            'available_models': self.get_available_models()
        }
    
    def update_config(self, config: Dict[str, Any]):
        """更新配置"""
        if 'base_url' in config:
            self.base_url = config['base_url']
        if 'default_model' in config:
            self.default_model = config['default_model']
        if 'temperature' in config:
            self.temperature = config['temperature']
        if 'top_p' in config:
            self.top_p = config['top_p']
        if 'max_tokens' in config:
            self.max_tokens = config['max_tokens']
        if 'system_prompt' in config:
            self.system_prompt = config['system_prompt']
