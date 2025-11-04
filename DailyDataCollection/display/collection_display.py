"""
数据收集统计显示器 - 专门处理数据收集统计显示功能
"""

from typing import List, Any, TYPE_CHECKING
from tabulate import tabulate

if TYPE_CHECKING:
    from core.mapsheet.current_date_files import CurrentDateFiles


class CollectionDisplay:
    """数据收集统计显示器 - 负责数据收集统计的显示功能"""
    
    @staticmethod
    def show_statistics(current_date_files: 'CurrentDateFiles'):
        """显示数据收集统计信息"""
        try:
            # 获取基础数据
            team_data, person_data = CollectionDisplay._get_team_and_person_data(current_date_files)
            map_data = CollectionDisplay._get_map_display_data(current_date_files)
            
            # 构建表格数据
            table_data = CollectionDisplay._build_table_data(team_data, person_data, map_data)
            
            # 添加总计行
            table_data.append([
                "TOTAL", "", "", 
                current_date_files.totalDaiyIncreasePointNum, 
                current_date_files.totalDailyPlanNum, 
                current_date_files.totalPointNum
            ])
            
            # 显示表格
            headers = ["TEAM", "NAME", "PERSON IN CHARGE", "INCREASE", "PLAN", "FINISHED POINT"]
            print(tabulate(table_data, headers, tablefmt="grid"))
            
            
            # 检查并报告异常情况
            CollectionDisplay._check_and_report_anomalies(current_date_files)
        except Exception as e:
            import logging
            logger = logging.getLogger('CollectionDisplay')
            logger.error(f"显示统计信息失败: {e}")

    @staticmethod
    def _get_team_and_person_data(current_date_files: 'CurrentDateFiles') -> tuple:
        """获取团队和负责人数据"""
        team_list = []
        person_list = []
        
        # 遍历排序后的图幅列表，确保与地图显示数据的顺序一致
        for mapsheet in current_date_files.sorted_mapsheets:
            map_info = current_date_files.__class__.maps_info.get(mapsheet.sequence, {})
            team_list.append(map_info.get('Team Number', ''))
            person_list.append(map_info.get('Leaders', ''))
        
        return team_list, person_list

    @staticmethod
    def _get_map_display_data(current_date_files: 'CurrentDateFiles') -> tuple:
        """获取地图显示数据"""
        map_name_list = []
        daily_collection_list = []
        daily_finished_list = []
        daily_plan_list = []
        
        empty_placeholder = ''  # 空值占位符
        
        # 遍历所有排序后的图幅，确保所有图幅都显示
        for mapsheet in current_date_files.sorted_mapsheets:
            map_name = mapsheet.romanName
            map_name_list.append(map_name)
            
            # 当天完成点数，如果为0则显示空字符串
            increased_count = current_date_files.dailyIncreasedPoints.get(map_name, 0)
            daily_collection_list.append(
                increased_count if increased_count > 0 else empty_placeholder
            )
            
            # 截止当天完成的总点数 - 现在总是显示，即使为0也显示数字
            finished_count = current_date_files.dailyFinishedPoints.get(map_name, 0)
            daily_finished_list.append(finished_count)  # 移除条件判断，总是显示
            
            # 计划状态
            daily_plan_list.append(current_date_files.DailyPlans.get(map_name, ''))
        
        return map_name_list, daily_collection_list, daily_finished_list, daily_plan_list

    @staticmethod
    def _build_table_data(team_data: List[str], person_data: List[str], 
                         map_data: tuple) -> List[List[Any]]:
        """构建收集统计表格数据"""
        map_name_list, daily_collection_list, daily_finished_list, daily_plan_list = map_data
        
        table_data = []
        for i in range(len(map_name_list)):
            table_data.append([
                team_data[i],
                map_name_list[i], 
                person_data[i], 
                daily_collection_list[i], 
                daily_plan_list[i], 
                daily_finished_list[i]
            ])
        
        return table_data

    @staticmethod
    def _check_and_report_anomalies(current_date_files: 'CurrentDateFiles') -> None:
        """检查并报告异常情况"""
        zero_finished_maps = []
        for mapsheet in current_date_files.sorted_mapsheets:
            finished_count = current_date_files.dailyFinishedPoints.get(mapsheet.romanName, 0)
            if finished_count == 0:
                # 检查这个图幅是否真的应该有数据
                has_current = mapsheet.currentPlacemarks is not None
                has_last = mapsheet.lastPlacemarks is not None
                has_error = hasattr(mapsheet, 'errorMsg') and mapsheet.errorMsg
                
                zero_finished_maps.append({
                    'name': mapsheet.romanName,
                    'has_current': has_current,
                    'has_last': has_last,
                    'has_error': has_error,
                    'current_total': getattr(mapsheet, 'currentTotalPointNum', None)
                })
        
        if zero_finished_maps:
            print(f"\n检测到 {len(zero_finished_maps)} 个图幅的FINISHED值为0:")
            for item in zero_finished_maps:
                status_info = []
                if item['has_current']:
                    status_info.append("有当前数据")
                if item['has_last']:
                    status_info.append("有历史数据")
                if item['has_error']:
                    status_info.append("有错误")
                
                status_str = ", ".join(status_info) if status_info else "截至目前无数据"
                print(f"   - {item['name']}: 图幅总完成数据={item['current_total']}, 状态=({status_str})")
            print()  # 空行分隔
