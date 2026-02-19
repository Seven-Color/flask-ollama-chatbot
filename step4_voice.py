"""
Step 4: 语音输入 - 麦克风录音
支持按住说话，自动识别
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
        .input-area { padding: 15px; background: white; border-top: 1px solid #eee; }
        .input-row { display: flex; gap: 10px; }
        #userInput {
            flex: 1; padding: 15px; border: 2px solid #ddd; border-radius: 25px;
            font-size: 1rem; outline: none;
        }
        #userInput:focus { border-color: #667eea; }
        #sendBtn {
            padding: 12px 25px; background: linear-gradient(135deg, #667eea, #764ba2);
            color: white; border: none; border-radius: 25px; cursor: pointer; font-size: 1rem;
        }
        .toolbar { display: flex; gap: 10px; margin-top: 10px; }
        .tool-btn {
            padding: 10px 20px; background: #f0f0f0; border: none; border-radius: 20px;
            cursor: pointer; font-size: 0.9rem; display: flex; align-items: center; gap: 5px;
        }
        .tool-btn:hover { background: #e0e0e0; }
        .tool-btn.recording { background: #ff4757; color: white; animation: pulse 1s infinite; }
        @keyframes pulse { 0%,100%{transform:scale(1);} 50%{transform:scale(1.05);} }
    </style>
</head>
<body>
    <div class="container">
        <header><h1>🤖 Ollama 聊天机器人 (语音版)</h1></header>
        <div class="messages" id="messages">
            <div class="message">
                <div class="avatar">AI</div>
                <div class="content">你好！可以说语音或打字~</div>
            </div>
        </div>
        <div class="input-area">
            <div class="input-row">
                <input type="text" id="userInput" placeholder="输入消息..." onkeydown="if(event.key==='Enter')sendMessage()">
                <button id="sendBtn" onclick="sendMessage()">发送</button>
            </div>
            <div class="toolbar">
                <button class="tool-btn" id="micBtn" onmousedown="startRecording()" onmouseup="stopRecording()" ontouchstart="startRecording()" ontouchend="stopRecording()">
                    🎤 按住说话
                </button>
                <button class="tool-btn" onclick="clearChat()">🗑️ 清空</button>
            </div>
        </div>
    </div>
    <script>
        const messages = document.getElementById('messages');
        let mediaRecorder = null;
        let audioChunks = [];
        
        async function sendMessage() {
            const input = document.getElementById('userInput');
            const msg = input.value.trim();
            if (!msg) return;
            
            addMessage(msg, 'user');
            input.value = '';
            
            const loading = addMessage('', 'ai');
            
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
                    loading.textContent += decoder.decode(value);
                    messages.scrollTop = messages.scrollHeight;
                }
            } catch(e) {
                loading.textContent = '错误: ' + e.message;
            }
        }
        
        function addMessage(text, sender) {
            const div = document.createElement('div');
            div.className = 'message ' + sender;
            div.innerHTML = `<div class="avatar">${sender==='user'?'你':'AI'}</div><div class="content">${text}</div>`;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
            return div.querySelector('.content');
        }
        
        async function startRecording() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({audio: true});
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                
                mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
                mediaRecorder.onstop = () => {
                    const audioBlob = new Blob(audioChunks, {type: 'audio/webm'});
                    // 暂时显示文字提示
                    addMessage('[语音消息已录制]', 'user');
                    sendMessage();
                };
                
                mediaRecorder.start();
                document.getElementById('micBtn').classList.add('recording');
                document.getElementById('micBtn').textContent = '🔴 松开结束';
            } catch(e) {
                addMessage('无法录音: ' + e.message, 'ai');
            }
        }
        
        function stopRecording() {
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                mediaRecorder.stop();
                mediaRecorder.stream.getTracks().forEach(t => t.stop());
                document.getElementById('micBtn').classList.remove('recording');
                document.getElementById('micBtn').textContent = '🎤 按住说话';
            }
        }
        
        function clearChat() {
            messages.innerHTML = '<div class="message"><div class="avatar">AI</div><div class="content">已清空~</div></div>';
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
                json={"model": MODEL, "messages": [{"role": "user", "content": message}], "stream": True},
                stream=True, timeout=120
            )
            for line in resp.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        content = chunk.get('message', {}).get('content', '')
                        if content: yield f"data: {content}\n\n"
                    except: continue
        except Exception as e:
            yield f"data: 错误: {str(e)}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    print("Step 4: Voice Input")
    print("Visit: http://localhost:5000")
    app.run(port=5000, debug=True)
