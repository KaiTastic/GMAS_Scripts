"""
文件属性模块

包含文件属性相关的类和方法
"""

import os
import time
import hashlib
from typing import Optional


class FileAttributes:
    """文件属性类，用于获取文件的各种属性信息"""

    def __init__(self, filepath: Optional[str] = None):
        self._filepath = filepath
        self._filename = None
        self._file_dir = None
        self._size = None
        self._creation_time = None
        self._modification_time = None
        self._access_time = None
        self._file_type = None
        self._data = None
        self._hashMD5 = None
        self._hashSHA265 = None

    def __getattr__(self, name: str):
        """动态获取文件属性"""
        if name == 'filepath':
            if self._filepath and os.path.exists(self._filepath) and os.path.isfile(self._filepath):
                return self._filepath
            return None
        if name == 'filename':
            if self._filename is None and self._filepath:
                self._filename = os.path.basename(self._filepath)
            return self._filename
        elif name == 'file_dir':
            if self._file_dir is None and self._filepath:
                self._file_dir = os.path.dirname(self._filepath)
            return self._file_dir
        elif name == 'size':
            if self._size is None and self._filepath:
                self._size = os.path.getsize(self._filepath)
            return self._size
        elif name == 'creation_time':
            if self._creation_time is None and self._filepath:
                self._creation_time = time.ctime(os.path.getctime(self._filepath))
            return self._creation_time
        elif name == 'modification_time':
            if self._modification_time is None and self._filepath:
                self._modification_time = time.ctime(os.path.getmtime(self._filepath))
            return self._modification_time
        elif name == 'access_time':
            if self._access_time is None and self._filepath:
                self._access_time = time.ctime(os.path.getatime(self._filepath))
            return self._access_time
        elif name == 'file_type':
            if self._file_type is None and self._filepath:
                self._file_type = self.__get_file_type()
            return self._file_type
        elif name == 'data':
            if self._data is None and self._filepath:
                with open(self._filepath, 'r') as file:
                    self._data = file.read()
            return self._data
        elif name == 'hashMD5':
            if self._filepath:
                if self._hashMD5 is None and self._data is None:
                    # Read file content
                    with open(self._filepath, 'rb') as file:
                        self._data = file.read()
                    self._hashMD5 = hashlib.md5(self._data).hexdigest()
            else:
                print(f"File path is None, hashMD5 is None")
                return None
            return self._hashMD5
        elif name == 'hashSHA265':
            if self._filepath:
                if self._hashSHA265 is None and self._data is None:
                    # Read file content
                    with open(self._filepath, 'rb') as file:
                        self._data = file.read()
                    self._hashSHA265 = hashlib.sha256(self._data).hexdigest()
            else:
                print(f"File path is None, hashSHA265 is None")
                return None
            return self._hashSHA265
        else:
            # print(f"AttributeError: {name} is not a valid attribute")
            return None

    def __get_file_type(self) -> Optional[str]:
        """获取文件类型"""
        if self._filepath and os.path.exists(self._filepath) and os.path.isfile(self._filepath):
            if os.path.splitext(self._filepath)[1]:
                return os.path.splitext(self._filepath)[1]
            else:
                return None
        else:
            return None
    
    def __str__(self) -> str:
        """返回文件属性的字符串表示"""
        return f"File Name: \t\t{self._filename}\n" \
               f"File Path: \t\t{self._filepath}\n" \
               f"File Size: \t\t{self.size} bytes\n" \
               f"Creation Time: \t\t{self._creation_time}\n" \
               f"Modification Time: \t{self._modification_time}\n" \
               f"Access Time: \t\t{self._access_time}\n" \
               f"File type: \t\t{self._file_type}\n"\
               f"MD5: \t\t\t{self._hashMD5}\n" \
               f"SHA265: \t\t{self._hashSHA265}"
