# -*- coding: utf-8 -*-
"""
多结果匹配处理模块 - 批量处理多个匹配结果
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import json

# 导入基础匹配结果类
try:
    from ..base_matcher import MatchResult
except ImportError:
    # 如果导入失败，使用本地定义
    from dataclasses import dataclass
    
    @dataclass
    class MatchResult:
        """基础匹配结果类"""
        matched_string: str = ""
        similarity_score: float = 0.0
        match_type: str = "none"
        confidence: float = 0.0
        is_matched: bool = False


@dataclass
class MultiMatchResult:
    """
    多匹配结果类 - 管理多个目标的匹配结果
    """
    source_string: str  # 源字符串
    
    # 匹配结果字典
    matches: Dict[str, MatchResult] = field(default_factory=dict)
    
    # 整体评估
    overall_score: float = 0.0
    is_complete: bool = False
    missing_targets: List[str] = field(default_factory=list)
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_match(self, target_name: str) -> Optional[MatchResult]:
        """
        获取指定目标的匹配结果
        
        Args:
            target_name: 目标名称
            
        Returns:
            Optional[MatchResult]: 匹配结果，未找到返回None
        """
        return self.matches.get(target_name)

    def get_matched_value(self, target_name: str) -> Optional[str]:
        """
        获取指定目标的匹配值
        
        Args:
            target_name: 目标名称
            
        Returns:
            Optional[str]: 匹配的字符串，未匹配返回None
        """
        match = self.get_match(target_name)
        return match.matched_string if match else None

    def has_match(self, target_name: str) -> bool:
        """
        检查指定目标是否匹配成功
        
        Args:
            target_name: 目标名称
            
        Returns:
            bool: 是否匹配成功
        """
        match = self.get_match(target_name)
        return match is not None and match.is_matched

    def get_match_score(self, target_name: str) -> float:
        """
        获取指定目标的匹配分数
        
        Args:
            target_name: 目标名称
            
        Returns:
            float: 匹配分数，未找到返回0.0
        """
        match = self.get_match(target_name)
        return match.similarity_score if match else 0.0

    def get_matched_targets(self) -> List[str]:
        """获取所有匹配成功的目标名称"""
        return [name for name, match in self.matches.items() if match.is_matched]

    def get_failed_targets(self) -> List[str]:
        """获取所有匹配失败的目标名称"""
        return [name for name, match in self.matches.items() if not match.is_matched]

    def get_summary(self) -> Dict[str, Any]:
        """获取匹配结果摘要"""
        return {
            'source': self.source_string,
            'overall_score': self.overall_score,
            'is_complete': self.is_complete,
            'matched_count': len(self.get_matched_targets()),
            'total_targets': len(self.matches),
            'missing_targets': self.missing_targets,
            'matched_values': {
                name: self.get_matched_value(name) 
                for name in self.get_matched_targets()
            }
        }

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'source_string': self.source_string,
            'matches': {
                name: {
                    'matched_string': match.matched_string,
                    'similarity_score': match.similarity_score,
                    'match_type': match.match_type,
                    'confidence': match.confidence,
                    'is_matched': match.is_matched
                }
                for name, match in self.matches.items()
            },
            'overall_score': self.overall_score,
            'is_complete': self.is_complete,
            'missing_targets': self.missing_targets,
            'metadata': self.metadata
        }

    def to_json(self, indent: int = 2) -> str:
        """转换为JSON"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def __str__(self) -> str:
        """字符串表示"""
        matched = len(self.get_matched_targets())
        total = len(self.matches)
        return (f"MultiMatchResult('{self.source_string[:30]}...', "
                f"score={self.overall_score:.3f}, "
                f"matched={matched}/{total}, "
                f"complete={self.is_complete})")


class ResultAnalyzer:
    """
    结果分析器 - 批量分析多个匹配结果
    """

    @staticmethod
    def analyze_batch_results(results: List[MultiMatchResult]) -> Dict[str, Any]:
        """
        批量分析匹配结果
        
        Args:
            results: 匹配结果列表
            
        Returns:
            Dict[str, Any]: 分析报告
        """
        if not results:
            return {
                'summary': {'total_count': 0, 'complete_count': 0, 'complete_rate': 0.0, 'avg_score': 0.0},
                'score_distribution': {'high': 0, 'medium': 0, 'low': 0},
                'target_statistics': {},
                'best_match': None,
                'worst_match': None
            }

        total_count = len(results)
        complete_count = sum(1 for r in results if r.is_complete)
        avg_score = sum(r.overall_score for r in results) / total_count

        # 使用集合操作优化性能
        all_targets = set()
        for result in results:
            all_targets.update(result.matches.keys())

        # 批量计算目标统计
        target_stats = {}
        for target in all_targets:
            target_results = [r for r in results if target in r.matches]
            matched_count = sum(1 for r in target_results if r.has_match(target))
            total_score = sum(r.get_match_score(target) for r in target_results)
            
            target_stats[target] = {
                'match_rate': matched_count / len(target_results) if target_results else 0,
                'avg_score': total_score / len(target_results) if target_results else 0,
                'matched_count': matched_count
            }

        # 分数分布统计
        score_distribution = {'high': 0, 'medium': 0, 'low': 0}
        for result in results:
            if result.overall_score >= 0.7:
                score_distribution['high'] += 1
            elif result.overall_score >= 0.4:
                score_distribution['medium'] += 1
            else:
                score_distribution['low'] += 1

        # 找到最好和最差的匹配
        best_match = max(results, key=lambda r: r.overall_score)
        worst_match = min(results, key=lambda r: r.overall_score)

        return {
            'summary': {
                'total_count': total_count,
                'complete_count': complete_count,
                'complete_rate': complete_count / total_count,
                'avg_score': avg_score
            },
            'score_distribution': score_distribution,
            'target_statistics': target_stats,
            'best_match': {
                'source': best_match.source_string,
                'score': best_match.overall_score,
                'matched_values': {
                    name: best_match.get_matched_value(name)
                    for name in best_match.get_matched_targets()
                }
            },
            'worst_match': {
                'source': worst_match.source_string,
                'score': worst_match.overall_score,
                'missing_targets': worst_match.missing_targets
            }
        }

    @staticmethod
    def find_patterns(results: List[MultiMatchResult]) -> Dict[str, Any]:
        """
        查找匹配模式
        
        Args:
            results: 匹配结果列表
            
        Returns:
            Dict[str, Any]: 模式分析报告
        """
        patterns = {
            'common_failures': {},
            'frequent_targets': {},
            'score_ranges': {
                'high': [],    # 0.8-1.0
                'medium': [],  # 0.5-0.8
                'low': []      # 0.0-0.5
            }
        }

        # 常见失败模式
        for result in results:
            if not result.is_complete:
                failure_key = tuple(sorted(result.missing_targets))
                patterns['common_failures'][failure_key] = \
                    patterns['common_failures'].get(failure_key, 0) + 1

        # 频繁匹配目标
        for result in results:
            for target in result.get_matched_targets():
                patterns['frequent_targets'][target] = \
                    patterns['frequent_targets'].get(target, 0) + 1

        # 分数范围分布
        for result in results:
            if result.overall_score >= 0.8:
                patterns['score_ranges']['high'].append(result.source_string)
            elif result.overall_score >= 0.5:
                patterns['score_ranges']['medium'].append(result.source_string)
            else:
                patterns['score_ranges']['low'].append(result.source_string)

        return patterns

    @staticmethod
    def generate_report(results: List[MultiMatchResult], include_patterns: bool = True) -> str:
        """
        生成分析报告
        
        Args:
            results: 匹配结果列表
            include_patterns: 是否包含模式分析
            
        Returns:
            str: 分析报告
        """
        analysis = ResultAnalyzer.analyze_batch_results(results)
        report = []
        
        report.append("批量匹配结果分析报告")
        report.append("=" * 50)

        # 总体统计
        summary = analysis['summary']
        report.append(f"\n总体统计:")
        report.append(f"  结果总数: {summary['total_count']}")
        report.append(f"  完全匹配: {summary['complete_count']} ({summary['complete_rate']:.1%})")
        report.append(f"  平均分数: {summary['avg_score']:.3f}")

        # 分数分布
        dist = analysis['score_distribution']
        report.append(f"\n分数分布:")
        report.append(f"  高分(>=0.7): {dist['high']} 个")
        report.append(f"  中分(0.4-0.7): {dist['medium']} 个")
        report.append(f"  低分(<0.4): {dist['low']} 个")

        # 目标统计
        report.append(f"\n目标匹配统计:")
        for target, stats in analysis['target_statistics'].items():
            report.append(f"  {target}: {stats['match_rate']:.1%} "
                         f"(平均分数: {stats['avg_score']:.3f})")

        # 最佳匹配
        best = analysis['best_match']
        report.append(f"\n最佳匹配:")
        report.append(f"  源字符串: {best['source']}")
        report.append(f"  匹配分数: {best['score']:.3f}")
        report.append(f"  匹配结果: {best['matched_values']}")

        # 最差匹配
        worst = analysis['worst_match']
        report.append(f"\n最差匹配:")
        report.append(f"  源字符串: {worst['source']}")
        report.append(f"  匹配分数: {worst['score']:.3f}")
        report.append(f"  缺失目标: {worst['missing_targets']}")

        # 模式分析
        if include_patterns:
            patterns = ResultAnalyzer.find_patterns(results)
            report.append(f"\n模式分析:")
            
            if patterns['common_failures']:
                report.append("  常见失败模式:")
                for failure, count in patterns['common_failures'].items():
                    report.append(f"    {list(failure)}: {count} 次")
            
            report.append(f"  高分结果 (≥0.8): {len(patterns['score_ranges']['high'])}")
            report.append(f"  中等结果 (0.5-0.8): {len(patterns['score_ranges']['medium'])}")
            report.append(f"  低分结果 (<0.5): {len(patterns['score_ranges']['low'])}")

        return "\n".join(report)


class ResultExporter:
    """
    结果导出器 - 导出多种格式的结果
    """

    @staticmethod
    def to_csv(results: List[MultiMatchResult], target_names: List[str]) -> str:
        """
        导出为CSV格式
        
        Args:
            results: 匹配结果列表
            target_names: 目标名称列表
            
        Returns:
            str: CSV格式的字符串
        """
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        headers = ['source_string', 'overall_score', 'is_complete'] + target_names
        writer.writerow(headers)
        
        # 写入数据
        for result in results:
            row = [
                result.source_string,
                result.overall_score,
                result.is_complete
            ]
            for target in target_names:
                value = result.get_matched_value(target)
                row.append(value if value is not None else '')
            writer.writerow(row)
        
        return output.getvalue()

    @staticmethod
    def to_excel_data(results: List[MultiMatchResult], target_names: List[str]) -> Dict[str, List[List[Any]]]:
        """
        准备Excel导出数据
        
        Args:
            results: 匹配结果列表
            target_names: 目标名称列表
            
        Returns:
            Dict[str, List[List[Any]]]: Excel工作表数据
        """
        # 主数据表
        main_data = []
        main_data.append(['源字符串', '总分', '完整性'] + target_names)
        
        for result in results:
            row = [
                result.source_string,
                result.overall_score,
                '完整' if result.is_complete else '不完整'
            ]
            for target in target_names:
                value = result.get_matched_value(target)
                row.append(value if value is not None else '')
            main_data.append(row)

        # 统计数据表
        analysis = ResultAnalyzer.analyze_batch_results(results)
        stats_data = []
        stats_data.append(['统计项', '数值'])
        stats_data.append(['结果总数', analysis['summary']['total_count']])
        stats_data.append(['完全匹配数', analysis['summary']['complete_count']])
        stats_data.append(['完全匹配率', f"{analysis['summary']['complete_rate']:.1%}"])
        stats_data.append(['平均分数', f"{analysis['summary']['avg_score']:.3f}"])

        return {
            '匹配结果': main_data,
            '统计信息': stats_data
        }

    @staticmethod
    def to_csv_row(result: MultiMatchResult) -> List[str]:
        """
        转换单个结果为CSV行
        
        Args:
            result: 匹配结果
            
        Returns:
            List[str]: CSV行数据
        """
        return [
            result.source_string,
            str(result.overall_score),
            str(result.is_complete),
            str(len(result.get_matched_targets())),
            str(len(result.matches)),
            ';'.join(result.missing_targets) if result.missing_targets else '',
            ';'.join([f"{k}:{v.matched_string}" for k, v in result.matches.items() if v.is_matched])
        ]

    @staticmethod
    def get_csv_headers() -> List[str]:
        """
        获取CSV表头
        
        Returns:
            List[str]: CSV表头
        """
        return [
            'source_string',
            'overall_score', 
            'is_complete',
            'matched_count',
            'total_targets',
            'missing_targets',
            'matched_values'
        ]

    @staticmethod
    def to_csv_batch(results: List[MultiMatchResult]) -> List[List[str]]:
        """
        批量转换为CSV数据
        
        Args:
            results: 匹配结果列表
            
        Returns:
            List[List[str]]: CSV数据（包含表头）
        """
        csv_data = [ResultExporter.get_csv_headers()]
        for result in results:
            csv_data.append(ResultExporter.to_csv_row(result))
        return csv_data

    @staticmethod
    def to_markdown(result: MultiMatchResult, include_analysis: bool = True) -> str:
        """
        转换为Markdown格式
        
        Args:
            result: 匹配结果
            include_analysis: 是否包含分析信息
            
        Returns:
            str: Markdown格式的字符串
        """
        md = []
        
        # 标题
        status_symbol = "[完整]" if result.is_complete else "[部分]"
        md.append(f"## {status_symbol} 多目标匹配结果")
        md.append("")
        
        # 基础信息
        md.append("### 基础信息")
        md.append(f"- **源字符串**: `{result.source_string}`")
        md.append(f"- **总体分数**: {result.overall_score:.3f}")
        md.append(f"- **匹配状态**: {'完整匹配' if result.is_complete else '部分匹配'}")
        md.append(f"- **匹配数量**: {len(result.get_matched_targets())}/{len(result.matches)}")
        md.append("")
        
        # 匹配详情
        md.append("### 匹配详情")
        for name, match in result.matches.items():
            status = "匹配" if match.is_matched else "未匹配"
            value = match.matched_string if match.matched_string else "N/A"
            score = match.similarity_score
            md.append(f"- **{name}**: {status} | `{value}` | 分数: {score:.3f}")
        md.append("")
        
        # 缺失目标
        if result.missing_targets:
            md.append("### 缺失目标")
            for target in result.missing_targets:
                md.append(f"- {target}")
            md.append("")
        
        return "\n".join(md)

    @staticmethod
    def to_json(result: MultiMatchResult, indent: int = 2) -> str:
        """
        转换为JSON格式
        
        Args:
            result: 匹配结果
            indent: 缩进级别
            
        Returns:
            str: JSON格式的字符串
        """
        import json
        return json.dumps(result.to_dict(), indent=indent, ensure_ascii=False)
