# Matcher Module

统一的匹配器入口模块，提供各种匹配功能的集成接口。

## 模块结构

```
matcher/
├── __init__.py           # 统一入口点，聚合所有匹配功能
├── README.md            # 本文档
└── string_matching/     # 字符串匹配算法模块
    ├── 核心组件/
    │   ├── base_matcher.py      # 基础抽象类
    │   ├── core_matcher.py      # 重构后的核心匹配器  
    │   ├── exact_matcher.py     # 精确匹配
    │   ├── fuzzy_matcher.py     # 模糊匹配
    │   └── hybrid_matcher.py    # 混合匹配
    ├── 专用模块/
    │   ├── targets/            # 目标配置和构建
    │   ├── results/            # 结果处理和分析
    │   ├── validators/         # 验证器和规则
    │   └── tests/             # 完整测试框架
    └── 兼容性/
        ├── compat.py          # 兼容层
        └── deprecated/        # 历史代码
```

## 功能模块

### string_matching/ - 字符串匹配算法

完整的字符串匹配解决方案，包含：

- **基础匹配器**: 精确匹配、模糊匹配、混合匹配策略
- **多目标匹配器**: 支持同时匹配多种类型的目标
- **结果处理**: 匹配结果分析、导出和可视化
- **验证器**: 匹配规则验证和质量控制
- **兼容层**: 向后兼容旧版本API

### 未来扩展

规划中的匹配类型：
- `image_matching/`: 图像匹配算法
- `pattern_matching/`: 模式匹配算法
- `semantic_matching/`: 语义匹配算法

## 快速使用

### 基础字符串匹配

```python
from core.utils.matcher import create_string_matcher

# 创建模糊匹配器
matcher = create_string_matcher("fuzzy", threshold=0.8)

# 单个字符串匹配
result = matcher.match_string("target", ["candidate1", "candidate2"])

# 批量匹配
targets = ["target1", "target2"]
candidates = ["candidate1", "candidate2", "candidate3"]
results = matcher.match_multiple(targets, candidates)
```

### 多目标匹配

```python
from core.utils.matcher import MultiTargetMatcher, TargetType

# 创建多目标匹配器
matcher = MultiTargetMatcher()

# 配置目标类型
targets = {
    "观测点": ["Point_A", "Point_B"],
    "观测日期": ["2025-01-15", "2025-01-16"]
}

candidates = ["Point_A_data", "2025-01-15_log", "Point_B_result"]

# 执行匹配
results = matcher.match_targets(targets, candidates)
```

### 名称匹配器

```python
from core.utils.matcher import create_name_matcher

# 创建名称匹配器
matcher = create_name_matcher("fuzzy", threshold=0.85)

# 匹配人名、地名等
result = matcher.match_name("张三", ["张山", "李四", "张三丰"])
```

## 设计理念

### 职责分离

- **根目录 matcher/**: 作为聚合层，提供统一的入口点和简化的导入路径
- **子目录模块**: 专注于具体的算法实现和功能扩展
- **避免过度工程化**: 保持适当的抽象层次

### 使用便捷性

```python
# 简洁的导入路径
from core.utils.matcher import MultiTargetMatcher

# 而不是复杂的深层导入
# from core.utils.matcher.string_matching.core_matcher import MultiTargetMatcher
```

### 扩展性设计

- 为未来的匹配类型预留统一接口
- 保持向后兼容性
- 支持插件式扩展

## 架构优势

1. **模块化设计**: 每个子模块职责明确，便于维护和扩展
2. **统一入口**: 简化用户使用，降低学习成本  
3. **向后兼容**: 保护现有代码投资
4. **测试完备**: 完整的测试框架保障代码质量
5. **文档齐全**: 详细的文档和示例代码

## 版本信息

- 当前版本: 基于重构阶段4 (2025-08-30)
- 核心功能: 字符串匹配算法和多目标匹配
- 兼容性: 支持旧版本API
- 测试覆盖率: 完整的单元测试和集成测试

更多详细信息请参考 `string_matching/docs/` 目录下的文档。
