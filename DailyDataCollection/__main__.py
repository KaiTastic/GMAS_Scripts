#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GMAS 数据收集系统 - 统一模块化入口
==================================

**完全模块化的主入口文件，支持多种运行模式和命令行参数**

本模块是 GMAS 数据收集系统的主入口点，
采用现代化的核心模块架构，移除所有向后兼容层。

主要功能：
---------
* 数据收集模式：收集指定日期的地质数据
* 文件监控模式：实时监控微信文件夹中的新增文件
* 报告生成：支持 KMZ、Excel、统计报告等多种格式
* 周报生成：在指定工作日自动生成周报告

运行模式：
---------
1. **数据收集模式**：
   - 基本用法：``python __main__.py --date 20250830``
   - 使用今天日期：``python __main__.py``

2. **文件监控模式**：
   - 基本监控：``python __main__.py --monitor``
   - 指定结束时间：``python __main__.py --monitor --endtime 183000``

3. **配置和调试**：
   - 详细输出：``python __main__.py --verbose --date 20250830``
   - 自定义配置：``python __main__.py --config custom_config.yaml``

支持的格式：
----------
- **日期格式**：YYYYMMDD, YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD
- **时间格式**：HHMMSS, HH:MM:SS, HH-MM-SS

.. note::
   本系统要求 Python 3.7+ 并依赖多个外部模块。
   详细的依赖和配置信息请参考项目文档。

.. warning::
   运行前请确保配置文件 ``config/settings.yaml`` 已正确配置，
   特别是工作空间路径和微信文件夹路径。

:author: GMAS Development Team
:version: 参见 __init__.py 中的版本定义
:license: 项目许可证
:repository: https://github.com/Kai-FnLock/GMAS_Scripts
"""

import sys
import os
import logging
import argparse
import cProfile
import pstats
from datetime import datetime, timedelta
from pathlib import Path

# ============================================================================
# 项目内部导入
# ============================================================================
"""
模块导入部分
===========

本节负责导入项目所需的所有内部模块，包括：

- **版本信息模块**：获取应用程序版本和标题
- **配置系统模块**：管理系统配置和设置
- **核心功能模块**：数据处理、监控、报告生成等
- **显示模块**：用户界面和报告显示

.. note::
   导入顺序很重要，首先添加项目根目录到 Python 路径，
   然后按依赖关系顺序导入各个模块。
"""
# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入版本信息 - 处理可能的导入失败
from __init__ import __version__, APP_FULL_VERSION, SYSTEM_TITLE

# 导入配置系统
from config import ConfigManager

# 导入核心模块
from core.mapsheet import CurrentDateFiles
from core.data_models import DateType
from core.reports import DataSubmition
from core.monitor import MonitorManager
from display import ReportDisplay

# ============================================================================
# 全局配置和初始化
# ============================================================================
"""
全局配置和系统初始化
==================

本节负责系统的全局配置和初始化工作：

1. **编码配置**：
   - 设置标准输出和错误输出为 UTF-8 编码
   - 配置环境变量以确保中文字符正确显示

2. **日志系统配置**：
   - 设置日志级别为 INFO
   - 配置文件和控制台双重输出
   - 使用 UTF-8 编码写入日志文件

3. **配置管理器初始化**：
   - 加载系统配置文件
   - 初始化全局配置对象

.. important::
   这些全局设置对整个应用程序的正常运行至关重要，
   修改时需要谨慎考虑对系统其他部分的影响。
"""

# 增强输出编码支持，确保中文字符正确显示
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gmas_collection.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 初始化配置管理器
config_manager = ConfigManager()
config = config_manager.get_config()


# ============================================================================
# 辅助函数和验证器
# ============================================================================
"""
输入验证和辅助函数
================

本节包含用于验证用户输入和提供辅助功能的函数。

主要功能：
---------
- **日期验证**：验证日期格式、范围和业务逻辑合理性
- **时间验证**：验证时间格式和合理性
- **错误处理**：提供详细的错误信息和建议

验证规则：
---------
- 日期必须为 YYYYMMDD 格式（支持分隔符自动清理）
- 日期范围：2020年1月1日至当前日期后30天
- 时间必须为 HHMMSS 格式（支持分隔符自动清理）
- 提供业务逻辑警告（如非工作时间、历史数据等）
"""

def validate_date(date_str):
    """
    增强版日期验证函数
    
    验证日期字符串的格式、范围和业务逻辑合理性。
    
    该函数执行多层次验证：
    
    1. **格式验证**：
       - 检查输入是否为空
       - 移除常见分隔符（-, /, .）
       - 验证长度为8位数字
    
    2. **范围验证**：
       - 最早日期：2020年1月1日（GMAS项目开始）
       - 最晚日期：当前日期后30天
       - 年份范围：2023年至次年
    
    3. **业务逻辑验证**：
       - 对未来日期发出警告
       - 对超过90天的历史数据发出警告
    
    :param date_str: 输入的日期字符串，支持YYYYMMDD格式
    :type date_str: str
    
    :return: 转换后的DateType对象
    :rtype: DateType
    
    :raises ValueError: 如果日期格式、范围或业务逻辑不正确
    
    :example:
        >>> validate_date("20250830")
        DateType(date_datetime=datetime(2025, 8, 30))
        >>> validate_date("2025-08-30")
        DateType(date_datetime=datetime(2025, 8, 30))
        >>> validate_date("invalid")
        ValueError: 日期字符串只能包含数字, 输入值: invalid
    
    .. note::
       支持的输入格式包括：YYYYMMDD, YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD
    
    .. warning::
       对于未来日期和历史数据会发出警告，但不会阻止执行
    """
    # 输入预处理 - 移除常见的分隔符和空格
    if date_str:
        date_str = date_str.strip().replace('-', '').replace('/', '').replace('.', '')
    
    # 基础格式验证
    if not date_str:
        raise ValueError("日期字符串不能为空")
    
    if not date_str.isdigit():
        raise ValueError(f"日期字符串只能包含数字, 输入值: {date_str}")
    
    if len(date_str) != 8:
        raise ValueError(f"日期长度不正确, 请确保长度为8位 (YYYYMMDD), 输入值: {date_str}")
    
    # 尝试解析日期
    try:
        date_datetime = datetime.strptime(date_str, "%Y%m%d")
    except ValueError as e:
        raise ValueError(f"日期格式不正确, 请确保格式为'YYYYMMDD', 输入值: {date_str}, 错误详情: {str(e)}")
    
    # 日期范围验证
    current_date = datetime.now()
    min_date = datetime(2020, 1, 1)  # GMAS项目最早开始日期
    max_date = current_date + timedelta(days=30)  # 允许未来30天
    
    if date_datetime < min_date:
        raise ValueError(f"日期过早, 不能早于{min_date.strftime('%Y-%m-%d')}, 输入值: {date_str}")
    
    if date_datetime > max_date:
        raise ValueError(f"日期过晚, 不能晚于{max_date.strftime('%Y-%m-%d')}, 输入值: {date_str}")
    
    # 业务逻辑验证
    year = date_datetime.year
    if year < 2023 or year > current_date.year + 1:
        raise ValueError(f"年份不在有效范围内 (2023-{current_date.year + 1}), 输入值: {date_str}")

    # 警告信息（不阻止执行）
    if date_datetime > current_date:
        logger.warning(f"注意: 指定的日期 {date_str} 是未来日期")
    
    days_ago = (current_date - date_datetime).days
    if days_ago > 90:
        logger.warning(f"注意: 指定的日期 {date_str} 距今已超过90天，可能没有相关数据")
    
    return DateType(date_datetime=date_datetime)


def validate_time(time_str, time_format="%H%M%S"):
    """
    增强版时间验证函数
    
    验证时间字符串的格式和合理性。
    
    该函数执行以下验证步骤：
    
    1. **格式验证**：
       - 检查输入是否为空
       - 移除常见分隔符（:, -, 空格）
       - 验证长度为6位数字（HHMMSS）
    
    2. **时间解析**：
       - 使用指定格式解析时间
       - 验证小时、分钟、秒的有效性
    
    3. **业务逻辑检查**：
       - 检查是否在合理的工作时间范围内（6:00-23:00）
       - 对非常规时间发出警告
    
    :param time_str: 输入的时间字符串，支持HHMMSS格式
    :type time_str: str
    :param time_format: 时间格式，默认为 '%H%M%S'
    :type time_format: str
    
    :return: 转换后的时间对象
    :rtype: datetime.time
    
    :raises ValueError: 如果时间格式不正确或不合理
    
    :example:
        >>> validate_time("183000")
        datetime.time(18, 30, 0)
        >>> validate_time("18:30:00")
        datetime.time(18, 30, 0)
        >>> validate_time("invalid")
        ValueError: 时间字符串只能包含数字, 输入值: invalid
    
    .. note::
       支持的输入格式包括：HHMMSS, HH:MM:SS, HH-MM-SS
    
    .. warning::
       对于非常规工作时间（早于6点或晚于23点）会发出警告
    """
    # 输入预处理 - 移除常见的分隔符和空格
    if time_str:
        time_str = time_str.strip().replace(':', '').replace('-', '').replace(' ', '')
    
    # 基础格式验证
    if not time_str:
        raise ValueError("时间字符串不能为空")
    
    if not time_str.isdigit():
        raise ValueError(f"时间字符串只能包含数字, 输入值: {time_str}")
    
    expected_length = 6  # HHMMSS 格式应该是6位
    if len(time_str) != expected_length:
        raise ValueError(f"时间长度不正确, 请确保长度为{expected_length}位 (HHMMSS), 输入值: {time_str}")
    
    # 尝试解析时间
    try:
        time_obj = datetime.strptime(time_str, time_format).time()
    except ValueError as e:
        raise ValueError(f"时间格式不正确, 请确保格式为'HHMMSS', 输入值: {time_str}, 错误详情: {str(e)}")
    
    # 时间合理性验证
    hour = time_obj.hour
    minute = time_obj.minute
    second = time_obj.second
    
    # 检查业务逻辑合理性（工作时间范围）
    if hour < 6 or hour > 23:
        logger.warning(f"注意: 指定的时间 {time_str} 在非常规工作时间范围内")
    
    # 检查分钟和秒是否合理
    if minute > 59 or second > 59:
        raise ValueError(f"时间值不合理, 分钟和秒不能超过59, 输入值: {time_str}")
    
    return time_obj


# ============================================================================
# 命令行参数解析
# ============================================================================
"""
命令行参数解析器
==============

本节实现了功能丰富的命令行参数解析系统，支持多种运行模式和配置选项。

参数分组：
---------
1. **主要功能参数组**：
   - ``--date``：指定收集数据的日期
   - ``--monitor``：启动文件监控模式
   - ``--endtime``：监控结束时间

2. **配置选项参数组**：
   - ``--config``：自定义配置文件路径
   - ``--workspace``：工作空间路径
   - ``--wechat-folder``：微信文件夹路径

3. **监控配置参数组**：
   - ``--no-fuzzy-match``：禁用模糊匹配
   - ``--fuzzy-threshold``：模糊匹配阈值
   - ``--check-interval``：文件检查间隔

4. **输出控制参数组**：
   - ``--verbose/-v``：详细输出模式
   - ``--quiet/-q``：静默模式
   - ``--log-level``：日志级别设置

5. **报告生成参数组**：
   - ``--no-kmz``：跳过KMZ报告生成
   - ``--no-excel``：跳过Excel报告生成
   - ``--no-statistics``：跳过统计报告生成

6. **调试选项参数组**：
   - ``--dry-run``：模拟运行模式
   - ``--debug``：调试模式
   - ``--profile``：性能分析模式

参数验证：
---------
- 冲突参数检查（如 ``--verbose`` 和 ``--quiet`` 不能同时使用）
- 依赖参数验证（如 ``--endtime`` 只能在 ``--monitor`` 模式下使用）
- 数据类型和范围验证（如模糊匹配阈值必须在0.0-1.0之间）

.. seealso::
   详细的使用示例请参考函数内的 epilog 部分
"""

def parse_args():
    """增强版命令行参数解析器
    
    创建并配置功能完整的命令行参数解析器，支持所有系统功能。
    
    该函数实现以下功能：
    
    1. **参数定义**：
       - 定义所有命令行参数及其属性
       - 设置参数分组以提高可读性
       - 配置帮助信息和使用示例
    
    2. **参数验证**：
       - 检查参数冲突（如 --verbose 和 --quiet）
       - 验证参数依赖关系
       - 验证参数值的合理性
    
    3. **参数后处理**：
       - 标准化参数格式
       - 设置默认值和派生值
       - 调用相应的验证函数
    
    :return: 解析后的命令行参数对象
    :rtype: argparse.Namespace
    
    :raises SystemExit: 当参数解析失败或用户请求帮助时
    
    .. note::
       该函数包含详细的使用示例和参数说明，
       可通过 ``python __main__.py --help`` 查看完整帮助信息。
    
    .. warning::
       参数验证失败时会调用 parser.error() 并终止程序执行。
    """
    parser = argparse.ArgumentParser(
        description=APP_FULL_VERSION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
                使用示例:
                基本数据收集:
                    python __main__.py --date 20250830
                    python __main__.py --date=2025-08-30
                    python __main__.py                          # 使用今天日期
                    
                文件监控模式:
                    python __main__.py --monitor
                    python __main__.py --monitor --endtime 183000
                    python __main__.py --monitor --date 20250830 --endtime 18:30:00
                    
                配置和调试:
                    python __main__.py --verbose --date 20250830
                    python __main__.py --config custom_config.yaml
                    python __main__.py --version
                    python __main__.py --help

                支持的日期格式: YYYYMMDD, YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD
                支持的时间格式: HHMMSS, HH:MM:SS, HH-MM-SS

                项目信息: https://github.com/Kai-FnLock/GMAS_Scripts
                """
            )

    # 版本信息
    parser.add_argument(
        '--version', 
        action='version', 
        version=APP_FULL_VERSION
    )
    
    # ========== 主要功能参数组 ==========
    main_group = parser.add_argument_group('主要功能', '控制程序运行模式的核心参数')
    
    main_group.add_argument(
        "--date",
        metavar="DATE",
        default=datetime.now().strftime("%Y%m%d"),
        help="收集数据的目标日期。支持多种格式: YYYYMMDD, YYYY-MM-DD, YYYY/MM/DD 等 (默认: 今天)"
    )
    
    main_group.add_argument(
        "--monitor",
        action='store_true',
        help="启动文件监控模式，实时监控微信文件夹中的新增文件"
    )
    
    main_group.add_argument(
        "--endtime",
        metavar="TIME", 
        help="监控模式下的停止时间。支持格式: HHMMSS, HH:MM:SS 等 (默认: 配置文件中的设置)"
    )
    
    # ========== 配置参数组 ==========
    config_group = parser.add_argument_group('配置选项', '系统配置和自定义设置')
    
    config_group.add_argument(
        "--config",
        metavar="FILE",
        help="指定自定义配置文件路径 (默认: config/settings.yaml)"
    )
    
    config_group.add_argument(
        "--workspace",
        metavar="PATH",
        help="指定工作空间路径，覆盖配置文件中的设置"
    )
    
    config_group.add_argument(
        "--wechat-folder",
        metavar="PATH",
        help="指定微信文件夹路径，覆盖配置文件中的设置"
    )
    
    # ========== 监控配置参数组 ==========
    monitor_group = parser.add_argument_group('监控配置', '文件监控模式的详细设置')
    
    monitor_group.add_argument(
        "--no-fuzzy-match",
        action='store_true',
        help="禁用模糊匹配，只使用精确文件名匹配"
    )
    
    monitor_group.add_argument(
        "--fuzzy-threshold",
        type=float,
        metavar="THRESHOLD",
        help="模糊匹配阈值 (0.0-1.0)，数值越高匹配越严格 (默认: 0.65)"
    )
    
    monitor_group.add_argument(
        "--check-interval",
        type=int,
        metavar="SECONDS",
        help="文件检查间隔时间（秒） (默认: 10)"
    )
    
    # ========== 输出控制参数组 ==========
    output_group = parser.add_argument_group('输出控制', '控制程序输出和日志的参数')
    
    output_group.add_argument(
        "--verbose", "-v",
        action='store_true',
        help="启用详细输出模式，显示更多调试信息"
    )
    
    output_group.add_argument(
        "--quiet", "-q",
        action='store_true',
        help="静默模式，减少输出信息"
    )
    
    output_group.add_argument(
        "--log-level",
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        metavar="LEVEL",
        help="设置日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
    
    output_group.add_argument(
        "--log-file",
        metavar="FILE",
        help="指定日志文件路径 (默认: gmas_collection.log)"
    )
    
    # ========== 报告生成参数组 ==========
    report_group = parser.add_argument_group('报告生成', '控制报告生成的参数')
    
    report_group.add_argument(
        "--no-kmz",
        action='store_true',
        help="跳过KMZ报告生成"
    )
    
    report_group.add_argument(
        "--no-excel",
        action='store_true',
        help="跳过Excel报告生成"
    )
    
    report_group.add_argument(
        "--no-statistics",
        action='store_true',
        help="跳过统计报告生成"
    )
    
    report_group.add_argument(
        "--statistics-file",
        metavar="FILE",
        help="指定统计报告输出文件路径，覆盖配置文件设置"
    )
    
    report_group.add_argument(
        "--force-weekly",
        action='store_true',
        help="强制生成周报告，忽略日期检查"
    )
    
    # ========== 调试和测试参数组 ==========
    debug_group = parser.add_argument_group('调试选项', '开发和测试用的参数')
    
    debug_group.add_argument(
        "--dry-run",
        action='store_true',
        help="模拟运行模式，不实际生成文件或修改数据"
    )
    
    debug_group.add_argument(
        "--debug",
        action='store_true',
        help="启用调试模式，输出详细的调试信息"
    )
    
    debug_group.add_argument(
        "--profile",
        action='store_true',
        help="启用性能分析模式"
    )
    
    # 解析参数
    args = parser.parse_args()
    
    # ========== 参数验证和后处理 ==========
    
    # 冲突参数检查
    if args.verbose and args.quiet:
        parser.error("--verbose 和 --quiet 不能同时使用")
    
    # 监控模式参数验证
    if args.endtime and not args.monitor:
        parser.error("--endtime 只能在监控模式 (--monitor) 下使用")
    
    if args.no_fuzzy_match and not args.monitor:
        parser.error("--no-fuzzy-match 只能在监控模式 (--monitor) 下使用")
    
    if args.fuzzy_threshold is not None:
        if not args.monitor:
            parser.error("--fuzzy-threshold 只能在监控模式 (--monitor) 下使用")
        if not (0.0 <= args.fuzzy_threshold <= 1.0):
            parser.error("--fuzzy-threshold 必须在 0.0 到 1.0 之间")
    
    # 日志级别设置
    if args.debug:
        args.log_level = 'DEBUG'
    elif args.verbose:
        args.log_level = 'INFO'
    elif args.quiet:
        args.log_level = 'WARNING'
    
    # 参数预处理和标准化
    try:
        # 验证日期格式（使用我们增强的验证函数）
        if args.date != datetime.now().strftime("%Y%m%d"):  # 如果不是默认值
            validate_date(args.date)  # 仅验证，不转换
        
        # 验证时间格式
        if args.endtime:
            validate_time(args.endtime)  # 仅验证，不转换
            
    except ValueError as e:
        parser.error(f"参数验证失败: {e}")
    
    return args


# ============================================================================
# 核心功能类
# ============================================================================
"""
核心功能类定义
============

本节定义了系统的核心功能类，主要包括数据收集器。

类设计原则：
-----------
- **单一职责**：每个类专注于特定功能
- **可扩展性**：支持未来功能扩展
- **错误处理**：完善的异常处理机制
- **配置驱动**：行为可通过配置文件控制

主要类：
-------
- **DataCollector**：数据收集器，负责协调整个数据收集流程

.. note::
   这些类的设计遵循面向对象的设计原则，
   确保代码的可维护性和可扩展性。
"""

class DataCollector:
    """数据收集器 - 优化版的数据收集逻辑
    
    该类负责协调整个数据收集流程，包括数据收集、报告生成、错误处理等。
    
    主要功能：
    ---------
    1. **数据收集协调**：
       - 初始化数据收集对象
       - 协调各个收集步骤
       - 处理收集过程中的异常
    
    2. **报告生成管理**：
       - 根据配置生成不同类型的报告
       - 支持条件性报告生成（基于命令行参数）
       - 处理报告生成失败的情况
    
    3. **显示和反馈**：
       - 显示收集进度和结果
       - 显示错误信息和统计数据
       - 提供用户友好的反馈
    
    4. **周报告处理**：
       - 检查是否需要生成周报告
       - 在指定工作日自动生成周报告
    
    :param collection_date: 数据收集的目标日期
    :type collection_date: DateType
    :param args: 命令行参数对象，用于控制行为
    :type args: argparse.Namespace, optional
    
    :example:
        >>> from core.data_models import DateType
        >>> from datetime import datetime
        >>> date_obj = DateType(date_datetime=datetime(2025, 8, 30))
        >>> collector = DataCollector(date_obj)
        >>> success = collector()
        >>> print(f"收集{'成功' if success else '失败'}")
    
    .. note::
       该类设计为可调用对象，通过 __call__ 方法执行主要逻辑。
    
    .. warning::
       数据收集过程可能耗时较长，建议在适当的环境中运行。
    """
    
    def __init__(self, collection_date, args=None):
        """
        初始化数据采集类
        
        设置数据收集器的基本参数和配置。
        
        :param collection_date: DateType 对象, 包含日期信息
        :type collection_date: DateType
        :param args: 命令行参数对象（可选）
        :type args: argparse.Namespace, optional
        
        .. note::
           构造函数会缓存配置对象以提高性能，
           并保存命令行参数以便后续使用。
        """
        self.collection_date = collection_date
        self.config = config  # 缓存配置
        self.args = args  # 保存命令行参数

    def __call__(self):
        """执行数据收集
        
        主要的数据收集执行方法，协调整个收集流程。
        
        执行流程：
        --------
        1. **初始化收集对象**：
           - 创建 CurrentDateFiles 实例
           - 设置收集参数
        
        2. **显示收集信息**：
           - 显示报告头部信息
           - 显示统计数据
           - 显示错误信息摘要
        
        3. **生成报告**：
           - 根据配置生成各类报告
           - 处理报告生成异常
        
        4. **生成周报告**：
           - 检查是否为周报告生成日
           - 自动生成周报告
        
        :return: 数据收集是否成功
        :rtype: bool
        
        :raises Exception: 数据收集过程中的各种异常
        
        .. note::
           该方法使用 try-catch 结构确保异常被正确处理和记录。
        """
        try:
            collection = CurrentDateFiles(self.collection_date)
            
            # 显示收集报告头部
            ReportDisplay.show_header(self.collection_date)
            
            # 显示统计信息
            collection.onScreenDisplay()
            
            # 显示错误信息
            self._display_error_information(collection)
            
            # 生成报告
            success = self._generate_reports(collection)
            
            # 生成周报告（如果需要）
            self._generate_weekly_report_if_needed(collection)
            
            logger.info("数据收集完成")
            return success
            
        except Exception as e:
            logger.error(f"数据收集过程中发生错误: {e}")
            return False

    def _display_error_information(self, collection):
        """显示错误信息，按团队分组
        
        调用报告显示模块来展示错误信息摘要。
        
        :param collection: 数据收集对象，包含错误信息
        :type collection: CurrentDateFiles
        
        .. note::
           错误信息会按团队进行分组显示，便于用户快速定位问题。
        """
        ReportDisplay.show_error_summary(collection)

    def _generate_reports(self, collection):
        """生成KMZ和Excel报告
        
        根据命令行参数决定是否生成各种类型的报告。
        
        支持的报告类型：
        -------------
        1. **KMZ报告**：地理信息文件，用于GIS软件
        2. **Excel报告**：电子表格格式的统计报告
        3. **统计报告**：详细的数据统计信息
        
        :param collection: 数据收集对象
        :type collection: CurrentDateFiles
        
        :return: 报告生成是否全部成功
        :rtype: bool
        
        .. note::
           可以通过命令行参数 (--no-kmz, --no-excel, --no-statistics) 
           跳过特定类型的报告生成。
        
        .. warning::
           如果所有报告都被跳过，方法会发出警告但仍返回 True。
        """
        logger.info("生成每日报告...")
        
        # 根据命令行参数决定是否生成各种报告
        reports_success = []
        
        # KMZ报告生成
        if not (self.args and self.args.no_kmz):
            kmz_success = self._generate_kmz_report(collection)
            reports_success.append(kmz_success)
        else:
            logger.info("跳过KMZ报告生成（--no-kmz）")
        
        # Excel报告生成  
        if not (self.args and self.args.no_excel):
            excel_success = self._generate_excel_report(collection)
            reports_success.append(excel_success)
        else:
            logger.info("跳过Excel报告生成（--no-excel）")
        
        # 统计报告生成
        if not (self.args and self.args.no_statistics):
            statistics_success = self._generate_statistics_report(collection)
            reports_success.append(statistics_success)
        else:
            logger.info("跳过统计报告生成（--no-statistics）")

        # 只有在有报告要生成时才检查成功率
        if not reports_success:
            logger.warning("所有报告都被跳过了")
            return True  # 如果所有报告都被跳过，认为是成功的
        
        return all(reports_success)

    def _generate_kmz_report(self, collection):
        """生成KMZ报告
        
        生成用于GIS软件的KMZ格式地理信息文件。
        
        :param collection: 数据收集对象
        :type collection: CurrentDateFiles
        
        :return: KMZ报告生成是否成功
        :rtype: bool
        
        .. note::
           KMZ文件包含地理坐标和相关的地质数据，
           可以在Google Earth等GIS软件中查看。
        """
        try:
            if collection.dailyKMZReport():
                logger.info("每日KMZ文件生成成功")
                return True
            else:
                logger.error("每日KMZ文件生成失败")
                return False
        except Exception as e:
            logger.error(f"每日KMZ文件生成异常: {e}")
            return False

    def _generate_excel_report(self, collection):
        """生成Excel报告
        
        生成电子表格格式的数据统计报告。
        
        :param collection: 数据收集对象
        :type collection: CurrentDateFiles
        
        :return: Excel报告生成是否成功
        :rtype: bool
        
        .. note::
           Excel报告包含详细的数据统计信息，
           便于进一步的数据分析和处理。
        """
        try:
            if collection.dailyExcelReport():
                logger.info("每日Excel报告生成成功")
                return True
            else:
                logger.error("每日Excel报告生成失败")
                return False
        except Exception as e:
            logger.error(f"Excel报告生成异常: {e}")
            return False

    def _generate_statistics_report(self, collection):
        """生成统计报告
        
        生成详细的数据统计报告，包含完成度、质量指标等。
        
        :param collection: 数据收集对象
        :type collection: CurrentDateFiles
        
        :return: 统计报告生成是否成功
        :rtype: bool
        
        .. note::
           统计报告文件路径可以通过配置文件或命令行参数自定义。
           报告包含每日的数据完成情况和质量统计信息。
        """
        try:
            # 使用配置管理器获取统计报告文件路径
            context = {
                'date_obj': self.collection_date,
                'custom_path': getattr(self.args, 'statistics_file', None) if self.args else None
            }
            
            stats_file_path = config_manager.get_statistics_file_path(context)
            
            if collection.write_completed_data_to_statistics_excel(stats_file_path):
                logger.info(f"统计报告生成成功: {stats_file_path}")
                return True
            else:
                logger.error(f"统计报告生成失败: {stats_file_path}")
                return False
        except Exception as e:
            logger.error(f"统计报告生成异常: {e}")
            return False
    
    def _generate_weekly_report_if_needed(self, collection):
        """如果需要则生成周报告
        
        检查当前日期是否为周报告生成日，如果是则自动生成周报告。
        
        :param collection: 数据收集对象
        :type collection: CurrentDateFiles
        
        .. note::
           周报告生成日由配置文件中的 weekdays 设置决定，
           通常设置为周五或其他特定工作日。
        """
        if self._should_generate_weekly_report():
            weekday_name = self.collection_date.date_datetime.strftime("%A")
            print(f'\n今天是{weekday_name}, 需要生成周报\n')
            logger.info("今天是数据提交日，生成周报告...")
            
            try:
                submitter = DataSubmition(self.collection_date, collection.allPoints)
                if submitter.weeklyPointToShp():
                    logger.info("周报告生成成功")
                else:
                    logger.error("周报告生成失败")
            except Exception as e:
                logger.error(f"周报告生成异常: {e}")

    def _should_generate_weekly_report(self):
        """检查是否需要生成周报告
        
        根据当前日期的星期几来判断是否需要生成周报告。
        
        :return: 是否需要生成周报告
        :rtype: bool
        
        .. note::
           判断依据是当前日期的 weekday() 值是否在配置的 weekdays 列表中。
           weekday() 返回 0-6，分别表示周一到周日。
        """
        return self.collection_date.date_datetime.weekday() in self.config['data_collection']['weekdays']


# ============================================================================
# 主要功能函数
# ============================================================================
"""
主要功能函数定义
==============

本节包含系统的两个主要功能函数：

1. **collect_data**：数据收集模式
2. **start_monitoring**：文件监控模式

这些函数是连接命令行接口和核心业务逻辑的桥梁。

设计原则：
---------
- **异常安全**：完善的异常处理机制
- **日志记录**：详细的操作日志
- **状态返回**：明确的成功/失败状态码
- **参数验证**：输入参数的严格验证

.. note::
   这些函数直接被主入口函数调用，
   是系统对外提供服务的主要接口。
"""

def collect_data(date_str: str = None, args=None):
    """正常数据收集模式
    
    执行指定日期的数据收集任务。
    
    该函数是数据收集模式的主入口，负责：
    
    1. **参数处理**：
       - 验证和处理输入的日期字符串
       - 如果未提供日期，使用当前日期
    
    2. **数据收集执行**：
       - 创建数据收集器实例
       - 执行完整的数据收集流程
    
    3. **异常处理**：
       - 捕获并记录各种异常
       - 提供用户友好的错误信息
    
    :param date_str: 目标日期字符串，支持多种格式
    :type date_str: str, optional
    :param args: 命令行参数对象，控制收集行为
    :type args: argparse.Namespace, optional
    
    :return: 执行状态码，0表示成功，1表示失败
    :rtype: int
    
    :example:
        >>> # 收集今天的数据
        >>> result = collect_data()
        >>> # 收集指定日期的数据
        >>> result = collect_data("20250830")
        >>> # 带参数的数据收集
        >>> result = collect_data("20250830", args)
    
    .. note::
       如果不提供日期参数，函数会自动使用当前系统日期。
    
    .. warning::
       数据收集过程可能耗时较长，请确保系统资源充足。
    """
    try:
        if date_str:
            current_date = validate_date(date_str)
        else:
            current_date = DateType(date_datetime=datetime.now())
            
        logger.info(f"开始数据收集 - 日期: {current_date.yyyymmdd_str}")
        
        collector = DataCollector(current_date, args)
        success = collector()
        
        return 0 if success else 1
        
    except ValueError as ve:
        logger.error(f"日期验证失败: {ve}")
        print(f"日期验证失败: {ve}")
        return 1
    except Exception as e:
        logger.error(f"数据收集失败: {e}")
        print(f"数据收集失败: {e}")
        return 1


def start_monitoring(date_str: str = None, endtime_str: str = None, args=None):
    """启动文件监控服务
    
    启动实时文件监控服务，监控微信文件夹中的新增文件。
    
    该函数实现以下功能：
    
    1. **监控初始化**：
       - 处理监控日期和结束时间
       - 配置监控参数（模糊匹配、阈值等）
       - 创建监控管理器实例
    
    2. **监控执行**：
       - 实时监控文件系统变化
       - 自动识别和处理相关文件
       - 支持用户手动中断（Ctrl+C）
    
    3. **后处理**：
       - 监控结束后自动执行数据收集
       - 生成完整的数据报告
    
    :param date_str: 监控日期字符串，默认为今天
    :type date_str: str, optional
    :param endtime_str: 监控结束时间字符串，格式为HHMMSS
    :type endtime_str: str, optional
    :param args: 命令行参数对象，控制监控行为
    :type args: argparse.Namespace, optional
    
    :return: 监控服务执行是否成功
    :rtype: bool
    
    :example:
        >>> # 启动基本监控（使用配置文件中的结束时间）
        >>> success = start_monitoring()
        >>> # 监控指定日期到指定时间
        >>> success = start_monitoring("20250830", "183000")
    
    .. note::
       监控服务会在达到指定结束时间或用户手动中断时停止。
       停止后会自动执行数据收集任务。
    
    .. warning::
       监控服务是长期运行的进程，请确保系统稳定性。
       建议在服务器或稳定的工作环境中运行。
    """
    try:
        if date_str:
            current_date = validate_date(date_str)
        else:
            current_date = DateType(date_datetime=datetime.now())
            
        logger.info(f"启动文件监控服务 - 监控日期: {current_date.yyyymmdd_str}")
        
        # 处理结束时间
        if endtime_str:
            try:
                endtime = validate_time(endtime_str)
                end_datetime = datetime.combine(current_date.date_datetime.date(), endtime)
            except ValueError as ve:
                logger.error(f"时间格式错误: {ve}")
                print(f"时间格式错误: {ve}")
                return False
        else:
            end_datetime = config_manager.get_monitor_endtime()
        
        # 创建监控管理器
        monitor_manager = MonitorManager(
            current_date=current_date,
            enable_fuzzy_matching=config['monitoring']['enable_fuzzy_matching'],
            fuzzy_threshold=config['monitoring']['fuzzy_threshold']
        )
        
        # 显示模糊匹配配置
        print("启动监控系统...")
        if config['monitoring']['enable_fuzzy_matching']:
            print(f"模糊匹配已启用 (阈值: {config['monitoring']['fuzzy_threshold']})")
        else:
            print("使用精确匹配模式")
        
        print(f"监控日期: {current_date.yyyymmdd_str}")
        print(f"预计结束时间: {end_datetime.strftime('%H:%M:%S')}")
        print("按 Ctrl+C 可以手动停止监控\n")
        
        # 定义完成后的处理函数
        def post_processing():
            logger.info("文件监控完成，开始执行数据收集...")
            try:
                collector = DataCollector(current_date, args)
                collector()
                logger.info("数据收集任务完成")
            except Exception as e:
                logger.error(f"数据收集任务执行出错: {e}")
        
        # 启动监控
        monitor_manager.start_monitoring(
            executor=post_processing,
            end_time=end_datetime
        )
        
        logger.info("文件监控服务已结束")
        return True
        
    except ValueError as ve:
        logger.error(f"日期验证失败: {ve}")
        print(f"日期验证失败: {ve}")
        return False
    except Exception as e:
        logger.error(f"监控服务启动失败: {e}")
        print(f"监控服务启动失败: {e}")
        return False


# ============================================================================
# 主入口函数
# ============================================================================
"""
应用程序主入口
============

本节包含应用程序的主入口函数和相关的辅助设置函数。

主要组件：
---------
1. **main()**：应用程序主入口函数
2. **setup_logging()**：日志系统配置函数
3. **setup_config()**：配置系统设置函数
4. **display_system_info()**：系统信息显示函数
5. **execute_*_mode()**：各种运行模式执行函数

执行流程：
---------
1. 解析命令行参数
2. 配置日志和系统设置
3. 显示系统信息
4. 根据参数选择并执行相应模式
5. 处理性能分析（如果启用）
6. 返回执行状态码

.. note::
   主入口函数采用分层设计，每个步骤都有专门的函数处理，
   确保代码的可读性和可维护性。
"""

def main():
    """增强版主入口函数
    
    应用程序的主入口点，协调整个程序的执行流程。
    
    该函数实现以下核心功能：
    
    1. **参数处理**：
       - 解析命令行参数
       - 验证参数有效性
       - 设置运行模式
    
    2. **系统初始化**：
       - 配置日志系统
       - 加载和调整配置
       - 初始化调试模式
    
    3. **执行控制**：
       - 根据参数选择运行模式
       - 处理用户中断
       - 管理性能分析
    
    4. **状态管理**：
       - 记录执行状态
       - 处理异常情况
       - 返回适当的退出码
    
    :return: 程序退出状态码，0表示成功，1表示失败
    :rtype: int
    
    :raises KeyboardInterrupt: 用户中断程序执行
    :raises Exception: 程序执行过程中的各种异常
    
    .. note::
       该函数使用结构化的异常处理，确保所有错误都被正确捕获和记录。
    
    .. warning::
       程序可能会运行很长时间，特别是在监控模式下。
       请确保系统资源充足并保持稳定。
    """
    try:
        args = parse_args()
        
        # ========== 日志配置 ==========
        setup_logging(args)
        
        # ========== 配置管理 ==========
        setup_config(args)
        
        # ========== 调试模式处理 ==========
        if args.debug:
            logger.debug("调试模式已启用")
            logger.debug(f"解析的参数: {vars(args)}")
        
        if args.dry_run:
            print("模拟运行模式 - 不会实际修改文件或数据")
            logger.info("运行在模拟模式下")
        
        # ========== 性能分析 ==========
        if args.profile:
            profiler = cProfile.Profile()
            profiler.enable()
        
        # ========== 显示系统信息 ==========
        display_system_info(args)
        
        # ========== 模式选择和执行 ==========
        if args.monitor:
            success = execute_monitor_mode(args)
        else:
            success = execute_collection_mode(args)
        
        # ========== 性能分析结果 ==========
        if args.profile:
            profiler.disable()
            stats = pstats.Stats(profiler)
            stats.sort_stats('cumulative')
            stats.print_stats(20)  # 显示前20个最耗时的函数
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("用户中断程序执行")
        if not args.quiet:
            print("\n程序被用户中断")
        return 1
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        if not args.quiet:
            print(f"程序执行失败: {e}")
        return 1


def setup_logging(args):
    """根据参数设置日志配置
    
    根据命令行参数动态配置日志系统。
    
    该函数执行以下配置：
    
    1. **日志级别设置**：
       - 根据 --log-level 参数设置日志级别
       - 支持 DEBUG, INFO, WARNING, ERROR, CRITICAL 级别
    
    2. **日志文件配置**：
       - 根据 --log-file 参数设置日志文件路径
       - 默认使用 'gmas_collection.log'
    
    3. **处理器管理**：
       - 重新配置日志处理器
       - 支持控制台和文件双重输出
       - 在静默模式下禁用文件日志
    
    :param args: 命令行参数对象
    :type args: argparse.Namespace
    
    .. note::
       该函数会修改全局的 logger 对象，
       影响整个应用程序的日志输出行为。
    
    .. warning::
       在静默模式下 (--quiet)，文件日志会被禁用，
       请确保这符合您的需求。
    """
    global logger
    
    # 重新配置日志级别
    if args.log_level:
        logging.getLogger().setLevel(getattr(logging, args.log_level))
        logger.setLevel(getattr(logging, args.log_level))
    
    # 配置日志文件
    log_file = args.log_file if args.log_file else 'gmas_collection.log'
    
    # 如果需要，重新配置日志处理器
    if args.log_level or args.log_file:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        handlers = [logging.StreamHandler()]
        if not args.quiet:
            handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
        
        logging.basicConfig(
            level=getattr(logging, args.log_level) if args.log_level else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=handlers,
            force=True
        )
        logger = logging.getLogger(__name__)


def setup_config(args):
    """根据参数设置配置
    
    根据命令行参数动态调整系统配置。
    
    该函数执行以下配置调整：
    
    1. **配置文件管理**：
       - 如果指定了自定义配置文件，重新加载配置
       - 记录配置文件使用情况
    
    2. **路径配置覆盖**：
       - 工作空间路径 (--workspace)
       - 微信文件夹路径 (--wechat-folder)
    
    3. **监控配置调整**：
       - 模糊匹配开关 (--no-fuzzy-match)
       - 模糊匹配阈值 (--fuzzy-threshold)
       - 检查间隔时间 (--check-interval)
    
    4. **报告配置设置**：
       - 统计报告文件路径 (--statistics-file)
    
    :param args: 命令行参数对象
    :type args: argparse.Namespace
    
    .. note::
       命令行参数的优先级高于配置文件设置，
       会覆盖配置文件中的相应值。
    
    .. warning::
       配置更改会影响全局 config 对象，
       请确保更改的配置符合系统要求。
    """
    global config_manager, config
    
    # 重新初始化配置管理器（如果指定了自定义配置文件）
    if args.config:
        config_manager = ConfigManager(config_file=args.config)
        config = config_manager.get_config()
        logger.info(f"使用自定义配置文件: {args.config}")
    
    # 覆盖配置文件中的设置
    if args.workspace:
        config['system']['workspace'] = args.workspace
        config['paths']['workspace'] = args.workspace
        logger.info(f"工作空间路径已覆盖: {args.workspace}")
    
    if args.wechat_folder:
        config['paths']['wechat_folder'] = args.wechat_folder
        logger.info(f"微信文件夹路径已覆盖: {args.wechat_folder}")
    
    # 监控相关配置覆盖
    if args.no_fuzzy_match:
        config['monitoring']['enable_fuzzy_matching'] = False
        logger.info("模糊匹配已禁用")
    
    if args.fuzzy_threshold is not None:
        config['monitoring']['fuzzy_threshold'] = args.fuzzy_threshold
        logger.info(f"模糊匹配阈值已设置为: {args.fuzzy_threshold}")
    
    if args.check_interval:
        config['monitoring']['time_interval_seconds'] = args.check_interval
        logger.info(f"检查间隔已设置为: {args.check_interval}秒")
    
    # 报告生成相关配置覆盖
    if args.statistics_file:
        # 确保 reports 配置节存在
        if 'reports' not in config:
            config['reports'] = {}
        if 'statistics' not in config['reports']:
            config['reports']['statistics'] = {}
        
        config['reports']['statistics']['daily_details_file'] = args.statistics_file
        logger.info(f"统计报告文件路径已覆盖: {args.statistics_file}")


def display_system_info(args):
    """显示系统信息
    
    根据用户设置显示相关的系统信息和运行参数。
    
    显示的信息包括：
    
    1. **基本信息**：
       - 系统标题和版本
       - 设定的目标日期
       - 当前系统时间
    
    2. **详细信息**（在详细模式下）：
       - 工作空间路径
       - 微信文件夹路径
       - 监控模式配置（如果启用监控）
    
    :param args: 命令行参数对象
    :type args: argparse.Namespace
    
    .. note::
       在静默模式下 (--quiet)，不会显示任何信息。
       在详细模式下 (--verbose, --debug)，会显示更多配置信息。
    """
    if not args.quiet:
        print(f"\n{'='*60}")
        print(SYSTEM_TITLE)
        print(f"{'='*60}")
        print(f"设定日期: {args.date}")
        print(f"当前系统时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if args.verbose or args.debug:
            print(f"工作空间: {config['paths']['workspace']}")
            print(f"微信文件夹: {config['paths']['wechat_folder']}")
            if args.monitor:
                print(f"模糊匹配: {'启用' if config['monitoring']['enable_fuzzy_matching'] else '禁用'}")
                if config['monitoring']['enable_fuzzy_matching']:
                    print(f"匹配阈值: {config['monitoring']['fuzzy_threshold']}")


def execute_monitor_mode(args):
    """执行监控模式
    
    启动文件监控模式并显示相关配置信息。
    
    该函数负责：
    
    1. **信息显示**：
       - 显示运行模式为文件监控
       - 显示监控停止时间（如果指定）
       - 显示匹配模式配置
    
    2. **监控启动**：
       - 调用 start_monitoring 函数
       - 传递相应的参数
    
    :param args: 命令行参数对象
    :type args: argparse.Namespace
    
    :return: 监控执行是否成功
    :rtype: bool
    
    .. note::
       该函数主要负责用户界面显示和参数传递，
       实际的监控逻辑在 start_monitoring 函数中实现。
    """
    if not args.quiet:
        print(f"\n运行模式: 文件监控")
        if args.endtime:
            print(f"监控停止时间: {args.endtime}")
        if args.no_fuzzy_match:
            print(f"匹配模式: 精确匹配")
        else:
            print(f"匹配模式: 模糊匹配 (阈值: {config['monitoring']['fuzzy_threshold']})")
    
    return start_monitoring(args.date, args.endtime)


def execute_collection_mode(args):
    """执行数据收集模式
    
    启动数据收集模式并显示相关配置信息。
    
    该函数负责：
    
    1. **信息显示**：
       - 显示运行模式为数据收集
       - 显示跳过的报告类型（如果有）
       - 显示特殊设置（如强制周报告）
    
    2. **收集启动**：
       - 调用 collect_data 函数
       - 传递相应的参数
    
    :param args: 命令行参数对象
    :type args: argparse.Namespace
    
    :return: 数据收集执行是否成功
    :rtype: bool
    
    .. note::
       该函数主要负责用户界面显示和参数传递，
       实际的数据收集逻辑在 collect_data 函数中实现。
    """
    if not args.quiet:
        print(f"\n运行模式: 数据收集")
        
        # 显示报告生成设置
        skip_options = []
        if args.no_kmz:
            skip_options.append("KMZ报告")
        if args.no_excel:
            skip_options.append("Excel报告")
        
        if skip_options:
            print(f" 跳过生成: {', '.join(skip_options)}")
        
        if args.force_weekly:
            print(f" 强制生成周报告")
    
    return collect_data(args.date, args)


if __name__ == "__main__":
    """
    程序入口点
    =========
    
    当该模块作为主程序运行时的入口点。
    
    执行流程：
    --------
    1. 调用 main() 函数执行主要逻辑
    2. 获取退出状态码
    3. 通过 sys.exit() 设置进程退出状态
    
    退出状态码：
    ----------
    - **0**：程序执行成功
    - **1**：程序执行失败或被用户中断
    
    .. note::
       这是 Python 模块的标准入口点模式，
       确保模块既可以被导入，也可以直接执行。
    
    .. seealso::
       更多使用方法请参考文档开头的详细说明
    """
    exit_code = main()
    sys.exit(exit_code)
