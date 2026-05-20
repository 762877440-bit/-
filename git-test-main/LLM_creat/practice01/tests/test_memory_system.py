# tests/test_memory_system.py
import pytest
from memory_system import MemorySystem, EphemeralMemorySystem


def test_add_and_search_memory():
    """测试添加和搜索记忆"""
    memory = EphemeralMemorySystem()
    
    # 添加记忆
    memory.add_memory("我叫张三", "用户自我介绍")
    
    # 搜索相关记忆
    results = memory.search_memory("我叫什么")
    
    assert len(results) == 1
    assert "张三" in results[0]["content"]


def test_search_memory_similarity():
    """测试搜索返回语义相关的记忆"""
    memory = EphemeralMemorySystem()
    
    memory.add_memory("我喜欢喝咖啡", "用户偏好")
    memory.add_memory("我住在北京", "用户位置")
    
    # 搜索与咖啡相关的记忆
    results = memory.search_memory("咖啡")
    
    assert len(results) == 1
    assert "咖啡" in results[0]["content"]


def test_delete_memory():
    """测试删除记忆后不再出现在搜索结果中"""
    memory = EphemeralMemorySystem()
    
    memory.add_memory("我叫李四", "用户自我介绍")
    
    # 验证存在
    results = memory.search_memory("李四")
    assert len(results) == 1
    
    # 删除
    memory.delete_memory("李四")
    
    # 验证已删除
    results = memory.search_memory("李四")
    assert len(results) == 0


def test_duplicate_memory_deduplication():
    """测试重复添加相似内容不产生过度冗余"""
    memory = EphemeralMemorySystem()
    
    # 添加相同内容
    memory.add_memory("我喜欢喝茶", "用户偏好")
    memory.add_memory("我喜欢喝茶", "用户偏好")
    
    # 应该只有一条记忆
    results = memory.search_memory("茶")
    assert len(results) == 1


def test_file_based_memory_persistence(tmp_path):
    """测试基于文件的记忆系统持久化"""
    memory = MemorySystem(storage_path=str(tmp_path))
    
    # 添加记忆
    memory.add_memory("测试持久化")
    
    # 创建新实例验证加载
    memory2 = MemorySystem(storage_path=str(tmp_path))
    results = memory2.search_memory("测试")
    
    assert len(results) == 1
    assert "测试持久化" in results[0]["content"]