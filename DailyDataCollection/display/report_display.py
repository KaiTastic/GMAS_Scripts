"""
报告显示器 - 专门处理报告相关的显示功能
"""

from typing import Dict, List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from core.mapsheet.current_date_files import CurrentDateFiles


class ReportDisplay:
    """报告显示器 - 负责所有报告相关的显示功能"""
    
    @staticmethod
    def show_header(collection_date):
        """显示数据收集报告头部"""
        print("\n" + "="*60)
        print(f"GMAS 每日数据收集报告 {collection_date.yyyymmdd_str}")
        print("="*60)

    @staticmethod
    def show_error_summary(current_date_files: 'CurrentDateFiles'):
        """显示错误信息汇总，按团队分组"""
        error_by_team = ReportDisplay._organize_errors_by_team(current_date_files)
        
        if error_by_team:
            print(f"\n文件中存在的错误信息:")
            for team_info, errors in error_by_team.items():
                print(f"\n{team_info}:")
                for error in errors:
                    print(f"  - {error}")
            print()

    @staticmethod
    def _organize_errors_by_team(current_date_files: 'CurrentDateFiles') -> Dict[str, List[str]]:
        """将错误信息按团队组织"""
        error_by_team = {}
        
        for mapsheet in current_date_files.currentDateFiles:
            if hasattr(mapsheet, 'errorMsg') and mapsheet.errorMsg:
                # 获取团队信息
                team_number = getattr(mapsheet, 'teamNumber', '未知团队')
                team_leader = getattr(mapsheet, 'teamleader', '未知负责人')
                roman_name = getattr(mapsheet, 'romanName', '未知图幅名称')
                
                team_key = f"{team_number} ({team_leader})"
                
                if team_key not in error_by_team:
                    error_by_team[team_key] = []
                
                # 格式化错误信息
                error_text = ReportDisplay._format_error_message(roman_name, mapsheet.errorMsg)
                error_by_team[team_key].append(error_text)
        
        return error_by_team

    @staticmethod
    def _format_error_message(roman_name: str, error_msg: Any) -> str:
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
