# Flask + Ollama Chatbot

基于 Flask 的 Ollama 大模型聊天应用，支持语音输入输出。

## 功能特性

- ✅ 文本聊天（调用 Ollama 本地大模型）
- ✅ 语音输入（Web Speech API / Whisper）
- ✅ 语音输出（TTS）
- ✅ 流式响应
- ✅ 对话历史

## 快速开始

### 1. 安装依赖

```bash
pip install flask flask-socketio openai-whisper pyttsx3 pyaudio
```

### 2. 安装 Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# 从 https://ollama.com/download/windows 下载
```

### 3. 启动 Ollama

```bash
ollama serve
ollama pull llama2  # 或其他模型
```

### 4. 启动聊天应用

```bash
python app.py
```

访问 http://localhost:5000

## 配置

在 `config.py` 中修改：

```python
OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama2"
```

## API 接口

### 聊天

```bash
POST /api/chat
Content-Type: application/json

{
    "message": "你好",
    "model": "llama2"
}
```

### 语音转文字 (STT)

```bash
POST /api/stt
Content-Type: audio/wav

# 上传音频文件
```

### 文字转语音 (TTS)

```bash
POST /api/tts
Content-Type: application/json

{
    "text": "你好，我是 AI 助手",
    "lang": "zh"
}
```

## 目录结构

```
flask-ollama-chatbot/
├── app.py              # 主应用
├── config.py           # 配置
├── static/
│   ├── index.html      # 前端页面
│   ├── style.css       # 样式
│   └── script.js       # 前端脚本
├── templates/
│   └── chat.html       # 聊天页面
└── README.md
```
