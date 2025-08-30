#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证器单元测试
"""

import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ...validators.common import (
    DateValidator, EmailValidator, PhoneValidator, URLValidator,
    NumberValidator, CompositeValidator, create_date_validator,
    create_number_validator
)
from ..base_test import BaseTestCase


class TestValidators(BaseTestCase):
    """验证器测试类"""
    
    def test_email_validator_valid_emails(self):
        """测试邮箱验证器 - 有效邮箱"""
        def test_func():
            validator = EmailValidator()
            valid_emails = [
                "test@example.com",
                "user.name@domain.org",
                "user+tag@company.co.uk",
                "123@number-domain.com"
            ]
            
            for email in valid_emails:
                if not validator.validate(email):
                    return False
            return True
        
        self.run_test_case(
            "email_validator_valid_emails",
            test_func,
            expected_result=True
        )
    
    def test_email_validator_invalid_emails(self):
        """测试邮箱验证器 - 无效邮箱"""
        def test_func():
            validator = EmailValidator()
            invalid_emails = [
                "invalid-email",
                "@domain.com",
                "user@",
                "user@domain",
                "user..name@domain.com",
                ""
            ]
            
            for email in invalid_emails:
                if validator.validate(email):
                    return False
            return True
        
        self.run_test_case(
            "email_validator_invalid_emails",
            test_func,
            expected_result=True
        )
    
    def test_email_validator_domain_whitelist(self):
        """测试邮箱验证器域名白名单"""
        def test_func():
            validator = EmailValidator(domain_whitelist=["example.com", "test.org"])
            
            # 白名单内的域名应该通过
            valid = validator.validate("user@example.com")
            # 白名单外的域名应该被拒绝
            invalid = not validator.validate("user@other.com")
            
            return valid and invalid
        
        self.run_test_case(
            "email_validator_domain_whitelist",
            test_func,
            expected_result=True
        )
    
    def test_phone_validator_valid_phones(self):
        """测试电话验证器 - 有效电话"""
        def test_func():
            validator = PhoneValidator()
            valid_phones = [
                "+1-555-123-4567",
                "555.123.4567",
                "(555) 123-4567",
                "15551234567",
                "+86 138 0013 8000"
            ]
            
            for phone in valid_phones:
                if not validator.validate(phone):
                    return False
            return True
        
        self.run_test_case(
            "phone_validator_valid_phones",
            test_func,
            expected_result=True
        )
    
    def test_phone_validator_invalid_phones(self):
        """测试电话验证器 - 无效电话"""
        def test_func():
            validator = PhoneValidator()
            invalid_phones = [
                "123",  # 太短
                "123456789012345678",  # 太长
                "abc-def-ghij",  # 非数字
                "",  # 空字符串
                "555-CALL-NOW"  # 包含字母
            ]
            
            for phone in invalid_phones:
                if validator.validate(phone):
                    return False
            return True
        
        self.run_test_case(
            "phone_validator_invalid_phones",
            test_func,
            expected_result=True
        )
    
    def test_phone_validator_country_codes(self):
        """测试电话验证器国家代码"""
        def test_func():
            validator = PhoneValidator(country_codes=["+1", "+86"])
            
            # 允许的国家代码应该通过
            valid = validator.validate("+1-555-123-4567")
            # 不允许的国家代码应该被拒绝
            invalid = not validator.validate("+44-20-1234-5678")
            
            return valid and invalid
        
        self.run_test_case(
            "phone_validator_country_codes",
            test_func,
            expected_result=True
        )
    
    def test_url_validator_valid_urls(self):
        """测试URL验证器 - 有效URL"""
        def test_func():
            validator = URLValidator()
            valid_urls = [
                "https://www.example.com",
                "http://example.org/path",
                "https://subdomain.example.com/path?param=value",
                "ftp://files.example.com/file.txt"
            ]
            
            for url in valid_urls:
                if not validator.validate(url):
                    return False
            return True
        
        self.run_test_case(
            "url_validator_valid_urls",
            test_func,
            expected_result=True
        )
    
    def test_url_validator_invalid_urls(self):
        """测试URL验证器 - 无效URL"""
        def test_func():
            validator = URLValidator()
            invalid_urls = [
                "not-a-url",
                "http://",
                "://missing-scheme.com",
                "",
                "just-text"
            ]
            
            for url in invalid_urls:
                if validator.validate(url):
                    return False
            return True
        
        self.run_test_case(
            "url_validator_invalid_urls",
            test_func,
            expected_result=True
        )
    
    def test_url_validator_allowed_schemes(self):
        """测试URL验证器允许的协议"""
        def test_func():
            validator = URLValidator(allowed_schemes=["https"])
            
            # 允许的协议应该通过
            valid = validator.validate("https://example.com")
            # 不允许的协议应该被拒绝
            invalid = not validator.validate("http://example.com")
            
            return valid and invalid
        
        self.run_test_case(
            "url_validator_allowed_schemes",
            test_func,
            expected_result=True
        )
    
    def test_date_validator_valid_dates(self):
        """测试日期验证器 - 有效日期"""
        def test_func():
            validator = DateValidator()
            valid_dates = [
                "2025-08-30",
                "2025/08/30",
                "08-30-2025",
                "30/08/2025"
            ]
            
            for date_str in valid_dates:
                if not validator.validate(date_str):
                    return False
            return True
        
        self.run_test_case(
            "date_validator_valid_dates",
            test_func,
            expected_result=True
        )
    
    def test_date_validator_invalid_dates(self):
        """测试日期验证器 - 无效日期"""
        def test_func():
            validator = DateValidator()
            invalid_dates = [
                "2025-13-01",  # 无效月份
                "2025-02-30",  # 无效日期
                "not-a-date",
                "",
                "25-08-30"  # 年份太短
            ]
            
            for date_str in invalid_dates:
                if validator.validate(date_str):
                    return False
            return True
        
        self.run_test_case(
            "date_validator_invalid_dates",
            test_func,
            expected_result=True
        )
    
    def test_date_validator_custom_formats(self):
        """测试日期验证器自定义格式"""
        def test_func():
            validator = DateValidator(date_formats=["%Y-%m-%d"])
            
            # 匹配格式应该通过
            valid = validator.validate("2025-08-30")
            # 不匹配格式应该被拒绝
            invalid = not validator.validate("08/30/2025")
            
            return valid and invalid
        
        self.run_test_case(
            "date_validator_custom_formats",
            test_func,
            expected_result=True
        )
    
    def test_number_validator_valid_numbers(self):
        """测试数字验证器 - 有效数字"""
        def test_func():
            validator = NumberValidator()
            valid_numbers = [
                "123",
                "456.78",
                "-123",
                "0",
                "3.14159"
            ]
            
            for num_str in valid_numbers:
                if not validator.validate(num_str):
                    return False
            return True
        
        self.run_test_case(
            "number_validator_valid_numbers",
            test_func,
            expected_result=True
        )
    
    def test_number_validator_invalid_numbers(self):
        """测试数字验证器 - 无效数字"""
        def test_func():
            validator = NumberValidator()
            invalid_numbers = [
                "not-a-number",
                "",
                "12.34.56",  # 多个小数点
                "abc123"
            ]
            
            for num_str in invalid_numbers:
                if validator.validate(num_str):
                    return False
            return True
        
        self.run_test_case(
            "number_validator_invalid_numbers",
            test_func,
            expected_result=True
        )
    
    def test_number_validator_range(self):
        """测试数字验证器范围"""
        def test_func():
            validator = NumberValidator(min_value=0, max_value=100)
            
            # 范围内的数字应该通过
            valid = validator.validate("50")
            # 范围外的数字应该被拒绝
            invalid = not validator.validate("150")
            
            return valid and invalid
        
        self.run_test_case(
            "number_validator_range",
            test_func,
            expected_result=True
        )
    
    def test_composite_validator(self):
        """测试复合验证器"""
        def test_func():
            email_validator = EmailValidator()
            domain_validator = EmailValidator(domain_whitelist=["example.com"])
            
            composite = CompositeValidator([email_validator, domain_validator])
            
            # 必须同时满足两个验证器
            valid = composite.validate("user@example.com")
            invalid = not composite.validate("user@other.com")
            
            return valid and invalid
        
        self.run_test_case(
            "composite_validator",
            test_func,
            expected_result=True
        )
    
    def test_create_date_validator_factory(self):
        """测试日期验证器工厂函数"""
        def test_func():
            validator = create_date_validator(["YYYY-MM-DD"])
            return isinstance(validator, DateValidator)
        
        self.run_test_case(
            "create_date_validator_factory",
            test_func,
            expected_result=True
        )
    
    def test_create_number_validator_factory(self):
        """测试数字验证器工厂函数"""
        def test_func():
            validator = create_number_validator(min_val=0, max_val=100)
            return isinstance(validator, NumberValidator)
        
        self.run_test_case(
            "create_number_validator_factory",
            test_func,
            expected_result=True
        )
    
    def test_validator_error_handling(self):
        """测试验证器错误处理"""
        def test_func():
            validator = DateValidator()
            
            # 测试None输入
            none_result = validator.validate(None)
            # 测试异常处理
            try:
                validator.validate("invalid")
                return not none_result  # None应该返回False
            except:
                return not none_result  # 异常情况下，确保None返回False
        
        self.run_test_case(
            "validator_error_handling",
            test_func,
            expected_result=True
        )
    
    def test_validator_confidence_score(self):
        """测试验证器置信度分数"""
        def test_func():
            validator = EmailValidator()
            
            # 有效邮箱应该有高置信度
            score = validator.get_confidence("user@example.com")
            return 0.8 <= score <= 1.0
        
        self.run_test_case(
            "validator_confidence_score",
            test_func,
            expected_result=True
        )
