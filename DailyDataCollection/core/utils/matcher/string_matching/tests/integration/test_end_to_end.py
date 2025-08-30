#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端集成测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ...core_matcher import MultiTargetMatcher
from ...targets.builder import TargetBuilder, PresetTargets
from ...results.multi_result import ResultAnalyzer
from ..base_test import BaseTestCase


class TestEndToEnd(BaseTestCase):
    """端到端集成测试类"""
    
    def test_complete_workflow(self):
        """测试完整工作流程"""
        def test_func():
            # 1. 创建匹配器
            matcher = MultiTargetMatcher()
            
            # 2. 配置多个目标
            targets = {
                "email": TargetBuilder.create_email_target("email")["email"],
                "phone": TargetBuilder.create_phone_target("phone")["phone"],
                "date": TargetBuilder.create_date_target("date")["date"],
                "person": TargetBuilder.create_name_target("person", ["john", "jane", "alice"])["person"]
            }
            matcher.add_targets(targets)
            
            # 3. 处理测试数据
            test_texts = [
                "Contact John at john@example.com or +1-555-123-4567 on 2025-08-30",
                "Jane's email: jane@company.org, phone: 555.987.6543, date: 20250829",
                "Alice can be reached at alice@test.com on 2025/08/28",
                "No contact information available"
            ]
            
            # 4. 批量匹配
            results = matcher.match_multiple(test_texts)
            
            # 5. 分析结果
            analyzer = ResultAnalyzer(results)
            report = analyzer.generate_report()
            
            # 验证结果
            return (len(results) == 4 and
                   report["statistics"]["complete_matches"] >= 1 and
                   report["statistics"]["average_score"] > 0.3)
        
        self.run_test_case(
            "complete_workflow",
            test_func,
            expected_result=True
        )
    
    def test_real_contact_extraction(self):
        """测试真实联系人信息提取"""
        def test_func():
            matcher = MultiTargetMatcher()
            
            # 配置联系人信息目标
            targets = {
                "email": TargetBuilder.create_email_target("email")["email"],
                "phone": TargetBuilder.create_phone_target("phone")["phone"],
                "name": TargetBuilder.create_name_target(
                    "name", 
                    ["mahrous", "ahmed", "mohamed", "john", "sarah"]
                )["name"]
            }
            matcher.add_targets(targets)
            
            # 真实场景文本
            contact_text = "Contact Mr. Mahrous at mahrous.doe@company.com or call +1-555-123-4567"
            result = matcher.match_string(contact_text)
            
            return (result.get_matched_value("email") == "mahrous.doe@company.com" and
                   result.get_matched_value("phone") == "+1-555-123-4567" and
                   result.get_matched_value("name").lower() == "mahrous")
        
        self.run_test_case(
            "real_contact_extraction",
            test_func,
            expected_result=True
        )
    
    def test_product_information_extraction(self):
        """测试产品信息提取"""
        def test_func():
            matcher = MultiTargetMatcher()
            
            # 配置产品信息目标
            targets = {
                "brand": TargetBuilder.create_name_target(
                    "brand", 
                    ["apple", "samsung", "google", "microsoft"]
                )["brand"],
                "product": TargetBuilder.create_name_target(
                    "product",
                    ["iphone", "galaxy", "pixel", "surface"]
                )["product"],
                "model": TargetBuilder.create_number_target(
                    "model",
                    patterns=[r'\d+']
                )["model"],
                "date": TargetBuilder.create_date_target("date")["date"]
            }
            matcher.add_targets(targets)
            
            product_text = "Apple iPhone 15 Pro released on 2023-09-22"
            result = matcher.match_string(product_text)
            
            return (result.get_matched_value("brand").lower() == "apple" and
                   result.get_matched_value("product").lower() == "iphone" and
                   result.get_matched_value("model") == "15" and
                   result.get_matched_value("date") == "2023-09-22")
        
        self.run_test_case(
            "product_information_extraction",
            test_func,
            expected_result=True
        )
    
    def test_multilingual_support(self):
        """测试多语言支持"""
        def test_func():
            matcher = MultiTargetMatcher()
            
            # 配置中英文混合目标
            targets = {
                "chinese_name": PresetTargets.chinese_name(),
                "english_name": TargetBuilder.create_name_target(
                    "english_name",
                    ["zhang", "san", "john", "smith"]
                )["english_name"],
                "email": TargetBuilder.create_email_target("email")["email"]
            }
            matcher.add_targets(targets)
            
            mixed_text = "张三 (Zhang San) 的邮箱是 zhang.san@example.com"
            result = matcher.match_string(mixed_text)
            
            return (result.get_matched_value("chinese_name") == "张三" and
                   result.get_matched_value("english_name").lower() in ["zhang", "san"] and
                   result.get_matched_value("email") == "zhang.san@example.com")
        
        self.run_test_case(
            "multilingual_support",
            test_func,
            expected_result=True
        )
    
    def test_complex_validation_workflow(self):
        """测试复杂验证工作流程"""
        def test_func():
            matcher = MultiTargetMatcher()
            
            # 配置带验证的目标
            targets = {
                "email": TargetBuilder.create_email_target(
                    "email",
                    domain_whitelist=["company.com", "example.org"]
                )["email"],
                "phone": TargetBuilder.create_phone_target(
                    "phone",
                    country_codes=["+1", "+86"]
                )["phone"],
                "department": TargetBuilder.create_name_target(
                    "department",
                    ["engineering", "marketing", "sales"]
                )["department"]
            }
            matcher.add_targets(targets)
            
            # 测试有效数据
            valid_text = "Engineering team: contact john@company.com or +1-555-123-4567"
            valid_result = matcher.match_string(valid_text)
            
            # 测试无效数据
            invalid_text = "Marketing team: contact sarah@invalid.com or +44-20-1234-5678"
            invalid_result = matcher.match_string(invalid_text)
            
            return (valid_result.overall_score > invalid_result.overall_score and
                   valid_result.get_matched_value("email") == "john@company.com")
        
        self.run_test_case(
            "complex_validation_workflow",
            test_func,
            expected_result=True
        )
    
    def test_performance_with_large_dataset(self):
        """测试大数据集性能"""
        def test_func():
            matcher = MultiTargetMatcher()
            
            # 配置基本目标
            targets = {
                "email": TargetBuilder.create_email_target("email")["email"],
                "phone": TargetBuilder.create_phone_target("phone")["phone"]
            }
            matcher.add_targets(targets)
            
            # 生成大量测试数据
            large_dataset = []
            for i in range(100):
                large_dataset.append(f"Contact user{i}@example.com or call +1-555-{i:03d}-{i*2:04d}")
            
            # 批量处理
            import time
            start_time = time.time()
            results = matcher.match_multiple(large_dataset)
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            return (len(results) == 100 and
                   processing_time < 5.0 and  # 应该在5秒内完成
                   all(r.get_matched_value("email") for r in results))
        
        self.run_test_case(
            "performance_with_large_dataset",
            test_func,
            expected_result=True
        )
    
    def test_error_recovery(self):
        """测试错误恢复"""
        def test_func():
            matcher = MultiTargetMatcher()
            
            # 配置目标
            targets = {
                "email": TargetBuilder.create_email_target("email")["email"],
                "phone": TargetBuilder.create_phone_target("phone")["phone"]
            }
            matcher.add_targets(targets)
            
            # 测试各种异常输入
            problematic_inputs = [
                "",  # 空字符串
                None,  # None值（如果处理的话）
                "   ",  # 只有空格
                "🎉💻📧",  # Emoji
                "A" * 10000,  # 超长字符串
                "\n\t\r",  # 控制字符
            ]
            
            successful_processes = 0
            for text in problematic_inputs:
                try:
                    if text is not None:  # 跳过None，因为match_string可能不接受None
                        result = matcher.match_string(text)
                        successful_processes += 1
                except:
                    pass  # 异常是可以接受的
            
            return successful_processes >= len(problematic_inputs) - 1  # 除了None之外都应该能处理
        
        self.run_test_case(
            "error_recovery",
            test_func,
            expected_result=True
        )
    
    def test_configuration_flexibility(self):
        """测试配置灵活性"""
        def test_func():
            matcher = MultiTargetMatcher()
            
            # 动态添加和移除目标
            email_target = TargetBuilder.create_email_target("email")["email"]
            phone_target = TargetBuilder.create_phone_target("phone")["phone"]
            
            # 添加邮箱目标
            matcher.add_target("email", email_target)
            result1 = matcher.match_string("Contact john@example.com")
            
            # 添加电话目标
            matcher.add_target("phone", phone_target)
            result2 = matcher.match_string("Contact john@example.com or +1-555-123-4567")
            
            # 移除邮箱目标
            matcher.remove_target("email")
            result3 = matcher.match_string("Contact john@example.com or +1-555-123-4567")
            
            return (result1.overall_score > 0 and
                   result2.overall_score > result1.overall_score and
                   result3.get_matched_value("email") is None and
                   result3.get_matched_value("phone") is not None)
        
        self.run_test_case(
            "configuration_flexibility",
            test_func,
            expected_result=True
        )
    
    def test_result_export_integration(self):
        """测试结果导出集成"""
        def test_func():
            matcher = MultiTargetMatcher()
            
            targets = {
                "email": TargetBuilder.create_email_target("email")["email"],
                "phone": TargetBuilder.create_phone_target("phone")["phone"]
            }
            matcher.add_targets(targets)
            
            # 生成测试结果
            test_data = [
                "Contact john@example.com",
                "Call +1-555-123-4567",
                "Email jane@test.org or phone 555.987.6543"
            ]
            
            results = matcher.match_multiple(test_data)
            
            # 分析和导出
            analyzer = ResultAnalyzer(results)
            
            # 测试不同导出格式
            from ...results.multi_result import ResultExporter
            exporter = ResultExporter(results)
            
            csv_data = exporter.to_csv()
            json_data = exporter.to_json()
            dict_data = exporter.to_dict()
            
            return (len(csv_data) > 0 and
                   len(json_data) > 0 and
                   len(dict_data) == 3)
        
        self.run_test_case(
            "result_export_integration",
            test_func,
            expected_result=True
        )
