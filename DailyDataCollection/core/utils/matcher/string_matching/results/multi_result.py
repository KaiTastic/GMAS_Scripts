# -*- coding: utf-8 -*-
"""
多结果匹配处理模块 - 批量处理多个匹配结果
"""

from typing import Dict, List, Optional, Any, Tuple
import json

# 直接导入具体类型，避免循环导入
try:
    from ..string_types.results import MultiMatchResult, BatchMatchResult, MatchResult, AnalysisReport
    from ..string_types.enums import ProcessingMode
except ImportError:
    # 处理独立运行的情况
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)
    
    from string_types.results import MultiMatchResult, BatchMatchResult, MatchResult, AnalysisReport
    from string_types.enums import ProcessingMode


class MultiResultProcessor:
    """
    多结果处理器 - 批量处理多个匹配结果
    """
    
    def __init__(self, mode: ProcessingMode = ProcessingMode.BATCH):
        """初始化处理器
        
        Args:
            mode: 处理模式
        """
        self.mode = mode
        self.results: List[MultiMatchResult] = []
    
    def add_result(self, result: MultiMatchResult) -> 'MultiResultProcessor':
        """添加匹配结果
        
        Args:
            result: 多目标匹配结果
            
        Returns:
            MultiResultProcessor: 返回自身以支持链式调用
        """
        self.results.append(result)
        return self
    
    def add_results(self, results: List[MultiMatchResult]) -> 'MultiResultProcessor':
        """批量添加匹配结果
        
        Args:
            results: 多目标匹配结果列表
            
        Returns:
            MultiResultProcessor: 返回自身以支持链式调用
        """
        self.results.extend(results)
        return self
    
    def process_all(self) -> BatchMatchResult:
        """处理所有结果
        
        Returns:
            BatchMatchResult: 批量处理结果
        """
        if not self.results:
            return BatchMatchResult()
        
        # 收集源字符串
        source_strings = [r.source_string for r in self.results]
        
        # 计算统计信息
        success_count = sum(1 for r in self.results if r.is_complete)
        failure_count = len(self.results) - success_count
        total_processed = len(self.results)
        
        # 计算平均分数
        if self.results:
            average_score = sum(r.overall_score for r in self.results) / total_processed
        else:
            average_score = 0.0
        
        # 创建处理摘要
        processing_summary = {
            "processing_mode": self.mode.value,
            "best_result": max(self.results, key=lambda r: r.overall_score) if self.results else None,
            "worst_result": min(self.results, key=lambda r: r.overall_score) if self.results else None
        }
        
        return BatchMatchResult(
            source_strings=source_strings,
            results=self.results,
            success_count=success_count,
            failure_count=failure_count,
            total_processed=total_processed,
            average_score=average_score,
            processing_summary=processing_summary
        )
    
    def get_successful_results(self) -> List[MultiMatchResult]:
        """获取成功的匹配结果"""
        return [r for r in self.results if r.is_complete]
    
    def get_failed_results(self) -> List[MultiMatchResult]:
        """获取失败的匹配结果"""
        return [r for r in self.results if not r.is_complete]
    
    def get_top_results(self, n: int = 10) -> List[MultiMatchResult]:
        """获取评分最高的n个结果"""
        return sorted(self.results, key=lambda r: r.overall_score, reverse=True)[:n]
    
    def get_results_by_score_range(self, min_score: float, max_score: float = 1.0) -> List[MultiMatchResult]:
        """根据分数范围筛选结果"""
        return [r for r in self.results if min_score <= r.overall_score <= max_score]
    
    def clear(self) -> 'MultiResultProcessor':
        """清空所有结果"""
        self.results.clear()
        return self


class ResultAnalyzer:
    """
    结果分析器 - 深度分析多个匹配结果
    """
    
    def __init__(self, results: List[MultiMatchResult]):
        """初始化分析器
        
        Args:
            results: 要分析的多目标匹配结果列表
        """
        self.results = results
    
    def analyze(self) -> AnalysisReport:
        """全面分析多个匹配结果
        
        Returns:
            AnalysisReport: 分析报告
        """
        if not self.results:
            return AnalysisReport()
        
        # 基础统计
        total_processed = len(self.results)
        successful_matches = sum(1 for r in self.results if r.is_complete)
        failed_matches = total_processed - successful_matches
        
        # 分数统计
        scores = [r.overall_score for r in self.results]
        average_score = sum(scores) / len(scores)
        best_score = max(scores)
        worst_score = min(scores)
        
        # 分数分布
        score_distribution = self._calculate_score_distribution(scores)
        
        # 目标统计
        target_statistics = self._calculate_target_statistics()
        
        # 性能指标
        performance_metrics = self._calculate_performance_metrics()
        
        # 生成建议
        recommendations = self._generate_recommendations()
        
        return AnalysisReport(
            total_processed=total_processed,
            successful_matches=successful_matches,
            failed_matches=failed_matches,
            average_score=average_score,
            best_score=best_score,
            worst_score=worst_score,
            score_distribution=score_distribution,
            target_statistics=target_statistics,
            performance_metrics=performance_metrics,
            recommendations=recommendations
        )
    
    def _calculate_score_distribution(self, scores: List[float]) -> Dict[str, int]:
        """计算分数分布"""
        distribution = {
            "excellent": 0,  # 0.9-1.0
            "good": 0,       # 0.8-0.9
            "fair": 0,       # 0.6-0.8
            "poor": 0,       # 0.4-0.6
            "very_poor": 0   # 0.0-0.4
        }
        
        for score in scores:
            if score >= 0.9:
                distribution["excellent"] += 1
            elif score >= 0.8:
                distribution["good"] += 1
            elif score >= 0.6:
                distribution["fair"] += 1
            elif score >= 0.4:
                distribution["poor"] += 1
            else:
                distribution["very_poor"] += 1
        
        return distribution
    
    def _calculate_target_statistics(self) -> Dict[str, Dict[str, Any]]:
        """计算目标统计信息"""
        target_stats = {}
        
        # 收集所有目标名称
        all_targets = set()
        for result in self.results:
            all_targets.update(result.matches.keys())
        
        # 为每个目标计算统计信息
        for target in all_targets:
            matches = []
            for result in self.results:
                if target in result.matches:
                    match = result.matches[target]
                    if match.is_matched:
                        matches.append(match)
            
            if matches:
                scores = [m.similarity_score for m in matches]
                target_stats[target] = {
                    "total_matches": len(matches),
                    "success_rate": len(matches) / len(self.results),
                    "average_score": sum(scores) / len(scores),
                    "best_score": max(scores),
                    "worst_score": min(scores)
                }
            else:
                target_stats[target] = {
                    "total_matches": 0,
                    "success_rate": 0.0,
                    "average_score": 0.0,
                    "best_score": 0.0,
                    "worst_score": 0.0
                }
        
        return target_stats
    
    def _calculate_performance_metrics(self) -> Dict[str, float]:
        """计算性能指标"""
        if not self.results:
            return {}
        
        # 完整匹配率
        completeness_scores = [r.completeness_ratio for r in self.results if hasattr(r, 'completeness_ratio')]
        avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0.0
        
        # 加权平均分数
        weighted_scores = [r.weighted_score for r in self.results if hasattr(r, 'weighted_score')]
        avg_weighted_score = sum(weighted_scores) / len(weighted_scores) if weighted_scores else 0.0
        
        return {
            "average_completeness": avg_completeness,
            "average_weighted_score": avg_weighted_score,
            "success_rate": sum(1 for r in self.results if r.is_complete) / len(self.results)
        }
    
    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if not self.results:
            return ["没有可分析的结果"]
        
        success_rate = sum(1 for r in self.results if r.is_complete) / len(self.results)
        avg_score = sum(r.overall_score for r in self.results) / len(self.results)
        
        if success_rate < 0.5:
            recommendations.append("成功率较低，建议检查目标配置和匹配策略")
        
        if avg_score < 0.6:
            recommendations.append("平均分数较低，建议调整模糊匹配阈值")
        
        # 检查目标统计
        target_stats = self._calculate_target_statistics()
        poor_targets = [name for name, stats in target_stats.items() 
                       if stats["success_rate"] < 0.3]
        
        if poor_targets:
            recommendations.append(f"以下目标表现较差，建议优化: {', '.join(poor_targets)}")
        
        return recommendations
    
    def _generate_analysis_summary(self) -> Dict[str, Any]:
        """生成分析摘要"""
        if not self.results:
            return {"message": "没有结果可分析"}
            
        total_processed = len(self.results)
        successful_matches = sum(1 for r in self.results if r.is_complete)
        
        scores = [r.overall_score for r in self.results]
        
        return {
            "total_processed": total_processed,
            "successful_matches": successful_matches,
            "success_rate": successful_matches / total_processed,
            "average_score": sum(scores) / len(scores),
            "best_score": max(scores),
            "worst_score": min(scores),
            "summary": f"处理了 {total_processed} 个结果，成功率 {successful_matches/total_processed:.2%}"
        }
    
    @staticmethod
    def analyze_batch_results(results: List[MultiMatchResult]) -> Dict[str, Any]:
        """静态方法：分析批量结果"""
        if not results:
            return {"message": "没有结果可分析", "analysis": {}}
            
        analyzer = ResultAnalyzer(results)
        return analyzer._generate_analysis_summary()
    
    @staticmethod
    def find_patterns(results: List[MultiMatchResult]) -> Dict[str, Any]:
        """静态方法：查找模式"""
        if not results:
            return {"common_failures": [], "frequent_targets": {}, "score_ranges": {}}
            
        # 找出常见失败模式
        common_failures = []
        all_missing = []
        for result in results:
            all_missing.extend(result.missing_targets)
        
        # 统计频繁出现的目标
        from collections import Counter
        frequent_targets = dict(Counter(target for result in results for target in result.matches.keys()))
        
        # 分数范围分析
        scores = [r.overall_score for r in results]
        score_ranges = {
            "min": min(scores) if scores else 0,
            "max": max(scores) if scores else 0,
            "avg": sum(scores) / len(scores) if scores else 0
        }
        
        return {
            "common_failures": list(set(all_missing)),
            "frequent_targets": frequent_targets,
            "score_ranges": score_ranges
        }
    
    @staticmethod
    def generate_report(results: List[MultiMatchResult], include_patterns: bool = False) -> str:
        """静态方法：生成分析报告"""
        if not results:
            return "没有结果可分析"
            
        analyzer = ResultAnalyzer(results)
        analysis = analyzer._generate_analysis_summary()
        
        report = f"分析报告\\n"
        report += f"总结果数: {len(results)}\\n"
        report += f"成功率: {analysis.get('success_rate', 0):.2%}\\n"
        
        if include_patterns:
            patterns = ResultAnalyzer.find_patterns(results)
            report += f"\\n模式分析:\\n"
            report += f"常见目标: {list(patterns['frequent_targets'].keys())}\\n"
            
        return report


class ResultExporter:
    """
    结果导出器
    """
    
    @staticmethod
    def export_to_json(results: List[MultiMatchResult], filepath: str = None) -> str:
        """导出为JSON格式"""
        data = {
            "total_results": len(results),
            "results": [r.to_dict() for r in results]
        }
        
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_str)
        
        return json_str
    
    @staticmethod
    def export_summary(results: List[MultiMatchResult]) -> Dict[str, Any]:
        """导出摘要信息"""
        if not results:
            return {"message": "没有结果可导出"}
        
        success_count = sum(1 for r in results if r.is_complete)
        avg_score = sum(r.overall_score for r in results) / len(results)
        
        return {
            "total_results": len(results),
            "successful_results": success_count,
            "success_rate": success_count / len(results),
            "average_score": avg_score,
            "best_score": max(r.overall_score for r in results),
            "worst_score": min(r.overall_score for r in results)
        }
    
    @staticmethod
    def to_csv_row(result: MultiMatchResult) -> List[str]:
        """将单个结果转换为CSV行"""
        return [result.source_string, str(result.overall_score), str(result.is_complete), str(result.match_count)]
    
    @staticmethod
    def to_csv_batch(results: List[MultiMatchResult]) -> List[List[str]]:
        """将批量结果转换为CSV"""
        if not results:
            return [["source_string", "overall_score", "is_complete", "match_count"]]
            
        data = [["source_string", "overall_score", "is_complete", "match_count"]]
        data.extend([ResultExporter.to_csv_row(result) for result in results])
        return data
    
    @staticmethod
    def to_json(result: MultiMatchResult) -> str:
        """将单个结果转换为JSON"""
        return json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
    
    @staticmethod
    def to_markdown(result: MultiMatchResult) -> str:
        """将单个结果转换为Markdown"""
        md = f"# 匹配结果\\n\\n"
        md += f"**源字符串**: {result.source_string}\\n\\n"
        md += f"**总体分数**: {result.overall_score:.3f}\\n\\n"
        md += f"**是否完整**: {'是' if result.is_complete else '否'}\\n\\n"
        
        if result.matches:
            md += "## 匹配详情\\n\\n"
            for name, match in result.matches.items():
                md += f"- **{name}**: {match.matched_string or 'N/A'} (分数: {match.similarity_score:.3f})\\n"
        
        return md


# 导出接口
__all__ = [
    'MultiMatchResult',
    'BatchMatchResult', 
    'MatchResult',
    'AnalysisReport',
    'MultiResultProcessor',
    'ResultAnalyzer',
    'ResultExporter'
]
