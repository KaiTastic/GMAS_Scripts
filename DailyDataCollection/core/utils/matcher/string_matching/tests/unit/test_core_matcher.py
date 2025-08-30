#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心匹配器单元测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ...core_matcher import MultiTargetMatcher
from ...targets.builder import TargetBuilder
from ...targets.config import TargetType, create_target_config
from ..base_test import BaseTestCase


class TestCoreMatcher(BaseTestCase):
    """核心匹配器测试类"""
    
    def setUp(self):
        """测试前设置"""
        super().setUp()
        self.matcher = MultiTargetMatcher()
        
    def test_matcher_creation(self):
        """测试匹配器创建"""
        def test_func():
            matcher = MultiTargetMatcher()
            return isinstance(matcher, MultiTargetMatcher)
        
        self.run_test_case(
            "matcher_creation",
            test_func,
            expected_result=True
        )
    
    def test_add_single_target(self):
        """测试添加单个目标"""
        def test_func():
            email_target = TargetBuilder.create_email_target("email")["email"]
            self.matcher.add_target("email", email_target)
            return "email" in self.matcher.targets
        
        self.run_test_case(
            "add_single_target",
            test_func,
            expected_result=True
        )
    
    def test_add_multiple_targets(self):
        """测试添加多个目标"""
        def test_func():
            targets = {
                "email": TargetBuilder.create_email_target("email")["email"],
                "phone": TargetBuilder.create_phone_target("phone")["phone"]
            }
            self.matcher.add_targets(targets)
            return len(self.matcher.targets) >= 2
        
        self.run_test_case(
            "add_multiple_targets",
            test_func,
            expected_result=True
        )
    
    def test_email_matching(self):
        """测试邮箱匹配"""
        def test_func():
            email_target = TargetBuilder.create_email_target("email")["email"]
            self.matcher.add_target("email", email_target)
            
            result = self.matcher.match_string("Contact john@example.com for info")
            return result.get_matched_value("email")
        
        self.run_test_case(
            "email_matching",
            test_func,
            expected_result="john@example.com"
        )
    
    def test_phone_matching(self):
        """测试电话号码匹配"""
        def test_func():
            phone_target = TargetBuilder.create_phone_target("phone")["phone"]
            self.matcher.add_target("phone", phone_target)
            
            result = self.matcher.match_string("Call me at +1-555-123-4567")
            return result.get_matched_value("phone")
        
        self.run_test_case(
            "phone_matching", 
            test_func,
            expected_result="+1-555-123-4567"
        )
    
    def test_date_matching(self):
        """测试日期匹配"""
        def test_func():
            date_target = TargetBuilder.create_date_target("date")["date"]
            self.matcher.add_target("date", date_target)
            
            result = self.matcher.match_string("Meeting on 2025-08-30")
            return result.get_matched_value("date")
        
        self.run_test_case(
            "date_matching",
            test_func,
            expected_result="2025-08-30"
        )
    
    def test_name_matching(self):
        """测试姓名匹配"""
        def test_func():
            name_target = TargetBuilder.create_name_target(
                "person", 
                names=["john", "jane", "alice", "bob"]
            )["person"]
            self.matcher.add_target("person", name_target)
            
            result = self.matcher.match_string("Hello John, how are you?")
            matched_name = result.get_matched_value("person")
            return matched_name.lower() if matched_name else None
        
        self.run_test_case(
            "name_matching",
            test_func,
            expected_result="john"
        )
    
    def test_multi_target_matching(self):
        """测试多目标匹配"""
        def test_func():
            targets = {
                "email": TargetBuilder.create_email_target("email")["email"],
                "phone": TargetBuilder.create_phone_target("phone")["phone"],
                "date": TargetBuilder.create_date_target("date")["date"]
            }
            self.matcher.add_targets(targets)
            
            text = "Contact john@example.com or +1-555-123-4567 on 2025-08-30"
            result = self.matcher.match_string(text)
            
            return (result.get_matched_value("email") == "john@example.com" and
                   result.get_matched_value("phone") == "+1-555-123-4567" and
                   result.get_matched_value("date") == "2025-08-30")
        
        self.run_test_case(
            "multi_target_matching",
            test_func,
            expected_result=True
        )
    
    def test_overall_score_calculation(self):
        """测试总分计算"""
        def test_func():
            targets = {
                "email": TargetBuilder.create_email_target("email")["email"],
                "phone": TargetBuilder.create_phone_target("phone")["phone"]
            }
            self.matcher.add_targets(targets)
            
            # 只匹配一个目标
            result = self.matcher.match_string("Email: john@example.com")
            return 0.4 <= result.overall_score <= 0.6  # 50%匹配
        
        self.run_test_case(
            "overall_score_calculation",
            test_func,
            expected_result=True
        )
    
    def test_complete_match_detection(self):
        """测试完整匹配检测"""
        def test_func():
            targets = {
                "email": TargetBuilder.create_email_target("email")["email"],
                "phone": TargetBuilder.create_phone_target("phone")["phone"]
            }
            self.matcher.add_targets(targets)
            
            # 匹配所有目标
            text = "Contact john@example.com or +1-555-123-4567"
            result = self.matcher.match_string(text)
            return result.is_complete
        
        self.run_test_case(
            "complete_match_detection",
            test_func,
            expected_result=True
        )
    
    def test_missing_targets_detection(self):
        """测试缺失目标检测"""
        def test_func():
            targets = {
                "email": TargetBuilder.create_email_target("email")["email"],
                "phone": TargetBuilder.create_phone_target("phone")["phone"],
                "date": TargetBuilder.create_date_target("date")["date"]
            }
            self.matcher.add_targets(targets)
            
            # 只提供邮箱
            result = self.matcher.match_string("Email: john@example.com")
            return "phone" in result.missing_targets and "date" in result.missing_targets
        
        self.run_test_case(
            "missing_targets_detection",
            test_func,
            expected_result=True
        )
    
    def test_batch_matching(self):
        """测试批量匹配"""
        def test_func():
            email_target = TargetBuilder.create_email_target("email")["email"]
            self.matcher.add_target("email", email_target)
            
            texts = [
                "Contact john@example.com",
                "Email: jane@company.org", 
                "No email here"
            ]
            
            results = self.matcher.match_multiple(texts)
            matched_count = sum(1 for r in results if r.get_matched_value("email"))
            return matched_count == 2
        
        self.run_test_case(
            "batch_matching",
            test_func,
            expected_result=True
        )
    
    def test_target_removal(self):
        """测试目标移除"""
        def test_func():
            email_target = TargetBuilder.create_email_target("email")["email"]
            self.matcher.add_target("email", email_target)
            
            # 移除目标
            self.matcher.remove_target("email")
            return "email" not in self.matcher.targets
        
        self.run_test_case(
            "target_removal",
            test_func,
            expected_result=True
        )
    
    def test_target_update(self):
        """测试目标更新"""
        def test_func():
            # 添加初始目标
            original_target = TargetBuilder.create_email_target("email")["email"]
            self.matcher.add_target("email", original_target)
            
            # 更新目标配置
            new_target = TargetBuilder.create_email_target("email", required=False)["email"]
            self.matcher.update_target("email", new_target)
            
            return self.matcher.targets["email"].required == False
        
        self.run_test_case(
            "target_update",
            test_func,
            expected_result=True
        )
    
    def test_clear_targets(self):
        """测试清空目标"""
        def test_func():
            # 添加多个目标
            targets = {
                "email": TargetBuilder.create_email_target("email")["email"],
                "phone": TargetBuilder.create_phone_target("phone")["phone"]
            }
            self.matcher.add_targets(targets)
            
            # 清空所有目标
            self.matcher.clear_targets()
            return len(self.matcher.targets) == 0
        
        self.run_test_case(
            "clear_targets",
            test_func,
            expected_result=True
        )
    
    def test_get_target_names(self):
        """测试获取目标名称"""
        def test_func():
            targets = {
                "email": TargetBuilder.create_email_target("email")["email"],
                "phone": TargetBuilder.create_phone_target("phone")["phone"]
            }
            self.matcher.add_targets(targets)
            
            target_names = self.matcher.get_target_names()
            return set(target_names) == {"email", "phone"}
        
        self.run_test_case(
            "get_target_names", 
            test_func,
            expected_result=True
        )
    
    def test_empty_text_handling(self):
        """测试空文本处理"""
        def test_func():
            email_target = TargetBuilder.create_email_target("email")["email"]
            self.matcher.add_target("email", email_target)
            
            result = self.matcher.match_string("")
            return result.overall_score == 0.0 and not result.is_complete
        
        self.run_test_case(
            "empty_text_handling",
            test_func,
            expected_result=True
        )
    
    def test_no_targets_handling(self):
        """测试无目标处理"""
        def test_func():
            # 不添加任何目标
            result = self.matcher.match_string("Some text")
            return result.overall_score == 0.0
        
        self.run_test_case(
            "no_targets_handling",
            test_func,
            expected_result=True
        )
