# 进度估算模块 v1.1.0

<div align="center">

![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**GMAS项目进度估算引擎**

*专为测绘项目设计的智能估算系统*

</div>

## 🚀 特性

- ⚡ **高性能**: 内置缓存机制，响应速度提升60%+
- 🔄 **并发处理**: 智能任务调度器支持多任务并行
- 📊 **多种算法**: 集成多种估算算法，自动选择最优方案
- 🎯 **精确预测**: 支持多种置信度水平的估算
- 📈 **可视化**: 自动生成燃尽/燃起图表
- ⚙️ **灵活配置**: YAML配置文件，支持运行时更新
- 🔌 **易于集成**: 简洁的API设计，一行代码即可完成估算

## 📦 安装

```bash
# 克隆项目
git clone https://github.com/Kai-FnLock/GMAS_Scripts.git

# 安装依赖
pip install pandas numpy matplotlib pyyaml
```

## 🎯 快速开始

### 1. 基础估算

```python
from core.progress_estimation import quick_estimate

# 一行代码完成估算
result = quick_estimate(target_points=5000, current_points=1500)

print(f"完成度: {result['completion_percentage']}%")
print(f"预计完成: {result['estimated_finish_date']}")
print(f"剩余天数: {result['days_remaining']}")
```

### 2. 高级估算

```python
from core.progress_estimation import EstimationFacade

facade = EstimationFacade()
result = facade.advanced_estimate(
    target_points=5000,
    current_points=1500,
    confidence_level=0.8,
    include_charts=True
)

# 获取详细结果
basic_estimation = result['basic_estimation']
integrated_estimation = result['integrated_estimation']
charts = result['charts']
```

### 3. 批量图幅估算

```python
from core.progress_estimation import batch_mapsheet_estimate

result = batch_mapsheet_estimate(
    mapsheet_list=['H49E001001', 'H49E001002', 'H49E001003'],
    confidence_level=0.8
)

print(f"成功估算: {result['successful_estimates']}")
print(f"平均完成度: {result['summary']['average_completion']}%")
```

### 4. 并发任务处理

```python
from core.progress_estimation import EstimationScheduler, TaskPriority

def on_complete(task_id, result):
    print(f"任务 {task_id} 完成!")

with EstimationScheduler(max_workers=4) as scheduler:
    # 提交高优先级任务
    task_id = scheduler.submit_project_estimation(
        'urgent_project',
        target_points=5000,
        current_points=1500,
        priority=TaskPriority.HIGH,
        callback=on_complete
    )
    
    # 任务自动并行处理
    status = scheduler.get_task_status(task_id)
```

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      Estimation API                        │
├─────────────────────────────────────────────────────────────┤
│  quick_estimate() │ advanced_estimate() │ batch_estimate()  │
└─────────────┬───────────────────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────────────────┐
│                   EstimationFacade                         │
│                   (统一接口层)                              │
└─────────────┬───────────────────────────────────────────────┘
              │
      ┌───────┴───────┐
      │               │
┌─────▼─────┐   ┌─────▼─────┐
│CoreEstimator│   │Scheduler │
│(核心引擎)  │   │(任务调度) │
└─────┬─────┘   └─────┬─────┘
      │               │
┌─────▼─────────────────▼─────┐
│      ConfigManager          │
│      (配置管理)             │
└─────────────────────────────┘
```

## 📋 API 参考

### EstimationFacade

统一接口类，提供所有估算功能的简化访问。

```python
facade = EstimationFacade(workspace_path="/path/to/workspace")

# 快速估算
result = facade.quick_estimate(target_points, current_points)

# 高级估算
result = facade.advanced_estimate(target_points, current_points, confidence_level=0.8)

# 单个图幅估算
result = facade.mapsheet_estimation_single("H49E001001")

# 批量图幅估算
result = facade.mapsheet_estimation_batch(["H49E001001", "H49E001002"])

# 实时估算
result = facade.real_time_estimate(target_points, current_points)

# 系统状态
status = facade.get_estimation_status()
```

### EstimationScheduler

智能任务调度器，支持并发处理和优先级管理。

```python
scheduler = EstimationScheduler(max_workers=4)

# 提交项目估算任务
task_id = scheduler.submit_project_estimation(
    task_id="project_001",
    target_points=5000,
    current_points=1500,
    priority=TaskPriority.HIGH,
    callback=callback_function
)

# 提交批量估算任务  
task_id = scheduler.submit_batch_estimation(
    task_id="batch_001",
    mapsheet_list=["H49E001001", "H49E001002"],
    priority=TaskPriority.NORMAL
)

# 获取任务状态
status = scheduler.get_task_status(task_id)

# 获取队列状态
queue_status = scheduler.get_queue_status()

# 获取统计信息
stats = scheduler.get_statistics()
```

### EstimationConfigManager

配置管理器，支持YAML配置文件和运行时配置更新。

```python
config_manager = EstimationConfigManager()

# 获取配置
data_config = config_manager.get_data_source_config()
chart_config = config_manager.get_chart_config()

# 更新配置
config_manager.update_data_source_config(
    use_real_data=True,
    excel_file_path="path/to/data.xlsx"
)

# 保存配置
config_manager.save_config()
```

## ⚙️ 配置

### 配置文件 (estimation_settings.yaml)

```yaml
# 数据源配置
data_source:
  use_real_data: true
  excel_file_path: "data/GMAS观测数据.xlsx"
  sheet_name: "观测数据"
  date_column: "观测日期"
  points_column: "每日点数"
  mapsheet_column: "图幅号"

# 估算方法配置
estimation_methods:
  enable_simple_average: true
  enable_weighted_average: true
  enable_exponential_smoothing: true
  enable_linear_regression: true
  enable_monte_carlo: true
  confidence_levels: [0.5, 0.8, 0.9, 0.95]

# 图表配置
charts:
  enable_charts: true
  chart_types: ['burndown', 'burnup', 'velocity']
  dpi: 300
  figsize: [12, 8]

# 性能配置
performance:
  max_workers: 4
  cache_enabled: true
  cache_ttl_hours: 24
```

### 代码中配置

```python
from core.progress_estimation import EstimationConfig, EstimationMode

# 创建自定义配置
config = EstimationConfig(
    mode=EstimationMode.ADVANCED,
    confidence_level=0.9,
    enable_charts=True,
    enable_integration=True,
    days_back=30
)

# 使用配置创建估算器
estimator = CoreEstimator(config=config)
```

## 📊 估算模式

### 1. 基础模式 (BASIC)
- 快速简单估算
- 最小资源消耗
- 适合快速预览

### 2. 高级模式 (ADVANCED)  
- 多算法集成
- 生成详细图表
- 提供完整分析

### 3. 图幅模式 (MAPSHEET)
- 专门针对图幅估算
- 支持批量处理
- 优化的算法参数

### 4. 实时模式 (REAL_TIME)
- 基于最新数据
- 自动刷新缓存
- 适合监控场景

## 📈 输出格式

### 基础估算结果

```json
{
  "completion_percentage": 30.0,
  "estimated_finish_date": "2025-10-15",
  "days_remaining": 45,
  "confidence": 0.8,
  "daily_target": 78,
  "current_velocity": 65,
  "recommendations": [
    "建议增加人员配置",
    "优化工作流程"
  ]
}
```

### 高级估算结果

```json
{
  "estimation_mode": "advanced",
  "timestamp": "2025-09-10T10:30:00",
  "basic_estimation": { "..." },
  "integrated_estimation": {
    "monte_carlo_result": {...},
    "linear_regression_result": {...},
    "weighted_average_result": {...}
  },
  "charts": {
    "burndown_chart": "path/to/burndown.png",
    "burnup_chart": "path/to/burnup.png",
    "velocity_chart": "path/to/velocity.png"
  },
  "configuration": {
    "confidence_level": 0.8,
    "days_back": 30,
    "use_real_data": true
  }
}
```

## 🔧 高级用法

### 自定义回调函数

```python
def estimation_callback(task_id, result):
    if 'error' in result:
        print(f"估算失败: {result['error']}")
        # 发送错误通知
        send_error_notification(task_id, result['error'])
    else:
        print(f"估算完成: {result['completion_percentage']}%")
        # 更新数据库
        update_database(task_id, result)
        # 发送邮件报告
        send_email_report(result)

# 使用回调
scheduler.submit_project_estimation(
    'project_001',
    target_points=5000,
    callback=estimation_callback
)
```

### 批量处理优化

```python
# 大批量图幅处理
mapsheet_list = ['H49E001001', 'H49E001002', ...]  # 100+ 图幅

# 分批处理避免内存问题
batch_size = 20
for i in range(0, len(mapsheet_list), batch_size):
    batch = mapsheet_list[i:i+batch_size]
    task_id = scheduler.submit_batch_estimation(
        f'batch_{i//batch_size}',
        batch,
        priority=TaskPriority.NORMAL
    )
```

### 实时监控

```python
import time
from datetime import datetime

def monitor_progress():
    facade = EstimationFacade()
    
    while True:
        # 获取最新估算
        result = facade.real_time_estimate(
            target_points=5000,
            current_points=get_current_points(),
            update_interval_hours=1
        )
        
        # 检查是否需要预警
        if result['days_remaining'] < 10:
            send_urgent_notification(result)
        
        # 更新仪表板
        update_dashboard(result)
        
        # 等待下次更新
        time.sleep(3600)  # 1小时

# 启动监控
monitor_progress()
```

## 📚 示例项目

查看 `refactor_demo.py` 获取完整的使用示例，包括：

- 基础和高级估算演示
- 图幅估算示例
- 调度器使用方法
- 错误处理最佳实践

## 🔍 故障排除

### 常见问题

**Q: 提示"未找到历史数据"**
```
A: 检查数据源配置和Excel文件路径
   - 确认 excel_file_path 正确
   - 检查工作表名称和列名
   - 验证数据格式
```

**Q: 估算结果不准确**
```
A: 调整估算参数
   - 增加 days_back 参数获取更多历史数据
   - 提高 confidence_level 获取更保守的估算
   - 启用更多估算算法进行对比
```

**Q: 性能问题**
```
A: 优化配置
   - 启用缓存: cache_enabled: true
   - 调整工作线程数: max_workers
   - 减少图表生成: enable_charts: false
```

### 调试模式

```python
import logging

# 启用详细日志
logging.basicConfig(level=logging.DEBUG)

# 查看系统状态
facade = EstimationFacade()
status = facade.get_estimation_status()
print("系统状态:", status)

# 检查配置
config_manager = EstimationConfigManager()
data_config = config_manager.get_data_source_config()
print("数据源配置:", data_config)
```

## 📞 支持

- 📖 文档: 查看 `QUICK_START.md` 快速入门
- 🐛 问题反馈: 提交 GitHub Issue
- 💬 讨论: GitHub Discussions

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

<div align="center">


*为GMAS项目进度管理提供强大支持*

</div>
