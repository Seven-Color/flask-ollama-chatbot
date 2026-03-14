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
    
    def __init__(self, app, llm_service, stt_service, tts_service):
        self.app = app
        self.llm_service = llm_service
        self.stt_service = stt_service
        self.tts_service = tts_service
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
        
        # 调用 LLM 服务
        try:
            response = self.llm_service.chat(
                message=message,
                history=history,
                model=model
            )
            
            # 更新历史
            history.append({'role': 'user', 'content': message})
            history.append({'role': 'assistant', 'content': response})
            
            return jsonify({
                'response': response,
                'session_id': session_id
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
        
        def generate():
            full_response = ""
            for token in self.llm_service.chat_stream(message, history, model):
                full_response += token
                yield f"data: {json.dumps({'token': token})}\n\n"
            
            history.append({'role': 'user', 'content': message})
            history.append({'role': 'assistant', 'content': full_response})
            yield f"data: {json.dumps({'done': True})}\n\n"
        
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
