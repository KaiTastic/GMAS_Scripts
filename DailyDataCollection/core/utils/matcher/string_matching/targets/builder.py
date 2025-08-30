# -*- coding: utf-8 -*-
"""
目标构建器模块 - 提供各种类型目标的构建方法
"""

from typing import List, Optional, Dict, Any, Callable
import re

try:
    from .config import TargetType, TargetConfig, create_target_config, MatchStrategy
    from ..validators.common import (
        DateValidator, EmailValidator, PhoneValidator, URLValidator,
        NumberValidator, create_date_validator, create_number_validator
    )
except ImportError:
    # 处理独立运行的情况
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)
    sys.path.insert(0, current_dir)
    
    from config import TargetType, TargetConfig, create_target_config, MatchStrategy
    from validators.common import (
        DateValidator, EmailValidator, PhoneValidator, URLValidator,
        NumberValidator, create_date_validator, create_number_validator
    )


class TargetBuilder:
    """目标构建器基类
    
    提供构建各种类型目标的通用接口
    """
    
    @staticmethod
    def create_name_target(name: str, names: List[str],
                          matcher_type: str = "hybrid",
                          fuzzy_threshold: float = 0.65,
                          case_sensitive: bool = False,
                          required: bool = True,
                          weight: float = 1.0,
                          **kwargs) -> Dict[str, TargetConfig]:
        """创建名称匹配目标
        
        Args:
            name: 目标名称
            names: 候选名称列表
            matcher_type: 匹配器类型
            fuzzy_threshold: 模糊匹配阈值
            case_sensitive: 是否区分大小写
            required: 是否必需
            weight: 权重
            **kwargs: 其他配置参数
            
        Returns:
            Dict[str, TargetConfig]: 目标配置字典
        """
        config = (create_target_config(TargetType.NAME)
                  .patterns(names)
                  .matcher_type(matcher_type)
                  .fuzzy_threshold(fuzzy_threshold)
                  .case_sensitive(case_sensitive)
                  .required(required)
                  .weight(weight))
        
        # 应用其他参数
        for key, value in kwargs.items():
            if hasattr(config, key):
                getattr(config, key)(value)
        
        return {name: config.build()}
    
    @staticmethod
    def create_date_target(name: str,
                          date_formats: Optional[List[str]] = None,
                          fuzzy_threshold: float = 0.8,
                          required: bool = True,
                          weight: float = 1.0,
                          **kwargs) -> Dict[str, TargetConfig]:
        """创建日期匹配目标
        
        Args:
            name: 目标名称
            date_formats: 日期格式列表
            fuzzy_threshold: 模糊匹配阈值
            required: 是否必需
            weight: 权重
            **kwargs: 其他配置参数
            
        Returns:
            Dict[str, TargetConfig]: 目标配置字典
        """
        if date_formats is None:
            # 默认日期格式
            date_formats = [
                r"\d{8}",           # YYYYMMDD
                r"\d{4}-\d{2}-\d{2}", # YYYY-MM-DD
                r"\d{4}/\d{2}/\d{2}", # YYYY/MM/DD
                r"\d{2}-\d{2}-\d{4}", # DD-MM-YYYY
                r"\d{2}/\d{2}/\d{4}"  # DD/MM/YYYY
            ]
        
        # 构建正则表达式模式
        regex_pattern = r"(\d{4}[-/]?\d{2}[-/]?\d{2}|\d{2}[-/]?\d{2}[-/]?\d{4})"
        
        config = create_target_config(
            target_type=TargetType.DATE,
            patterns=date_formats,
            matcher_strategy=MatchStrategy.FUZZY,
            fuzzy_threshold=fuzzy_threshold,
            required=required
        )
        
        # 应用其他参数
        for key, value in kwargs.items():
            if hasattr(config, key):
                getattr(config, key)(value)
        
        return {name: config.build()}
    
    @staticmethod
    def create_extension_target(name: str, extensions: List[str],
                               case_sensitive: bool = False,
                               required: bool = False,
                               weight: float = 0.5,
                               **kwargs) -> Dict[str, TargetConfig]:
        """创建文件扩展名匹配目标
        
        Args:
            name: 目标名称
            extensions: 扩展名列表
            case_sensitive: 是否区分大小写
            required: 是否必需
            weight: 权重
            **kwargs: 其他配置参数
            
        Returns:
            Dict[str, TargetConfig]: 目标配置字典
        """
        # 确保扩展名以点开头
        normalized_exts = []
        for ext in extensions:
            if not ext.startswith('.'):
                ext = '.' + ext
            normalized_exts.append(ext)
        
        # 构建正则表达式
        regex_pattern = r"\.([a-zA-Z0-9]+)$"
        
        config = (create_target_config(TargetType.FILE_EXTENSION)
                  .patterns(normalized_exts)
                  .matcher_type("exact")
                  .case_sensitive(case_sensitive)
                  .required(required)
                  .weight(weight)
                  .regex(regex_pattern))
        
        # 应用其他参数
        for key, value in kwargs.items():
            if hasattr(config, key):
                getattr(config, key)(value)
        
        return {name: config.build()}
    
    @staticmethod
    def create_number_target(name: str,
                           number_patterns: Optional[List[str]] = None,
                           fuzzy_threshold: float = 0.9,
                           allow_float: bool = True,
                           min_value: Optional[float] = None,
                           max_value: Optional[float] = None,
                           required: bool = False,
                           weight: float = 0.8,
                           **kwargs) -> Dict[str, TargetConfig]:
        """创建数字匹配目标
        
        Args:
            name: 目标名称
            number_patterns: 数字模式列表
            fuzzy_threshold: 模糊匹配阈值
            allow_float: 是否允许小数
            min_value: 最小值
            max_value: 最大值
            required: 是否必需
            weight: 权重
            **kwargs: 其他配置参数
            
        Returns:
            Dict[str, TargetConfig]: 目标配置字典
        """
        if number_patterns is None:
            number_patterns = [
                r"\d+",             # 整数
                r"\d+\.\d+",        # 小数
                r"\d{1,3}(,\d{3})*", # 带逗号的数字
            ]
        
        # 构建正则表达式
        regex_pattern = r"(\d+(?:[.,]\d+)*)"
        
        # 创建验证器
        validator = create_number_validator(allow_float, min_value, max_value)
        
        config = (create_target_config(TargetType.NUMBER)
                  .patterns(number_patterns)
                  .matcher_type("fuzzy")
                  .fuzzy_threshold(fuzzy_threshold)
                  .required(required)
                  .weight(weight)
                  .regex(regex_pattern)
                  .validator(validator.validate))
        
        # 应用其他参数
        for key, value in kwargs.items():
            if hasattr(config, key):
                getattr(config, key)(value)
        
        return {name: config.build()}
    
    @staticmethod
    def create_email_target(name: str,
                           domains: Optional[List[str]] = None,
                           strict: bool = True,
                           required: bool = False,
                           weight: float = 1.0,
                           **kwargs) -> Dict[str, TargetConfig]:
        """创建邮箱匹配目标
        
        Args:
            name: 目标名称
            domains: 允许的域名列表
            strict: 是否严格验证
            required: 是否必需
            weight: 权重
            **kwargs: 其他配置参数
            
        Returns:
            Dict[str, TargetConfig]: 目标配置字典
        """
        patterns = domains or []
        
        # 邮箱正则表达式
        if strict:
            regex_pattern = r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
        else:
            regex_pattern = r"([^\s@]+@[^\s@]+\.[^\s@]+)"
        
        # 创建验证器
        validator = EmailValidator(strict)
        
        config = (create_target_config(TargetType.EMAIL)
                  .patterns(patterns)
                  .matcher_type("fuzzy")
                  .required(required)
                  .weight(weight)
                  .regex(regex_pattern)
                  .validator(validator.validate))
        
        # 应用其他参数
        for key, value in kwargs.items():
            if hasattr(config, key):
                getattr(config, key)(value)
        
        return {name: config.build()}
    
    @staticmethod
    def create_phone_target(name: str,
                           country_code: Optional[str] = None,
                           patterns: Optional[List[str]] = None,
                           required: bool = False,
                           weight: float = 1.0,
                           **kwargs) -> Dict[str, TargetConfig]:
        """创建电话号码匹配目标
        
        Args:
            name: 目标名称
            country_code: 国家代码
            patterns: 自定义模式列表
            required: 是否必需
            weight: 权重
            **kwargs: 其他配置参数
            
        Returns:
            Dict[str, TargetConfig]: 目标配置字典
        """
        if patterns is None:
            patterns = []
        
        # 通用电话号码正则表达式
        regex_pattern = r"(\+?\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4})"
        
        # 根据国家代码调整模式
        if country_code == 'CN':
            regex_pattern = r"(1[3-9]\d{9}|\+86[-.\s]?1[3-9]\d{9})"
        elif country_code == 'US':
            regex_pattern = r"(\+?1[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4})"
        
        # 创建验证器
        validator = PhoneValidator(country_code)
        
        config = (create_target_config(TargetType.PHONE)
                  .patterns(patterns)
                  .matcher_type("fuzzy")
                  .required(required)
                  .weight(weight)
                  .regex(regex_pattern)
                  .validator(validator.validate))
        
        # 应用其他参数
        for key, value in kwargs.items():
            if hasattr(config, key):
                getattr(config, key)(value)
        
        return {name: config.build()}
    
    @staticmethod
    def create_url_target(name: str,
                         schemes: Optional[List[str]] = None,
                         require_scheme: bool = True,
                         required: bool = False,
                         weight: float = 1.0,
                         **kwargs) -> Dict[str, TargetConfig]:
        """创建URL匹配目标
        
        Args:
            name: 目标名称
            schemes: 允许的协议列表
            require_scheme: 是否要求协议
            required: 是否必需
            weight: 权重
            **kwargs: 其他配置参数
            
        Returns:
            Dict[str, TargetConfig]: 目标配置字典
        """
        patterns = schemes or ["http://", "https://", "ftp://"]
        
        # URL正则表达式
        if require_scheme:
            regex_pattern = r"(https?://[^\s/$.?#].[^\s]*)"
        else:
            regex_pattern = r"((https?://)?[^\s/$.?#].[^\s]*)"
        
        # 创建验证器
        validator = URLValidator(require_scheme)
        
        config = (create_target_config(TargetType.URL)
                  .patterns(patterns)
                  .matcher_type("fuzzy")
                  .required(required)
                  .weight(weight)
                  .regex(regex_pattern)
                  .validator(validator.validate))
        
        # 应用其他参数
        for key, value in kwargs.items():
            if hasattr(config, key):
                getattr(config, key)(value)
        
        return {name: config.build()}
    
    @staticmethod
    def create_custom_target(name: str,
                           patterns: List[str],
                           matcher_type: str = "hybrid",
                           fuzzy_threshold: float = 0.65,
                           case_sensitive: bool = False,
                           required: bool = True,
                           weight: float = 1.0,
                           regex_pattern: Optional[str] = None,
                           validator: Optional[Callable] = None,
                           preprocessor: Optional[Callable] = None,
                           **kwargs) -> Dict[str, TargetConfig]:
        """创建自定义匹配目标
        
        Args:
            name: 目标名称
            patterns: 模式列表
            matcher_type: 匹配器类型
            fuzzy_threshold: 模糊匹配阈值
            case_sensitive: 是否区分大小写
            required: 是否必需
            weight: 权重
            regex_pattern: 正则表达式模式
            validator: 验证函数
            preprocessor: 预处理函数
            **kwargs: 其他配置参数
            
        Returns:
            Dict[str, TargetConfig]: 目标配置字典
        """
        config = (create_target_config(TargetType.CUSTOM)
                  .patterns(patterns)
                  .matcher_type(matcher_type)
                  .fuzzy_threshold(fuzzy_threshold)
                  .case_sensitive(case_sensitive)
                  .required(required)
                  .weight(weight))
        
        if regex_pattern:
            config.regex(regex_pattern)
        
        if validator:
            config.validator(validator)
        
        if preprocessor:
            config.preprocessor(preprocessor)
        
        # 应用其他参数
        for key, value in kwargs.items():
            if hasattr(config, key):
                getattr(config, key)(value)
        
        return {name: config.build()}


class PresetTargets:
    """预设目标配置
    
    提供常用的目标配置预设
    """
    
    @staticmethod
    def chinese_name() -> Dict[str, TargetConfig]:
        """中文姓名目标"""
        return TargetBuilder.create_custom_target(
            name="chinese_name",
            patterns=[],
            regex_pattern=r"([\u4e00-\u9fff]{2,4})",
            matcher_type="fuzzy",
            fuzzy_threshold=0.8,
            weight=1.5
        )
    
    @staticmethod
    def english_name() -> Dict[str, TargetConfig]:
        """英文姓名目标"""
        return TargetBuilder.create_custom_target(
            name="english_name",
            patterns=[],
            regex_pattern=r"([A-Z][a-z]+\s+[A-Z][a-z]+)",
            matcher_type="fuzzy",
            fuzzy_threshold=0.7,
            weight=1.5
        )
    
    @staticmethod
    def ip_address() -> Dict[str, TargetConfig]:
        """IP地址目标"""
        ip_pattern = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
        
        def validate_ip(ip: str) -> bool:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            try:
                return all(0 <= int(part) <= 255 for part in parts)
            except ValueError:
                return False
        
        return TargetBuilder.create_custom_target(
            name="ip_address",
            patterns=[],
            regex_pattern=ip_pattern,
            validator=validate_ip,
            weight=1.0
        )
    
    @staticmethod
    def version_number() -> Dict[str, TargetConfig]:
        """版本号目标"""
        return TargetBuilder.create_custom_target(
            name="version",
            patterns=[],
            regex_pattern=r"(v?\d+\.\d+(?:\.\d+)?)",
            matcher_type="fuzzy",
            fuzzy_threshold=0.9,
            weight=0.8
        )
    
    @staticmethod
    def currency() -> Dict[str, TargetConfig]:
        """货币金额目标"""
        currency_pattern = r"([$¥€£]\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"
        
        return TargetBuilder.create_custom_target(
            name="currency",
            patterns=["$", "¥", "€", "£"],
            regex_pattern=currency_pattern,
            matcher_type="hybrid",
            weight=1.2
        )
    
    @staticmethod
    def file_path() -> Dict[str, TargetConfig]:
        """文件路径目标"""
        # Windows和Unix路径
        path_pattern = r"([A-Za-z]:\\(?:[^\\/:*?\"<>|\r\n]+\\)*[^\\/:*?\"<>|\r\n]*|/(?:[^/\0]+/)*[^/\0]*)"
        
        return TargetBuilder.create_custom_target(
            name="file_path",
            patterns=[],
            regex_pattern=path_pattern,
            matcher_type="fuzzy",
            fuzzy_threshold=0.7,
            weight=1.0
        )


def get_preset_target(preset_name: str) -> Optional[Dict[str, TargetConfig]]:
    """获取预设目标配置
    
    Args:
        preset_name: 预设名称
        
    Returns:
        Optional[Dict[str, TargetConfig]]: 目标配置字典
    """
    presets = {
        'chinese_name': PresetTargets.chinese_name,
        'english_name': PresetTargets.english_name,
        'ip_address': PresetTargets.ip_address,
        'version': PresetTargets.version_number,
        'currency': PresetTargets.currency,
        'file_path': PresetTargets.file_path,
    }
    
    preset_func = presets.get(preset_name)
    return preset_func() if preset_func else None
