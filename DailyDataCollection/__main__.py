#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GMAS 数据收集系统 - 统一模块化入口 V4.0

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
from tabulate import tabulate

# 初始化配置管理器
config_manager = ConfigManager()
config = config_manager.get_config()

# 导入重构后的核心模块 - 完全模块化，无向后兼容
from core.mapsheet import CurrentDateFiles
from core.data_models import DateIterator, DateType
from core.file_handlers import KMZFile
from core.reports import DataSubmition
from core.monitor import MonitorManager
from core.utils import list_fullpath_of_files_with_keywords, find_files_with_max_number

logger.info("所有核心模块导入成功 - 完全模块化结构")


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


def validate_bool(value):
    """
    将字符串转换为布尔值
    :param value: 输入的字符串
    :return: 布尔值
    :raises ArgumentTypeError: 如果输入值不是合法的布尔值
    """
    if isinstance(value, bool):
        return value
    if value.lower() in {'true', '1', 'yes', 'y'}:
        return True
    elif value.lower() in {'false', '0', 'no', 'n'}:
        return False
    else:
        raise argparse.ArgumentTypeError(f"无效的布尔值: {value}")


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
  python __main__.py --mode test
  python __main__.py --mode=test
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
    
    parser.add_argument(
        "--mode",
        choices=['test', 'analyze', 'testdate'],
        help="特殊运行模式: test(模块测试), analyze(历史分析), testdate(指定日期测试)"
    )
    
    return parser.parse_args()


# ============================================================================
# 核心功能类
# ============================================================================

class DataCollector:
    """数据收集器 - 简化版的数据收集逻辑"""
    
    def __init__(self, collection_date):
        """
        初始化数据采集类
        :param collection_date: DateType 对象, 包含日期信息
        """
        self.collection_date = collection_date

    def __call__(self):
        """执行数据收集"""
        try:
            collection = CurrentDateFiles(self.collection_date)
            
            # 显示统计信息
            print("\n" + "="*50)
            print("GMAS 每日数据收集报告")
            print("="*50)
            collection.onScreenDisplay()
            
            # 显示错误信息
            if collection.errorMsg:
                print(f"\n文件中存在的错误信息:")
                for error in collection.errorMsg:
                    if error:
                        print(f"  - {error}")
                print()
            
            # 生成报告
            logger.info("生成每日报告...")
            
            # 生成KMZ报告
            if collection.dailyKMZReport():
                logger.info("KMZ报告生成成功")
            else:
                logger.error("KMZ报告生成失败")
            
            # 生成Excel报告
            if collection.dailyExcelReport():
                logger.info("Excel报告生成成功")
            else:
                logger.error("Excel报告生成失败")
            
            # 检查是否需要生成周报告
            if self.collection_date.date_datetime.weekday() in config['data_collection']['weekdays']:
                print(f'\n今天是{self.collection_date.date_datetime.strftime("%A")}, 需要生成周报\n')
                logger.info("今天是数据提交日，生成周报告...")
                submitter = DataSubmition(self.collection_date, collection.allPoints)
                if submitter.weeklyPointToShp():
                    logger.info("周报告生成成功")
                else:
                    logger.error("周报告生成失败")
            
            logger.info("数据收集完成")
            return True
            
        except Exception as e:
            logger.error(f"数据收集过程中发生错误: {e}")
            return False


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
        
    except Exception as e:
        logger.error(f"数据收集失败: {e}")
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
            endtime = validate_time(endtime_str)
            end_datetime = datetime.combine(current_date.date_datetime.date(), endtime)
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
        
    except Exception as e:
        logger.error(f"监控服务启动失败: {e}")
        return False


def test_modules():
    """测试重构后的模块"""
    try:
        logger.info("开始模块测试...")
        
        # 测试工具函数
        logger.info("✓ 工具函数模块导入成功")
        
        # 测试数据模型
        from core.data_models import ObservationData, FileAttributes, DateIterator
        logger.info("✓ 数据模型模块导入成功")
        
        # 测试文件处理器
        from core.file_handlers import FileIO, GeneralIO, KMZFile
        logger.info("✓ 文件处理模块导入成功")
        
        # 测试图幅处理
        from core.mapsheet import MapsheetDailyFile, CurrentDateFiles
        logger.info("✓ 图幅处理模块导入成功")
        
        # 测试报告生成
        from core.reports import DataSubmition
        logger.info("✓ 报告生成模块导入成功")
        
        # 测试监控模块
        from core.monitor import MonitorManager
        logger.info("✓ 监控模块导入成功")
        
        print("✅ 所有模块测试通过")
        logger.info("所有模块测试通过")
        return True
        
    except ImportError as e:
        print(f"❌ 模块测试失败: {e}")
        logger.error(f"模块测试失败: {e}")
        return False


def historical_analysis():
    """历史数据分析"""
    try:
        logger.info("开始历史数据分析...")
        print("\n历史数据分析 - 最近7天统计")
        print("=" * 50)
        
        # 回溯分析最近一周的数据
        date = DateType(date_datetime=datetime.now())
        total_increase = 0
        
        for i in range(7):  # 分析最近7天
            if date.date_datetime <= datetime.strptime(config['data_collection']['traceback_date'], "%Y%m%d"):
                break
                
            try:
                collection = CurrentDateFiles(date)
                daily_increase = collection.totalDaiyIncreasePointNum
                total_increase += daily_increase
                
                print(f"{date.yyyymmdd_str}: 新增 {daily_increase} 个点")
                
            except Exception as e:
                print(f"{date.yyyymmdd_str}: 分析失败 - {e}")
                
            date = DateType(date_datetime=date.date_datetime - timedelta(days=1))
        
        print(f"\n最近7天总计新增: {total_increase} 个点")
        logger.info("历史数据分析完成")
        return True
        
    except Exception as e:
        logger.error(f"历史数据分析失败: {e}")
        return False


def test_specific_date(test_date_str: str = None):
    """测试指定日期的数据收集功能"""
    try:
        # 如果没有指定日期，使用默认测试日期
        if not test_date_str:
            test_date_str = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
            
        logger.info(f"开始测试指定日期数据收集: {test_date_str}")
        
        # 创建指定日期的DateType对象
        test_date = validate_date(test_date_str)
        logger.info(f"测试日期: {test_date.yyyymmdd_str} ({test_date.date_datetime.strftime('%Y-%m-%d %A')})")
        
        # 收集指定日期的数据
        collection = CurrentDateFiles(test_date)
        
        # 显示统计信息
        print(f"\n指定日期数据收集测试结果 - {test_date_str}")
        print("=" * 50)
        collection.onScreenDisplay()
        
        # 测试报告生成
        logger.info("测试KMZ报告生成...")
        if collection.dailyKMZReport():
            logger.info("✓ KMZ报告生成成功")
            print("✅ KMZ报告生成成功")
        else:
            logger.warning("✗ KMZ报告生成失败")
            print("❌ KMZ报告生成失败")
            
        logger.info("测试Excel报告生成...")
        if collection.dailyExcelReport():
            logger.info("✓ Excel报告生成成功")
            print("✅ Excel报告生成成功")
        else:
            logger.warning("✗ Excel报告生成失败")
            print("❌ Excel报告生成失败")
        
        # 检查是否是数据提交日
        if test_date.date_datetime.weekday() in config['data_collection']['weekdays']:
            logger.info("测试日期是数据提交日，测试周报告生成...")
            submitter = DataSubmition(test_date, collection.allPoints)
            if submitter.weeklyPointToShp():
                logger.info("✓ 周报告生成成功")
                print("✅ 周报告生成成功")
            else:
                logger.warning("✗ 周报告生成失败")
                print("❌ 周报告生成失败")
        
        # 显示详细统计
        print(f"\n详细统计信息:")
        print(f"总文件数: {len(collection.currentDateFiles)}")
        print(f"当日新增点数: {collection.totalDaiyIncreasePointNum}")
        print(f"当日新增线路数: {collection.totalDaiyIncreaseRouteNum}")
        print(f"截止当日总点数: {collection.totalPointNum}")
        print(f"截止当日总线路数: {collection.totalRoutesNum}")
        print(f"当日计划数: {collection.totalDailyPlanNum}")
        
        # 检查错误信息
        errors = collection.errorMsg
        if errors:
            logger.warning("发现以下错误:")
            print("\n发现错误:")
            for error in errors:
                if error:
                    logger.warning(f"  - {error}")
                    print(f"  - {error}")
        else:
            logger.info("✓ 没有发现错误")
            print("✅ 没有发现错误")
        
        logger.info(f"指定日期({test_date_str})数据收集测试完成")
        return True
        
    except Exception as e:
        logger.error(f"指定日期数据收集测试失败: {e}")
        print(f"❌ 测试失败: {e}")
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
        
        # 特殊模式处理
        if args.mode == 'test':
            print("运行模式: 模块测试")
            success = test_modules()
            return 0 if success else 1
            
        elif args.mode == 'analyze':
            print("运行模式: 历史数据分析")
            success = historical_analysis()
            return 0 if success else 1
            
        elif args.mode == 'testdate':
            print(f"运行模式: 指定日期测试 ({args.date})")
            success = test_specific_date(args.date)
            return 0 if success else 1
        
        # 监控模式
        elif args.monitor:
            print("运行模式: 文件监控")
            if args.endtime:
                print(f"监控停止时间: {args.endtime}")
            success = start_monitoring(args.date, args.endtime)
            return 0 if success else 1
        
        # 默认数据收集模式
        else:
            print("运行模式: 数据收集")
            return collect_data(args.date)
            
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        print(f"❌ 程序执行失败: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
