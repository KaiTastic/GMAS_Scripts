# 图幅管理器使用指南

## 概述

图幅管理器（MapsheetManager）是一个统一的图幅信息管理模块，提供了一致的图幅初始化和配置管理功能，避免了收集模块和监控模块之间的代码重复和配置不一致。

## 核心功能

### 1. 统一的图幅信息管理
- 从配置文件自动读取图幅信息
- 提供序号和团队编号的双重索引
- 统一的字段映射和数据验证

### 2. 配置一致性保证
- 图幅序号范围：41-51（统一配置在 `mapsheet` 节）
- 团队编号范围：316-326（从实际数据自动计算）
- 消除了监控配置中的重复序号设置
- 自动验证配置一致性

### 3. 模块间一致性
- 收集模块和监控模块使用相同的初始化逻辑
- 确保图幅列表完全一致
- 避免配置不同步问题

## 使用方式

### 基本使用

```python
from core.mapsheet.mapsheet_manager import mapsheet_manager

# 获取图幅信息摘要
summary = mapsheet_manager.get_summary()
print(f"图幅总数: {summary['total_mapsheets']}")
print(f"序号范围: {summary['sequence_range']}")
print(f"团队范围: {summary['team_range']}")
```

### 创建图幅集合

```python
# 在收集模块中
from core.mapsheet.mapsheet_daily import MapsheetDailyFile
mapsheets = mapsheet_manager.create_mapsheet_collection(MapsheetDailyFile, current_date)

# 在监控模块中  
from core.monitor.mapsheet_monitor import MonitorMapSheet
mapsheets = mapsheet_manager.create_mapsheet_collection(MonitorMapSheet, current_date)
```

### 查询图幅信息

```python
# 按序号查询
mapsheet_info = mapsheet_manager.get_mapsheet_info(41.0)

# 按团队编号查询
team_info = mapsheet_manager.get_mapsheet_by_team_number("Team 316")

# 获取所有图幅文件名
filenames = mapsheet_manager.get_mapsheet_filenames()
```

## 重构后的架构优势

### 1. 代码复用
- 图幅初始化逻辑统一管理
- 避免在不同模块中重复相同的配置读取代码
- 减少维护成本

### 2. 配置一致性
- 单一数据源，避免配置分散
- 自动验证序号和团队编号的映射关系
- 统一的错误处理和日志记录

### 3. 扩展性
- 新增图幅类型时只需修改管理器
- 支持不同的图幅类创建
- 便于添加新的查询和验证功能

### 4. 向后兼容
- 保持原有API接口不变
- CurrentDateFiles.mapsInfo() 方法仍可用（已标记为弃用）
- 渐进式迁移，降低风险

## 配置优化说明

### V4.1 配置统一优化
- **移除重复配置**：删除了 `monitoring.sequence_min/max` 配置项
- **单一数据源**：图幅序号统一配置在 `mapsheet.sequence_min/max`
- **智能计算**：团队编号范围从实际数据自动计算，无需手动配置
- **避免不一致**：消除了监控模块和图幅模块配置不同步的风险

### 配置文件结构
```yaml
# 图幅序号配置（唯一的序号配置）
mapsheet:
  sequence_min: 41    # 图幅起始序号
  sequence_max: 51    # 图幅结束序号

# 监控配置（已移除sequence_min/max）
monitoring:
  time_interval_seconds: 10
  enable_fuzzy_matching: true
  # 注意：不再包含序号范围配置
```

## 配置验证

图幅管理器会自动验证以下一致性：
- 图幅数量与配置范围匹配
- 序号连续性检查
- 团队编号映射正确性
- Excel文件数据完整性

## 迁移指导

### 旧代码模式
```python
# 旧方式 - 分散的配置读取
from core.mapsheet.current_date_files import CurrentDateFiles
maps_info = CurrentDateFiles.mapsInfo()
for seq in range(SEQUENCE_MIN, SEQUENCE_MAX + 1):
    # 手动创建图幅对象...
```

### 新代码模式
```python
# 新方式 - 统一的管理器
from core.mapsheet.mapsheet_manager import mapsheet_manager
mapsheets = mapsheet_manager.create_mapsheet_collection(MapsheetClass, date)
```

## 注意事项

1. **单例模式**：图幅管理器使用单例模式，确保全局唯一实例
2. **配置更新**：修改YAML配置后需重启应用以生效
3. **依赖关系**：图幅管理器依赖ConfigManager，确保配置系统正常工作
4. **错误处理**：图幅信息加载失败时会抛出异常，需要适当处理

## 测试验证

系统提供了完整的测试覆盖：
- 配置一致性验证
- 模块初始化测试
- 图幅列表一致性检查
- 序号映射关系验证

重构后的系统确保了收集模块和监控模块的完全一致性，提高了代码质量和维护效率。
