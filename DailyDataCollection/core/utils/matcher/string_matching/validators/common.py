# -*- coding: utf-8 -*-
"""
验证器模块 - 提供各种字符串验证功能
"""

import re
from datetime import datetime
from typing import Optional, List, Callable

# 直接导入具体类型，避免循环导入
try:
    from ..string_types.validators import Validator, ValidationResult, ValidatorType, ValidationRule, ValidationSchema
    from ..string_types.enums import ValidationLevel
    from ..string_types.configs import ValidatorConfig
except ImportError:
    # 处理独立运行的情况
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)
    
    from string_types.validators import Validator, ValidationResult, ValidatorType, ValidationRule, ValidationSchema
    from string_types.enums import ValidationLevel
    from string_types.configs import ValidatorConfig

# 为了兼容性，保留本地别名和实现
# 注：原本在这里定义的 Validator 抽象基类已经移动到 string_types.validators 模块


class DateValidator(Validator):
    """日期验证器"""
    
    def __init__(self, formats: Optional[List[str]] = None):
        """初始化日期验证器
        
        Args:
            formats: 支持的日期格式列表
        """
        self.formats = formats or [
            "%Y%m%d", "%Y-%m-%d", "%Y/%m/%d",
            "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y",
            "%d.%m.%Y", "%Y.%m.%d", "%Y-%m-%d %H:%M:%S"
        ]
    
    def validate(self, value: str) -> bool:
        """验证日期字符串"""
        for fmt in self.formats:
            try:
                datetime.strptime(value, fmt)
                return True
            except ValueError:
                continue
        return False
    
    def get_error_message(self) -> str:
        return f"Invalid date format. Supported formats: {', '.join(self.formats)}"


class NumberValidator(Validator):
    """数字验证器"""
    
    def __init__(self, allow_float: bool = True, 
                 min_value: Optional[float] = None,
                 max_value: Optional[float] = None):
        """初始化数字验证器
        
        Args:
            allow_float: 是否允许小数
            min_value: 最小值
            max_value: 最大值
        """
        self.allow_float = allow_float
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, value: str) -> bool:
        """验证数字字符串"""
        try:
            # 移除逗号并尝试转换
            cleaned = value.replace(',', '').replace(' ', '')
            
            if self.allow_float:
                num = float(cleaned)
            else:
                if '.' in cleaned:
                    return False
                num = int(cleaned)
            
            # 检查范围
            if self.min_value is not None and num < self.min_value:
                return False
            if self.max_value is not None and num > self.max_value:
                return False
            
            return True
        except ValueError:
            return False
    
    def get_error_message(self) -> str:
        msg = "Invalid number format"
        if not self.allow_float:
            msg += " (integers only)"
        if self.min_value is not None or self.max_value is not None:
            msg += f" (range: {self.min_value}-{self.max_value})"
        return msg


class EmailValidator(Validator):
    """邮箱验证器"""
    
    def __init__(self, strict: bool = True):
        """初始化邮箱验证器
        
        Args:
            strict: 是否使用严格验证
        """
        self.strict = strict
        if strict:
            # 更严格的邮箱正则表达式
            self.pattern = re.compile(
                r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            )
        else:
            # 宽松的邮箱正则表达式
            self.pattern = re.compile(r'.+@.+\..+')
    
    def validate(self, value: str) -> bool:
        """验证邮箱地址"""
        if not value or len(value) > 254:  # RFC 5321 限制
            return False
        
        return bool(self.pattern.match(value.strip()))
    
    def get_error_message(self) -> str:
        return "Invalid email address format"


class PhoneValidator(Validator):
    """电话号码验证器"""
    
    def __init__(self, country_code: Optional[str] = None):
        """初始化电话验证器
        
        Args:
            country_code: 国家代码 (如 'US', 'CN')
        """
        self.country_code = country_code
        
        # 通用电话号码模式
        self.patterns = [
            re.compile(r'^\+?\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}$'),
            re.compile(r'^\d{10,15}$'),  # 纯数字
            re.compile(r'^\(\d{3}\)\s?\d{3}[-.\s]?\d{4}$'),  # (123) 456-7890
        ]
        
        # 特定国家模式
        if country_code == 'US':
            self.patterns.append(re.compile(r'^\d{3}-\d{3}-\d{4}$'))
        elif country_code == 'CN':
            self.patterns.append(re.compile(r'^1[3-9]\d{9}$'))
    
    def validate(self, value: str) -> bool:
        """验证电话号码"""
        cleaned = re.sub(r'[^\d+()-.\s]', '', value)
        
        for pattern in self.patterns:
            if pattern.match(cleaned):
                return True
        
        return False
    
    def get_error_message(self) -> str:
        return f"Invalid phone number format for {self.country_code or 'any'} region"


class URLValidator(Validator):
    """URL验证器"""
    
    def __init__(self, require_scheme: bool = True):
        """初始化URL验证器
        
        Args:
            require_scheme: 是否要求协议部分
        """
        self.require_scheme = require_scheme
        
        if require_scheme:
            self.pattern = re.compile(
                r'^https?://[^\s/$.?#].[^\s]*$',
                re.IGNORECASE
            )
        else:
            self.pattern = re.compile(
                r'^(https?://)?[^\s/$.?#].[^\s]*$',
                re.IGNORECASE
            )
    
    def validate(self, value: str) -> bool:
        """验证URL"""
        return bool(self.pattern.match(value.strip()))
    
    def get_error_message(self) -> str:
        return "Invalid URL format"


class LengthValidator(Validator):
    """长度验证器"""
    
    def __init__(self, min_length: int = 0, max_length: Optional[int] = None):
        """初始化长度验证器
        
        Args:
            min_length: 最小长度
            max_length: 最大长度
        """
        self.min_length = min_length
        self.max_length = max_length
    
    def validate(self, value: str) -> bool:
        """验证字符串长度"""
        length = len(value)
        
        if length < self.min_length:
            return False
        
        if self.max_length is not None and length > self.max_length:
            return False
        
        return True
    
    def get_error_message(self) -> str:
        if self.max_length is not None:
            return f"Length must be between {self.min_length} and {self.max_length}"
        else:
            return f"Length must be at least {self.min_length}"


class RegexValidator(Validator):
    """正则表达式验证器"""
    
    def __init__(self, pattern: str, flags: int = 0):
        """初始化正则验证器
        
        Args:
            pattern: 正则表达式模式
            flags: 正则表达式标志
        """
        self.pattern = re.compile(pattern, flags)
        self.pattern_str = pattern
    
    def validate(self, value: str) -> bool:
        """验证字符串"""
        return bool(self.pattern.match(value))
    
    def get_error_message(self) -> str:
        return f"Value does not match pattern: {self.pattern_str}"


class CompositeValidator(Validator):
    """组合验证器"""
    
    def __init__(self, validators: List[Validator], require_all: bool = True):
        """初始化组合验证器
        
        Args:
            validators: 验证器列表
            require_all: 是否需要所有验证器都通过
        """
        self.validators = validators
        self.require_all = require_all
    
    def validate(self, value: str) -> bool:
        """验证字符串"""
        results = [validator.validate(value) for validator in self.validators]
        
        if self.require_all:
            return all(results)
        else:
            return any(results)
    
    def get_error_message(self) -> str:
        if self.require_all:
            return "Value must pass all validation rules"
        else:
            return "Value must pass at least one validation rule"


# 预定义验证器实例
COMMON_VALIDATORS = {
    'date': DateValidator(),
    'email': EmailValidator(),
    'phone': PhoneValidator(),
    'url': URLValidator(),
    'positive_number': NumberValidator(min_value=0),
    'integer': NumberValidator(allow_float=False),
    'non_empty': LengthValidator(min_length=1),
}


def get_validator(validator_name: str) -> Optional[Validator]:
    """获取预定义的验证器
    
    Args:
        validator_name: 验证器名称
        
    Returns:
        Optional[Validator]: 验证器实例
    """
    return COMMON_VALIDATORS.get(validator_name)


def create_date_validator(*formats: str) -> DateValidator:
    """创建日期验证器
    
    Args:
        *formats: 日期格式列表
        
    Returns:
        DateValidator: 日期验证器
    """
    return DateValidator(list(formats) if formats else None)


def create_number_validator(allow_float: bool = True,
                          min_value: Optional[float] = None,
                          max_value: Optional[float] = None) -> NumberValidator:
    """创建数字验证器"""
    return NumberValidator(allow_float, min_value, max_value)


def create_length_validator(min_length: int = 0,
                          max_length: Optional[int] = None) -> LengthValidator:
    """创建长度验证器"""
    return LengthValidator(min_length, max_length)


def create_regex_validator(pattern: str, flags: int = 0) -> RegexValidator:
    """创建正则验证器"""
    return RegexValidator(pattern, flags)


def create_composite_validator(*validators: Validator,
                             require_all: bool = True) -> CompositeValidator:
    """创建组合验证器"""
    return CompositeValidator(list(validators), require_all)
