"""
文件工具函数模块

包含文件搜索、处理等工具函数
"""

import os
import re
from typing import List, Dict, Tuple


def list_fullpath_of_files_with_keywords(directory: str, keywords: List[str]) -> List[str]:
    """
    返回当前目录下所有含多个特定字符串(不区分大小写)列表的文件全路径
    
    Args:
        directory: 搜索目录
        keywords: 关键字列表
        
    Returns:
        包含所有关键字的文件路径列表
    """
    matches = []
    for root, _, files in os.walk(directory):
        for file in files:
            if all(keyword.lower() in file.lower() for keyword in keywords):
                matches.append(os.path.join(root, file))
    return matches


def find_files_with_max_number(directory: str) -> Dict[str, Tuple[str, int]]:
    """
    从指定目录中查找包含相同基础文件名的文件, 并返回括号中数字最大的文件
    
    Args:
        directory: 搜索目录
        
    Returns:
        字典，键为基础文件名，值为(文件路径, 数字)元组
    """
    files_dict = {}
    # 遍历目录中的所有文件
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            # 去掉括号中的数字, 例如: 'file(1).txt' 返回 'file.txt'
            base_name = re.sub(r'\(\d+\)', '', filename)
            # 在文件名中查找括号内的数字。正则表达式 `r'\((\d+)\)'` 匹配括号内的一个或多个数字, 并返回一个 `Match` 对象。如果没有找到匹配项, 则返回 `None`
            match = re.search(r'\((\d+)\)', filename)
            # 从 `Match` 对象中提取括号内的数字, 并将其转换为整数。如果找到了匹配项, 则使用 `int(match.group(1))` 提取括号内的数字；否则, 返回 -1
            # 提取括号中的数字, 例如: 'file(1).txt' 返回 1, 'file.txt' 返回 -1
            number = int(match.group(1)) if match else -1        
            file_path = os.path.join(root, filename)
            # 如果文件名不在字典中, 则将其添加到字典中
            if base_name not in files_dict:
                files_dict[base_name] = (file_path, number)
            # 如果文件名在字典中, 则比较括号中的数字, 保留数字最大的文件
            else:
                existing_file, existing_number = files_dict[base_name]
                if number > existing_number:
                    files_dict[base_name] = (file_path, number)
    # 清除括号中数字为-1的文件
    files_dict = {base_name: (file_path, number) for base_name, (file_path, number) in files_dict.items() if number != -1}
    # 输出包含相同基础文件名中括号内数字最大的文件
    return files_dict
