# 监控模块重构说明

## 重构概述

原有的 `monitor.py` 文件（385行）已经重构为模块化的设计，提高了代码的可维护性、可测试性和可扩展性。

## 新的模块结构

```
core/monitor/
├── __init__.py              # 模块入口
├── file_validator.py        # 文件验证器
├── display_manager.py       # 显示管理器
├── mapsheet_monitor.py      # 图幅监控器
├── event_handler.py         # 事件处理器
└── monitor_manager.py       # 监控管理器
```

## 各模块职责

### 1. FileValidator (file_validator.py)
- **职责**: KMZ文件的验证逻辑
- **功能**: 
  - 验证文件扩展名
  - 验证日期格式和有效性
  - 验证图幅名称
  - 区分完成点文件和计划路线文件

### 2. DisplayManager (display_manager.py)
- **职责**: 所有的显示和输出逻辑
- **功能**:
  - 格式化表格显示
  - 状态信息输出
  - 错误信息显示
  - 催促模式提醒

### 3. MonitorMapSheet & MonitorMapSheetCollection (mapsheet_monitor.py)
- **职责**: 图幅的监控和管理
- **功能**:
  - 单个图幅状态管理
  - 图幅集合的组织
  - 数据更新逻辑

### 4. FileEventHandler (event_handler.py)
- **职责**: 文件系统事件处理
- **功能**:
  - 监听文件创建事件
  - 协调验证和更新流程
  - 管理待收集文件列表

### 5. MonitorManager (monitor_manager.py)
- **职责**: 整个监控流程的协调
- **功能**:
  - 启动和停止监控
  - 管理监控循环
  - 处理超时和完成逻辑

## 🚀 使用方式

### 基本使用
```python
from datetime import datetime
from core.data_models.date_types import DateType
from core.monitor import MonitorManager

# 创建监控管理器
current_date = DateType(date_datetime=datetime.now())
monitor_manager = MonitorManager(current_date)

# 启动监控
monitor_manager.start_monitoring()
```

### 带回调函数的使用
```python
def post_processing():
    print("监控完成，开始后续处理...")

monitor_manager.start_monitoring(
    executor=post_processing,
    end_time=datetime.now().replace(hour=20, minute=30)
)
```

### 获取监控状态
```python
status = monitor_manager.get_monitoring_status()
print(f"剩余文件数: {status['remaining_files']}")
```

## 重构带来的优势

### 1. **职责分离**
- 每个类都有明确的单一职责
- 减少了类之间的耦合

### 2. **易于测试**
- 每个模块可以独立测试
- 依赖注入使得模拟测试更容易

### 3. **易于维护**
- 代码结构清晰，修改影响范围小
- 新功能可以独立添加

### 4. **易于扩展**
- 可以轻松添加新的文件类型验证器
- 可以插入不同的显示方式
- 可以添加新的事件处理逻辑

### 5. **更好的错误处理**
- 集中的错误显示逻辑
- 更详细的错误信息

## 迁移指南

### 原代码使用方式:
```python
if __name__ == "__main__":
    datenow = DateType(date_datetime=datetime.now())
    event_handler = DataHandler(currentDate=datenow)
    event_handler.obsserverService()
```

### 新代码使用方式:
```python
if __name__ == "__main__":
    current_date = DateType(date_datetime=datetime.now())
    monitor_manager = MonitorManager(current_date)
    monitor_manager.start_monitoring()
```

## 兼容性说明

- 原有的 `monitor.py` 文件保持不变，确保向后兼容
- 新的重构版本在 `monitor_refactored.py` 中提供
- 可以逐步迁移到新的模块化版本

## 测试建议

```python
# 测试文件验证器
def test_file_validator():
    validator = KMZFileValidator(current_date, mapsheet_names)
    assert validator.validate_finished_file("test_finished_points_and_tracks_20250829.kmz")

# 测试监控管理器
def test_monitor_manager():
    manager = MonitorManager(current_date)
    status = manager.get_monitoring_status()
    assert 'planned_files' in status
```

这种模块化设计使得代码更加健壮、可维护，并为将来的功能扩展提供了良好的基础。
