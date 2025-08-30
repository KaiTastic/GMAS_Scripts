#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据生成器和样本数据
"""

import random
import json
from typing import List, Dict, Any
from datetime import datetime, timedelta


class TestDataGenerator:
    """测试数据生成器"""
    
    @staticmethod
    def generate_contact_data(count: int = 100) -> List[str]:
        """生成联系人测试数据
        
        Args:
            count: 生成数量
            
        Returns:
            List[str]: 联系人文本列表
        """
        names = ["John", "Jane", "Alice", "Bob", "Charlie", "Diana", "Eve", "Frank",
                "Mahrous", "Ahmed", "Mohamed", "Sarah", "Lisa", "Mike", "Anna"]
        
        domains = ["example.com", "test.org", "company.net", "gmail.com", "outlook.com"]
        
        contact_data = []
        
        for i in range(count):
            name = random.choice(names)
            domain = random.choice(domains)
            
            # 生成邮箱
            email = f"{name.lower()}.{random.randint(100, 999)}@{domain}"
            
            # 生成电话
            phone_formats = [
                f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                f"555.{random.randint(100, 999)}.{random.randint(1000, 9999)}",
                f"({random.randint(100, 999)}) {random.randint(100, 999)}-{random.randint(1000, 9999)}"
            ]
            phone = random.choice(phone_formats)
            
            # 生成日期
            base_date = datetime(2025, 1, 1)
            random_days = random.randint(0, 365)
            date = (base_date + timedelta(days=random_days)).strftime("%Y-%m-%d")
            
            # 生成不同格式的联系人信息
            formats = [
                f"Contact {name} at {email} or {phone} on {date}",
                f"{name}'s email: {email}, phone: {phone}, date: {date}",
                f"Reach {name} via {email} or call {phone}",
                f"Meeting with {name} ({email}) scheduled for {date}",
                f"{name} - {email} - {phone}"
            ]
            
            contact_data.append(random.choice(formats))
        
        return contact_data
    
    @staticmethod
    def generate_product_data(count: int = 50) -> List[str]:
        """生成产品信息测试数据
        
        Args:
            count: 生成数量
            
        Returns:
            List[str]: 产品信息文本列表
        """
        brands = ["Apple", "Samsung", "Google", "Microsoft", "Sony", "HP", "Dell", "Lenovo"]
        products = ["iPhone", "Galaxy", "Pixel", "Surface", "PlayStation", "Laptop", "Desktop", "Tablet"]
        
        product_data = []
        
        for i in range(count):
            brand = random.choice(brands)
            product = random.choice(products)
            model = random.randint(1, 20)
            version = f"{random.randint(1, 5)}.{random.randint(0, 9)}"
            
            # 生成发布日期
            year = random.randint(2020, 2025)
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            date = f"{year}-{month:02d}-{day:02d}"
            
            # 生成价格
            price = random.randint(99, 2999)
            currency = random.choice(["$", "€", "¥"])
            
            formats = [
                f"{brand} {product} {model} released on {date}",
                f"{brand} {product} {model} Pro version {version} launched {date}",
                f"New {brand} {product} {model} available from {date}, price {currency}{price}",
                f"{brand} announces {product} {model} for {date} release",
                f"{brand} {product} {model} - {version} - {currency}{price}.00"
            ]
            
            product_data.append(random.choice(formats))
        
        return product_data
    
    @staticmethod
    def generate_multilingual_data(count: int = 30) -> List[str]:
        """生成多语言测试数据
        
        Args:
            count: 生成数量
            
        Returns:
            List[str]: 多语言文本列表
        """
        chinese_names = ["张三", "李四", "王五", "赵六", "陈七", "刘八"]
        english_names = ["Zhang San", "Li Si", "Wang Wu", "Zhao Liu", "Chen Qi", "Liu Ba"]
        
        multilingual_data = []
        
        for i in range(count):
            chinese_name = random.choice(chinese_names)
            english_name = random.choice(english_names)
            
            # 生成邮箱和电话
            email = f"{english_name.lower().replace(' ', '.')}@example.com"
            phone = f"+86-138-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
            
            # 生成IP地址
            ip = f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
            
            # 生成版本号
            version = f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
            
            formats = [
                f"{chinese_name} ({english_name}) 的邮箱: {email}",
                f"联系 {chinese_name} 电话 {phone} 或邮件 {email}",
                f"{chinese_name} version {version} found at IP {ip}",
                f"用户 {chinese_name} ({english_name}) - {email} - {phone}",
                f"{chinese_name} 开发的版本 {version} 部署在 {ip}"
            ]
            
            multilingual_data.append(random.choice(formats))
        
        return multilingual_data
    
    @staticmethod
    def generate_edge_case_data(count: int = 20) -> List[str]:
        """生成边界情况测试数据
        
        Args:
            count: 生成数量
            
        Returns:
            List[str]: 边界情况文本列表
        """
        edge_cases = [
            "",  # 空字符串
            "   ",  # 只有空格
            "No contact information available",  # 无匹配内容
            "Invalid email@ and phone 123",  # 无效格式
            "test@invalid-domain",  # 不完整邮箱
            "Email: user@domain.toolongextension",  # 异常域名
            "Phone: 123-456-7890-1234-5678",  # 超长电话
            "Date: 2025-13-40",  # 无效日期
            "Email user@domain.com phone +1-555-123-4567 on 2025-02-30",  # 混合有效无效
            "🎉 Contact info: 📧 user@example.com 📞 +1-555-123-4567",  # 包含emoji
            "UPPERCASE@EXAMPLE.COM",  # 大写邮箱
            "user@DOMAIN.COM",  # 混合大小写
            "Multiple emails: user1@test.com, user2@test.org, user3@test.net",  # 多个邮箱
            "Phone numbers: +1-555-1234, +1-555-5678, +1-555-9012",  # 多个电话
            "Very long text with contact info buried deep inside: " + "a" * 1000 + " email: hidden@example.com",  # 超长文本
            "Special chars: user+tag@example.com, phone: +1-(555)-123-4567",  # 特殊字符
            "Unicode: müller@example.de, téléphone: +33-1-23-45-67-89",  # Unicode字符
            "Mixed formats: Call John at john@example.com or (555) 123-4567 on 12/25/2025",  # 混合格式
        ]
        
        # 如果需要更多数据，随机选择并稍作修改
        result = edge_cases.copy()
        while len(result) < count:
            base = random.choice(edge_cases[:10])  # 从前10个基础案例中选择
            modified = f"Case {len(result)}: {base}"
            result.append(modified)
        
        return result[:count]
    
    @staticmethod
    def generate_performance_test_data(count: int = 1000) -> List[str]:
        """生成性能测试数据
        
        Args:
            count: 生成数量
            
        Returns:
            List[str]: 性能测试文本列表
        """
        # 混合各种类型的数据
        contact_data = TestDataGenerator.generate_contact_data(count // 3)
        product_data = TestDataGenerator.generate_product_data(count // 3)
        multilingual_data = TestDataGenerator.generate_multilingual_data(count // 3)
        
        # 合并并打乱顺序
        all_data = contact_data + product_data + multilingual_data
        random.shuffle(all_data)
        
        # 确保达到所需数量
        while len(all_data) < count:
            all_data.append(f"Additional test data {len(all_data)}: test@example.com")
        
        return all_data[:count]
    
    @staticmethod
    def save_test_data(data: List[str], filename: str):
        """保存测试数据到文件
        
        Args:
            data: 测试数据
            filename: 文件名
        """
        test_data_dict = {
            "generated_at": datetime.now().isoformat(),
            "count": len(data),
            "data": data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(test_data_dict, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def load_test_data(filename: str) -> List[str]:
        """从文件加载测试数据
        
        Args:
            filename: 文件名
            
        Returns:
            List[str]: 测试数据
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                test_data_dict = json.load(f)
                return test_data_dict.get("data", [])
        except FileNotFoundError:
            return []


# 预定义的测试数据集
SAMPLE_CONTACT_DATA = [
    "Contact mahrous at mahrous.doe@company.com or +1-555-123-4567 on 2025-08-30",
    "Ahmed's email: ahmed@gmail.com, phone: 555.987.6543, date: 20250829", 
    "Mohamed can be reached at mohamed@outlook.com on 2025/08/28",
    "No contact information available for this entry",
    "Engineering team: contact john.doe@company.com or call +1-555-123-4567",
    "Marketing dept: reach sarah@gmail.com at phone: (555) 987-6543",
    "Sales contact: mike@company.com, telephone: 555.246.8135",
    "Support: invalid-email@, phone: 123 (invalid)",
    "No department specified and no valid contact info"
]

SAMPLE_PRODUCT_DATA = [
    "Apple iPhone 15 Pro released on 2023-09-22",
    "Samsung Galaxy S24 launched 2024-01-17", 
    "Google Pixel 8 Pro available from 2023-10-12",
    "Microsoft Surface Pro 9 came out 2022-10-25",
    "Samsung Galaxy Watch 6 Classic released 2023-08-11",
    "Apple iPad Air 5 model A2588 from 2022-03-18",
    "Sony PlayStation 5 restocked 2023-12-01",
    "Some random text without product information"
]

SAMPLE_MULTILINGUAL_DATA = [
    "张三 (Zhang San) version 2.1.0 found at IP 192.168.1.100, cost $199.99",
    "John Smith developed v1.5 for server 10.0.0.1, budget €1,500.00", 
    "李四 created version 3.0.1 on machine 172.16.0.50, price ¥2,999.00",
    "Random text without any structured information",
    "联系张三 电话 +86-138-0013-8000 邮箱 zhangsan@example.com",
    "Contact Alice at alice@test.org or 中文电话 +86-139-1234-5678"
]


def generate_all_test_datasets():
    """生成所有测试数据集并保存到文件"""
    generator = TestDataGenerator()
    
    # 生成各种测试数据
    datasets = {
        "contact_data_100.json": generator.generate_contact_data(100),
        "product_data_50.json": generator.generate_product_data(50),
        "multilingual_data_30.json": generator.generate_multilingual_data(30),
        "edge_case_data_20.json": generator.generate_edge_case_data(20),
        "performance_data_1000.json": generator.generate_performance_test_data(1000)
    }
    
    # 保存到文件
    for filename, data in datasets.items():
        generator.save_test_data(data, filename)
        print(f"Generated {filename} with {len(data)} items")


if __name__ == "__main__":
    generate_all_test_datasets()
