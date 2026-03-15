"""
LLM Service - 大语言模型服务
使用 LangChain 调用 Ollama
"""

import requests
from typing import List, Dict, Any, Optional, Generator


class LLMService:
    """
    大语言模型服务
    支持：Ollama, LangChain 封装
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        # 默认配置
        self.config = config or {}
        self.base_url = self.config.get('base_url', 'http://localhost:11434')
        self.default_model = self.config.get('default_model', 'llama2')
        self.temperature = self.config.get('temperature', 0.7)
        self.top_p = self.config.get('top_p', 0.9)
        self.max_tokens = self.config.get('max_tokens', 2048)
        self.system_prompt = self.config.get('system_prompt', '')
        
        # LangChain 相关（可选）
        self.use_langchain = self.config.get('use_langchain', False)
        
        # 尝试初始化 LangChain
        self._langchain_model = None
        if self.use_langchain:
            self._init_langchain()
    
    def _init_langchain(self):
        """初始化 LangChain"""
        try:
            from langchain_community.llms import Ollama
            from langchain_core.prompts import PromptTemplate
            from langchain_community.chat_message_histories import ChatMessageHistory
            
            self._langchain_model = Ollama(
                model=self.default_model,
                base_url=self.base_url,
                temperature=self.temperature,
                top_p=self.top_p,
                num_ctx=self.max_tokens
            )
            
            # 记忆模板
            self.prompt = PromptTemplate(
                input_variables=["history", "input"],
                template=self.system_prompt + "\n\n历史记录:\n{history}\n\n用户: {input}\n助手:"
            )
            
            # 对话记忆
            self.memory = ChatMessageHistory()
            
        except ImportError:
            print("LangChain 未安装，将使用原生 API")
            self.use_langchain = False
    
    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [m['name'] for m in models]
        except:
            pass
        return [self.default_model]
    
    def chat(self, message: str, history: List[Dict] = None, 
             model: Optional[str] = None) -> str:
        """
        聊天（同步）
        """
        model = model or self.default_model
        history = history or []
        
        if self.use_langchain and self._langchain_model:
            return self._chat_langchain(message, history, model)
        else:
            return self._chat_native(message, history, model)
    
    def _chat_langchain(self, message: str, history: List[Dict], model: str) -> str:
        """使用 LangChain 聊天"""
        # 构建历史字符串
        history_text = ""
        for h in history[-10:]:  # 限制历史长度
            role = h.get('role', 'user')
            content = h.get('content', '')
            history_text += f"{role}: {content}\n"
        
        # 调用
        prompt = self.prompt.format(history=history_text, input=message)
        response = self._langchain_model.invoke(prompt)
        
        return response
    
    def _chat_native(self, message: str, history: List[Dict], model: str) -> str:
        """使用原生 API 聊天"""
        url = f"{self.base_url}/api/chat"
        
        # 构建消息
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        
        for h in history:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        
        messages.append({"role": "user", "content": message})
        
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
                    model: Optional[str] = None) -> Generator[str, None, None]:
        """
        聊天（流式）
        """
        model = model or self.default_model
        history = history or []
        
        url = f"{self.base_url}/api/chat"
        
        # 构建消息
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        
        for h in history:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        
        messages.append({"role": "user", "content": message})
        
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
            'use_langchain': self.use_langchain,
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
        if 'use_langchain' in config:
            self.use_langchain = config['use_langchain']
            if self.use_langchain:
                self._init_langchain()
