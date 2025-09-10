# GMAS 进度估算模块

新增的进度估算模块为 GMAS 数据收集系统提供了强大的项目进度跟踪、完成日期预测和可视化功能。

## 模块概述

`core/progress_estimation` 模块包含以下组件：

- **DataAnalyzer**: 数据分析器，处理历史观测数据
- **FinishDateEstimator**: 完成日期估算器，使用多种算法预测项目完成时间
- **ProgressCharts**: 图表生成器，创建燃尽图、燃起图和综合仪表板
- **ProgressTracker**: 主控制器，整合所有功能

## 主要功能

### 1. 数据分析
- 加载和分析历史观测数据
- 计算每日完成速度和趋势
- 分析团队表现和工作模式
- 提供统计摘要和趋势分析

### 2. 完成日期估算
- **简单平均法**: 基于历史平均速度估算
- **加权平均法**: 近期数据权重更高的估算
- **线性回归法**: 基于趋势的线性预测
- **蒙特卡洛模拟**: 考虑工作日/周末模式的随机模拟

### 3. 可视化图表
- **燃尽图 (Burndown Chart)**: 显示剩余工作量随时间减少的趋势
- **燃起图 (Burnup Chart)**: 显示累计完成量和目标对比
- **速度趋势图**: 每日完成量和移动平均线
- **综合仪表板**: 包含所有关键指标的综合视图

### 4. 进度跟踪
- 项目配置和进度管理
- 每日目标计算和可行性评估
- 自动生成项目建议
- 完整的进度报告生成

## 使用示例

### 基本使用

```python
from core.progress_estimation import ProgressTracker
from core.data_models.date_types import DateType
from datetime import datetime, timedelta

# 创建进度跟踪器
tracker = ProgressTracker(workspace_path="./data")

# 初始化项目
tracker.initialize_project(
    target_points=2000,    # 目标总点数
    current_points=650,    # 当前已完成点数
    start_date=DateType(datetime.now() - timedelta(days=45)),
    target_date=DateType(datetime.now() + timedelta(days=30))
)

# 加载历史数据
tracker.load_historical_data(
    start_date=DateType(datetime.now() - timedelta(days=21))
)

# 获取进度摘要
summary = tracker.get_current_progress_summary()
print(f"完成率: {summary['completion_percentage']:.1f}%")

# 生成完整报告（包含图表）
report = tracker.generate_progress_report(include_charts=True)
```

### 高级功能

```python
from core.progress_estimation import DataAnalyzer, FinishDateEstimator, ProgressCharts

# 单独使用数据分析器
analyzer = DataAnalyzer(workspace_path="./data")
analyzer.load_historical_data(start_date, end_date)
trend = analyzer.get_velocity_trend()

# 使用多种估算方法
estimator = FinishDateEstimator(analyzer)
estimates = estimator.get_multiple_estimates(target_points=2000, current_points=650)

# 生成特定图表
charts = ProgressCharts(analyzer, output_dir="./charts")
dashboard_path = charts.generate_progress_dashboard(2000, 650, estimator)
```

## 输出示例

### 进度摘要
```
项目基本信息:
- 目标点数: 2000
- 当前点数: 650  
- 完成率: 32.5%

完成日期预估:
- 预估完成日期: 2025-10-10
- 剩余天数: 30.5
- 置信度: 80.0%
- 估算方法: monte_carlo

每日目标:
- 每日需完成: 46.6 点
- 可行性评估: achievable
```

### 项目建议
系统会自动分析项目状态并生成建议：
- 完成速度呈上升趋势，保持当前工作模式
- 预估完成日期晚于目标日期，建议调整计划或增加资源
- 活跃团队数量较少，考虑增加人力投入

## 生成的图表

模块会生成以下类型的图表文件：

1. **燃尽图** (`burndown_chart_YYYYMMDD.png`)
   - 显示剩余工作量随时间的变化
   - 包含实际进度线和理想进度线
   - 标注重要时间节点

2. **燃起图** (`burnup_chart_YYYYMMDD.png`)
   - 显示累计完成量与目标对比
   - 包含理想进度和实际进度
   - 直观显示项目进展

3. **速度趋势图** (`velocity_chart_YYYYMMDD.png`)
   - 每日完成量柱状图
   - 移动平均线
   - 团队活跃度分析

4. **综合仪表板** (`progress_dashboard_YYYYMMDD.png`)
   - 项目进度概览（饼图）
   - 燃尽趋势简化视图
   - 每日完成量趋势
   - 统计信息和预估信息汇总

## 技术特性

### 数据处理
- 支持多种日期格式
- 自动处理工作日/周末模式
- 模拟数据生成（用于测试和演示）
- 异常处理和数据验证

### 算法实现
- 多种预测算法可选
- 置信度计算
- 不确定性评估
- 自动选择最佳估算方法

### 可视化
- 支持中文字体（在环境允许的情况下）
- 可配置的颜色主题
- 高分辨率图表输出
- 响应式布局设计

## 集成说明

该模块完全集成到现有的 GMAS 系统中：

1. **数据模型兼容**: 使用现有的 `DateType` 和 `ObservationData` 类
2. **配置系统集成**: 支持系统配置管理器
3. **日志系统**: 统一的日志记录和错误处理
4. **模块化设计**: 可独立使用或与其他模块组合使用

## 依赖项

模块需要以下 Python 包：
- `matplotlib`: 图表生成
- `pandas`: 数据处理和分析
- `numpy`: 数值计算
- `lxml`: XML/KML 文件处理（继承自现有系统）

## 测试覆盖

模块包含完整的测试套件：
- 单元测试覆盖所有主要功能
- 集成测试验证端到端工作流
- 模拟数据测试确保在无历史数据时正常工作
- 异常处理测试

运行测试：
```bash
python -m unittest tests.test_progress_estimation -v
```

## 使用场景

1. **项目管理**: 跟踪地质观测项目进度
2. **资源规划**: 基于历史数据优化人力资源分配
3. **进度汇报**: 自动生成可视化进度报告
4. **风险管理**: 提前识别可能的进度延误
5. **团队协调**: 分析团队表现和工作模式

该模块为 GMAS 系统增加了强大的项目管理和预测能力，帮助项目团队更好地规划和控制地质观测工作的进度。