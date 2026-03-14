"""
STT Service - 语音识别服务
支持多种后端：Web Speech API, Whisper
"""

import os
import json
from typing import Optional, Dict, Any


class STTService:
    """
    语音识别服务
    支持多种模式：
    - websocket: 浏览器 Web Speech API（前端处理）
    - whisper: OpenAI Whisper（本地/云端）
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.mode = self.config.get('mode', 'websocket')  # websocket / whisper
        self.language = self.config.get('language', 'zh-CN')
        
        # Whisper 配置
        self.whisper_model = self.config.get('whisper_model', 'base')
        self.whisper_device = self.config.get('whisper_device', 'cpu')
        self._whisper_model = None
    
    def _init_whisper(self):
        """初始化 Whisper 模型"""
        if self._whisper_model is None:
            try:
                import whisper
                self._whisper_model = whisper.load_model(
                    self.whisper_model, 
                    device=self.whisper_device
                )
            except ImportError:
                raise ImportError("请安装 openai-whisper: pip install openai-whisper")
    
    def transcribe(self, audio_data, language: Optional[str] = None) -> str:
        """
        语音转文字
        """
        language = language or self.language
        
        if self.mode == 'whisper':
            return self._transcribe_whisper(audio_data, language)
        else:
            # Web Speech API 模式需要前端处理
            return self._transcribe_websocket(audio_data)
    
    def _transcribe_whisper(self, audio_file, language: str) -> str:
        """使用 Whisper 转写"""
        self._init_whisper()
        
        # 保存临时文件
        temp_path = "/tmp/stt_input.wav"
        audio_file.save(temp_path)
        
        try:
            import whisper
            result = self._whisper_model.transcribe(temp_path, language=language)
            text = result["text"]
            
            os.remove(temp_path)
            return text
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise RuntimeError(f"Whisper 转写失败: {str(e)}")
    
    def _transcribe_websocket(self, audio_file) -> str:
        """
        Web Speech API 模式
        实际识别由前端浏览器完成，此处接收已转写的文本
        """
        # 前端 Web Speech API 直接返回文字
        # 这里接收 JSON 格式的转写结果
        try:
            data = json.loads(audio_file.read().decode('utf-8'))
            return data.get('text', '')
        except:
            return ""
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return {
            'mode': self.mode,
            'language': self.language,
            'whisper_model': self.whisper_model,
            'whisper_device': self.whisper_device,
            'available_modes': ['websocket', 'whisper'],
            'available_languages': ['zh-CN', 'en-US', 'ja-JP', 'ko-KR']
        }
    
    def update_config(self, config: Dict[str, Any]):
        """更新配置"""
        if 'mode' in config:
            self.mode = config['mode']
        if 'language' in config:
            self.language = config['language']
        if 'whisper_model' in config:
            self.whisper_model = config['whisper_model']
            self._whisper_model = None  # 重置模型
        if 'whisper_device' in config:
            self.whisper_device = config['whisper_device']
            self._whisper_model = None


class WebSpeechSTT:
    """
    Web Speech API 前端包装器
    用于生成前端 JavaScript 代码
    """
    
    @staticmethod
    def get_js_code() -> str:
        """获取 Web Speech API 调用代码"""
        return """
// Web Speech API 封装
class WebSpeechSTT {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        
        if ('webkitSpeechRecognition' in window) {
            this.recognition = new webkitSpeechRecognition();
        } else if ('SpeechRecognition' in window) {
            this.recognition = new SpeechRecognition();
        }
        
        if (this.recognition) {
            this.recognition.continuous = false;
            this.recognition.interimResults = true;
            this.recognition.lang = 'zh-CN';
        }
    }
    
    start(lang = 'zh-CN') {
        return new Promise((resolve, reject) => {
            if (!this.recognition) {
                reject(new Error('浏览器不支持语音识别'));
                return;
            }
            
            this.recognition.lang = lang;
            
            this.recognition.onstart = () => {
                this.isListening = true;
            };
            
            this.recognition.onresult = (event) => {
                let finalTranscript = '';
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    if (event.results[i].isFinal) {
                        finalTranscript += event.results[i][0].transcript;
                    }
                }
                if (finalTranscript) {
                    resolve(finalTranscript);
                }
            };
            
            this.recognition.onerror = (event) => {
                this.isListening = false;
                reject(new Error(event.error));
            };
            
            this.recognition.onend = () => {
                this.isListening = false;
            };
            
            this.recognition.start();
        });
    }
    
    stop() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
    }
    
    isSupported() {
        return this.recognition !== null;
    }
}
"""
