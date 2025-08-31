"""
匹配器模块 - 提供各种匹配功能的统一入口

模块结构：
- string_matching/: 字符串匹配算法和策略
  - 基础匹配器：精确匹配、模糊匹配、混合匹配
  - 多目标匹配器：支持同时匹配多种类型的目标
  - 结果处理：匹配结果分析和导出
  - 验证器：匹配规则验证
  - 兼容层：向后兼容旧版本API
- 未来可扩展: image_matching/, pattern_matching/ 等

快速使用:
    from core.utils.matcher import MultiTargetMatcher, create_string_matcher
    
    # 创建基础字符串匹配器
    matcher = create_string_matcher("fuzzy", threshold=0.8)
    result = matcher.match_string("target", ["candidate1", "candidate2"])
    
    # 使用多目标匹配器
    multi_matcher = MultiTargetMatcher()
    results = multi_matcher.match_targets(targets, candidates)
"""

# 字符串匹配相关 - 核心功能
try:
    from .string_matching import (
        # 基础匹配器
        StringMatcher,
        ExactStringMatcher,
        FuzzyStringMatcher, 
        HybridStringMatcher,
        SimilarityCalculator,
        
        # 名称匹配器
        NameMatcher,
        ExactNameMatcher,
        FuzzyNameMatcher,
        HybridNameMatcher,
        
        # 工厂函数
        create_string_matcher,
        create_name_matcher,
        MatcherFactory,
        
        # 多目标匹配器 (新版本)
        MultiTargetMatcher,
        TargetType,
        TargetConfig,
        TargetBuilder,
        create_target_config,
        
        # 结果处理
        MultiMatchResult,
        ResultAnalyzer,
        ResultExporter,
        
        # 验证器
        Validator,
        get_validator,
        
        # 兼容性组件 - 已移除
        # LegacyMultiTargetMatcher,
        # create_legacy_matcher,
        # LegacyMatcherWrapper
    )
    
    __all__ = [
        # 基础匹配器
        'StringMatcher',
        'ExactStringMatcher',
        'FuzzyStringMatcher',
        'HybridStringMatcher', 
        'SimilarityCalculator',
        
        # 名称匹配器
        'NameMatcher',
        'ExactNameMatcher',
        'FuzzyNameMatcher',
        'HybridNameMatcher',
        
        # 工厂函数
        'create_string_matcher',
        'create_name_matcher',
        'MatcherFactory',
        
        # 多目标匹配器
        'MultiTargetMatcher',
        'TargetType',
        'TargetConfig',
        'TargetBuilder',
        'create_target_config',
        
        # 结果处理
        'MultiMatchResult',
        'ResultAnalyzer', 
        'ResultExporter',
        
        # 验证器
        'Validator',
        'get_validator',
        
        # 兼容性组件 - 已移除
        # 'LegacyMultiTargetMatcher',
        # 'create_legacy_matcher',
        # 'LegacyMatcherWrapper'
    ]

except ImportError as e:
    print(f"Warning: Could not import string_matching components: {e}")
    __all__ = []

# 未来可添加其他匹配类型
# from .image_matching import ImageMatcher
# from .pattern_matching import PatternMatcher
