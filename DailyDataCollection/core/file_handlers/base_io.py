"""
基础文件IO模块

包含抽象文件IO基类和通用文件IO实现
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Optional, Any

# 创建 logger 实例
logger = logging.getLogger('File IO')
logger.setLevel(logging.ERROR)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class FileIO(ABC):
    """抽象文件IO基类"""
    
    def __init__(self, filepath: Optional[str] = None):
        if filepath is not None and os.path.exists(filepath) and os.path.isfile(filepath):
            self.filepath = filepath
        else:
            logger.error(f"文件路径无效（为空/不存在/不是有效文件路径）: {filepath}")
            self.filepath = None

    @abstractmethod
    def read(self) -> Any:
        """读取文件内容"""
        pass

    @abstractmethod
    def write(self, content: Any) -> bool:
        """写入文件内容"""
        pass

    @abstractmethod
    def delete(self) -> bool:
        """删除文件"""
        pass

    @abstractmethod
    def update(self, content: Any) -> bool:
        """更新文件内容"""
        pass


class GeneralIO(FileIO):
    """通用文件IO实现"""

    def __init__(self, filepath: Optional[str] = None, mode: str = 'r', encoding: str = 'utf-8'):
        super().__init__(filepath)
        self.mode = mode
        self.encoding = encoding

    def read(self) -> Optional[str]:
        """读取文件内容"""
        if not self.filepath:
            logger.error("文件路径为空，无法读取")
            return None
            
        try:
            with open(self.filepath, self.mode, encoding=self.encoding) as file:
                return file.read()
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            return None

    def write(self, content: str) -> bool:
        """写入文件内容"""
        if not self.filepath:
            logger.error("文件路径为空，无法写入")
            return False
            
        try:
            with open(self.filepath, 'w', encoding=self.encoding) as file:
                file.write(content)
            return True
        except Exception as e:
            logger.error(f"写入文件失败: {e}")
            return False

    def delete(self) -> bool:
        """删除文件"""
        if not self.filepath:
            logger.error("文件路径为空，无法删除")
            return False
            
        try:
            os.remove(self.filepath)
            return True
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return False

    def update(self, content: str) -> bool:
        """更新文件内容（追加模式）"""
        if not self.filepath:
            logger.error("文件路径为空，无法更新")
            return False
            
        try:
            with open(self.filepath, 'a', encoding=self.encoding) as file:
                file.write(content)
            return True
        except Exception as e:
            logger.error(f"更新文件失败: {e}")
            return False
