"""
估算方法智能集成器
负责多种估算方法的结果比较、选择和组合
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import logging
from statistics import stdev, mean

logger = logging.getLogger(__name__)


class MethodIntegrator:
    """多种估算方法的智能集成器"""
    
    def __init__(self):
        """初始化集成器"""
        self.method_weights = {
            'simple_average': 0.2,
            'weighted_average': 0.3,
            'linear_regression': 0.3,
            'monte_carlo': 0.2
        }
        
        # 方法适用性规则
        self.method_rules = {
            'simple_average': {
                'min_data_points': 3,
                'preferred_data_quality': ['poor', 'medium'],
                'reliability_weight': 0.7
            },
            'weighted_average': {
                'min_data_points': 7,
                'preferred_data_quality': ['medium', 'good'],
                'reliability_weight': 0.8
            },
            'linear_regression': {
                'min_data_points': 10,
                'preferred_data_quality': ['good', 'excellent'],
                'reliability_weight': 0.9
            },
            'monte_carlo': {
                'min_data_points': 14,
                'preferred_data_quality': ['excellent'],
                'reliability_weight': 0.95
            }
        }
    
    def integrate_estimation_results(self, estimations: Dict[str, Dict], 
                                   data_quality: Dict[str, Any]) -> Dict[str, Any]:
        """
        智能集成多种估算方法的结果
        
        Args:
            estimations: 各种方法的估算结果
            data_quality: 数据质量评估结果
            
        Returns:
            Dict: 集成后的结果，包含推荐方法和综合估算
        """
        try:
            # 1. 筛选有效的估算结果
            valid_estimations = self._filter_valid_estimations(estimations)
            
            if not valid_estimations:
                return self._create_fallback_integration()
            
            # 2. 计算方法可靠性评分
            method_scores = self._calculate_method_reliability(valid_estimations, data_quality)
            
            # 3. 选择最佳方法
            best_method = self._select_best_method(method_scores, valid_estimations)
            
            # 4. 计算加权组合估算
            ensemble_estimation = self._calculate_ensemble_estimation(
                valid_estimations, method_scores
            )
            
            # 5. 分析结果一致性
            consistency_analysis = self._analyze_result_consistency(valid_estimations)
            
            # 6. 生成方法推荐
            recommendations = self._generate_method_recommendations(
                method_scores, data_quality, consistency_analysis
            )
            
            return {
                'best_method': best_method,
                'ensemble_estimation': ensemble_estimation,
                'method_scores': method_scores,
                'consistency_analysis': consistency_analysis,
                'recommendations': recommendations,
                'integration_confidence': self._calculate_integration_confidence(
                    valid_estimations, consistency_analysis
                )
            }
            
        except Exception as e:
            logger.error(f"集成估算结果失败: {e}")
            return self._create_fallback_integration()
    
    def _filter_valid_estimations(self, estimations: Dict[str, Dict]) -> Dict[str, Dict]:
        """筛选有效的估算结果"""
        valid = {}
        
        for method, result in estimations.items():
            if (result.get('status') not in ['fallback', 'error'] and 
                result.get('estimated_date') and
                result.get('confidence', 0) > 0.1):
                valid[method] = result
        
        return valid
    
    def _calculate_method_reliability(self, estimations: Dict[str, Dict], 
                                    data_quality: Dict[str, Any]) -> Dict[str, float]:
        """计算各方法的可靠性评分"""
        scores = {}
        quality = data_quality.get('quality', 'poor')
        total_days = data_quality.get('total_days', 0)
        activity_rate = data_quality.get('activity_rate', 0)
        
        for method, result in estimations.items():
            base_score = result.get('confidence', 0)
            
            # 根据方法规则调整评分
            if method in self.method_rules:
                rules = self.method_rules[method]
                
                # 数据量适配性
                if total_days >= rules['min_data_points']:
                    base_score *= 1.1
                else:
                    base_score *= 0.8
                
                # 数据质量适配性
                if quality in rules['preferred_data_quality']:
                    base_score *= 1.2
                
                # 活跃度调整
                if activity_rate > 0.7:
                    base_score *= rules['reliability_weight']
                elif activity_rate > 0.4:
                    base_score *= (rules['reliability_weight'] * 0.8)
                else:
                    base_score *= (rules['reliability_weight'] * 0.6)
            
            scores[method] = min(1.0, base_score)
        
        return scores
    
    def _select_best_method(self, method_scores: Dict[str, float], 
                           estimations: Dict[str, Dict]) -> Dict[str, Any]:
        """选择最佳估算方法"""
        if not method_scores:
            return None
        
        best_method_name = max(method_scores.keys(), key=lambda x: method_scores[x])
        best_estimation = estimations[best_method_name]
        
        return {
            'method': best_method_name,
            'estimation': best_estimation,
            'reliability_score': method_scores[best_method_name],
            'reason': f"基于数据质量和方法特性，{best_method_name}方法最适合当前情况"
        }
    
    def _calculate_ensemble_estimation(self, estimations: Dict[str, Dict], 
                                     method_scores: Dict[str, float]) -> Dict[str, Any]:
        """计算加权组合估算"""
        try:
            # 收集估算数据
            dates = []
            days_remaining = []
            confidences = []
            weights = []
            
            for method, result in estimations.items():
                if method in method_scores and method_scores[method] > 0.3:
                    dates.append(result['estimated_date'])
                    days_remaining.append(result['days_remaining'])
                    confidences.append(result['confidence'])
                    weights.append(method_scores[method])
            
            if not dates:
                return None
            
            # 归一化权重
            total_weight = sum(weights)
            normalized_weights = [w / total_weight for w in weights]
            
            # 加权平均天数
            weighted_days = sum(d * w for d, w in zip(days_remaining, normalized_weights))
            weighted_confidence = sum(c * w for c, w in zip(confidences, normalized_weights))
            
            # 计算标准差（不确定性）
            days_std = stdev(days_remaining) if len(days_remaining) > 1 else 0
            
            # 组合估算日期
            ensemble_date = datetime.now() + timedelta(days=weighted_days)
            
            return {
                'estimated_date': ensemble_date,
                'days_remaining': weighted_days,
                'confidence': weighted_confidence,
                'uncertainty_days': days_std,
                'methods_used': list(estimations.keys()),
                'method_weights': dict(zip(estimations.keys(), normalized_weights)),
                'status': 'ensemble'
            }
            
        except Exception as e:
            logger.error(f"计算组合估算失败: {e}")
            return None
    
    def _analyze_result_consistency(self, estimations: Dict[str, Dict]) -> Dict[str, Any]:
        """分析结果一致性"""
        try:
            dates = [result['estimated_date'] for result in estimations.values()]
            days_list = [result['days_remaining'] for result in estimations.values()]
            
            if len(dates) < 2:
                return {'consistency': 'insufficient_data', 'score': 0}
            
            # 计算日期范围
            date_range_days = (max(dates) - min(dates)).days
            
            # 计算天数标准差
            days_std = stdev(days_list)
            mean_days = mean(days_list)
            coefficient_of_variation = days_std / mean_days if mean_days > 0 else float('inf')
            
            # 一致性评分
            if date_range_days <= 7 and coefficient_of_variation <= 0.2:
                consistency = 'high'
                score = 0.9
            elif date_range_days <= 21 and coefficient_of_variation <= 0.5:
                consistency = 'medium'
                score = 0.6
            elif date_range_days <= 60 and coefficient_of_variation <= 1.0:
                consistency = 'low'
                score = 0.3
            else:
                consistency = 'very_low'
                score = 0.1
            
            return {
                'consistency': consistency,
                'score': score,
                'date_range_days': date_range_days,
                'days_std': days_std,
                'coefficient_of_variation': coefficient_of_variation,
                'analysis': f"方法间预测差异为{date_range_days}天，变异系数为{coefficient_of_variation:.2f}"
            }
            
        except Exception as e:
            logger.error(f"分析结果一致性失败: {e}")
            return {'consistency': 'error', 'score': 0}
    
    def _generate_method_recommendations(self, method_scores: Dict[str, float],
                                       data_quality: Dict[str, Any],
                                       consistency: Dict[str, Any]) -> List[str]:
        """生成方法选择建议"""
        recommendations = []
        
        quality = data_quality.get('quality', 'poor')
        consistency_score = consistency.get('score', 0)
        
        # 数据质量建议
        if quality == 'poor':
            recommendations.append("数据质量较差，建议优先考虑简单平均法")
        elif quality == 'excellent':
            recommendations.append("数据质量优秀，可以使用线性回归法或蒙特卡洛方法")
        
        # 一致性建议
        if consistency_score > 0.8:
            recommendations.append("各方法结果高度一致，预测可靠性高")
        elif consistency_score < 0.3:
            recommendations.append("各方法结果差异较大，建议谨慎使用预测结果")
        
        # 方法特定建议
        best_methods = sorted(method_scores.items(), key=lambda x: x[1], reverse=True)[:2]
        if len(best_methods) >= 2:
            recommendations.append(f"推荐使用{best_methods[0][0]}方法，{best_methods[1][0]}方法作为参考")
        
        return recommendations
    
    def _calculate_integration_confidence(self, estimations: Dict[str, Dict],
                                        consistency: Dict[str, Any]) -> float:
        """计算集成结果的置信度"""
        try:
            # 基础置信度（方法数量）
            base_confidence = min(0.8, len(estimations) * 0.2)
            
            # 一致性调整
            consistency_score = consistency.get('score', 0)
            confidence = base_confidence * (0.5 + 0.5 * consistency_score)
            
            # 个别方法置信度调整
            avg_confidence = mean([e.get('confidence', 0) for e in estimations.values()])
            confidence = confidence * (0.7 + 0.3 * avg_confidence)
            
            return min(1.0, confidence)
            
        except Exception as e:
            logger.error(f"计算集成置信度失败: {e}")
            return 0.5
    
    def _create_fallback_integration(self) -> Dict[str, Any]:
        """创建回退集成结果"""
        return {
            'best_method': None,
            'ensemble_estimation': None,
            'method_scores': {},
            'consistency_analysis': {'consistency': 'no_data', 'score': 0},
            'recommendations': ['无有效估算结果，建议检查数据质量'],
            'integration_confidence': 0.0
        }
    
    def update_method_weights(self, performance_history: Dict[str, List[float]]):
        """根据历史表现更新方法权重"""
        try:
            for method, performances in performance_history.items():
                if method in self.method_weights and performances:
                    avg_performance = mean(performances)
                    # 简单的权重调整策略
                    self.method_weights[method] = min(1.0, avg_performance)
            
            # 归一化权重
            total = sum(self.method_weights.values())
            if total > 0:
                for method in self.method_weights:
                    self.method_weights[method] /= total
                    
        except Exception as e:
            logger.error(f"更新方法权重失败: {e}")
