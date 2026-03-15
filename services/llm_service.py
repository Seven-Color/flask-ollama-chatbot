"""
LLM Service - 大语言模型服务
使用 LangChain Ollama 封装调用 Ollama
"""

import os
# 解决 Windows httpx 代理问题
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

from typing import List, Dict, Any, Optional, Iterator
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


class LLMService:
    """
    大语言模型服务
    使用 LangChain Ollama 封装
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        # 默认配置
        self.config = config or {}
        self.base_url = self.config.get('base_url', 'http://localhost:11434')
        self.default_model = self.config.get('default_model', 'qwen3:0.6b')
        self.temperature = self.config.get('temperature', 0.7)
        self.top_p = self.config.get('top_p', 0.9)
        self.max_tokens = self.config.get('max_tokens', 2048)
        self.system_prompt = self.config.get('system_prompt', '')
        
        # 初始化 LangChain Ollama 聊天模型
        self._chat_model = ChatOllama(
            model=self.default_model,
            base_url=self.base_url,
            temperature=self.temperature,
            top_p=self.top_p,
            num_ctx=self.max_tokens,
        )
        
        # 对话历史 (每个 session_id 对应一个消息列表)
        self._message_histories: Dict[str, List[Dict]] = {}
    
    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [m['name'] for m in models]
        except Exception as e:
            print(f"获取模型列表失败: {e}")
        return [self.default_model]
    
    def chat(self, message: str, history: List[Dict] = None, 
             model: Optional[str] = None, system_prompt: str = "") -> str:
        """
        聊天（同步）- 使用 LangChain Ollama
        """
        # 如果指定了不同模型，需要重新初始化
        if model and model != self._chat_model.model:
            self._chat_model = ChatOllama(
                model=model,
                base_url=self.base_url,
                temperature=self.temperature,
                top_p=self.top_p,
                num_ctx=self.max_tokens,
            )
        
        # 构建消息
        messages = self._build_langchain_messages(message, history, system_prompt)
        
        # 调用 LangChain Ollama
        try:
            response = self._chat_model.invoke(messages)
            return response.content
        except Exception as e:
            return f"Error: {str(e)}"
    
    def chat_stream(self, message: str, history: List[Dict] = None,
                    model: Optional[str] = None, system_prompt: str = "") -> Iterator[str]:
        """
        聊天（流式）- 使用 LangChain Ollama
        """
        # 如果指定了不同模型，需要重新初始化
        if model and model != self._chat_model.model:
            self._chat_model = ChatOllama(
                model=model,
                base_url=self.base_url,
                temperature=self.temperature,
                top_p=self.top_p,
                num_ctx=self.max_tokens,
            )
        
        # 构建消息
        messages = self._build_langchain_messages(message, history, system_prompt)
        
        # 流式调用 LangChain Ollama
        try:
            for chunk in self._chat_model.stream(messages):
                # 流式返回的是 AIMessage 对象，需要获取 content
                content = None
                if hasattr(chunk, 'content'):
                    content = chunk.content
                elif chunk:
                    content = str(chunk)
                
                # 跳过空内容
                if content:
                    yield content
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def _build_langchain_messages(self, message: str, history: List[Dict] = None, system_prompt: str = "") -> List:
        """构建 LangChain 消息列表"""
        messages = []
        
        # 添加系统提示（优先使用传入的 system_prompt）
        prompt = system_prompt or self.system_prompt
        if prompt:
            messages.append(SystemMessage(content=prompt))
        
        # 添加历史消息
        if history:
            for h in history:
                role = h.get('role', 'user')
                content = h.get('content', '')
                if role == 'user':
                    messages.append(HumanMessage(content=content))
                elif role == 'assistant':
                    messages.append(AIMessage(content=content))
        
        # 添加当前消息
        messages.append(HumanMessage(content=message))
        
        return messages
    
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
        
        # 重新初始化模型
        self._chat_model = ChatOllama(
            model=self.default_model,
            base_url=self.base_url,
            temperature=self.temperature,
            top_p=self.top_p,
            num_ctx=self.max_tokens,
        )
