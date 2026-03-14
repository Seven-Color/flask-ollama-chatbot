"""
Flask + Ollama 聊天应用
支持文本聊天、语音输入、语音输出
"""

import json
import requests
import threading
import base64
import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from config import *

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 对话历史存储
conversations = {}


def call_ollama(prompt, model=DEFAULT_MODEL, history=None):
    """调用 Ollama API"""
    url = f"{OLLAMA_BASE_URL}/api/generate"
    
    # 构建消息
    messages = []
    if history:
        for h in history[-MAX_HISTORY:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
        }
    }
    
    try:
        response = requests.post(url, json=payload, stream=True, timeout=120)
        response.raise_for_status()
        
        full_response = ""
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    token = data.get("response", "")
                    full_response += token
                    # 发送流式响应
                    yield token
                except:
                    continue
        
        return full_response
    except Exception as e:
        yield f"Error: {str(e)}"


def call_ollama_chat(messages, model=DEFAULT_MODEL):
    """调用 Ollama Chat API"""
    url = f"{OLLAMA_BASE_URL}/api/chat"
    
    payload = {
        "model": model,
        "messages": messages[-MAX_HISTORY:],
        "stream": True,
    }
    
    try:
        response = requests.post(url, json=payload, stream=True, timeout=120)
        response.raise_for_status()
        
        full_response = ""
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    if "message" in data:
                        token = data["message"].get("content", "")
                        full_response += token
                        yield token
                except:
                    continue
        
        return full_response
    except Exception as e:
        yield f"Error: {str(e)}"


# ==================== 路由 ====================

@app.route('/')
def index():
    """主页"""
    return render_template('chat.html')


@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)


@app.route('/api/models')
def get_models():
    """获取可用模型列表"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags")
        models = response.json().get("models", [])
        return jsonify({"models": [m["name"] for m in models]})
    except:
        return jsonify({"models": AVAILABLE_MODELS})


@app.route('/api/chat', methods=['POST'])
def chat():
    """聊天接口"""
    data = request.json
    message = data.get('message', '')
    model = data.get('model', DEFAULT_MODEL)
    session_id = data.get('session_id', 'default')
    
    if not message:
        return jsonify({"error": "Empty message"}), 400
    
    # 获取历史
    if session_id not in conversations:
        conversations[session_id] = []
    history = conversations[session_id]
    
    # 添加用户消息
    history.append({"role": "user", "content": message})
    
    # 调用 Ollama
    messages = [{"role": h["role"], "content": h["content"]} for h in history]
    
    full_response = ""
    for token in call_ollama_chat(messages, model):
        full_response += token
    
    # 添加助手回复
    history.append({"role": "assistant", "content": full_response})
    
    return jsonify({
        "response": full_response,
        "session_id": session_id
    })


@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """流式聊天接口"""
    data = request.json
    message = data.get('message', '')
    model = data.get('model', DEFAULT_MODEL)
    session_id = data.get('session_id', 'default')
    
    if not message:
        return jsonify({"error": "Empty message"}), 400
    
    if session_id not in conversations:
        conversations[session_id] = []
    history = conversations[session_id]
    
    history.append({"role": "user", "content": message})
    messages = [{"role": h["role"], "content": h["content"]} for h in history]
    
    def generate():
        full_response = ""
        for token in call_ollama_chat(messages, model):
            full_response += token
            yield f"data: {json.dumps({'token': token})}\n\n"
        
        history.append({"role": "assistant", "content": full_response})
        yield f"data: {json.dumps({'done': True})}\n\n"
    
    return app.response_class(generate(), mimetype='text/event-stream')


@app.route('/api/history', methods=['GET', 'DELETE'])
def history():
    """获取或清除历史"""
    session_id = request.args.get('session_id', 'default')
    
    if request.method == 'DELETE':
        if session_id in conversations:
            del conversations[session_id]
        return jsonify({"status": "cleared"})
    
    return jsonify({"history": conversations.get(session_id, [])})


@app.route('/api/stt', methods=['POST'])
def stt():
    """语音转文字 (Whisper)"""
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file"}), 400
    
    audio_file = request.files['audio']
    
    # 保存临时文件
    temp_path = "/tmp/temp_audio.wav"
    audio_file.save(temp_path)
    
    try:
        # 使用 Whisper
        import whisper
        model = whisper.load_model("base")
        result = model.transcribe(temp_path)
        text = result["text"]
        
        os.remove(temp_path)
        return jsonify({"text": text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/tts', methods=['POST'])
def tts():
    """文字转语音"""
    data = request.json
    text = data.get('text', '')
    lang = data.get('lang', 'zh')
    
    if not text:
        return jsonify({"error": "Empty text"}), 400
    
    try:
        # 使用 pyttsx3 (本地TTS)
        import pyttsx3
        engine = pyttsx3.init()
        
        # 保存到文件
        output_path = "/tmp/tts_output.wav"
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        
        # 读取返回
        with open(output_path, 'rb') as f:
            audio_data = base64.b64encode(f.read()).decode()
        
        os.remove(output_path)
        return jsonify({"audio": audio_data, "format": "wav"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== WebSocket ====================

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('response', {'data': 'Connected'})


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


@socketio.on('message')
def handle_message(message):
    """处理实时消息"""
    session_id = message.get('session_id', 'default')
    msg = message.get('message', '')
    model = message.get('model', DEFAULT_MODEL)
    
    if session_id not in conversations:
        conversations[session_id] = []
    
    history = conversations[session_id]
    history.append({"role": "user", "content": msg})
    messages = [{"role": h["role"], "content": h["content"]} for h in history]
    
    full_response = ""
    for token in call_ollama_chat(messages, model):
        full_response += token
        emit('response', {'token': token})
    
    history.append({"role": "assistant", "content": full_response})
    emit('response', {'done': True})


@socketio.on('voice_input')
def handle_voice(data):
    """处理语音输入"""
    # Web Speech API 会直接返回文字
    text = data.get('text', '')
    if text:
        emit('voice_text', {'text': text})


# ==================== 主程序 ====================

if __name__ == '__main__':
    print(f"""
==========================================
  Flask + Ollama Chatbot
  Open http://localhost:{PORT}
==========================================
    """)
    
    socketio.run(app, host=HOST, port=PORT, debug=True)
