"""
Step 2: 带 Web UI 的聊天界面
在 Step 1 基础上增加美观的聊天界面
"""
from flask import Flask, render_template_string, request, jsonify
import requests

app = Flask(__name__)

# ============== 配置 ==============
OLLAMA_URL = "http://localhost:11434"
MODEL = "llama3.2"

# ============== HTML 模板 ==============
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
        header h1 { font-size: 1.5rem; }
        .messages {
            flex: 1; padding: 20px; overflow-y: auto; background: #f5f5f5;
        }
        .message {
            display: flex; gap: 10px; margin-bottom: 15px; max-width: 80%;
        }
        .message.user { align-self: flex-end; flex-direction: row-reverse; }
        .avatar {
            width: 40px; height: 40px; border-radius: 50%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;
        }
        .message.user .avatar { background: linear-gradient(135deg, #11998e, #38ef7d); }
        .content {
            padding: 12px 18px; border-radius: 18px; background: white;
            line-height: 1.5; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .message.user .content { background: linear-gradient(135deg, #667eea, #764ba2); color: white; }
        .input-area {
            padding: 15px; background: white; border-top: 1px solid #eee;
            display: flex; gap: 10px;
        }
        #userInput {
            flex: 1; padding: 15px; border: 2px solid #ddd; border-radius: 25px;
            font-size: 1rem; outline: none;
        }
        #userInput:focus { border-color: #667eea; }
        #sendBtn {
            padding: 12px 25px; background: linear-gradient(135deg, #667eea, #764ba2);
            color: white; border: none; border-radius: 25px; cursor: pointer; font-size: 1rem;
        }
        #sendBtn:hover { transform: translateY(-2px); }
    </style>
</head>
<body>
    <div class="container">
        <header><h1>🤖 Ollama 聊天机器人</h1></header>
        <div class="messages" id="messages">
            <div class="message">
                <div class="avatar">AI</div>
                <div class="content">你好！我是 AI 助手，有什么可以帮你的？</div>
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
            
            const loading = addMessage('正在思考...', 'ai');
            
            try {
                const resp = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: msg})
                });
                const data = await resp.json();
                loading.remove();
                
                if (data.reply) {
                    addMessage(data.reply, 'ai');
                } else {
                    addMessage('错误: ' + (data.error || '未知错误'), 'ai');
                }
            } catch(e) {
                loading.remove();
                addMessage('网络错误: ' + e.message, 'ai');
            }
        }
        
        function addMessage(text, sender) {
            const div = document.createElement('div');
            div.className = 'message ' + sender;
            div.innerHTML = `<div class="avatar">${sender==='user'?'你':'AI'}</div><div class="content">${text}</div>`;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
            return div;
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    
    if not message:
        return jsonify({'error': '消息不能为空'}), 400
    
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": message}],
                "stream": False
            },
            timeout=120
        )
        
        if resp.status_code == 200:
            reply = resp.json()['message']['content']
            return jsonify({'reply': reply})
        else:
            return jsonify({'error': resp.text}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Flask Ollama Chat - Step 2")
    print("Visit: http://localhost:5000")
    app.run(port=5000, debug=True)
