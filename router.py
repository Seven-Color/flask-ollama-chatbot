"""
Router - 信息流控制中心
负责协调各个服务模块，处理请求流程
"""

from typing import Dict, Any, Optional, Callable
from flask import request, jsonify
import json


class Router:
    """
    路由器 - 协调各服务模块
    """
    
    def __init__(self, app, llm_service, stt_service, tts_service, memory_service=None):
        self.app = app
        self.llm_service = llm_service
        self.stt_service = stt_service
        self.tts_service = tts_service
        self.memory_service = memory_service
        self.conversations: Dict[str, list] = {}
        
        self._register_routes()
    
    def _register_routes(self):
        """注册路由"""
        # 聊天
        self.app.add_url_rule('/api/chat', 'chat', self._handle_chat, methods=['POST'])
        self.app.add_url_rule('/api/chat/stream', 'chat_stream', self._handle_chat_stream, methods=['POST'])
        
        # 语音
        self.app.add_url_rule('/api/stt', 'stt', self._handle_stt, methods=['POST'])
        self.app.add_url_rule('/api/tts', 'tts', self._handle_tts, methods=['POST'])
        
        # 历史
        self.app.add_url_rule('/api/history', 'history', self._handle_history, 
                             methods=['GET', 'DELETE'])
        
        # 配置
        self.app.add_url_rule('/api/config', 'get_config', self._get_config, methods=['GET'])
        self.app.add_url_rule('/api/config', 'set_config', self._set_config, methods=['POST'])
        
        # 模型
        self.app.add_url_rule('/api/models', 'get_models', self._get_models, methods=['GET'])
        
        # 记忆相关路由
        if self.memory_service:
            self.app.add_url_rule('/api/memory', 'memory', self._handle_memory, methods=['GET', 'POST'])
        
        # 路由页面
        self.app.add_url_rule('/', 'index', self._index)
    
    def _index(self):
        from flask import render_template
        return render_template('chat.html')
    
    def _get_models(self):
        """获取可用模型"""
        models = self.llm_service.get_available_models()
        return jsonify({'models': models})
    
    def _handle_chat(self):
        """处理聊天请求"""
        data = request.json
        message = data.get('message', '')
        model = data.get('model', self.llm_service.default_model)
        session_id = data.get('session_id', 'default')
        
        if not message:
            return jsonify({'error': 'Empty message'}), 400
        
        # 获取/创建会话历史
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        history = self.conversations[session_id]
        
        # 智能 RAG: 先判断是否需要检索记忆
        memory_context = ""
        memory_used = False
        
        if self.memory_service:
            # 让大模型判断是否需要检索记忆
            check_prompt = f"""请判断以下用户问题是否需要了解用户的个人信息、生活习惯、兴趣爱好等记忆内容才能回答。

用户问题: {message}

请直接回答"需要"或"不需要"，不要有其他内容。"""
            
            # 用简短的历史进行判断
            short_history = history[-4:] if len(history) > 4 else history
            need_memory = self.llm_service.chat(
                message=check_prompt,
                history=short_history,
                model=model,
                system_prompt=""
            ).strip()
            
            # 如果判断需要检索，则获取记忆
            if '需要' in need_memory:
                memory_context = self.memory_service.search_memory(message)
                memory_used = bool(memory_context)
        
        # 构建 system prompt
        system_prompt = ""
        if memory_context:
            system_prompt = f"""你是一个智能助手。以下是用户的记忆信息，可以帮助你更好地理解和回答用户的问题：

{memory_context}

请根据以上记忆信息，结合当前对话内容回答用户的问题。"""
        
        # 调用 LLM 服务
        try:
            response = self.llm_service.chat(
                message=message,
                history=history,
                model=model,
                system_prompt=system_prompt
            )
            
            # 更新历史
            history.append({'role': 'user', 'content': message})
            history.append({'role': 'assistant', 'content': response})
            
            return jsonify({
                'response': response,
                'session_id': session_id,
                'memory_used': memory_used
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def _handle_chat_stream(self):
        """流式聊天"""
        from flask import Response
        data = request.json
        message = data.get('message', '')
        model = data.get('model', self.llm_service.default_model)
        session_id = data.get('session_id', 'default')
        
        if not message:
            return jsonify({'error': 'Empty message'}), 400
        
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        history = self.conversations[session_id]
        
        # 智能 RAG: 先判断是否需要检索记忆
        memory_context = ""
        memory_used = False
        if self.memory_service:
            # 让大模型判断是否需要检索记忆
            check_prompt = f"""请判断以下用户问题是否需要了解用户的个人信息、生活习惯、兴趣爱好等记忆内容才能回答。

用户问题: {message}

请直接回答"需要"或"不需要"，不要有其他内容。"""
            
            short_history = history[-4:] if len(history) > 4 else history
            need_memory = self.llm_service.chat(
                message=check_prompt,
                history=short_history,
                model=model,
                system_prompt=""
            ).strip()
            
            if '需要' in need_memory:
                memory_context = self.memory_service.search_memory(message)
                memory_used = bool(memory_context)
        
        # 构建带有记忆的 system prompt
        system_prompt = ""
        if memory_context:
            system_prompt = f"""你是一个智能助手。以下是用户的记忆信息，可以帮助你更好地理解和回答用户的问题：

{memory_context}

请根据以上记忆信息，结合当前对话内容回答用户的问题。"""
        
        def generate():
            nonlocal memory_used
            full_response = ""
            for token in self.llm_service.chat_stream(message, history, model, system_prompt):
                full_response += token
                yield f"data: {json.dumps({'token': token})}\n\n"
            
            history.append({'role': 'user', 'content': message})
            history.append({'role': 'assistant', 'content': full_response})
            yield f"data: {json.dumps({'done': True, 'memory_used': memory_used})}\n\n"
        
        return Response(generate(), mimetype='text/event-stream')
    
    def _handle_stt(self):
        """语音转文字"""
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file'}), 400
        
        audio_file = request.files['audio']
        
        try:
            text = self.stt_service.transcribe(audio_file)
            return jsonify({'text': text})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def _handle_tts(self):
        """文字转语音"""
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'Empty text'}), 400
        
        try:
            audio_data = self.tts_service.synthesize(text)
            return jsonify({'audio': audio_data, 'format': 'wav'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def _handle_history(self):
        """历史记录"""
        session_id = request.args.get('session_id', 'default')
        
        if request.method == 'DELETE':
            if session_id in self.conversations:
                del self.conversations[session_id]
            return jsonify({'status': 'cleared'})
        
        return jsonify({'history': self.conversations.get(session_id, [])})
    
    def _get_config(self):
        """获取配置"""
        return jsonify({
            'llm': self.llm_service.get_config(),
            'stt': self.stt_service.get_config(),
            'tts': self.tts_service.get_config()
        })
    
    def _set_config(self):
        """设置配置"""
        data = request.json
        
        if 'llm' in data:
            self.llm_service.update_config(data['llm'])
        if 'stt' in data:
            self.stt_service.update_config(data['stt'])
        if 'tts' in data:
            self.tts_service.update_config(data['tts'])
        
        return jsonify({'status': 'updated'})
    
    def _handle_memory(self):
        """记忆相关操作"""
        if not self.memory_service:
            return jsonify({'error': 'Memory service not configured'}), 500
        
        action = request.args.get('action', 'search')
        
        if action == 'search':
            # 搜索记忆
            query = request.args.get('query', '')
            memory_content = self.memory_service.search_memory(query)
            return jsonify({'memory': memory_content})
        
        elif action == 'summary':
            # 获取记忆摘要
            summary = self.memory_service.get_memory_summary()
            return jsonify({'summary': summary})
        
        elif action == 'add':
            # 添加到胶囊
            data = request.json
            text = data.get('text', '')
            self.memory_service.add_to_capsule(text)
            return jsonify({'status': 'added', 'capsule_size': len(self.memory_service.current_capsule['content'])})
        
        elif action == 'summarize':
            # 总结胶囊
            summary = self.memory_service.summarize_capsule(self.llm_service)
            return jsonify({'summary': summary})
        
        return jsonify({'error': 'Unknown action'}), 400
