"""
Step 1: 基础 Flask + Ollama 聊天
最小可运行版本
"""
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Ollama 配置
OLLAMA_URL = "http://localhost:11434"
MODEL = "llama3.2"  # 确保你已下载这个模型: ollama pull llama3.2

@app.route('/')
def index():
    return '''
    <h1>🤖 Ollama 聊天机器人</h1>
    <form action="/chat" method="post">
        <input type="text" name="message" placeholder="输入消息" size="50">
        <button type="submit">发送</button>
    </form>
    '''

@app.route('/chat', methods=['POST'])
def chat():
    message = request.form.get('message', '')
    
    try:
        # 调用 Ollama API
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": message}],
                "stream": False
            },
            timeout=60
        )
        
        if resp.status_code == 200:
            reply = resp.json()['message']['content']
            return f'''
            <h1>🤖 回复</h1>
            <p>{reply}</p>
            <a href="/">返回</a>
            '''
        else:
            return f"<p>错误: {resp.text}</p><a href='/'>返回</a>"
            
    except Exception as e:
        return f"<p>连接失败: {e}</p><a href='/'>返回</a>"

if __name__ == '__main__':
    print(f"""
🚀 启动成功！
    访问: http://localhost:5000
    模型: {MODEL}
    
    确保 Ollama 已启动: ollama serve
    """)
    app.run(port=5000, debug=True)
