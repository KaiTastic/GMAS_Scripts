#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GMAS 数据收集系统 - 统一模块化入口

完全模块化的主入口文件，支持多种运行模式和命令行参数
采用现代化的核心模块架构，移除所有向后兼容层
"""

import sys
import os
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入版本信息
try:
    from __init__ import __version__, APP_FULL_VERSION, SYSTEM_TITLE
except ImportError:
    # 如果作为脚本直接运行，使用本地版本定义
    __version__ = "2.3.1"
    APP_FULL_VERSION = f"GMAS 数据自动收集与处理工具 {__version__}"
    SYSTEM_TITLE = f"GMAS 数据收集系统 v{__version__}"

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

# 导入新的配置系统和模块
from config import ConfigManager

# 初始化配置管理器
config_manager = ConfigManager()
config = config_manager.get_config()

# 导入核心模块
from core.mapsheet import CurrentDateFiles
from core.data_models import DateType
from core.reports import DataSubmition
from core.monitor import MonitorManager


# ============================================================================
# 辅助函数和验证器
# ============================================================================

def validate_date(date_str):
    """
    增强版日期验证函数
    
    验证日期字符串的格式、范围和业务逻辑合理性
    
    :param date_str: 输入的日期字符串，支持YYYYMMDD格式
    :return: 转换后的DateType对象
    :raises ValueError: 如果日期格式、范围或业务逻辑不正确
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
    
    验证时间字符串的格式和合理性
    
    :param time_str: 输入的时间字符串，支持HHMMSS格式
    :param time_format: 时间格式，默认为 'HHMMSS'
    :return: 转换后的时间对象
    :raises ValueError: 如果时间格式不正确或不合理
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

def parse_args():
    """增强版命令行参数解析器"""
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

class DataCollector:
    """数据收集器 - 优化版的数据收集逻辑"""
    
    def __init__(self, collection_date, args=None):
        """
        初始化数据采集类
        :param collection_date: DateType 对象, 包含日期信息
        :param args: 命令行参数对象（可选）
        """
        self.collection_date = collection_date
        self.config = config  # 缓存配置
        self.args = args  # 保存命令行参数

    def __call__(self):
        """执行数据收集"""
        try:
            collection = CurrentDateFiles(self.collection_date)
            
            # 显示统计信息
            self._display_collection_header()
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

    def _display_collection_header(self):
        """显示收集报告头部"""
        print("\n" + "="*60)
        print(f"GMAS 每日数据收集报告 {self.collection_date.yyyymmdd_str}")
        print("="*60)

    def _display_error_information(self, collection):
        """显示错误信息，按团队分组"""
        error_by_team = self._organize_errors_by_team(collection)
        
        if error_by_team:
            print(f"\n文件中存在的错误信息:")
            for team_info, errors in error_by_team.items():
                print(f"\n{team_info}:")
                for error in errors:
                    print(f"  - {error}")
            print()

    def _organize_errors_by_team(self, collection):
        """将错误信息按团队组织"""
        error_by_team = {}
        
        for mapsheet in collection.currentDateFiles:
            if hasattr(mapsheet, 'errorMsg') and mapsheet.errorMsg:
                # 获取团队信息
                team_number = getattr(mapsheet, 'teamNumber', '未知团队')
                team_leader = getattr(mapsheet, 'teamleader', '未知负责人')
                roman_name = getattr(mapsheet, 'romanName', '未知图幅名称')
                
                team_key = f"{team_number} ({team_leader})"
                
                if team_key not in error_by_team:
                    error_by_team[team_key] = []
                
                # 格式化错误信息
                error_text = self._format_error_message(roman_name, mapsheet.errorMsg)
                error_by_team[team_key].append(error_text)
        
        return error_by_team

    def _format_error_message(self, roman_name, error_msg):
        """格式化单个错误信息"""
        error_text = f"{roman_name}: "
        if isinstance(error_msg, dict):
            # 如果错误信息是字典格式，逐个解析
            for file_name, errors in error_msg.items():
                error_text += f"\n      文件 {file_name}:"
                if isinstance(errors, list):
                    for error in errors:
                        error_text += f"\n        - {error}"
                else:
                    error_text += f"\n        - {errors}"
        else:
            error_text += str(error_msg)
        return error_text

    def _generate_reports(self, collection):
        """生成KMZ和Excel报告"""
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
        """生成KMZ报告"""
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
        """生成Excel报告"""
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
        """生成统计报告"""
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
        """如果需要则生成周报告"""
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
        """检查是否需要生成周报告"""
        return self.collection_date.date_datetime.weekday() in self.config['data_collection']['weekdays']


# ============================================================================
# 主要功能函数
# ============================================================================

def collect_data(date_str: str = None, args=None):
    """正常数据收集模式"""
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
    """启动文件监控服务"""
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

def main():
    """增强版主入口函数"""
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
            import cProfile
            import pstats
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
    """根据参数设置日志配置"""
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
    """根据参数设置配置"""
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
    """显示系统信息"""
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
    """执行监控模式"""
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
    """执行数据收集模式"""
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
    exit_code = main()
    sys.exit(exit_code)
