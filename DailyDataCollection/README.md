# GMAS Daily Data Collection System - GMAS每日数据收集系统

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Version](https://img.shields.io/badge/Version-2.4.0-blue)
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
# Method 1: Install all dependencies at once | 方法1：一次安装所有依赖
pip install pandas openpyxl lxml pyzipper xmlschema tabulate pyyaml python-Levenshtein rapidfuzz watchdog gdal

# Method 2: Step by step installation | 方法2：分步安装
# Core dependencies (required) | 核心依赖（必需）
pip install pandas openpyxl lxml pyzipper xmlschema tabulate pyyaml

# Advanced features (recommended) | 高级功能（推荐）
pip install python-Levenshtein rapidfuzz watchdog

# Geospatial support (optional) | 地理空间支持（可选）
pip install gdal

# For development/testing | 开发/测试用
pip install pytest pytest-cov

# Method 3: Using requirements file | 方法3：使用requirements文件
# Create requirements.txt with above packages | 创建包含上述包的requirements.txt
pip install -r requirements.txt
```

### Quick Setup | 快速设置

```bash
# 1. Clone repository | 克隆仓库
git clone https://github.com/Kai-FnLock/GMAS_Scripts.git
cd GMAS_Scripts/DailyDataCollection

# 2. Install dependencies | 安装依赖
pip install pandas openpyxl lxml pyzipper xmlschema tabulate pyyaml python-Levenshtein rapidfuzz watchdog

# 3. Configure settings | 配置设置
# Edit config/settings.yaml to match your environment | 编辑 config/settings.yaml 以匹配您的环境

# 4. Test installation | 测试安装
python __main__.py --help

# 5. Run first data collection | 运行首次数据收集
python __main__.py --dry-run
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

### V2.4.0 Features | V2.4.0版本功能

- **System Enhancement | 系统功能增强**: Improved stability and reliability | 提升稳定性和可靠性
- **Performance Optimization | 性能优化**: Enhanced algorithms and processing efficiency | 增强算法和处理效率
- **User Experience | 用户体验**: Better interaction and feedback mechanisms | 更好的交互和反馈机制
- **Centralized Version Management | 版本信息集中管理**: Unified version control across all modules | 跨模块统一版本控制
- **Code Cleanup and Optimization | 代码清理优化**: Professional formatting and compatibility | 专业格式化和兼容性提升
- **Enhanced Configuration | 增强配置系统**: Seamless version-config integration | 版本配置无缝集成
- **Modular Architecture | 模块化架构**: Refactored from monolith to specialized modules | 从单体文件重构为专门模块
- **Smart String Matching | 智能字符串匹配**: 98.8% accuracy KMZ filename matching | KMZ文件名匹配准确率达98.8%
- **Intelligent Monitoring | 智能监控**: Real-time file system monitoring with fuzzy matching | 实时文件系统监控，支持模糊匹配
- **YAML Configuration | YAML配置**: Modern configuration management system | 现代配置管理系统
- **Multi-language Support | 多语言支持**: Chinese-English mixed content processing | 中英文混合内容处理

## Configuration | 配置系统

The system uses YAML-based configuration for easy customization:
系统使用基于YAML的配置，便于自定义：

```yaml
# config/settings.yaml - Complete configuration example | 完整配置示例
system:
  workspace: "D:\\RouteDesign"
  current_path: null  # Auto-set to script directory | 自动设置为脚本所在目录
  
platform:
  wechat_folders:
    windows: "D:\\Users\\[username]\\Documents\\WeChat Files\\[wxid]\\FileStorage\\File"
    macos: "/Users/[username]/Library/Containers/com.tencent.xinWeChat/Data/Library/Application Support/com.tencent.xinWeChat/[version]/[wxid]/Message/MessageTemp"
  
monitoring:
  time_interval_seconds: 10      # Folder refresh check interval (seconds) | 文件夹刷新检查间隔（秒）
  status_interval_minutes: 30    # Monitor status refresh interval (minutes) | 监视状态刷新间隔（分钟）
  end_time:                      # Monitor end time | 监控结束时间
    hour: 20
    minute: 30
    second: 0
  enable_fuzzy_matching: true    # Enable fuzzy matching | 启用模糊匹配
  fuzzy_threshold: 0.65          # Fuzzy matching threshold | 模糊匹配阈值
  
mapsheet:
  sequence_min: 41               # Mapsheet sequence range (Group 3.2) | 图幅序号范围（Group 3.2）
  sequence_max: 51
  
data_collection:
  traceback_date: "20250710"     # File traceback start date | 文件回溯查找起始日期
  weekdays: [5]                  # Data submission weekdays (Saturday=5) | 数据提交的工作日（周六=5）
  traceback_days: 60             # Traceback search days | 回溯查找天数
  traceforward_days: 7           # Forward search days | 向前查找天数
  collection_weekdays: [5]       # Weekly data collection days (Saturday) | 每周数据收集日（周六）

reports:
  output_formats: ["kmz", "excel", "statistics"]
  excel:
    include_charts: true
  statistics:
    daily_details_file: "统计详情.xlsx"  # Statistics details file | 统计详情文件
```

### Configuration Options | 配置选项说明

| Configuration Item 配置项 | Description 说明 | Default Value 默认值 |
|---------------------------|-----------------|-------------------|
| `system.workspace` | Main workspace path 主工作空间路径 | `"D:\\RouteDesign"` |
| `monitoring.fuzzy_threshold` | Fuzzy matching similarity threshold (0.0-1.0) 模糊匹配相似度阈值 | `0.65` |
| `monitoring.time_interval_seconds` | File check interval in seconds 文件检查间隔秒数 | `10` |
| `mapsheet.sequence_min/max` | Mapsheet sequence range 图幅序号范围 | `41-51` |
| `data_collection.weekdays` | Data submission days (0=Monday, 6=Sunday) 数据提交日（0=周一，6=周日） | `[5]` |

### Core Modules | 核心模块

- **Data Models | 数据模型**: KMZ/KML processing, observation data management | KMZ/KML处理，观测数据管理
- **File Handlers | 文件处理器**: Geographic data format support (KMZ, KML, SHP) | 地理数据格式支持
- **Smart Matcher | 智能匹配器**: Advanced string matching with fuzzy logic | 高级字符串匹配，支持模糊逻辑
- **Monitor System | 监控系统**: Real-time file monitoring and validation | 实时文件监控和验证
- **Report Generator | 报告生成**: Excel reports and data submission formats | Excel报告和数据提交格式

## Project Structure | 项目结构

```
DailyDataCollection/
├── __init__.py                 # Version info and package initialization | 版本信息和包初始化
├── __main__.py                 # Main entry point with command line support | 主入口点，支持命令行参数
├── logger.py                   # Logging configuration file | 日志配置文件
├── config/                     # Configuration system | 配置系统
│   ├── __init__.py
│   ├── config_manager.py      # Configuration manager for YAML | 配置管理器，处理YAML配置
│   ├── logger_manager.py      # Logging manager | 日志管理器
│   └── settings.yaml          # YAML configuration file (main config) | YAML配置文件（主要配置）
├── core/                       # Core modules | 核心模块
│   ├── __init__.py
│   ├── data_models/           # Data models | 数据模型
│   │   ├── date_types.py      # Date type handling | 日期类型处理
│   │   ├── file_attributes.py # File attribute models | 文件属性模型
│   │   └── observation_data.py # Observation data models | 观测数据模型
│   ├── file_handlers/         # File handlers | 文件处理器
│   │   ├── base_io.py         # Basic IO operations | 基础IO操作
│   │   └── kmz_handler.py     # KMZ/KML file processing | KMZ/KML文件处理
│   ├── mapsheet/              # Mapsheet management | 图幅管理
│   │   ├── current_date_files.py # Current date file management | 当前日期文件管理
│   │   ├── mapsheet_daily.py  # Daily mapsheet processing | 每日图幅处理
│   │   └── mapsheet_manager.py # Mapsheet manager | 图幅管理器
│   ├── map_export/            # Map export | 地图导出
│   │   ├── call_mapexport.py  # Map export caller | 地图导出调用
│   │   ├── mapExport.py       # Map export main logic | 地图导出主逻辑
│   │   └── simple_call_mapexport.py # Simplified export interface | 简化导出接口
│   ├── monitor/               # Monitoring system | 监控系统
│   │   ├── event_handler.py   # Event handler | 事件处理器
│   │   ├── file_validator.py  # File validator | 文件验证器
│   │   ├── mapsheet_monitor.py # Mapsheet monitor | 图幅监控
│   │   ├── monitor_manager.py  # Monitor manager | 监控管理器
│   │   └── name_matcher_simple.py # Simple name matcher | 简单名称匹配
│   ├── reports/               # Report generation | 报告生成
│   │   └── data_submission.py # Data submission reports | 数据提交报告
│   └── utils/                 # Utility functions | 工具函数
│       ├── file_utils.py      # File utility functions | 文件工具函数
│       └── matcher/           # String matching tools | 字符串匹配工具
├── display/                   # Display modules | 显示模块
│   ├── collection_display.py  # Collection process display | 收集过程显示
│   ├── message_display.py     # Message display | 消息显示
│   ├── monitor_display.py     # Monitor display | 监控显示
│   └── report_display.py      # Report display | 报告显示
├── tests/                     # Test files | 测试文件
│   ├── test_modular_architecture.py # Modular architecture tests | 模块化架构测试
│   └── __testData__/          # Test data | 测试数据
├── resource/                  # Resource files | 资源文件
│   └── kml_xsd/              # KML schema files | KML架构文件
│       ├── 220/              # KML 2.2.0 schema | KML 2.2.0 架构
│       └── 230/              # KML 2.3.0 schema | KML 2.3.0 架构
└── Design/                    # Design documents | 设计文档
    ├── 构造KMZ文件类的思路.md # Design concept document | 设计思路文档
    └── ClassDiagram.eapx      # Class diagram design | 类图设计
```

## Usage Methods | 使用方式

### Command Line | 命令行

```bash
# Basic usage | 基本用法
python __main__.py                          # Use today's date for collection | 使用今天日期收集数据
python __main__.py --date 20250901          # Specify date for collection | 指定日期收集数据
python __main__.py --date 2025-09-01        # Support multiple date formats | 支持多种日期格式

# Monitoring mode | 监控模式
python __main__.py --monitor                # Start file monitoring | 启动文件监控
python __main__.py --monitor --endtime 183000  # Specify monitoring end time | 指定监控结束时间
python __main__.py --monitor --date 20250901 --endtime 18:30:00

# Advanced options | 高级选项
python __main__.py --verbose                # Verbose output mode | 详细输出模式
python __main__.py --debug                  # Debug mode | 调试模式
python __main__.py --dry-run               # Simulate run (no file modification) | 模拟运行（不修改文件）
python __main__.py --no-kmz               # Skip KMZ report generation | 跳过KMZ报告生成
python __main__.py --no-excel             # Skip Excel report generation | 跳过Excel报告生成
python __main__.py --force-weekly         # Force weekly report generation | 强制生成周报告

# Configuration options | 配置选项
python __main__.py --config custom.yaml    # Use custom configuration file | 使用自定义配置文件
python __main__.py --workspace /path/to/workspace  # Specify workspace | 指定工作空间
python __main__.py --fuzzy-threshold 0.8   # Set fuzzy matching threshold | 设置模糊匹配阈值

# Help and version | 帮助和版本
python __main__.py --help                  # Show complete help information | 显示完整帮助信息
python __main__.py --version              # Show version information | 显示版本信息
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

- **Python Version | Python版本**: 3.10+ (推荐3.10+，需支持YAML配置)
- **Operating System | 操作系统**: Windows 10/11, macOS, Linux
- **Memory | 内存**: 4GB minimum, 8GB recommended | 最少4GB，推荐8GB
- **Storage | 存储**: 1GB available space | 1GB可用空间
- **Dependencies | 依赖项**: pandas, openpyxl, lxml, pyzipper, xmlschema, tabulate, pyyaml

## Project Status | 项目状态

- **[完成] ✅ Centralized Version Management | 版本信息集中管理**: Single source of truth for all versions | 所有版本信息的唯一来源
- **[完成] ✅ Code Quality Improvements | 代码质量改进**: Professional formatting and cross-platform compatibility | 专业格式化和跨平台兼容性
- **[完成] ✅ YAML Configuration**: Modern YAML-based configuration system | 现代YAML配置系统
- **[完成] ✅ Unified MapsheetManager**: Consistent mapsheet handling across modules | 跨模块一致的图幅处理
- **[完成] ✅ Project Structure Cleanup**: Redundant files removed, optimized organization | 项目结构清理，优化组织
- **[完成] ✅ Modular Refactoring**: Core functionality split into specialized modules | 核心功能拆分为专门模块
- **[完成] ✅ Modern Architecture**: Clean, maintainable codebase design | 现代架构，清洁可维护的代码设计
- **[完成] ✅ Smart Matching**: Advanced string matching system deployed | 高级字符串匹配系统部署
- **[完成] ✅ Monitor Refactoring**: Monitoring system split into specialized modules | 监控系统拆分为专门模块
- **[进行中] 🔄 Continuous Improvement**: Ongoing optimization based on usage | 基于使用情况的持续优化

## Quick Problem Resolution | 常见问题快速解决

#### ImportError / ModuleNotFoundError

```bash
pip install pandas openpyxl lxml pyzipper xmlschema tabulate python-Levenshtein rapidfuzz watchdog pyyaml
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
- **Configuration Guide | 配置指南**: [config/settings.yaml](./config/settings.yaml)

## Testing | 测试

### Quick Tests | 快速测试

```bash
# Test system installation | 测试系统安装
python -c "from core.mapsheet import CurrentDateFiles; print('[Success] Core modules imported')"

# Test configuration system | 测试配置系统
python -c "from config import ConfigManager; config = ConfigManager(); print('[Success] Configuration loaded')"

# Test date handling | 测试日期处理
python -c "from core.data_models import DateType; from datetime import datetime; date = DateType(date_datetime=datetime.now()); print(f'[Success] Date: {date.yyyymmdd_str}')"

# Dry run test | 模拟运行测试
python __main__.py --dry-run --verbose
```

### Test Suite | 测试套件

```bash
# Run main test suite | 运行主测试套件
python tests/test_modular_architecture.py

# Run with verbose output | 详细输出运行
python -m unittest tests.test_modular_architecture -v

# Test specific components | 测试特定组件
python -c "
import unittest
import sys
sys.path.insert(0, '.')
from tests.test_modular_architecture import TestCoreModules
suite = unittest.TestLoader().loadTestsFromTestCase(TestCoreModules)
unittest.TextTestRunner(verbosity=2).run(suite)
"
```

### Development Testing | 开发测试

```bash
# Test with different dates | 测试不同日期
python __main__.py --date 20250901 --dry-run
python __main__.py --date 2025-08-31 --dry-run

# Test monitoring mode | 测试监控模式
python __main__.py --monitor --dry-run --endtime 120000

# Test configuration override | 测试配置覆盖
python __main__.py --workspace /tmp/test --dry-run

# Performance testing | 性能测试
python __main__.py --profile --dry-run
```

### Troubleshooting Tests | 故障排除测试

```bash
# Test dependency imports | 测试依赖导入
python -c "
required_modules = ['pandas', 'openpyxl', 'lxml', 'pyzipper', 'xmlschema', 'tabulate', 'yaml']
for module in required_modules:
    try:
        __import__(module)
        print(f'✅ {module} - OK')
    except ImportError as e:
        print(f'❌ {module} - ERROR: {e}')
"

# Test file system access | 测试文件系统访问
python -c "
import os
from config import ConfigManager
config = ConfigManager().get_config()
workspace = config['system']['workspace']
print(f'Workspace: {workspace}')
print(f'Workspace exists: {os.path.exists(workspace)}')
print(f'Workspace writable: {os.access(workspace, os.W_OK) if os.path.exists(workspace) else False}')
"
```

## Version History | 版本历史

- **v2.4.0** (September 1, 2025 | 2025年9月1日): System enhancement and performance optimization | 系统功能增强与性能优化
- **v2.3.1** (September 1, 2025 | 2025年9月1日): Centralized version management, code cleanup and optimization | 版本信息集中管理，代码清理优化
- **v2.3.0** (August 31, 2025 | 2025年8月31日): YAML configuration system, unified MapsheetManager, project cleanup | YAML配置系统，统一图幅管理器，项目清理
- **v2.2.1** (August 31, 2025 | 2025年8月31日): Smart matching system, monitor refactoring | 智能匹配系统，监控模块重构
- **v2.2.0** (August 30, 2025 | 2025年8月30日): Stability enhancements | 稳定性增强
- **v2.1** (August 29, 2025 | 2025年8月29日): Migration complete with backward compatibility | 迁移完成，向后兼容
- **v2.0** (August 29, 2025 | 2025年8月29日): Complete modular refactoring | 完整模块化重构
- **v1.0** (November 8, 2024 | 2024年11月8日): Original single-file implementation | 原始单文件实现

## Contributing | 贡献

1. Create feature branch | 创建功能分支
2. Implement changes and add tests | 实现更改并添加测试
3. Update documentation | 更新文档
4. Submit pull request | 提交拉取请求

## FAQ | 常见问题

### Q: How to configure WeChat folder path? | 如何配置微信文件夹路径？
**A:** Edit the `platform.wechat_folders` section in `config/settings.yaml` file and set the path for your operating system.

**答:** 编辑 `config/settings.yaml` 文件中的 `platform.wechat_folders` 部分，设置对应操作系统的路径。

### Q: What to do if fuzzy matching is not accurate enough? | 模糊匹配不够准确怎么办？
**A:** You can adjust the matching threshold through the `--fuzzy-threshold` parameter or configuration file. Higher values mean stricter matching.

**答:** 可以通过 `--fuzzy-threshold` 参数或配置文件调整匹配阈值，数值越高匹配越严格。

### Q: How to run the program without generating certain types of reports? | 如何运行程序不生成某种类型的报告？
**A:** Use the corresponding skip parameters: `--no-kmz`, `--no-excel`, `--no-statistics`.

**答:** 使用相应的跳过参数：`--no-kmz`、`--no-excel`、`--no-statistics`。

### Q: What to do if encoding errors occur during program execution? | 程序运行时出现编码错误怎么办？
**A:** Ensure your system supports UTF-8 encoding. Windows users may need to set the environment variable `PYTHONIOENCODING=utf-8`.

**答:** 确保系统支持UTF-8编码，Windows用户可能需要设置环境变量 `PYTHONIOENCODING=utf-8`。

### Q: How to view detailed runtime logs? | 如何查看详细的运行日志？
**A:** Use `--verbose` or `--debug` parameters. Log files are saved as `gmas_collection.log` by default.

**答:** 使用 `--verbose` 或 `--debug` 参数，日志文件默认保存为 `gmas_collection.log`。

## Contact | 联系方式

- **Author | 作者**: Kai Cao
- **Email | 邮箱**: caokai_cgs@163.com
- **Project | 项目**: [GMAS_Scripts/DailyDataCollection](https://github.com/Kai-FnLock/GMAS_Scripts)

---

**License | 许可证**: Full Copyright - All rights reserved | 保留所有权利

If this project helps you, please give it a star! | 如果这个项目对您有帮助，请给它一个星标！
