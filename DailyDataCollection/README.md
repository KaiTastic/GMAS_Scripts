# GMAS Daily Data Collection System - GMAS每日数据收集系统

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![Version](https://img.shields.io/badge/Version-2.3.0-blue)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Modular](https://img.shields.io/badge/Architecture-Modular-orange)
![Matching](https://img.shields.io/badge/Smart%20Matching-98.8%25-yellow)
![YAML Config](https://img.shields.io/badge/YAML-Configuration-orange)
![Rights](https://img.shields.io/badge/Rights-All%20Rights%20Reserved-red)

[English](./README_en.md) | [中文](./README_cn.md)

A modular system for collecting and processing GMAS daily field data with intelligent file monitoring and KMZ/KML processing capabilities.

模块化的GMAS每日野外数据收集和处理系统，具备智能文件监控和KMZ/KML处理功能。

## Quick Start | 快速开始

### Installation | 安装

```bash
# Core dependencies | 核心依赖
pip install pandas openpyxl lxml pyzipper xmlschema tabulate

# Optional: Advanced features | 可选：高级功能
pip install python-Levenshtein rapidfuzz watchdog gdal
```

### Basic Usage | 基本使用

#### Recommended Usage | 推荐使用方式

```python
# Use modern core modules | 使用现代核心模块
from core.mapsheet import CurrentDateFiles
from core.file_handlers import KMZFile
from core.data_models import DateType
from datetime import datetime

# Create and use objects | 创建和使用对象
date = DateType(date_datetime=datetime.now())
collection = CurrentDateFiles(date)
collection.onScreenDisplay()
collection.dailyExcelReportUpdate()
```

#### Alternative Usage | 其他使用方式

```python
from core.mapsheet import CurrentDateFiles
from core.file_handlers import KMZFile
from core.data_models import DateType
from datetime import datetime

date = DateType(date_datetime=datetime.now())
collection = CurrentDateFiles(date)
collection.onScreenDisplay()
```

## Key Features | 主要功能

### V2.3.0 Features | V2.3.0版本功能

- **Modular Architecture | 模块化架构**: Refactored from monolith to specialized modules | 从单体文件重构为专门模块
- **Smart String Matching | 智能字符串匹配**: 98.8% accuracy KMZ filename matching | KMZ文件名匹配准确率达98.8%
- **Intelligent Monitoring | 智能监控**: Real-time file system monitoring with fuzzy matching | 实时文件系统监控，支持模糊匹配
- **YAML Configuration | YAML配置**: Modern configuration management system | 现代配置管理系统
- **Multi-language Support | 多语言支持**: Chinese-English mixed content processing | 中英文混合内容处理
- **Performance Optimization | 性能优化**: Multi-threading and caching mechanisms | 多线程和缓存机制

### Core Modules | 核心模块

- **Data Models | 数据模型**: KMZ/KML processing, observation data management | KMZ/KML处理，观测数据管理
- **File Handlers | 文件处理器**: Geographic data format support (KMZ, KML, SHP) | 地理数据格式支持
- **Smart Matcher | 智能匹配器**: Advanced string matching with fuzzy logic | 高级字符串匹配，支持模糊逻辑
- **Monitor System | 监控系统**: Real-time file monitoring and validation | 实时文件监控和验证
- **Report Generator | 报告生成**: Excel reports and data submission formats | Excel报告和数据提交格式

## Usage Methods | 使用方式

### Command Line | 命令行

```bash
# Display help | 显示帮助
python __main__.py --help

# Generate daily reports | 生成每日报告
python __main__.py --daily-report

# Background monitoring | 后台监控
python monitor.py

# New entry point | 新入口点
python main.py
```

### Monitoring System | 监控系统

```python
from core.monitor import MonitorManager
from core.data_models import DateType
from datetime import datetime

# Smart monitoring with fuzzy matching | 智能监控，支持模糊匹配
current_date = DateType(date_datetime=datetime.now())
monitor_manager = MonitorManager(current_date, enable_fuzzy_matching=True)
monitor_manager.start_monitoring()
```

## System Requirements | 系统要求

- **Python Version | Python版本**: 3.8+ (3.10+ recommended | 推荐3.10+)
- **Operating System | 操作系统**: Windows 10/11, macOS, Linux
- **Memory | 内存**: 4GB minimum, 8GB recommended | 最少4GB，推荐8GB
- **Storage | 存储**: 1GB available space | 1GB可用空间

## Project Status | 项目状态

- **✅ YAML Configuration**: Modern YAML-based configuration system | 现代YAML配置系统
- **✅ Unified MapsheetManager**: Consistent mapsheet handling across modules | 跨模块一致的图幅处理
- **✅ Project Structure Cleanup**: Redundant files removed, optimized organization | 项目结构清理，优化组织
- **✅ Modular Refactoring**: Core functionality split into specialized modules | 核心功能拆分为专门模块
- **✅ Modern Architecture**: Clean, maintainable codebase design | 现代架构，清洁可维护的代码设计
- **✅ Smart Matching**: Advanced string matching system deployed | 高级字符串匹配系统部署
- **✅ Monitor Refactoring**: Monitoring system split into specialized modules | 监控系统拆分为专门模块
- **🔄 Continuous Improvement**: Ongoing optimization based on usage | 基于使用情况的持续优化

## Quick Problem Resolution | 常见问题快速解决

#### ImportError / ModuleNotFoundError

```bash
pip install pandas openpyxl lxml pyzipper xmlschema tabulate python-Levenshtein rapidfuzz watchdog
```

#### AttributeError: 'CurrentDateFiles' object has no attribute 'dailyExcelReportUpdate'

```python
# Use core modules | 使用核心模块
from core.mapsheet import CurrentDateFiles  # ✅ Correct | 正确
# Not: from DailyFileGenerator import CurrentDateFiles  # ❌ Wrong | 错误
```

#### Performance Issues | 性能问题

```python
# Adjust fuzzy matching threshold | 调整模糊匹配阈值
FUZZY_MATCHING_THRESHOLD = 0.8  # Higher = stricter, faster | 更高=更严格，更快
```

## Documentation | 文档

For detailed documentation, please refer to:
详细文档请参考：

- **English Documentation | 英文文档**: [README_en.md](./README_en.md)
- **Chinese Documentation | 中文文档**: [README_cn.md](./README_cn.md)
- **Bug Fix Report | Bug修复报告**: [BUGFIX_REPORT.md](./BUGFIX_REPORT.md)

## Testing | 测试

```bash
# Quick test | 快速测试
python -c "from core.mapsheet import CurrentDateFiles; print('[Success] System working')"

# Run test suite | 运行测试套件
python tests/test_DailyFileGenerator.py

# String matching tests | 字符串匹配测试
cd core/utils/matcher/string_matching && python run_comprehensive_tests.py
```

## Version History | 版本历史

- **v2.3.0** (August 31, 2025): YAML configuration system, unified MapsheetManager, project cleanup | YAML配置系统，统一图幅管理器，项目清理
- **v2.2.1** (August 31, 2025): Smart matching system, monitor refactoring | 智能匹配系统，监控模块重构
- **v2.2.0** (August 30, 2025): Stability enhancements | 稳定性增强
- **v2.1** (August 29, 2025): Migration complete with backward compatibility | 迁移完成，向后兼容
- **v2.0** (August 29, 2025): Complete modular refactoring | 完整模块化重构
- **v1.0** (November 8, 2024): Original single-file implementation | 原始单文件实现

## Contributing | 贡献

1. Create feature branch | 创建功能分支
2. Implement changes and add tests | 实现更改并添加测试
3. Update documentation | 更新文档
4. Submit pull request | 提交拉取请求

## Contact | 联系方式

- **Author | 作者**: Kai Cao
- **Email | 邮箱**: caokai_cgs@163.com
- **Project | 项目**: [GMAS_Scripts/DailyDataCollection](https://github.com/Kai-FnLock/GMAS_Scripts)

---

**License | 许可证**: Full Copyright - All rights reserved | 保留所有权利

If this project helps you, please give it a star! | 如果这个项目对您有帮助，请给它一个星标！
