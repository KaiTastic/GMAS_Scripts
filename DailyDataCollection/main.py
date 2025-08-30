"""
GMAS 数据收集系统 - 主入口

使用重构后的模块化架构的示例和主要功能入口
"""

import sys
import logging
import io
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 为Windows控制台配置UTF-8编码
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

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


def main():
    """主函数 - 演示重构后模块的使用"""
    try:
        # 导入重构后的模块
        from core.mapsheet import CurrentDateFiles
        from core.data_models import DateIterator, DateType
        from core.file_handlers import KMZFile
        from core.reports import DataSubmition
        from config import TRACEBACK_DATE, COLLECTION_WEEKDAYS
        
        logger.info("GMAS 数据收集系统启动")
        
        # 获取当前日期
        current_date = DateType(date_datetime=datetime.now())
        logger.info(f"当前处理日期: {current_date.yyyymmdd_str}")
        
        # 收集当日数据
        logger.info("开始收集当日数据...")
        collection = CurrentDateFiles(current_date)
        
        # 显示统计信息
        print("\n" + "="*50)
        print("GMAS 每日数据收集报告")
        print("="*50)
        collection.onScreenDisplay()
        
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
        if current_date.date_datetime.weekday() in COLLECTION_WEEKDAYS:
            logger.info("今天是数据提交日，生成周报告...")
            submitter = DataSubmition(current_date, collection.allPoints)
            if submitter.weeklyPointToShp():
                logger.info("周报告生成成功")
            else:
                logger.error("周报告生成失败")
        
        # 检查错误信息
        errors = collection.errorMsg
        if errors:
            logger.warning("发现以下错误:")
            for error in errors:
                try:
                    logger.warning(f"  - {error}")
                except UnicodeEncodeError:
                    # 处理包含特殊字符的错误信息
                    safe_error = str(error).encode('ascii', 'replace').decode('ascii')
                    logger.warning(f"  - {safe_error} (原始错误包含特殊字符)")
                except Exception as e:
                    logger.warning(f"  - 记录错误信息时出错: {e}")
        
        logger.info("数据收集完成")
        
    except ImportError as e:
        logger.error(f"导入模块失败: {e}")
        logger.error("请确保所有依赖包已安装且配置文件正确")
        return 1
    except Exception as e:
        logger.error(f"运行时错误: {e}")
        return 1
    
    return 0


def test_modules():
    """测试重构后的模块"""
    try:
        logger.info("开始模块测试...")
        
        # 测试文件工具
        from core.utils import list_fullpath_of_files_with_keywords, find_files_with_max_number
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
        
        logger.info("所有模块测试通过")
        return True
        
    except ImportError as e:
        logger.error(f"模块测试失败: {e}")
        return False


def test_specific_date_collection(test_date_str: str = None):
    """测试指定日期的数据收集功能"""
    try:
        from core.mapsheet import CurrentDateFiles
        from core.data_models import DateType
        from core.reports import DataSubmition
        from config import COLLECTION_WEEKDAYS
        
        # 如果没有指定日期，使用默认测试日期
        if not test_date_str:
            test_date_str = "20250828"  # 使用昨天作为测试日期
            
        logger.info(f"开始测试指定日期数据收集: {test_date_str}")
        
        # 创建指定日期的DateType对象
        test_date = DateType(yyyymmdd_str=test_date_str)
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
            logger.info(f"✓ KMZ报告生成成功")
        else:
            logger.warning("✗ KMZ报告生成失败")
            
        logger.info("测试Excel报告生成...")
        if collection.dailyExcelReport():
            logger.info(f"✓ Excel报告生成成功")
        else:
            logger.warning("✗ Excel报告生成失败")
        
        # 检查是否是数据提交日
        if test_date.date_datetime.weekday() in COLLECTION_WEEKDAYS:
            logger.info(f"测试日期是数据提交日，测试周报告生成...")
            submitter = DataSubmition(test_date, collection.allPoints)
            if submitter.weeklyPointToShp():
                logger.info("✓ 周报告生成成功")
            else:
                logger.warning("✗ 周报告生成失败")
        
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
            for error in errors:
                try:
                    logger.warning(f"  - {error}")
                except UnicodeEncodeError:
                    safe_error = str(error).encode('ascii', 'replace').decode('ascii')
                    logger.warning(f"  - {safe_error} (原始错误包含特殊字符)")
                except Exception as e:
                    logger.warning(f"  - 记录错误信息时出错: {e}")
        else:
            logger.info("✓ 没有发现错误")
        
        logger.info(f"指定日期({test_date_str})数据收集测试完成")
        return True
        
    except Exception as e:
        logger.error(f"指定日期数据收集测试失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return False


def start_monitoring():
    """启动文件监控服务"""
    try:
        logger.info("启动文件监控服务...")
        
        # 导入重构后的监控模块
        from core.data_models import DateType
        from core.monitor import MonitorManager
        from config import MONITOR_ENDTIME, ENABLE_FUZZY_MATCHING, FUZZY_MATCHING_THRESHOLD
        
        # 设置当前日期
        current_date = DateType(date_datetime=datetime.now())
        logger.info(f"开始监控 {current_date.yyyymmdd_str} 的数据收集...")
        
        # 创建监控管理器（使用配置文件中的模糊匹配设置）
        monitor_manager = MonitorManager(
            current_date=current_date,
            enable_fuzzy_matching=ENABLE_FUZZY_MATCHING,
            fuzzy_threshold=FUZZY_MATCHING_THRESHOLD
        )
        
        if ENABLE_FUZZY_MATCHING:
            logger.info(f"模糊匹配已启用，相似度阈值: {FUZZY_MATCHING_THRESHOLD}")
        else:
            logger.info("使用精确匹配模式")
        
        # 定义完成后的处理函数
        def post_processing():
            """监控完成后的处理逻辑"""
            logger.info("文件监控完成，开始执行后续处理任务...")
            
            # 执行数据收集和报告生成
            try:
                result = main()
                if result == 0:
                    logger.info("后续处理任务完成")
                else:
                    logger.error("后续处理任务执行失败")
            except Exception as e:
                logger.error(f"后续处理任务执行出错: {e}")
        
        # 启动监控
        print(f"开始监控微信文件夹中的KMZ文件...")
        print(f"监控日期: {current_date.yyyymmdd_str}")
        print(f"预计结束时间: {MONITOR_ENDTIME}")
        print("按 Ctrl+C 可以手动停止监控")
        
        monitor_manager.start_monitoring(
            executor=post_processing,
            end_time=MONITOR_ENDTIME
        )
        
        logger.info("文件监控服务已结束")
        
    except ImportError as e:
        logger.error(f"无法导入监控模块: {e}")
        logger.info("尝试使用传统监控模块...")
        return start_legacy_monitoring()
        
    except Exception as e:
        logger.error(f"监控服务启动失败: {e}")
        logger.info("尝试使用传统监控模块...")
        return start_legacy_monitoring()


def start_legacy_monitoring():
    """启动传统监控服务（向后兼容）"""
    try:
        logger.info("启动传统文件监控服务...")
        
        # 导入传统监控模块
        from deprecated.monitor_legacy import DataHandler, DateType
        
        # 设置当前日期
        current_date = DateType(date_datetime=datetime.now())
        
        # 创建传统事件处理器
        event_handler = DataHandler(currentDate=current_date)
        
        # 定义完成后的处理函数
        def post_processing():
            logger.info("传统监控完成，开始执行后续处理任务...")
            try:
                result = main()
                if result == 0:
                    logger.info("后续处理任务完成")
                else:
                    logger.error("后续处理任务执行失败")
            except Exception as e:
                logger.error(f"后续处理任务执行出错: {e}")
        
        # 启动传统监控
        print("使用传统监控模块...")
        event_handler.obsserverService(event_handler, executor=post_processing)
        
        logger.info("传统文件监控服务已结束")
        
    except Exception as e:
        logger.error(f"传统监控服务也启动失败: {e}")
        logger.error("请检查监控模块配置")
        return False
    
    return True


def historical_analysis():
    """历史数据分析示例"""
    try:
        from core.mapsheet import CurrentDateFiles
        from core.data_models import DateType
        from config import TRACEBACK_DATE
        
        logger.info("开始历史数据分析...")
        
        # 回溯分析最近一周的数据
        date = DateType(date_datetime=datetime.now())
        total_increase = 0
        
        for i in range(7):  # 分析最近7天
            if date.date_datetime <= datetime.strptime(TRACEBACK_DATE, "%Y%m%d"):
                break
                
            collection = CurrentDateFiles(date)
            daily_increase = collection.totalDaiyIncreasePointNum
            total_increase += daily_increase
            
            print(f"{date.yyyymmdd_str}: 新增 {daily_increase} 个点")
            
            date = DateType(date_datetime=date.date_datetime - timedelta(days=1))
        
        print(f"\n最近7天总计新增: {total_increase} 个点")
        logger.info("历史数据分析完成")
        
    except Exception as e:
        logger.error(f"历史数据分析失败: {e}")


if __name__ == "__main__":
    print("GMAS 数据收集系统 v2.0 (重构版)")
    print("=" * 40)
    
    # 选择运行模式
    mode = input("请选择运行模式:\n1. 正常数据收集\n2. 启动文件监控\n3. 模块测试\n4. 历史数据分析\n5. 指定日期数据收集测试\n请输入 (1-5): ").strip()
    
    if mode == "1":
        exit_code = main()
        sys.exit(exit_code)
    elif mode == "2":
        start_monitoring()
    elif mode == "3":
        test_modules()
    elif mode == "4":
        historical_analysis()
    elif mode == "5":
        # 指定日期测试
        test_date = input("请输入测试日期 (格式: YYYYMMDD，直接回车使用默认日期20250828): ").strip()
        if not test_date:
            test_specific_date_collection()
        else:
            test_specific_date_collection(test_date)
    else:
        print("无效的选择，运行正常数据收集...")
        exit_code = main()
        sys.exit(exit_code)
