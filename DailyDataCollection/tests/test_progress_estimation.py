"""
进度估算模块测试

测试数据分析、完成日期估算和图表生成功能
"""

import unittest
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.progress_estimation import DataAnalyzer, FinishDateEstimator, ProgressCharts, ProgressTracker
from core.data_models.date_types import DateType


class TestDataAnalyzer(unittest.TestCase):
    """测试数据分析器"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.analyzer = DataAnalyzer(self.temp_dir)
        
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_initialization(self):
        """测试初始化"""
        self.assertIsInstance(self.analyzer, DataAnalyzer)
        self.assertEqual(self.analyzer.workspace_path, self.temp_dir)
        
    def test_load_historical_data(self):
        """测试加载历史数据"""
        start_date = DateType(datetime.now() - timedelta(days=7))
        end_date = DateType(datetime.now())
        
        # 这个测试使用模拟数据，应该能成功
        result = self.analyzer.load_historical_data(start_date, end_date)
        self.assertTrue(result)
        self.assertFalse(self.analyzer.historical_data.empty)
        
    def test_calculate_daily_velocity(self):
        """测试计算每日速度"""
        # 先加载数据
        start_date = DateType(datetime.now() - timedelta(days=7))
        self.analyzer.load_historical_data(start_date)
        
        # 计算速度
        result = self.analyzer.calculate_daily_velocity()
        self.assertFalse(result.empty)
        self.assertIn('velocity_7day', result.columns)
        
    def test_get_velocity_trend(self):
        """测试获取速度趋势"""
        # 先加载数据
        start_date = DateType(datetime.now() - timedelta(days=14))
        self.analyzer.load_historical_data(start_date)
        self.analyzer.calculate_daily_velocity()
        
        trend = self.analyzer.get_velocity_trend()
        self.assertIsInstance(trend, dict)
        if trend:  # 如果有足够数据
            self.assertIn('trend_direction', trend)


class TestFinishDateEstimator(unittest.TestCase):
    """测试完成日期估算器"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.analyzer = DataAnalyzer(self.temp_dir)
        
        # 加载一些测试数据
        start_date = DateType(datetime.now() - timedelta(days=14))
        self.analyzer.load_historical_data(start_date)
        self.analyzer.calculate_daily_velocity()
        
        self.estimator = FinishDateEstimator(self.analyzer)
        
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_initialization(self):
        """测试初始化"""
        self.assertIsInstance(self.estimator, FinishDateEstimator)
        self.assertEqual(self.estimator.data_analyzer, self.analyzer)
        
    def test_estimate_finish_date(self):
        """测试估算完成日期"""
        result = self.estimator.estimate_finish_date(
            target_points=1000,
            current_points=300,
            method='simple_average'
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('estimated_date', result)
        self.assertIn('days_remaining', result)
        self.assertIn('method', result)
        
    def test_estimate_completed_project(self):
        """测试已完成项目的估算"""
        result = self.estimator.estimate_finish_date(
            target_points=100,
            current_points=100
        )
        
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['days_remaining'], 0)
        
    def test_multiple_estimates(self):
        """测试多种估算方法"""
        estimates = self.estimator.get_multiple_estimates(
            target_points=1000,
            current_points=300
        )
        
        self.assertIsInstance(estimates, dict)
        self.assertTrue(len(estimates) > 0)
        
    def test_recommended_estimate(self):
        """测试推荐估算"""
        result = self.estimator.get_recommended_estimate(
            target_points=1000,
            current_points=300
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('estimated_date', result)


class TestProgressCharts(unittest.TestCase):
    """测试进度图表生成器"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.chart_dir = os.path.join(self.temp_dir, 'charts')
        
        self.analyzer = DataAnalyzer(self.temp_dir)
        start_date = DateType(datetime.now() - timedelta(days=14))
        self.analyzer.load_historical_data(start_date)
        self.analyzer.calculate_daily_velocity()
        
        self.charts = ProgressCharts(self.analyzer, self.chart_dir)
        
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_initialization(self):
        """测试初始化"""
        self.assertIsInstance(self.charts, ProgressCharts)
        self.assertTrue(os.path.exists(self.chart_dir))
        
    def test_generate_burndown_chart(self):
        """测试生成燃尽图"""
        estimator = FinishDateEstimator(self.analyzer)
        
        chart_path = self.charts.generate_burndown_chart(
            target_points=1000,
            current_points=300,
            finish_estimator=estimator
        )
        
        if chart_path:  # 如果成功生成
            self.assertTrue(os.path.exists(chart_path))
            self.assertTrue(chart_path.endswith('.png'))
            
    def test_generate_burnup_chart(self):
        """测试生成燃起图"""
        estimator = FinishDateEstimator(self.analyzer)
        
        chart_path = self.charts.generate_burnup_chart(
            target_points=1000,
            current_points=300,
            finish_estimator=estimator
        )
        
        if chart_path:  # 如果成功生成
            self.assertTrue(os.path.exists(chart_path))
            self.assertTrue(chart_path.endswith('.png'))
            
    def test_generate_velocity_chart(self):
        """测试生成速度图"""
        chart_path = self.charts.generate_velocity_chart()
        
        if chart_path:  # 如果成功生成
            self.assertTrue(os.path.exists(chart_path))
            self.assertTrue(chart_path.endswith('.png'))
            
    def test_generate_all_charts(self):
        """测试批量生成图表"""
        estimator = FinishDateEstimator(self.analyzer)
        
        chart_paths = self.charts.generate_all_charts(
            target_points=1000,
            current_points=300,
            finish_estimator=estimator
        )
        
        self.assertIsInstance(chart_paths, dict)
        # 检查生成的文件是否存在
        for chart_type, path in chart_paths.items():
            if path:
                self.assertTrue(os.path.exists(path))


class TestProgressTracker(unittest.TestCase):
    """测试进度跟踪器"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.tracker = ProgressTracker(self.temp_dir)
        
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_initialization(self):
        """测试初始化"""
        self.assertIsInstance(self.tracker, ProgressTracker)
        self.assertEqual(self.tracker.workspace_path, self.temp_dir)
        
    def test_initialize_project(self):
        """测试项目初始化"""
        result = self.tracker.initialize_project(
            target_points=1000,
            current_points=300,
            start_date=DateType(datetime.now() - timedelta(days=30))
        )
        
        self.assertTrue(result)
        self.assertEqual(self.tracker.project_config['target_points'], 1000)
        self.assertEqual(self.tracker.project_config['current_points'], 300)
        
    def test_load_historical_data(self):
        """测试加载历史数据"""
        start_date = DateType(datetime.now() - timedelta(days=14))
        result = self.tracker.load_historical_data(start_date)
        
        self.assertTrue(result)
        self.assertIsNotNone(self.tracker.finish_estimator)
        
    def test_get_current_progress_summary(self):
        """测试获取进度摘要"""
        self.tracker.initialize_project(1000, 300)
        self.tracker.load_historical_data()
        
        summary = self.tracker.get_current_progress_summary()
        
        self.assertIsInstance(summary, dict)
        self.assertIn('project_info', summary)
        self.assertIn('completion_percentage', summary)
        
    def test_generate_progress_report(self):
        """测试生成进度报告"""
        self.tracker.initialize_project(1000, 300)
        self.tracker.load_historical_data()
        
        # 生成不包含图表的报告以减少测试时间
        report = self.tracker.generate_progress_report(include_charts=False)
        
        self.assertIsInstance(report, dict)
        self.assertIn('summary', report)
        self.assertIn('recommendations', report)
        
    def test_update_current_progress(self):
        """测试更新当前进度"""
        self.tracker.initialize_project(1000, 300)
        
        result = self.tracker.update_current_progress(400)
        self.assertTrue(result)
        self.assertEqual(self.tracker.project_config['current_points'], 400)
        
    def test_get_daily_target(self):
        """测试计算每日目标"""
        target_date = DateType(datetime.now() + timedelta(days=30))
        self.tracker.initialize_project(1000, 300, target_date=target_date)
        self.tracker.load_historical_data()
        
        daily_target = self.tracker.get_daily_target()
        
        self.assertIsInstance(daily_target, dict)
        if 'error' not in daily_target:
            self.assertIn('daily_target', daily_target)
            self.assertIn('feasibility', daily_target)


class TestModuleIntegration(unittest.TestCase):
    """测试模块集成"""
    
    def test_module_imports(self):
        """测试模块导入"""
        try:
            from core.progress_estimation import DataAnalyzer, FinishDateEstimator, ProgressCharts, ProgressTracker
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"模块导入失败: {e}")
            
    def test_end_to_end_workflow(self):
        """测试端到端工作流程"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 1. 创建进度跟踪器
            tracker = ProgressTracker(temp_dir)
            
            # 2. 初始化项目
            success = tracker.initialize_project(
                target_points=1000,
                current_points=300,
                start_date=DateType(datetime.now() - timedelta(days=30))
            )
            self.assertTrue(success)
            
            # 3. 加载历史数据
            success = tracker.load_historical_data()
            self.assertTrue(success)
            
            # 4. 获取进度摘要
            summary = tracker.get_current_progress_summary()
            self.assertIn('project_info', summary)
            
            # 5. 生成报告（不包含图表以节省时间）
            report = tracker.generate_progress_report(include_charts=False)
            self.assertIn('summary', report)
            
            print("✓ 端到端工作流程测试通过")
            
        except Exception as e:
            self.fail(f"端到端工作流程测试失败: {e}")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    print("GMAS 进度估算模块测试")
    print("=" * 50)
    
    # 设置测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestDataAnalyzer,
        TestFinishDateEstimator,
        TestProgressCharts,
        TestProgressTracker,
        TestModuleIntegration
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 显示结果摘要
    print("\n" + "=" * 50)
    print("测试结果摘要:")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("✓ 所有测试通过 - 进度估算模块正常")
    else:
        print("✗ 部分测试失败 - 请检查模块实现")
        
        if result.failures:
            print("\n失败的测试:")
            for test, traceback in result.failures:
                print(f"- {test}: {traceback}")
        
        if result.errors:
            print("\n错误的测试:")
            for test, traceback in result.errors:
                print(f"- {test}: {traceback}")