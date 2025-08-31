#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GMAS 数据收集系统 - 统一模块化入口 V2.0

完全模块化的主入口文件，支持多种运行模式和命令行参数
采用现代化的核心模块架构，移除所有向后兼容层
"""

import sys
import os
import logging
import argparse
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

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
    验证日期字符串的长度和格式
    :param date_str: 输入的日期字符串
    :return: 转换后的日期对象
    :raises ValueError: 如果日期格式不正确或长度不符合
    """
    if len(date_str) != 8:
        raise ValueError(f"日期长度不正确, 请确保长度为8位, 输入值: {date_str}")
    try:
        date_datetime = datetime.strptime(date_str, "%Y%m%d")
        return DateType(date_datetime=date_datetime)
    except ValueError:
        raise ValueError(f"日期不合法或格式不正确, 请确保格式为'YYYYMMDD', 输入值: {date_str}")


def validate_time(time_str, time_format="%H%M%S"):
    """
    验证时间字符串的格式
    :param time_str: 输入的时间字符串
    :param time_format: 时间格式，默认为 'HHMMSS'
    :return: 转换后的时间对象
    :raises ValueError: 如果时间格式不正确
    """
    expected_length = 6  # HHMMSS 格式应该是6位
    if len(time_str) != expected_length:
        raise ValueError(f"时间长度不正确, 请确保长度为{expected_length}位, 输入值: {time_str}")
    try:
        return datetime.strptime(time_str, time_format).time()
    except ValueError:
        raise ValueError(f"时间不合法或格式不正确, 请确保格式为'{time_format}', 输入值: {time_str}")


# ============================================================================
# 命令行参数解析
# ============================================================================

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="GMAS 数据收集系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        示例:
        python __main__.py --date 20250830
        python __main__.py --date=20250830
        python __main__.py --monitor --endtime 183000
        python __main__.py --monitor --endtime=183000
        """
        )

    parser.add_argument(
        "--date",
        default=datetime.now().strftime("%Y%m%d"),
        help="收集数据的日期，格式为YYYYMMDD (默认: 今天)"
        )
    
    parser.add_argument(
        "--monitor",
        action='store_true',
        help="启动文件监控模式"
    )
    
    parser.add_argument(
        "--endtime",
        help="监控停止时间，格式为HHMMSS"
    )
    
    return parser.parse_args()


# ============================================================================
# 核心功能类
# ============================================================================

class DataCollector:
    """数据收集器 - 优化版的数据收集逻辑"""
    
    def __init__(self, collection_date):
        """
        初始化数据采集类
        :param collection_date: DateType 对象, 包含日期信息
        """
        self.collection_date = collection_date
        self.config = config  # 缓存配置

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
        print("\n" + "="*50)
        print(f"GMAS 每日数据收集报告 {self.collection_date.yyyymmdd_str}")
        print("="*50)

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
                roman_name = getattr(mapsheet, 'romanName', '未知图幅')
                
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
                        error_text += f"\n        • {error}"
                else:
                    error_text += f"\n        • {errors}"
        else:
            error_text += str(error_msg)
        return error_text

    def _generate_reports(self, collection):
        """生成KMZ和Excel报告"""
        logger.info("生成每日报告...")
        
        kmz_success = self._generate_kmz_report(collection)
        excel_success = self._generate_excel_report(collection)
        
        return kmz_success and excel_success

    def _generate_kmz_report(self, collection):
        """生成KMZ报告"""
        try:
            if collection.dailyKMZReport():
                logger.info("KMZ报告生成成功")
                return True
            else:
                logger.error("KMZ报告生成失败")
                return False
        except Exception as e:
            logger.error(f"KMZ报告生成异常: {e}")
            return False

    def _generate_excel_report(self, collection):
        """生成Excel报告"""
        try:
            if collection.dailyExcelReport():
                logger.info("Excel报告生成成功")
                return True
            else:
                logger.error("Excel报告生成失败")
                return False
        except Exception as e:
            logger.error(f"Excel报告生成异常: {e}")
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

def collect_data(date_str: str = None):
    """正常数据收集模式"""
    try:
        if date_str:
            current_date = validate_date(date_str)
        else:
            current_date = DateType(date_datetime=datetime.now())
            
        logger.info(f"开始数据收集 - 日期: {current_date.yyyymmdd_str}")
        
        collector = DataCollector(current_date)
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


def start_monitoring(date_str: str = None, endtime_str: str = None):
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
                collector = DataCollector(current_date)
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
    """主入口函数"""
    try:
        args = parse_args()
        
        # 显示系统信息
        print(f"\n设定日期: {args.date}")
        print(f"当前系统时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 监控模式
        if args.monitor:
            print("运行模式: 文件监控")
            if args.endtime:
                print(f"监控停止时间: {args.endtime}")
            success = start_monitoring(args.date, args.endtime)
            return 0 if success else 1
        
        # 默认数据收集模式
        else:
            print("运行模式: 数据收集")
            return collect_data(args.date)
            
    except KeyboardInterrupt:
        logger.info("用户中断程序执行")
        print("\n程序被用户中断")
        return 1
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        print(f"程序执行失败: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
