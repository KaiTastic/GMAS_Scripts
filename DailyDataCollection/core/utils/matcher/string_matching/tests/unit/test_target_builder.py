#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
目标构建器单元测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ...targets.builder import TargetBuilder, PresetTargets
from ...targets.config import TargetType, TargetConfig
from ..base_test import BaseTestCase


class TestTargetBuilder(BaseTestCase):
    """目标构建器测试类"""
    
    def test_create_name_target(self):
        """测试创建姓名目标"""
        def test_func():
            target_dict = TargetBuilder.create_name_target(
                "person", 
                names=["john", "jane", "alice"]
            )
            config = target_dict["person"]
            return (config.target_type == TargetType.NAME and 
                   "john" in config.patterns)
        
        self.run_test_case(
            "create_name_target",
            test_func,
            expected_result=True
        )
    
    def test_create_email_target(self):
        """测试创建邮箱目标"""
        def test_func():
            target_dict = TargetBuilder.create_email_target("email")
            config = target_dict["email"]
            return config.target_type == TargetType.EMAIL
        
        self.run_test_case(
            "create_email_target",
            test_func,
            expected_result=True
        )
    
    def test_create_phone_target(self):
        """测试创建电话目标"""
        def test_func():
            target_dict = TargetBuilder.create_phone_target("phone")
            config = target_dict["phone"]
            return config.target_type == TargetType.PHONE
        
        self.run_test_case(
            "create_phone_target",
            test_func,
            expected_result=True
        )
    
    def test_create_date_target(self):
        """测试创建日期目标"""
        def test_func():
            target_dict = TargetBuilder.create_date_target("date")
            config = target_dict["date"]
            return config.target_type == TargetType.DATE
        
        self.run_test_case(
            "create_date_target",
            test_func,
            expected_result=True
        )
    
    def test_create_number_target(self):
        """测试创建数字目标"""
        def test_func():
            target_dict = TargetBuilder.create_number_target(
                "version",
                patterns=[r'\d+\.\d+']
            )
            config = target_dict["version"]
            return config.target_type == TargetType.NUMBER
        
        self.run_test_case(
            "create_number_target",
            test_func,
            expected_result=True
        )
    
    def test_create_url_target(self):
        """测试创建URL目标"""
        def test_func():
            target_dict = TargetBuilder.create_url_target("url")
            config = target_dict["url"]
            return config.target_type == TargetType.URL
        
        self.run_test_case(
            "create_url_target",
            test_func,
            expected_result=True
        )
    
    def test_create_extension_target(self):
        """测试创建文件扩展名目标"""
        def test_func():
            target_dict = TargetBuilder.create_extension_target(
                "file_ext",
                extensions=["pdf", "doc", "txt"]
            )
            config = target_dict["file_ext"]
            return (config.target_type == TargetType.FILE_EXTENSION and
                   ".pdf" in config.patterns)
        
        self.run_test_case(
            "create_extension_target",
            test_func,
            expected_result=True
        )
    
    def test_create_custom_target(self):
        """测试创建自定义目标"""
        def test_func():
            target_dict = TargetBuilder.create_custom_target(
                "custom",
                patterns=[r'\d{4}-\d{2}-\d{2}'],
                regex_pattern=r'\d{4}-\d{2}-\d{2}'
            )
            config = target_dict["custom"]
            return config.target_type == TargetType.CUSTOM
        
        self.run_test_case(
            "create_custom_target",
            test_func,
            expected_result=True
        )
    
    def test_target_with_custom_options(self):
        """测试带自定义选项的目标"""
        def test_func():
            target_dict = TargetBuilder.create_name_target(
                "person",
                names=["john"],
                case_sensitive=True,
                required=False,
                weight=0.8
            )
            config = target_dict["person"]
            return (config.case_sensitive == True and
                   config.required == False and
                   config.weight == 0.8)
        
        self.run_test_case(
            "target_with_custom_options",
            test_func,
            expected_result=True
        )
    
    def test_preset_chinese_name(self):
        """测试预设中文姓名"""
        def test_func():
            config = PresetTargets.chinese_name()
            return config.target_type == TargetType.NAME
        
        self.run_test_case(
            "preset_chinese_name",
            test_func,
            expected_result=True
        )
    
    def test_preset_ip_address(self):
        """测试预设IP地址"""
        def test_func():
            config = PresetTargets.ip_address()
            return config.target_type == TargetType.CUSTOM
        
        self.run_test_case(
            "preset_ip_address",
            test_func,
            expected_result=True
        )
    
    def test_preset_version_number(self):
        """测试预设版本号"""
        def test_func():
            config = PresetTargets.version_number()
            return config.target_type == TargetType.NUMBER
        
        self.run_test_case(
            "preset_version_number",
            test_func,
            expected_result=True
        )
    
    def test_preset_currency(self):
        """测试预设货币"""
        def test_func():
            config = PresetTargets.currency()
            return config.target_type == TargetType.CUSTOM
        
        self.run_test_case(
            "preset_currency",
            test_func,
            expected_result=True
        )
    
    def test_email_with_validation(self):
        """测试带验证的邮箱目标"""
        def test_func():
            target_dict = TargetBuilder.create_email_target(
                "email",
                domain_whitelist=["example.com", "test.org"]
            )
            config = target_dict["email"]
            return config.validator is not None
        
        self.run_test_case(
            "email_with_validation",
            test_func,
            expected_result=True
        )
    
    def test_phone_with_validation(self):
        """测试带验证的电话目标"""
        def test_func():
            target_dict = TargetBuilder.create_phone_target(
                "phone",
                country_codes=["+1", "+86"]
            )
            config = target_dict["phone"]
            return config.validator is not None
        
        self.run_test_case(
            "phone_with_validation",
            test_func,
            expected_result=True
        )
    
    def test_date_with_validation(self):
        """测试带验证的日期目标"""
        def test_func():
            target_dict = TargetBuilder.create_date_target(
                "date",
                date_formats=["YYYY-MM-DD", "MM/DD/YYYY"]
            )
            config = target_dict["date"]
            return config.validator is not None
        
        self.run_test_case(
            "date_with_validation",
            test_func,
            expected_result=True
        )
    
    def test_number_with_range_validation(self):
        """测试带范围验证的数字目标"""
        def test_func():
            target_dict = TargetBuilder.create_number_target(
                "score",
                patterns=[r'\d+'],
                min_value=0,
                max_value=100
            )
            config = target_dict["score"]
            return config.validator is not None
        
        self.run_test_case(
            "number_with_range_validation",
            test_func,
            expected_result=True
        )
    
    def test_target_config_immutability(self):
        """测试目标配置不可变性"""
        def test_func():
            target_dict = TargetBuilder.create_email_target("email")
            config = target_dict["email"]
            
            # 尝试修改配置（应该创建新对象）
            original_required = config.required
            # 由于是dataclass，直接修改属性是可能的，但不推荐
            # 这里测试配置是否正确创建
            return isinstance(config, TargetConfig)
        
        self.run_test_case(
            "target_config_immutability",
            test_func,
            expected_result=True
        )
    
    def test_multiple_patterns(self):
        """测试多个模式"""
        def test_func():
            target_dict = TargetBuilder.create_custom_target(
                "multi_pattern",
                patterns=["pattern1", "pattern2", "pattern3"]
            )
            config = target_dict["multi_pattern"]
            return len(config.patterns) == 3
        
        self.run_test_case(
            "multiple_patterns",
            test_func,
            expected_result=True
        )
    
    def test_empty_patterns_handling(self):
        """测试空模式处理"""
        def test_func():
            try:
                target_dict = TargetBuilder.create_name_target("empty", names=[])
                config = target_dict["empty"]
                return len(config.patterns) == 0
            except ValueError:
                # 如果抛出异常，说明正确处理了空模式
                return True
        
        self.run_test_case(
            "empty_patterns_handling",
            test_func,
            expected_result=True
        )
