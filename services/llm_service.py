"""
LLM Service - 大语言模型服务
使用 LangChain 兼容接口调用 Ollama
"""

import requests
import json
from typing import List, Dict, Any, Optional, Generator
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.callbacks import CallbackManagerForLLMRun


class OllamaChat(BaseChatModel):
    """
    LangChain 兼容的 Ollama 聊天模型
    使用原生 Ollama API
    """
    
    model: str = "qwen3:0.6b"
    """Ollama 模型名称"""
    
    base_url: str = "http://localhost:11434"
    """Ollama API 地址"""
    
    temperature: float = 0.7
    """温度参数"""
    
    top_p: float = 0.9
    """top_p 参数"""
    
    max_tokens: int = 2048
    """最大 token 数"""
    
    system_prompt: str = ""
    """系统提示词"""
    
    @property
    def _llm_type(self) -> str:
        return "ollama_chat"
    
    def _convert_message_to_dict(self, message: BaseMessage) -> Dict:
        """将 LangChain 消息转换为 Ollama 格式"""
        if isinstance(message, HumanMessage):
            return {"role": "user", "content": message.content}
        elif isinstance(message, AIMessage):
            return {"role": "assistant", "content": message.content}
        elif isinstance(message, SystemMessage):
            return {"role": "system", "content": message.content}
        else:
            return {"role": "user", "content": str(message.content)}
    
    def _build_messages(self, messages: List[BaseMessage]) -> List[Dict]:
        """构建 Ollama 消息格式"""
        ollama_messages = []
        
        for msg in messages:
            ollama_messages.append(self._convert_message_to_dict(msg))
        
        return ollama_messages
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """同步生成"""
        ollama_messages = self._build_messages(messages)
        
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "num_ctx": self.max_tokens,
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            
            content = data.get("message", {}).get("content", "")
            
            message = AIMessage(content=content)
            generation = ChatGeneration(message=message)
            return ChatResult(generations=[generation])
            
        except Exception as e:
            message = AIMessage(content=f"Error: {str(e)}")
            generation = ChatGeneration(message=message)
            return ChatResult(generations=[generation])
    
    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Generator[ChatGeneration, None, None]:
        """流式生成"""
        ollama_messages = self._build_messages(messages)
        
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": True,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "num_ctx": self.max_tokens,
            }
        }
        
        try:
            response = requests.post(url, json=payload, stream=True, timeout=120)
            response.raise_for_status()
            
            full_content = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "message" in data:
                            token = data["message"].get("content", "")
                            if token:
                                full_content += token
                                yield ChatGeneration(
                                    message=AIMessage(content=token)
                                )
                    except:
                        continue
                        
        except Exception as e:
            yield ChatGeneration(
                message=AIMessage(content=f"Error: {str(e)}")
            )


class LLMService:
    """
    大语言模型服务
    内部使用 LangChain 兼容的 OllamaChat
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
        
        # 初始化 LangChain 兼容的聊天模型
        self._chat_model = OllamaChat(
            model=self.default_model,
            base_url=self.base_url,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            system_prompt=self.system_prompt
        )
        
        # 对话历史 (每个 session_id 对应一个消息列表)
        self._message_histories: Dict[str, List[BaseMessage]] = {}
    
    def _get_history(self, session_id: str) -> List[BaseMessage]:
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
    
    def chat(self, message: str, history: List[Dict] = None, 
             model: Optional[str] = None) -> str:
        """
        聊天（同步）- 使用 LangChain 接口
        """
        # 如果指定了不同模型，需要重新初始化
        if model and model != self._chat_model.model:
            self._chat_model = OllamaChat(
                model=model,
                base_url=self.base_url,
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
                system_prompt=self.system_prompt
            )
        
        # 构建消息
        messages = self._build_langchain_messages(message, history)
        
        # 调用 LangChain 接口
        try:
            response = self._chat_model.invoke(messages)
            return response.content
        except Exception as e:
            return f"Error: {str(e)}"
    
    def chat_stream(self, message: str, history: List[Dict] = None,
                    model: Optional[str] = None) -> Generator[str, None]:
        """
        聊天（流式）- 使用 LangChain 接口
        """
        # 如果指定了不同模型，需要重新初始化
        if model and model != self._chat_model.model:
            self._chat_model = OllamaChat(
                model=model,
                base_url=self.base_url,
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
                system_prompt=self.system_prompt
            )
        
        # 构建消息
        messages = self._build_langchain_messages(message, history)
        
        # 流式调用 LangChain 接口
        try:
            for chunk in self._chat_model.stream(messages):
                if chunk.message.content:
                    yield chunk.message.content
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def _build_langchain_messages(self, message: str, history: List[Dict] = None) -> List[BaseMessage]:
        """构建 LangChain 消息列表"""
        messages = []
        
        # 添加系统提示
        if self.system_prompt:
            messages.append(SystemMessage(content=self.system_prompt))
        
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
        self._chat_model = OllamaChat(
            model=self.default_model,
            base_url=self.base_url,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            system_prompt=self.system_prompt
        )
