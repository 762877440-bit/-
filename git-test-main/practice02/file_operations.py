import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


def list_directory_files(directory_path: str) -> Dict[str, Any]:
    """
    列出某个目录下的所有文件及其属性信息
    
    Args:
        directory_path: 目录路径
    
    Returns:
        包含文件信息的字典
    """
    if not os.path.exists(directory_path):
        return {
            "success": False,
            "error": f"目录不存在: {directory_path}"
        }
    
    if not os.path.isdir(directory_path):
        return {
            "success": False,
            "error": f"路径不是目录: {directory_path}"
        }
    
    files_info = []
    
    try:
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            stat_info = os.stat(item_path)
            
            file_info = {
                "name": item,
                "path": item_path,
                "type": "directory" if os.path.isdir(item_path) else "file",
                "size": stat_info.st_size,
                "size_human": _format_size(stat_info.st_size),
                "created_time": datetime.fromtimestamp(stat_info.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                "modified_time": datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "accessed_time": datetime.fromtimestamp(stat_info.st_atime).strftime("%Y-%m-%d %H:%M:%S")
            }
            
            files_info.append(file_info)
        
        return {
            "success": True,
            "directory": directory_path,
            "total_items": len(files_info),
            "files": files_info
        }
    
    except PermissionError:
        return {
            "success": False,
            "error": f"没有权限访问目录: {directory_path}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"列出目录文件时出错: {str(e)}"
        }


def _format_size(size_bytes: int) -> str:
    """
    格式化文件大小为人类可读格式
    
    Args:
        size_bytes: 文件大小（字节）
    
    Returns:
        格式化后的文件大小字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def rename_file(directory_path: str, old_name: str, new_name: str) -> Dict[str, Any]:
    """
    修改某个目录下某个文件的名字
    
    Args:
        directory_path: 目录路径
        old_name: 原文件名
        new_name: 新文件名
    
    Returns:
        操作结果字典
    """
    old_path = os.path.join(directory_path, old_name)
    new_path = os.path.join(directory_path, new_name)
    
    if not os.path.exists(old_path):
        return {
            "success": False,
            "error": f"文件不存在: {old_path}"
        }
    
    if os.path.exists(new_path):
        return {
            "success": False,
            "error": f"目标文件已存在: {new_path}"
        }
    
    try:
        os.rename(old_path, new_path)
        return {
            "success": True,
            "message": f"文件重命名成功: {old_name} -> {new_name}",
            "old_path": old_path,
            "new_path": new_path
        }
    except PermissionError:
        return {
            "success": False,
            "error": f"没有权限重命名文件: {old_path}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"重命名文件时出错: {str(e)}"
        }


def delete_file(directory_path: str, filename: str) -> Dict[str, Any]:
    """
    删除某个目录下的某个文件
    
    Args:
        directory_path: 目录路径
        filename: 要删除的文件名
    
    Returns:
        操作结果字典
    """
    file_path = os.path.join(directory_path, filename)
    
    if not os.path.exists(file_path):
        return {
            "success": False,
            "error": f"文件不存在: {file_path}"
        }
    
    try:
        if os.path.isdir(file_path):
            os.rmdir(file_path)
            return {
                "success": True,
                "message": f"目录删除成功: {filename}",
                "deleted_path": file_path
            }
        else:
            os.remove(file_path)
            return {
                "success": True,
                "message": f"文件删除成功: {filename}",
                "deleted_path": file_path
            }
    except PermissionError:
        return {
            "success": False,
            "error": f"没有权限删除文件: {file_path}"
        }
    except OSError as e:
        return {
            "success": False,
            "error": f"删除文件时出错: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"删除文件时出错: {str(e)}"
        }


def create_file_with_content(directory_path: str, filename: str, content: str) -> Dict[str, Any]:
    """
    在某个目录下新建1个文件，并且写入内容
    
    Args:
        directory_path: 目录路径
        filename: 文件名
        content: 要写入的内容
    
    Returns:
        操作结果字典
    """
    if not os.path.exists(directory_path):
        return {
            "success": False,
            "error": f"目录不存在: {directory_path}"
        }
    
    if not os.path.isdir(directory_path):
        return {
            "success": False,
            "error": f"路径不是目录: {directory_path}"
        }
    
    file_path = os.path.join(directory_path, filename)
    
    if os.path.exists(file_path):
        return {
            "success": False,
            "error": f"文件已存在: {file_path}"
        }
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        file_size = os.path.getsize(file_path)
        
        return {
            "success": True,
            "message": f"文件创建成功: {filename}",
            "file_path": file_path,
            "content_length": len(content),
            "file_size": file_size,
            "file_size_human": _format_size(file_size)
        }
    except PermissionError:
        return {
            "success": False,
            "error": f"没有权限创建文件: {file_path}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"创建文件时出错: {str(e)}"
        }


def read_file_content(directory_path: str, filename: str) -> Dict[str, Any]:
    """
    读取某个目录下的某个文件内容
    
    Args:
        directory_path: 目录路径
        filename: 文件名
    
    Returns:
        包含文件内容的字典
    """
    file_path = os.path.join(directory_path, filename)
    
    if not os.path.exists(file_path):
        return {
            "success": False,
            "error": f"文件不存在: {file_path}"
        }
    
    if os.path.isdir(file_path):
        return {
            "success": False,
            "error": f"路径是目录，不是文件: {file_path}"
        }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_size = os.path.getsize(file_path)
        stat_info = os.stat(file_path)
        
        return {
            "success": True,
            "file_path": file_path,
            "content": content,
            "content_length": len(content),
            "file_size": file_size,
            "file_size_human": _format_size(file_size),
            "encoding": "utf-8",
            "modified_time": datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        }
    except PermissionError:
        return {
            "success": False,
            "error": f"没有权限读取文件: {file_path}"
        }
    except UnicodeDecodeError:
        return {
            "success": False,
            "error": f"文件编码不是UTF-8，无法读取: {file_path}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"读取文件时出错: {str(e)}"
        }


def parse_command(user_input: str) -> Dict[str, Any]:
    """
    解析用户的自然语言命令
    
    Args:
        user_input: 用户输入的命令
    
    Returns:
        解析后的命令信息
    """
    user_input = user_input.strip()
    
    # 列出文件命令
    if "列出" in user_input and "文件" in user_input:
        directory = "."
        if "目录" in user_input and "下" in user_input:
            parts = user_input.split("列出")
            if len(parts) > 1:
                dir_part = parts[1].split("目录")[0].strip()
                if dir_part:
                    directory = dir_part
        return {
            "command": "list",
            "directory": directory
        }
    
    # 修改文件名命令
    if "修改" in user_input and ("改成" in user_input or "修改为" in user_input):
        directory = "."
        old_name = ""
        new_name = ""
        
        if "目录" in user_input and "下" in user_input:
            parts = user_input.split("修改")
            if len(parts) > 1:
                dir_part = parts[1].split("目录")[0].strip()
                if dir_part:
                    directory = dir_part
        
        rest = user_input.split("下")[1] if "下" in user_input else user_input
        
        if "改成" in rest:
            name_parts = rest.split("改成")
            old_name = name_parts[0].strip().replace("某个文件", "").replace("文件", "").replace("名字", "")
            new_name = name_parts[1].strip()
        elif "修改为" in rest:
            name_parts = rest.split("修改为")
            old_name = name_parts[0].strip().replace("某个文件", "").replace("文件", "").replace("名字", "")
            new_name = name_parts[1].strip()
        
        return {
            "command": "rename",
            "directory": directory,
            "old_name": old_name,
            "new_name": new_name
        }
    
    # 删除文件命令
    if "删除" in user_input and "文件" in user_input:
        directory = "."
        filename = ""
        
        if "目录" in user_input and "下" in user_input:
            parts = user_input.split("删除")
            if len(parts) > 1:
                dir_part = parts[1].split("目录")[0].strip()
                if dir_part:
                    directory = dir_part
        
        rest = user_input.split("下")[1] if "下" in user_input else user_input
        filename = rest.strip().replace("某个文件", "").replace("文件", "").replace("删除", "").strip()
        
        return {
            "command": "delete",
            "directory": directory,
            "filename": filename
        }
    
    # 创建文件命令
    if "新建" in user_input or "创建" in user_input:
        directory = "."
        filename = ""
        content = ""
        
        if "目录" in user_input and "下" in user_input:
            dir_part = user_input.split("目录")[0].strip()
            if dir_part.startswith("在"):
                dir_part = dir_part[1:].strip()
            if dir_part:
                directory = dir_part
        
        rest = user_input.split("下")[1] if "下" in user_input else user_input
        
        if "写入" in rest:
            content_parts = rest.split("写入")
            file_part = content_parts[0].strip().replace("1个文件", "").replace("文件", "").replace("新建", "").replace("创建", "").replace("在", "").replace("，并且", "").strip()
            content = content_parts[1].strip().replace("内容", "").strip()
            filename = file_part
        else:
            filename = rest.strip().replace("1个文件", "").replace("文件", "").replace("新建", "").replace("创建", "").replace("在", "").strip()
        
        return {
            "command": "create",
            "directory": directory,
            "filename": filename,
            "content": content
        }
    
    # 读取文件命令
    if "读取" in user_input and "内容" in user_input:
        directory = "."
        filename = ""
        
        if "目录" in user_input and "下" in user_input:
            parts = user_input.split("读取")
            if len(parts) > 1:
                dir_part = parts[1].split("目录")[0].strip()
                if dir_part:
                    directory = dir_part
        
        rest = user_input.split("下")[1] if "下" in user_input else user_input
        filename = rest.strip().replace("某个文件", "").replace("文件", "").replace("的内容", "").replace("读取", "").strip()
        
        return {
            "command": "read",
            "directory": directory,
            "filename": filename
        }
    
    return {
        "command": "unknown",
        "original_input": user_input
    }


if __name__ == "__main__":
    print("文件操作工具函数")
    print("=" * 60)
    print("支持以下操作：")
    print("1. 列出文件 - 例如：'列出test目录下的文件' 或 '列出文件'")
    print("2. 修改文件名 - 例如：'修改test目录下文件old.txt改成new.txt'")
    print("3. 删除文件 - 例如：'删除test目录下的文件file.txt'")
    print("4. 创建文件 - 例如：'在test目录下新建文件hello.txt写入Hello World'")
    print("5. 读取文件 - 例如：'读取test目录下文件hello.txt的内容'")
    print("6. 输入 '退出' 或 'quit' 结束程序")
    print("=" * 60)
    
    while True:
        user_input = input("\n请输入操作命令: ").strip()
        
        if user_input.lower() in ['退出', 'quit', 'exit', 'q']:
            print("程序已退出！")
            break
        
        if not user_input:
            continue
        
        command_info = parse_command(user_input)
        
        if command_info["command"] == "list":
            print(f"\n正在列出目录 {command_info['directory']} 下的文件...")
            result = list_directory_files(command_info['directory'])
            if result['success']:
                print(f"目录: {result['directory']}")
                print(f"总文件数: {result['total_items']}")
                print("\n文件列表:")
                for file_info in result['files']:
                    print(f"  - {file_info['name']} ({file_info['type']}) - {file_info['size_human']}")
            else:
                print(f"错误: {result['error']}")
        
        elif command_info["command"] == "rename":
            print(f"\n正在重命名文件...")
            result = rename_file(
                command_info['directory'],
                command_info['old_name'],
                command_info['new_name']
            )
            if result['success']:
                print(f"成功: {result['message']}")
            else:
                print(f"错误: {result['error']}")
        
        elif command_info["command"] == "delete":
            print(f"\n正在删除文件...")
            result = delete_file(
                command_info['directory'],
                command_info['filename']
            )
            if result['success']:
                print(f"成功: {result['message']}")
            else:
                print(f"错误: {result['error']}")
        
        elif command_info["command"] == "create":
            print(f"\n正在创建文件...")
            result = create_file_with_content(
                command_info['directory'],
                command_info['filename'],
                command_info['content']
            )
            if result['success']:
                print(f"成功: {result['message']}")
                print(f"文件大小: {result['file_size_human']}")
            else:
                print(f"错误: {result['error']}")
        
        elif command_info["command"] == "read":
            print(f"\n正在读取文件内容...")
            result = read_file_content(
                command_info['directory'],
                command_info['filename']
            )
            if result['success']:
                print(f"文件: {result['file_path']}")
                print(f"文件大小: {result['file_size_human']}")
                print(f"修改时间: {result['modified_time']}")
                print(f"\n文件内容:")
                print(result['content'])
            else:
                print(f"错误: {result['error']}")
        
        else:
            print(f"无法识别的命令: {user_input}")
            print("请参考支持的命令格式重新输入")
