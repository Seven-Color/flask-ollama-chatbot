"""
Flask + Ollama 聊天应用 (纯 Flask 版本)
简单稳定，兼容性好
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, Response, stream_with_context

# 配置
SECRET_KEY = "ollama-chat-secret-key"
HOST = "127.0.0.1"
PORT = 6000
OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama2"
MAX_HISTORY = 20

# 创建 Flask 应用
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# 对话历史
conversations = {}

# ==================== LLM 服务 ====================

def call_ollama(prompt, history, model):
    """调用 Ollama API"""
    import requests
    
    url = f"{OLLAMA_BASE_URL}/api/chat"
    
    # 构建消息
    messages = []
    for h in history:
        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": model,
        "messages": messages[-MAX_HISTORY:],
        "stream": True,
    }
    
    try:
        response = requests.post(url, json=payload, stream=True, timeout=120)
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    if "message" in data:
                        yield data["message"].get("content", "")
                except:
                    continue
    except Exception as e:
        yield f"Error: {str(e)}"


# ==================== 路由 ====================

@app.route('/')
def index():
    """主页"""
    return render_template('chat.html')


@app.route('/api/models')
def get_models():
    """获取可用模型"""
    import requests
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        models = response.json().get("models", [])
        return jsonify({"models": [m["name"] for m in models]})
    except:
        return jsonify({"models": [DEFAULT_MODEL]})


@app.route('/api/chat', methods=['POST'])
def chat():
    """聊天接口（同步）"""
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
    
    # 调用 Ollama
    full_response = ""
    for token in call_ollama(message, history, model):
        full_response += token
    
    # 更新历史
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": full_response})
    
    return jsonify({"response": full_response, "session_id": session_id})


@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """聊天接口（流式）"""
    data = request.json
    message = data.get('message', '')
    model = data.get('model', DEFAULT_MODEL)
    session_id = data.get('session_id', 'default')
    
    if not message:
        return jsonify({"error": "Empty message"}), 400
    
    if session_id not in conversations:
        conversations[session_id] = []
    history = conversations[session_id]
    
    def generate():
        full_response = ""
        for token in call_ollama(message, history, model):
            full_response += token
            yield f"data: {json.dumps({'token': token})}\n\n"
        
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": full_response})
        yield f"data: {json.dumps({'done': True})}\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')


@app.route('/api/history', methods=['GET', 'DELETE'])
def history():
    """历史记录"""
    session_id = request.args.get('session_id', 'default')
    
    if request.method == 'DELETE':
        if session_id in conversations:
            del conversations[session_id]
        return jsonify({"status": "cleared"})
    
    return jsonify({"history": conversations.get(session_id, [])})


# ==================== 主程序 ====================

if __name__ == '__main__':
    print(f"""
==========================================
  Flask + Ollama Chatbot (纯 Flask)
  访问 http://localhost:{PORT}
==========================================
    """)
    
    app.run(host=HOST, port=PORT, debug=False, threaded=True)
