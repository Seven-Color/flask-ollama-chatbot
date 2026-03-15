"""
Memory Service - 记忆服务
负责存储和检索用户记忆
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any


class MemoryService:
    """
    记忆服务
    使用本地文件系统存储记忆（Markdown格式）
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # 记忆库目录
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.memory_dir = os.path.join(base_dir, 'memory')
        os.makedirs(self.memory_dir, exist_ok=True)
        
        # 记忆库文件
        self.memory_file = os.path.join(self.memory_dir, 'user_memory.md')
        self.conversations_file = os.path.join(self.memory_dir, 'conversations.json')
        
        # 初始化记忆库
        self._init_memory()
        
        # 当前胶囊
        self.current_capsule = {
            'content': [],
            'created_at': datetime.now().isoformat()
        }
    
    def _init_memory(self):
        """初始化记忆库"""
        if not os.path.exists(self.memory_file):
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                f.write("# 用户记忆库\n\n")
                f.write("## 个人信息\n\n")
                f.write("- **姓名**: \n")
                f.write("- **年龄**: \n")
                f.write("- **职业**: \n")
                f.write("- **爱好**: \n")
                f.write("\n## 生活习惯\n\n")
                f.write("- **作息时间**: \n")
                f.write("- **饮食习惯**: \n")
                f.write("- **运动偏好**: \n")
                f.write("\n## 重要日期\n\n")
                f.write("- 生日: \n")
                f.write("- 纪念日: \n")
                f.write("\n## 历史对话摘要\n\n")
        
        if not os.path.exists(self.conversations_file):
            self._save_conversations([])
    
    def _save_conversations(self, conversations: List[Dict]):
        """保存对话历史"""
        with open(self.conversations_file, 'w', encoding='utf-8') as f:
            json.dump(conversations, f, ensure_ascii=False, indent=2)
    
    def _load_conversations(self) -> List[Dict]:
        """加载对话历史"""
        if os.path.exists(self.conversations_file):
            with open(self.conversations_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def add_to_capsule(self, text: str):
        """添加内容到当前语音胶囊"""
        self.current_capsule['content'].append({
            'text': text,
            'timestamp': datetime.now().isoformat()
        })
    
    def summarize_capsule(self, llm_service) -> str:
        """
        总结当前胶囊内容
        使用 LLM 服务进行总结
        """
        if not self.current_capsule['content']:
            return ""
        
        # 构建总结提示
        content_texts = [item['text'] for item in self.current_capsule['content']]
        combined_text = "\n".join(content_texts)
        
        prompt = f"""请分析以下用户语音输入，提取关键信息并总结：

用户输入：
{combined_text}

请从以下方面提取信息：
1. 用户的兴趣爱好
2. 用户的日常生活习惯
3. 用户提到的重要事件或安排
4. 用户的情绪状态
5. 任何值得记忆的个人信息

请用简洁的markdown格式总结。"""
        
        try:
            summary = llm_service.chat(prompt)
            
            # 保存到记忆库
            self._append_to_memory(summary)
            
            # 清空当前胶囊
            self.current_capsule = {
                'content': [],
                'created_at': datetime.now().isoformat()
            }
            
            return summary
        except Exception as e:
            return f"总结失败: {str(e)}"
    
    def _append_to_memory(self, content: str):
        """追加内容到记忆库"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(self.memory_file, 'a', encoding='utf-8') as f:
            f.write(f"\n### {timestamp}\n\n")
            f.write(f"{content}\n")
    
    def search_memory(self, query: str, limit: int = 5) -> str:
        """
        搜索记忆库
        返回与查询相关的记忆内容
        """
        if not os.path.exists(self.memory_file):
            return ""
        
        # 简单实现：读取记忆库内容
        with open(self.memory_file, 'r', encoding='utf-8') as f:
            memory_content = f.read()
        
        # 如果查询为空，返回全部内容
        if not query.strip():
            return memory_content[:2000] if len(memory_content) > 2000 else memory_content
        
        # 简单关键词匹配（生产环境可用向量检索）
        query_keywords = query.lower().split()
        lines = memory_content.split('\n')
        relevant_lines = []
        
        for line in lines:
            line_lower = line.lower()
            if any(kw in line_lower for kw in query_keywords):
                relevant_lines.append(line)
        
        if relevant_lines:
            return '\n'.join(relevant_lines[:limit * 2])
        
        return memory_content[:1000]
    
    def get_memory_summary(self) -> str:
        """获取记忆库摘要"""
        if not os.path.exists(self.memory_file):
            return "记忆库为空"
        
        with open(self.memory_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 返回前1000字符
        return content[:1000] + "..." if len(content) > 1000 else content
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return {
            'memory_dir': self.memory_dir,
            'memory_file': self.memory_file,
            'capsule_size': len(self.current_capsule['content'])
        }
    
    def update_config(self, config: Dict[str, Any]):
        """更新配置"""
        pass
