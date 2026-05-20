# memory_system.py
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

# 简化的记忆系统实现（使用JSON文件存储）
class MemorySystem:
    def __init__(self, storage_path: str = "./memory"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        self.memory_file = os.path.join(storage_path, "memories.json")
        self._load_memories()
    
    def _load_memories(self):
        """从文件加载记忆"""
        if os.path.exists(self.memory_file):
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                self.memories = json.load(f)
        else:
            self.memories = []
    
    def _save_memories(self):
        """保存记忆到文件"""
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.memories, f, ensure_ascii=False, indent=2)
    
    def add_memory(self, content: str, context: Optional[str] = None):
        """
        添加记忆
        :param content: 记忆内容
        :param context: 上下文（可选）
        """
        memory = {
            "id": len(self.memories) + 1,
            "content": content,
            "context": context,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # 检查是否存在相似记忆（简化去重）
        existing_idx = None
        for i, m in enumerate(self.memories):
            if content in m["content"] or m["content"] in content:
                existing_idx = i
                break
        
        if existing_idx is not None:
            # 更新现有记忆
            self.memories[existing_idx]["content"] = content
            self.memories[existing_idx]["updated_at"] = datetime.now().isoformat()
        else:
            self.memories.append(memory)
        
        self._save_memories()
    
    def search_memory(self, query: str, top_k: int = 5, similarity_threshold: float = 0.3) -> List[Dict]:
        """
        搜索相关记忆（简化的字符串匹配）
        :param query: 查询字符串
        :param top_k: 返回数量
        :param similarity_threshold: 相似度阈值
        :return: 匹配的记忆列表
        """
        results = []
        
        for memory in self.memories:
            # 简单的关键词匹配相似度计算
            memory_text = memory["content"] + " " + (memory["context"] or "")
            query_words = query.lower().split()
            match_count = sum(1 for word in query_words if word in memory_text.lower())
            similarity = match_count / len(query_words) if query_words else 0
            
            if similarity >= similarity_threshold:
                results.append({
                    "memory": memory,
                    "similarity": similarity
                })
        
        # 按相似度排序
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return [r["memory"] for r in results[:top_k]]
    
    def delete_memory(self, keyword: str) -> bool:
        """
        删除包含关键词的记忆
        :param keyword: 关键词
        :return: 是否删除成功
        """
        original_count = len(self.memories)
        self.memories = [m for m in self.memories if keyword.lower() not in m["content"].lower()]
        if len(self.memories) != original_count:
            self._save_memories()
            return True
        return False
    
    def get_all_memories(self) -> List[Dict]:
        """获取所有记忆"""
        return self.memories
    
    def clear_all(self):
        """清空所有记忆"""
        self.memories = []
        self._save_memories()

# Mock向量数据库实现（用于测试）
class EphemeralMemorySystem:
    """内存中的临时记忆系统，用于测试"""
    def __init__(self):
        self.memories = []
    
    def add_memory(self, content: str, context: Optional[str] = None):
        # 检查是否存在相似记忆（去重）
        for m in self.memories:
            if content == m["content"]:
                # 如果内容相同，不重复添加
                return
        
        memory = {
            "id": len(self.memories) + 1,
            "content": content,
            "context": context,
            "created_at": datetime.now().isoformat()
        }
        self.memories.append(memory)
    
    def search_memory(self, query: str, top_k: int = 5, similarity_threshold: float = 0.3) -> List[Dict]:
        """
        搜索相关记忆
        :param query: 查询字符串
        :param top_k: 返回数量
        :param similarity_threshold: 相似度阈值
        :return: 匹配的记忆列表
        """
        results = []
        
        for memory in self.memories:
            memory_text = memory["content"] + " " + (memory["context"] or "")
            memory_text_lower = memory_text.lower()
            query_lower = query.lower()
            
            # 检查记忆内容中是否包含查询中的任意字符（简单的字符匹配）
            match_chars = sum(1 for char in query_lower if char in memory_text_lower)
            similarity = match_chars / len(query_lower) if query_lower else 0
            
            if similarity >= similarity_threshold:
                results.append({
                    "memory": memory,
                    "similarity": similarity
                })
        
        # 按相似度排序
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return [r["memory"] for r in results[:top_k]]
    
    def delete_memory(self, keyword: str) -> bool:
        original_count = len(self.memories)
        self.memories = [m for m in self.memories if keyword.lower() not in m["content"].lower()]
        return len(self.memories) != original_count
    
    def get_all_memories(self) -> List[Dict]:
        """获取所有记忆"""
        return self.memories