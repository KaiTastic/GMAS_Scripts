#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码评估器 - 对多目标字符串匹配器进行全面的代码质量评估
"""

import ast
import os
import time
import inspect
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path


class QualityLevel(Enum):
    """代码质量等级"""
    EXCELLENT = "优秀"
    GOOD = "良好"
    FAIR = "一般"
    POOR = "较差"
    CRITICAL = "严重"


@dataclass
class CodeMetrics:
    """代码指标"""
    lines_of_code: int
    lines_of_comments: int
    blank_lines: int
    cyclomatic_complexity: int
    functions_count: int
    classes_count: int
    imports_count: int
    docstring_coverage: float
    test_coverage: float = 0.0


@dataclass
class QualityIssue:
    """质量问题"""
    severity: QualityLevel
    category: str
    description: str
    file_path: str
    line_number: int = 0
    suggestion: str = ""


class TestEvaluator:
    """测试评估器
    
    对代码进行多维度的质量评估
    """
    
    def __init__(self, project_root: str):
        """初始化评估器
        
        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root)
        self.code_metrics: Dict[str, CodeMetrics] = {}
        self.quality_issues: List[QualityIssue] = []
        self.evaluation_results: Dict[str, Any] = {}
        
    def evaluate_project(self) -> Dict[str, Any]:
        """评估整个项目
        
        Returns:
            Dict[str, Any]: 评估结果
        """
        print("🔍 开始代码质量评估...")
        
        # 1. 收集代码指标
        self._collect_code_metrics()
        
        # 2. 分析代码质量问题
        self._analyze_quality_issues()
        
        # 3. 评估测试覆盖率
        self._evaluate_test_coverage()
        
        # 4. 生成评估报告
        report = self._generate_evaluation_report()
        
        self.evaluation_results = report
        return report
    
    def _collect_code_metrics(self):
        """收集代码指标"""
        print("📊 收集代码指标...")
        
        python_files = list(self.project_root.glob("**/*.py"))
        
        for file_path in python_files:
            if self._should_analyze_file(file_path):
                metrics = self._analyze_file_metrics(file_path)
                self.code_metrics[str(file_path)] = metrics
    
    def _should_analyze_file(self, file_path: Path) -> bool:
        """判断是否应该分析文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否分析
        """
        # 跳过缓存文件和测试数据
        exclude_patterns = ['__pycache__', '.pyc', 'test_data', '.git']
        
        for pattern in exclude_patterns:
            if pattern in str(file_path):
                return False
        
        return True
    
    def _analyze_file_metrics(self, file_path: Path) -> CodeMetrics:
        """分析单个文件的指标
        
        Args:
            file_path: 文件路径
            
        Returns:
            CodeMetrics: 文件指标
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.splitlines()
            total_lines = len(lines)
            
            # 计算注释行和空行
            comment_lines = 0
            blank_lines = 0
            
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    blank_lines += 1
                elif stripped.startswith('#'):
                    comment_lines += 1
            
            code_lines = total_lines - comment_lines - blank_lines
            
            # 解析AST
            try:
                tree = ast.parse(content)
                
                functions_count = len([n for n in ast.walk(tree) 
                                     if isinstance(n, ast.FunctionDef)])
                classes_count = len([n for n in ast.walk(tree) 
                                   if isinstance(n, ast.ClassDef)])
                imports_count = len([n for n in ast.walk(tree) 
                                   if isinstance(n, (ast.Import, ast.ImportFrom))])
                
                # 计算圈复杂度（简化版）
                complexity = self._calculate_complexity(tree)
                
                # 计算文档字符串覆盖率
                docstring_coverage = self._calculate_docstring_coverage(tree)
                
            except SyntaxError:
                # 语法错误时使用默认值
                functions_count = 0
                classes_count = 0
                imports_count = 0
                complexity = 1
                docstring_coverage = 0.0
            
            return CodeMetrics(
                lines_of_code=code_lines,
                lines_of_comments=comment_lines,
                blank_lines=blank_lines,
                cyclomatic_complexity=complexity,
                functions_count=functions_count,
                classes_count=classes_count,
                imports_count=imports_count,
                docstring_coverage=docstring_coverage
            )
            
        except Exception as e:
            print(f"警告: 分析文件 {file_path} 时出错: {e}")
            return CodeMetrics(0, 0, 0, 1, 0, 0, 0, 0.0)
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """计算圈复杂度
        
        Args:
            tree: AST树
            
        Returns:
            int: 圈复杂度
        """
        complexity = 1  # 基础复杂度
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor,
                               ast.ExceptHandler, ast.With, ast.AsyncWith)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _calculate_docstring_coverage(self, tree: ast.AST) -> float:
        """计算文档字符串覆盖率
        
        Args:
            tree: AST树
            
        Returns:
            float: 覆盖率百分比
        """
        documentable_items = []
        documented_items = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                documentable_items.append(node)
                
                # 检查是否有文档字符串
                if (node.body and isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Constant) and 
                    isinstance(node.body[0].value.value, str)):
                    documented_items.append(node)
        
        if not documentable_items:
            return 100.0  # 没有可文档化的项目
        
        return (len(documented_items) / len(documentable_items)) * 100
    
    def _analyze_quality_issues(self):
        """分析代码质量问题"""
        print("🔍 分析代码质量问题...")
        
        for file_path, metrics in self.code_metrics.items():
            self._check_file_quality(file_path, metrics)
    
    def _check_file_quality(self, file_path: str, metrics: CodeMetrics):
        """检查单个文件的质量问题
        
        Args:
            file_path: 文件路径
            metrics: 文件指标
        """
        # 检查文件大小
        if metrics.lines_of_code > 500:
            self.quality_issues.append(QualityIssue(
                severity=QualityLevel.FAIR,
                category="代码结构",
                description=f"文件过大: {metrics.lines_of_code} 行代码",
                file_path=file_path,
                suggestion="考虑将大文件拆分为多个小文件"
            ))
        
        # 检查复杂度
        if metrics.cyclomatic_complexity > 20:
            self.quality_issues.append(QualityIssue(
                severity=QualityLevel.POOR,
                category="代码复杂度",
                description=f"圈复杂度过高: {metrics.cyclomatic_complexity}",
                file_path=file_path,
                suggestion="简化逻辑结构，拆分复杂函数"
            ))
        elif metrics.cyclomatic_complexity > 10:
            self.quality_issues.append(QualityIssue(
                severity=QualityLevel.FAIR,
                category="代码复杂度",
                description=f"圈复杂度较高: {metrics.cyclomatic_complexity}",
                file_path=file_path,
                suggestion="考虑重构复杂的逻辑结构"
            ))
        
        # 检查文档覆盖率
        if metrics.docstring_coverage < 50:
            self.quality_issues.append(QualityIssue(
                severity=QualityLevel.FAIR,
                category="文档质量",
                description=f"文档覆盖率低: {metrics.docstring_coverage:.1f}%",
                file_path=file_path,
                suggestion="增加函数和类的文档字符串"
            ))
        
        # 检查注释比例
        total_lines = metrics.lines_of_code + metrics.lines_of_comments + metrics.blank_lines
        if total_lines > 0:
            comment_ratio = metrics.lines_of_comments / total_lines
            if comment_ratio < 0.1 and metrics.lines_of_code > 50:
                self.quality_issues.append(QualityIssue(
                    severity=QualityLevel.FAIR,
                    category="代码可读性",
                    description=f"注释较少: {comment_ratio:.1%}",
                    file_path=file_path,
                    suggestion="增加必要的注释以提高代码可读性"
                ))
    
    def _evaluate_test_coverage(self):
        """评估测试覆盖率"""
        print("🧪 评估测试覆盖率...")
        
        # 统计测试文件和源代码文件
        test_files = []
        source_files = []
        
        for file_path in self.code_metrics.keys():
            path = Path(file_path)
            if 'test' in path.name or 'tests' in str(path):
                test_files.append(file_path)
            else:
                source_files.append(file_path)
        
        # 计算测试覆盖率（简化估算）
        if source_files:
            test_ratio = len(test_files) / len(source_files)
            avg_test_coverage = min(test_ratio * 100, 100)
            
            # 更新所有文件的测试覆盖率
            for file_path in self.code_metrics:
                self.code_metrics[file_path].test_coverage = avg_test_coverage
            
            # 检查测试覆盖率
            if avg_test_coverage < 50:
                self.quality_issues.append(QualityIssue(
                    severity=QualityLevel.POOR,
                    category="测试质量",
                    description=f"测试覆盖率不足: {avg_test_coverage:.1f}%",
                    file_path="项目整体",
                    suggestion="增加更多的单元测试和集成测试"
                ))
    
    def _generate_evaluation_report(self) -> Dict[str, Any]:
        """生成评估报告
        
        Returns:
            Dict[str, Any]: 评估报告
        """
        print("📋 生成评估报告...")
        
        # 汇总统计
        total_metrics = self._aggregate_metrics()
        
        # 按严重程度分类问题
        issues_by_severity = {}
        for issue in self.quality_issues:
            severity = issue.severity.value
            if severity not in issues_by_severity:
                issues_by_severity[severity] = []
            issues_by_severity[severity].append(issue)
        
        # 计算整体质量分数
        quality_score = self._calculate_quality_score(total_metrics, issues_by_severity)
        
        # 生成建议
        recommendations = self._generate_recommendations(issues_by_severity)
        
        report = {
            'evaluation_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'project_metrics': {
                'total_files': len(self.code_metrics),
                'total_lines_of_code': total_metrics.lines_of_code,
                'total_lines_of_comments': total_metrics.lines_of_comments,
                'total_functions': total_metrics.functions_count,
                'total_classes': total_metrics.classes_count,
                'average_complexity': total_metrics.cyclomatic_complexity / len(self.code_metrics) if self.code_metrics else 0,
                'average_docstring_coverage': total_metrics.docstring_coverage / len(self.code_metrics) if self.code_metrics else 0,
                'estimated_test_coverage': total_metrics.test_coverage
            },
            'quality_score': quality_score,
            'quality_level': self._get_quality_level(quality_score),
            'issues_summary': {
                'total_issues': len(self.quality_issues),
                'by_severity': {severity: len(issues) for severity, issues in issues_by_severity.items()}
            },
            'detailed_issues': [
                {
                    'severity': issue.severity.value,
                    'category': issue.category,
                    'description': issue.description,
                    'file': os.path.basename(issue.file_path),
                    'line': issue.line_number,
                    'suggestion': issue.suggestion
                }
                for issue in self.quality_issues
            ],
            'recommendations': recommendations,
            'file_metrics': {
                os.path.basename(path): {
                    'lines_of_code': metrics.lines_of_code,
                    'complexity': metrics.cyclomatic_complexity,
                    'docstring_coverage': metrics.docstring_coverage,
                    'functions': metrics.functions_count,
                    'classes': metrics.classes_count
                }
                for path, metrics in self.code_metrics.items()
            }
        }
        
        return report
    
    def _aggregate_metrics(self) -> CodeMetrics:
        """汇总所有文件的指标
        
        Returns:
            CodeMetrics: 汇总指标
        """
        if not self.code_metrics:
            return CodeMetrics(0, 0, 0, 0, 0, 0, 0, 0.0, 0.0)
        
        total_loc = sum(m.lines_of_code for m in self.code_metrics.values())
        total_comments = sum(m.lines_of_comments for m in self.code_metrics.values())
        total_blank = sum(m.blank_lines for m in self.code_metrics.values())
        total_complexity = sum(m.cyclomatic_complexity for m in self.code_metrics.values())
        total_functions = sum(m.functions_count for m in self.code_metrics.values())
        total_classes = sum(m.classes_count for m in self.code_metrics.values())
        total_imports = sum(m.imports_count for m in self.code_metrics.values())
        
        avg_docstring = sum(m.docstring_coverage for m in self.code_metrics.values()) / len(self.code_metrics)
        avg_test_coverage = sum(m.test_coverage for m in self.code_metrics.values()) / len(self.code_metrics)
        
        return CodeMetrics(
            lines_of_code=total_loc,
            lines_of_comments=total_comments,
            blank_lines=total_blank,
            cyclomatic_complexity=total_complexity,
            functions_count=total_functions,
            classes_count=total_classes,
            imports_count=total_imports,
            docstring_coverage=avg_docstring,
            test_coverage=avg_test_coverage
        )
    
    def _calculate_quality_score(self, metrics: CodeMetrics, 
                                issues_by_severity: Dict[str, List]) -> float:
        """计算质量分数
        
        Args:
            metrics: 代码指标
            issues_by_severity: 按严重程度分类的问题
            
        Returns:
            float: 质量分数 (0-100)
        """
        base_score = 100.0
        
        # 根据问题严重程度扣分
        severity_weights = {
            QualityLevel.CRITICAL.value: 20,
            QualityLevel.POOR.value: 10,
            QualityLevel.FAIR.value: 5,
            QualityLevel.GOOD.value: 2,
            QualityLevel.EXCELLENT.value: 0
        }
        
        for severity, issues in issues_by_severity.items():
            weight = severity_weights.get(severity, 5)
            base_score -= len(issues) * weight
        
        # 根据覆盖率调整分数
        if metrics.docstring_coverage < 50:
            base_score -= 10
        if metrics.test_coverage < 50:
            base_score -= 15
        
        # 确保分数在合理范围内
        return max(0, min(100, base_score))
    
    def _get_quality_level(self, score: float) -> str:
        """根据分数获取质量等级
        
        Args:
            score: 质量分数
            
        Returns:
            str: 质量等级
        """
        if score >= 90:
            return QualityLevel.EXCELLENT.value
        elif score >= 80:
            return QualityLevel.GOOD.value
        elif score >= 60:
            return QualityLevel.FAIR.value
        elif score >= 40:
            return QualityLevel.POOR.value
        else:
            return QualityLevel.CRITICAL.value
    
    def _generate_recommendations(self, issues_by_severity: Dict[str, List]) -> List[str]:
        """生成改进建议
        
        Args:
            issues_by_severity: 按严重程度分类的问题
            
        Returns:
            List[str]: 建议列表
        """
        recommendations = []
        
        # 根据问题类型生成建议
        issue_categories = {}
        for issues in issues_by_severity.values():
            for issue in issues:
                category = issue.category
                if category not in issue_categories:
                    issue_categories[category] = 0
                issue_categories[category] += 1
        
        # 生成针对性建议
        if issue_categories.get('代码复杂度', 0) > 0:
            recommendations.append("简化复杂的函数和类，遵循单一职责原则")
        
        if issue_categories.get('文档质量', 0) > 0:
            recommendations.append("增加函数、类和模块的文档字符串")
        
        if issue_categories.get('测试质量', 0) > 0:
            recommendations.append("编写更多的单元测试和集成测试")
        
        if issue_categories.get('代码结构', 0) > 0:
            recommendations.append("重构大文件，提高代码的模块化程度")
        
        if issue_categories.get('代码可读性', 0) > 0:
            recommendations.append("增加必要的注释，提高代码可读性")
        
        if not recommendations:
            recommendations.append("代码质量良好，继续保持！")
        
        return recommendations
    
    def print_evaluation_report(self):
        """打印评估报告"""
        if not self.evaluation_results:
            print("错误: 没有可显示的评估结果")
            return
        
        report = self.evaluation_results
        
        print(f"\n{'='*70}")
        print(f"📊 代码质量评估报告")
        print(f"{'='*70}")
        print(f"评估时间: {report['evaluation_time']}")
        print(f"质量分数: {report['quality_score']:.1f}/100")
        print(f"质量等级: {report['quality_level']}")
        
        print(f"\n📈 项目指标:")
        print(f"  总文件数: {report['project_metrics']['total_files']}")
        print(f"  总代码行数: {report['project_metrics']['total_lines_of_code']}")
        print(f"  总注释行数: {report['project_metrics']['total_lines_of_comments']}")
        print(f"  函数总数: {report['project_metrics']['total_functions']}")
        print(f"  类总数: {report['project_metrics']['total_classes']}")
        print(f"  平均复杂度: {report['project_metrics']['average_complexity']:.1f}")
        print(f"  文档覆盖率: {report['project_metrics']['average_docstring_coverage']:.1f}%")
        print(f"  测试覆盖率: {report['project_metrics']['estimated_test_coverage']:.1f}%")
        
        print(f"\n⚠️  质量问题汇总:")
        print(f"  总问题数: {report['issues_summary']['total_issues']}")
        for severity, count in report['issues_summary']['by_severity'].items():
            if count > 0:
                print(f"  {severity}: {count} 个")
        
        if report['detailed_issues']:
            print(f"\n🔍 详细问题列表:")
            for i, issue in enumerate(report['detailed_issues'][:10], 1):  # 只显示前10个
                print(f"  {i}. [{issue['severity']}] {issue['category']}")
                print(f"     {issue['description']}")
                print(f"     文件: {issue['file']}")
                if issue['suggestion']:
                    print(f"     建议: {issue['suggestion']}")
                print()
        
        print(f"🎯 改进建议:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        print(f"{'='*70}\n")
    
    def save_evaluation_report(self, filepath: str):
        """保存评估报告到文件
        
        Args:
            filepath: 保存路径
        """
        if not self.evaluation_results:
            print("错误: 没有可保存的评估结果")
            return
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.evaluation_results, f, ensure_ascii=False, indent=2)
        
        print(f"评估报告已保存到: {filepath}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='代码质量评估器')
    parser.add_argument('--project', '-p', 
                       default=os.path.dirname(os.path.abspath(__file__)), 
                       help='项目根目录')
    parser.add_argument('--output', '-o', help='保存报告到文件')
    parser.add_argument('--quiet', '-q', action='store_true', help='静默模式')
    
    args = parser.parse_args()
    
    # 创建评估器
    evaluator = TestEvaluator(args.project)
    
    # 执行评估
    report = evaluator.evaluate_project()
    
    # 显示结果
    if not args.quiet:
        evaluator.print_evaluation_report()
    
    # 保存报告
    if args.output:
        evaluator.save_evaluation_report(args.output)
    
    # 根据质量等级返回退出码
    quality_level = report['quality_level']
    if quality_level in ['优秀', '良好']:
        exit_code = 0
    elif quality_level == '一般':
        exit_code = 1
    else:
        exit_code = 2
    
    return exit_code


if __name__ == '__main__':
    import sys
    sys.exit(main())
