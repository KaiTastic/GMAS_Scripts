# Results 模块使用指南

Results 模块是一个完整的字符串匹配结果处理系统，提供单一结果深度分析和多结果批量处理功能。

## 主要特性

### 1. 单一结果深度分析
- 详细的匹配信息存储
- 智能属性访问
- 上下文分析
- 质量评估
- 多种导出格式

### 2. 多结果批量处理
- 多目标匹配管理
- 批量分析功能
- 统计报告生成
- 模式识别

### 3. 配置管理
- 可定制的分析参数
- 导出格式配置
- 性能优化选项

## 基本使用

### 创建单一结果

```python
from core.utils.matcher.string_matching.results import SingleMatchResult

result = SingleMatchResult(
    matched_string="北京市",
    similarity_score=0.95,
    match_type="exact", 
    confidence=0.90,
    target_name="city",
    original_target="beijing",
    match_position=0,
    match_length=3,
    preprocessing_applied=["normalize", "clean"],
    metadata={"source": "user_input"}
)
```

### 智能属性访问

```python
# 置信度等级
print(result.confidence_level.value)  # "very_high"

# 匹配类型枚举
print(result.match_type_enum.value)   # "exact"

# 高置信度判断
print(result.is_high_confidence)     # True

# 匹配范围
print(result.match_span)             # (0, 3)
```

### 上下文分析

```python
source_text = "北京市是中国的首都"
context = result.get_context(source_text, context_length=5)
print(context)  # "**北京市**是中国的首"
```

### 质量分析

```python
from core.utils.matcher.string_matching.results import SingleResultAnalyzer

analysis = SingleResultAnalyzer.analyze_result(result)
print(f"质量等级: {analysis['quality']['level']}")
print(f"质量分数: {analysis['quality']['score']:.3f}")
```

### 结果导出

```python
from core.utils.matcher.string_matching.results import SingleResultExporter

# CSV格式
csv_row = SingleResultExporter.to_csv_row(result)

# Markdown格式
markdown = SingleResultExporter.to_markdown(result)
```

## 多结果处理

### 创建多结果

```python
from core.utils.matcher.string_matching.results import MultiMatchResult, MatchResult

matches = {
    'city': MatchResult('北京', 0.95, 'exact', 0.90, True),
    'district': MatchResult('朝阳区', 0.88, 'fuzzy', 0.85, True),
    'street': MatchResult(None, 0.0, 'none', 0.0, False)
}

multi_result = MultiMatchResult(
    source_string="北京市朝阳区某某街道",
    matches=matches,
    overall_score=0.82,
    is_complete=False,
    missing_targets=['street']
)
```

### 查询匹配结果

```python
# 获取匹配值
city = multi_result.get_matched_value('city')     # '北京'

# 检查是否匹配
has_district = multi_result.has_match('district') # True

# 获取匹配分数
score = multi_result.get_match_score('street')    # 0.0
```

### 批量分析

```python
from core.utils.matcher.string_matching.results import ResultAnalyzer

results = [multi_result1, multi_result2, ...]  # 多个结果
analysis = ResultAnalyzer.analyze_batch_results(results)

print(f"总数: {analysis['summary']['total_count']}")
print(f"完成率: {analysis['summary']['complete_rate']:.1%}")
print(f"平均分数: {analysis['summary']['avg_score']:.3f}")
```

## 配置管理

### 分析器配置

```python
from core.utils.matcher.string_matching.results import AnalyzerConfig

config = AnalyzerConfig(
    quality_weights={
        'similarity_score': 0.4,
        'confidence': 0.3,
        'match_type_bonus': 0.2,
        'consistency_check': 0.1
    },
    context_length=20,
    batch_size=1000
)
```

### 导出器配置

```python
from core.utils.matcher.string_matching.results import ExporterConfig

export_config = ExporterConfig(
    csv_encoding='utf-8',
    markdown_include_analysis=True,
    json_indent=2
)
```

## 最佳实践

### 1. 错误处理
- 使用 `validate()` 方法检查结果完整性
- 处理导入异常和运行时错误
- 验证输入参数的有效性

### 2. 性能优化
- 批量处理大量结果时使用适当的 batch_size
- 启用缓存以提高重复分析的性能
- 合理设置上下文长度

### 3. 数据一致性
- 确保匹配位置和长度的一致性
- 验证分数范围 (0.0-1.0)
- 保持目标名称的规范化

## 扩展功能

该模块设计为可扩展的，支持：
- 自定义匹配类型
- 新的导出格式
- 额外的质量评估指标
- 高级分析算法

## 故障排除

### 常见问题

1. **导入错误**: 确保从正确的路径导入模块
2. **验证失败**: 检查必需字段是否完整
3. **性能问题**: 调整批处理大小和缓存设置

### 调试技巧

- 使用 `result.validate()` 检查数据完整性
- 启用详细日志记录
- 检查配置参数是否正确

---

更多信息请参考模块源代码和测试用例。
