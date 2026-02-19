"""
Step 3: 流式响应 - 打字机效果
让 AI 回复逐字显示，更有交互感
"""
from flask import Flask, render_template_string, request, jsonify, Response
import requests
import json

app = Flask(__name__)

OLLAMA_URL = "http://localhost:11434"
MODEL = "llama3.2"

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Ollama 聊天机器人</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            height: 100vh; display: flex; justify-content: center; align-items: center;
        }
        .container {
            width: 90%; max-width: 800px; height: 85vh;
            background: white; border-radius: 20px; overflow: hidden;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            display: flex; flex-direction: column;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 20px; text-align: center;
        }
        .messages { flex: 1; padding: 20px; overflow-y: auto; background: #f5f5f5; }
        .message { display: flex; gap: 10px; margin-bottom: 15px; max-width: 80%; }
        .message.user { align-self: flex-end; flex-direction: row-reverse; }
        .avatar {
            width: 40px; height: 40px; border-radius: 50%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;
        }
        .message.user .avatar { background: linear-gradient(135deg, #11998e, #38ef7d); }
        .content {
            padding: 12px 18px; border-radius: 18px; background: white;
            line-height: 1.6; box-shadow: 0 2px 5px rgba(0,0,0,0.1); white-space: pre-wrap;
        }
        .message.user .content { background: linear-gradient(135deg, #667eea, #764ba2); color: white; }
        .typing::after { content: '|'; animation: blink 0.7s infinite; }
        @keyframes blink { 50% { opacity: 0; } }
        .input-area { padding: 15px; background: white; border-top: 1px solid #eee; display: flex; gap: 10px; }
        #userInput {
            flex: 1; padding: 15px; border: 2px solid #ddd; border-radius: 25px;
            font-size: 1rem; outline: none;
        }
        #userInput:focus { border-color: #667eea; }
        #sendBtn {
            padding: 12px 25px; background: linear-gradient(135deg, #667eea, #764ba2);
            color: white; border: none; border-radius: 25px; cursor: pointer; font-size: 1rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <header><h1>🤖 Ollama 聊天机器人 (流式响应)</h1></header>
        <div class="messages" id="messages">
            <div class="message">
                <div class="avatar">AI</div>
                <div class="content">你好！我是 AI 助手，开始聊天吧~</div>
            </div>
        </div>
        <div class="input-area">
            <input type="text" id="userInput" placeholder="输入消息..." onkeydown="if(event.key==='Enter')sendMessage()">
            <button id="sendBtn" onclick="sendMessage()">发送</button>
        </div>
    </div>
    <script>
        const messages = document.getElementById('messages');
        
        async function sendMessage() {
            const input = document.getElementById('userInput');
            const msg = input.value.trim();
            if (!msg) return;
            
            addMessage(msg, 'user');
            input.value = '';
            
            const loading = addMessage('', 'ai', true);
            
            try {
                const resp = await fetch('/chat/stream', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: msg})
                });
                
                const reader = resp.body.getReader();
                const decoder = new TextDecoder();
                
                while (true) {
                    const {done, value} = await reader.read();
                    if (done) break;
                    const text = decoder.decode(value);
                    loading.textContent += text;
                    messages.scrollTop = messages.scrollHeight;
                }
                loading.classList.remove('typing');
                
            } catch(e) {
                loading.textContent = '错误: ' + e.message;
                loading.classList.remove('typing');
            }
        }
        
        function addMessage(text, sender, isTyping = false) {
            const div = document.createElement('div');
            div.className = 'message ' + sender;
            if (isTyping) div.classList.add('typing');
            div.innerHTML = `<div class="avatar">${sender==='user'?'你':'AI'}</div><div class="content">${text}</div>`;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
            return div.querySelector('.content');
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/chat/stream', methods=['POST'])
def chat_stream():
    data = request.json
    message = data.get('message', '')
    
    def generate():
        try:
            resp = requests.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": MODEL,
                    "messages": [{"role": "user", "content": message}],
                    "stream": True
                },
                stream=True,
                timeout=120
            )
            
            for line in resp.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        content = chunk.get('message', {}).get('content', '')
                        if content:
                            yield f"data: {content}\n\n"
                    except:
                        continue
        except Exception as e:
            yield f"data: 错误: {str(e)}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    print("Step 3: Stream Response")
    print("Visit: http://localhost:5000")
    app.run(port=5000, debug=True)
