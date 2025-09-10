"""
已完成项目智能处理器
专门处理已达到或超过目标的图幅项目
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class CompletedProjectHandler:
    """已完成项目的智能处理器"""
    
    def __init__(self, skip_estimation: bool = False):
        """
        初始化处理器
        
        Args:
            skip_estimation: 是否完全跳过估算计算（True=节省资源，False=保持完整分析）
        """
        self.skip_estimation = skip_estimation
        self.completion_categories = {
            'exactly_completed': (100, 100),      # 正好完成
            'slightly_over': (100, 110),          # 轻微超额 
            'moderately_over': (110, 125),        # 中度超额
            'significantly_over': (125, float('inf'))  # 显著超额
        }
    
    def is_project_completed(self, current_points: int, target_points: int) -> bool:
        """判断项目是否已完成"""
        return current_points >= target_points if target_points > 0 else False
    
    def analyze_completion_status(self, current_points: int, target_points: int, 
                                historical_data: pd.DataFrame = None) -> Dict[str, Any]:
        """
        分析完成状态
        
        Args:
            current_points: 当前完成点数
            target_points: 目标点数
            historical_data: 历史数据（用于回溯分析）
            
        Returns:
            Dict: 完成状态分析结果
        """
        if not self.is_project_completed(current_points, target_points):
            return {'status': 'not_completed'}
        
        # 基础完成分析
        completion_rate = (current_points / target_points * 100) if target_points > 0 else 100
        excess_points = current_points - target_points
        excess_rate = (excess_points / target_points * 100) if target_points > 0 else 0
        
        # 分类完成类型
        completion_category = self._categorize_completion(completion_rate)
        
        # 回溯分析实际完成日期
        completion_analysis = self._analyze_actual_completion(
            target_points, historical_data
        ) if historical_data is not None else {}
        
        # 效率评估
        efficiency_assessment = self._assess_efficiency(
            completion_rate, completion_analysis
        )
        
        # 生成建议
        recommendations = self._generate_completion_recommendations(
            completion_category, excess_rate, efficiency_assessment
        )
        
        return {
            'status': 'completed',
            'completion_rate': completion_rate,
            'excess_points': excess_points,
            'excess_rate': excess_rate,
            'completion_category': completion_category,
            'completion_analysis': completion_analysis,
            'efficiency_assessment': efficiency_assessment,
            'recommendations': recommendations,
            'display_text': self._generate_display_text(completion_rate, completion_analysis)
        }
    
    def create_completed_estimation_result(self, current_points: int, target_points: int,
                                         method: str, historical_data: pd.DataFrame = None) -> Dict[str, Any]:
        """
        为已完成项目创建估算结果
        
        Args:
            current_points: 当前点数
            target_points: 目标点数  
            method: 估算方法名称
            historical_data: 历史数据
            
        Returns:
            Dict: 估算结果（已完成格式）
        """
        if self.skip_estimation:
            # 策略A：最简单的已完成标记
            return {
                'estimated_date': datetime.now(),
                'estimated_finish_date': '-',  # 已完成显示"-"
                'days_remaining': 0,
                'remaining_points': 0,
                'confidence': 1.0,
                'method': method,
                'status': 'completed_skipped',
                'message': '项目已完成，跳过估算计算'
            }
        
        # 策略B：完整的已完成分析
        completion_status = self.analyze_completion_status(
            current_points, target_points, historical_data
        )
        
        # 回溯分析实际完成日期
        actual_completion_date = completion_status.get('completion_analysis', {}).get(
            'actual_completion_date', datetime.now()
        )
        
        days_early = completion_status.get('completion_analysis', {}).get(
            'days_early', 0
        )
        
        return {
            'estimated_date': actual_completion_date,
            'estimated_finish_date': '-',  # 已完成显示"-"
            'days_remaining': 0,
            'remaining_points': 0,
            'confidence': 1.0,
            'method': method,
            'status': 'completed',
            'completion_details': completion_status,
            'days_early': days_early,
            'efficiency_score': completion_status.get('efficiency_assessment', {}).get('score', 1.0),
            'message': completion_status.get('display_text', '项目已完成')
        }
    
    def _categorize_completion(self, completion_rate: float) -> str:
        """对完成情况进行分类"""
        for category, (min_rate, max_rate) in self.completion_categories.items():
            if min_rate <= completion_rate < max_rate:
                return category
        return 'unknown'
    
    def _analyze_actual_completion(self, target_points: int, 
                                 historical_data: pd.DataFrame) -> Dict[str, Any]:
        """回溯分析实际完成日期"""
        try:
            if historical_data is None or historical_data.empty:
                return {}
            
            # 查找累计点数达到目标的最早日期
            if 'cumulative_points' in historical_data.columns:
                completed_records = historical_data[
                    historical_data['cumulative_points'] >= target_points
                ].copy()
                
                if not completed_records.empty:
                    # 最早完成日期
                    completed_records = completed_records.sort_values('date')
                    actual_completion_date = completed_records.iloc[0]['date']
                    
                    # 计算提前天数（相对于今天）
                    days_early = (datetime.now() - actual_completion_date).days
                    
                    # 计算达到目标的速度
                    completion_velocity = target_points / len(
                        historical_data[historical_data['date'] <= actual_completion_date]
                    )
                    
                    return {
                        'actual_completion_date': actual_completion_date,
                        'days_early': max(0, days_early),
                        'completion_velocity': completion_velocity,
                        'found_actual_date': True
                    }
            
            return {'found_actual_date': False}
            
        except Exception as e:
            logger.warning(f"回溯分析实际完成日期失败: {e}")
            return {}
    
    def _assess_efficiency(self, completion_rate: float, 
                          completion_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """评估项目效率"""
        try:
            # 基于完成率的效率评分
            if completion_rate >= 125:
                efficiency_level = "优秀+"
                score = 1.0
            elif completion_rate >= 110:
                efficiency_level = "优秀"
                score = 0.9
            elif completion_rate >= 100:
                efficiency_level = "良好"
                score = 0.8
            else:
                efficiency_level = "一般"
                score = 0.6
            
            # 考虑提前完成的天数
            days_early = completion_analysis.get('days_early', 0)
            if days_early > 0:
                score = min(1.0, score + (days_early / 30) * 0.1)  # 每提前30天加0.1分
            
            return {
                'level': efficiency_level,
                'score': score,
                'completion_rate': completion_rate,
                'days_early': days_early
            }
            
        except Exception as e:
            logger.warning(f"效率评估失败: {e}")
            return {'level': '未知', 'score': 0.5}
    
    def _generate_completion_recommendations(self, completion_category: str,
                                           excess_rate: float,
                                           efficiency_assessment: Dict[str, Any]) -> List[str]:
        """生成针对已完成项目的建议"""
        recommendations = []
        
        # 基于完成类型的建议
        if completion_category == 'exactly_completed':
            recommendations.append("项目按计划准确完成，目标设定合理")
        elif completion_category == 'slightly_over':
            recommendations.append("项目轻微超额完成，表现良好")
        elif completion_category == 'moderately_over':
            recommendations.append("项目中度超额完成，建议检查目标设定是否过于保守")
        elif completion_category == 'significantly_over':
            recommendations.append("项目显著超额完成，强烈建议重新评估目标设定方法")
        
        # 基于效率的建议
        efficiency_level = efficiency_assessment.get('level', '')
        if efficiency_level == "优秀+":
            recommendations.append("团队效率极高，可考虑承担更具挑战性的目标")
        elif efficiency_level == "优秀":
            recommendations.append("团队效率很好，可适当提升未来项目目标")
        
        # 基于超额率的建议
        if excess_rate > 25:
            recommendations.append(f"超额完成{excess_rate:.1f}%，建议分析高效完成的因素以复制到其他项目")
        elif excess_rate > 10:
            recommendations.append("适度超额完成，团队表现稳定")
        
        return recommendations
    
    def _generate_display_text(self, completion_rate: float, 
                              completion_analysis: Dict[str, Any]) -> str:
        """生成用于显示的文本"""
        if completion_rate == 100:
            base_text = "✅ 已完成"
        elif completion_rate > 100:
            excess = completion_rate - 100
            base_text = f"✅ 已完成 (超额{excess:.1f}%)"
        else:
            base_text = "✅ 已完成"
        
        # 添加提前完成信息
        days_early = completion_analysis.get('days_early', 0)
        if days_early > 0:
            base_text += f" (提前{days_early}天)"
        
        return base_text
    
    def should_skip_complex_analysis(self, completion_rate: float) -> bool:
        """判断是否应该跳过复杂分析"""
        # 对于显著超额完成的项目，可能存在数据质量问题，建议跳过复杂分析
        return completion_rate > 200  # 超过200%可能有数据问题
    
    def get_completion_summary(self, completed_projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取已完成项目的汇总分析"""
        if not completed_projects:
            return {}
        
        total_projects = len(completed_projects)
        completion_rates = [p.get('completion_rate', 100) for p in completed_projects]
        
        # 分类统计
        category_counts = {}
        for project in completed_projects:
            category = project.get('completion_category', 'unknown')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # 效率统计
        efficiency_scores = [
            p.get('efficiency_assessment', {}).get('score', 0.5) 
            for p in completed_projects
        ]
        
        avg_efficiency = sum(efficiency_scores) / len(efficiency_scores) if efficiency_scores else 0
        avg_completion_rate = sum(completion_rates) / len(completion_rates) if completion_rates else 100
        
        return {
            'total_completed_projects': total_projects,
            'average_completion_rate': avg_completion_rate,
            'average_efficiency_score': avg_efficiency,
            'completion_category_distribution': category_counts,
            'over_target_projects': len([r for r in completion_rates if r > 100]),
            'significantly_over_projects': len([r for r in completion_rates if r > 125])
        }
