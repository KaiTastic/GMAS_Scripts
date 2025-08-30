"""
重构后的监控模块 - 使用模块化设计的新版监控系统

这个文件展示了如何使用重构后的监控模块。
原有的monitor.py可以保留作为兼容性选项。
"""

from datetime import datetime
from core.data_models.date_types import DateType
from core.monitor import MonitorManager
from config import MONITOR_ENDTIME


def main():
    """主函数 - 启动监控服务"""
    # 设置当前日期
    current_date = DateType(date_datetime=datetime.now())
    # 测试日期（如需要）
    # current_date = DateType(date_datetime=datetime(2025, 4, 3))
    
    # 创建监控管理器
    monitor_manager = MonitorManager(current_date)
    
    # 可选的执行器函数
    def post_processing():
        """监控完成后的处理逻辑"""
        print("开始执行后续处理任务...")
        # 这里可以添加其他处理逻辑，比如生成报告、发送通知等
    
    try:
        # 启动监控
        print(f"开始监控 {current_date.yyyymmdd_str} 的数据收集...")
        monitor_manager.start_monitoring(
            executor=post_processing,
            end_time=MONITOR_ENDTIME
        )
        
    except Exception as e:
        print(f"监控过程中发生错误: {e}")
        # 可以添加错误处理逻辑
    finally:
        print("监控服务已结束")


def get_monitoring_status():
    """获取监控状态的示例函数"""
    current_date = DateType(date_datetime=datetime.now())
    monitor_manager = MonitorManager(current_date)
    
    status = monitor_manager.get_monitoring_status()
    print("当前监控状态:")
    print(f"  日期: {status['current_date']}")
    print(f"  计划文件数: {status['planned_files']}")
    print(f"  剩余文件数: {status['remaining_files']}")
    print(f"  是否完成: {status['is_complete']}")
    
    if status['remaining_file_list']:
        print(f"  待收集文件: {', '.join(status['remaining_file_list'])}")


if __name__ == "__main__":
    main()
