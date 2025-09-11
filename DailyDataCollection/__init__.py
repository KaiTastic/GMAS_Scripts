# !/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   Daily Data Collection for GMAS Project
@Time    :   2024/12/25 06:27:28
@Author  :   Kai Cao 
@Version :   2.4.2
@Contact :   caokai_cgs@163.com
@License :   (C)Copyright 2023-, All rights reserved.
@Prerequisites:   Python 3.10
Copyright Statement:   Full Copyright
@Desc    :   None
'''

# 版本信息统一管理
VERSION_MAJOR = 2
VERSION_MINOR = 4
VERSION_BUILD = 2
VERSION_INFO = (VERSION_MAJOR, VERSION_MINOR, VERSION_BUILD)
VERSION_STRING = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_BUILD}"

# 标准化版本字符串格式
__version__ = VERSION_STRING
__version_info__ = VERSION_INFO

# 应用程序名称和完整版本描述
APP_NAME = "GMAS 数据自动收集与处理工具"
APP_FULL_VERSION = f"{APP_NAME} {VERSION_STRING}"

# 系统标题格式
SYSTEM_TITLE = f"GMAS 数据收集系统 v{VERSION_STRING}"
