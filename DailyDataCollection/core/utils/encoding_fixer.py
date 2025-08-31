# -*- coding: utf-8 -*-
"""
编码修复工具
用于解决监控系统中文输出乱码问题
"""

import sys
import os
import locale
from io import TextIOWrapper

class EncodingFixer:
    """编码修复器"""
    
    @staticmethod
    def setup_utf8_environment():
        """设置UTF-8环境"""
        # 设置环境变量
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['LANG'] = 'zh_CN.UTF-8'
        
        # 重新配置标准输入输出
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
        if hasattr(sys.stdin, 'reconfigure'):
            sys.stdin.reconfigure(encoding='utf-8')
    
    @staticmethod
    def safe_print(*args, **kwargs):
        """安全的中文打印函数"""
        try:
            # 确保所有参数都是字符串并使用UTF-8编码
            str_args = []
            for arg in args:
                if isinstance(arg, str):
                    str_args.append(arg)
                else:
                    str_args.append(str(arg))
            
            # 使用UTF-8编码打印
            text = ' '.join(str_args)
            
            # 如果在Windows命令行中，尝试使用cp65001编码
            if os.name == 'nt':
                try:
                    # 尝试直接打印
                    print(text, **kwargs)
                except UnicodeEncodeError:
                    # 如果失败，尝试使用cp65001编码
                    if hasattr(sys.stdout, 'buffer'):
                        sys.stdout.buffer.write((text + '\n').encode('utf-8'))
                        sys.stdout.buffer.flush()
                    else:
                        print(text.encode('utf-8', errors='replace').decode('utf-8'), **kwargs)
            else:
                print(text, **kwargs)
                
        except Exception as e:
            # 如果所有方法都失败，使用基本的ASCII安全打印
            try:
                safe_text = str(args[0]) if args else ""
                print(f"[编码错误] {safe_text}", **kwargs)
            except:
                print("[输出编码错误]", **kwargs)

# 全局编码修复器实例
encoding_fixer = EncodingFixer()

def setup_encoding():
    """设置编码环境的便捷函数"""
    encoding_fixer.setup_utf8_environment()

def safe_print(*args, **kwargs):
    """安全打印的便捷函数"""
    encoding_fixer.safe_print(*args, **kwargs)
