"""
TTS Service - 语音合成服务
支持多种后端：pyttsx3, gtts, Edge TTS
"""

import base64
import os
import json
from typing import Optional, Dict, Any


class TTSService:
    """
    语音合成服务
    支持多种模式：
    - pyttsx3: 本地语音合成（离线）
    - gtts: Google TTS（在线）
    - edge: Microsoft Edge TTS（在线，更自然）
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.mode = self.config.get('mode', 'pyttsx3')  # pyttsx3 / gtts / edge
        self.language = self.config.get('language', 'zh')
        self.rate = self.config.get('rate', 150)  # 语速
        self.volume = self.config.get('volume', 1.0)  # 音量
        self.voice = self.config.get('voice', None)  # 声音
        
        # Edge TTS 声音选项
        self.edge_voice = self.config.get('edge_voice', 'zh-CN-XiaoxiaoNeural')
    
    def synthesize(self, text: str, language: Optional[str] = None) -> str:
        """
        文字转语音
        返回 base64 编码的音频数据
        """
        language = language or self.language
        
        if self.mode == 'pyttsx3':
            return self._synthesize_pyttsx3(text)
        elif self.mode == 'gtts':
            return self._synthesize_gtts(text, language)
        elif self.mode == 'edge':
            return self._synthesize_edge(text, language)
        else:
            raise ValueError(f"不支持的 TTS 模式: {self.mode}")
    
    def _synthesize_pyttsx3(self, text: str) -> str:
        """使用 pyttsx3 本地合成"""
        try:
            import pyttsx3
            
            engine = pyttsx3.init()
            
            # 设置参数
            engine.setProperty('rate', self.rate)
            engine.setProperty('volume', self.volume)
            
            if self.voice:
                engine.setProperty('voice', self.voice)
            else:
                # 尝试获取中文语音
                voices = engine.getProperty('voices')
                for v in voices:
                    if 'chinese' in v.name.lower() or 'zh' in v.languages.lower():
                        engine.setProperty('voice', v.id)
                        break
            
            # 保存到文件
            output_path = "/tmp/tts_output.mp3"
            engine.save_to_file(text, output_path)
            engine.runAndWait()
            
            # 读取并编码
            with open(output_path, 'rb') as f:
                audio_data = base64.b64encode(f.read()).decode()
            
            os.remove(output_path)
            return audio_data
            
        except Exception as e:
            raise RuntimeError(f"pyttsx3 合成失败: {str(e)}")
    
    def _synthesize_gtts(self, text: str, language: str) -> str:
        """使用 Google TTS"""
        try:
            from gtts import gTTS
            
            # 语言代码映射
            lang_map = {'zh': 'zh-CN', 'en': 'en', 'ja': 'ja', 'ko': 'ko'}
            lang_code = lang_map.get(language, 'zh-CN')
            
            # 保存到文件
            output_path = "/tmp/tts_output.mp3"
            tts = gTTS(text=text, lang=lang_code)
            tts.save(output_path)
            
            # 读取并编码
            with open(output_path, 'rb') as f:
                audio_data = base64.b64encode(f.read()).decode()
            
            os.remove(output_path)
            return audio_data
            
        except ImportError:
            raise ImportError("请安装 gTTS: pip install gTTS")
        except Exception as e:
            raise RuntimeError(f"gTTS 合成失败: {str(e)}")
    
    def _synthesize_edge(self, text: str, language: str) -> str:
        """使用 Microsoft Edge TTS"""
        try:
            from edge_tts import Communicate
            
            # 语言-声音映射
            voice_map = {
                'zh': 'zh-CN-XiaoxiaoNeural',
                'en': 'en-US-AriaNeural',
                'ja': 'ja-JP-NanamiNeural',
                'ko': 'ko-KR-SunHiNeural'
            }
            
            voice = self.edge_voice or voice_map.get(language, 'zh-CN-XiaoxiaoNeural')
            
            # 生成
            output_path = "/tmp/tts_output.mp3"
            
            async def generate():
                communicate = Communicate(text, voice)
                await communicate.save(output_path)
            
            # 运行异步
            import asyncio
            asyncio.run(generate())
            
            # 读取并编码
            with open(output_path, 'rb') as f:
                audio_data = base64.b64encode(f.read()).decode()
            
            os.remove(output_path)
            return audio_data
            
        except ImportError:
            raise ImportError("请安装 edge-tts: pip install edge-tts")
        except Exception as e:
            raise RuntimeError(f"Edge TTS 合成失败: {str(e)}")
    
    def get_available_voices(self) -> list:
        """获取可用声音列表"""
        if self.mode == 'pyttsx3':
            try:
                import pyttsx3
                engine = pyttsx3.init()
                voices = engine.getProperty('voices')
                return [{'id': v.id, 'name': v.name, 'languages': v.languages} 
                        for v in voices]
            except:
                return []
        elif self.mode == 'edge':
            return [
                {'id': 'zh-CN-XiaoxiaoNeural', 'name': '晓晓 (女)', 'lang': 'zh'},
                {'id': 'zh-CN-YunxiNeural', 'name': '云希 (男)', 'lang': 'zh'},
                {'id': 'zh-CN-YunyangNeural', 'name': '云扬 (男)', 'lang': 'zh'},
                {'id': 'en-US-AriaNeural', 'name': 'Aria (女)', 'lang': 'en'},
                {'id': 'en-US-GuyNeural', 'name': 'Guy (男)', 'lang': 'en'},
            ]
        else:
            return []
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return {
            'mode': self.mode,
            'language': self.language,
            'rate': self.rate,
            'volume': self.volume,
            'voice': self.voice,
            'edge_voice': self.edge_voice,
            'available_modes': ['pyttsx3', 'gtts', 'edge'],
            'available_voices': self.get_available_voices()
        }
    
    def update_config(self, config: Dict[str, Any]):
        """更新配置"""
        if 'mode' in config:
            self.mode = config['mode']
        if 'language' in config:
            self.language = config['language']
        if 'rate' in config:
            self.rate = config['rate']
        if 'volume' in config:
            self.volume = config['volume']
        if 'voice' in config:
            self.voice = config['voice']
        if 'edge_voice' in config:
            self.edge_voice = config['edge_voice']


class BrowserTTS:
    """
    浏览器原生 TTS 包装器
    """
    
    @staticmethod
    def get_js_code() -> str:
        """获取浏览器 TTS 调用代码"""
        return """
// 浏览器原生 SpeechSynthesis API 封装
class BrowserTTS {
    constructor() {
        this.synth = window.speechSynthesis;
        this.voices = [];
        this.isSpeaking = false;
        
        // 加载声音列表
        this.synth.onvoiceschanged = () => {
            this.voices = this.synth.getVoices();
        };
    }
    
    speak(text, options = {}) {
        return new Promise((resolve, reject) => {
            if (!this.synth) {
                reject(new Error('浏览器不支持语音合成'));
                return;
            }
            
            // 停止当前语音
            this.synth.cancel();
            
            const utterance = new SpeechSynthesisUtterance(text);
            
            // 设置参数
            utterance.rate = options.rate || 1.0;
            utterance.volume = options.volume || 1.0;
            utterance.pitch = options.pitch || 1.0;
            
            // 选择声音
            if (options.voice) {
                const voice = this.voices.find(v => v.name === options.voice);
                if (voice) {
                    utterance.voice = voice;
                }
            } else {
                // 默认选择中文
                const zhVoice = this.voices.find(v => v.lang.startsWith('zh'));
                if (zhVoice) {
                    utterance.voice = zhVoice;
                }
            }
            
            utterance.onstart = () => {
                this.isSpeaking = true;
            };
            
            utterance.onend = () => {
                this.isSpeaking = false;
                resolve();
            };
            
            utterance.onerror = (e) => {
                this.isSpeaking = false;
                reject(e);
            };
            
            this.synth.speak(utterance);
        });
    }
    
    stop() {
        if (this.synth) {
            this.synth.cancel();
            this.isSpeaking = false;
        }
    }
    
    getVoices() {
        return this.voices.map(v => ({
            name: v.name,
            lang: v.lang,
            localService: v.localService
        }));
    }
    
    isSupported() {
        return this.synth !== null;
    }
}
"""
