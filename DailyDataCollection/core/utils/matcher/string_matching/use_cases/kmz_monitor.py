# -*- coding: utf-8 -*-
"""
KMZ文件监控集成模块
基于实验结果的智能KMZ文件监控和匹配系统
"""

import os
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
from threading import Event, Lock

try:
    from .use_cases.kmz_matcher import KMZFileMatcher
    from ..data_models.date_types import DateType
except ImportError:
    # 处理独立运行的情况
    import sys
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, current_dir)
    sys.path.insert(0, parent_dir)
    
    from core.utils.matcher.string_matching.use_cases.kmz_matcher import KMZFileMatcher


@dataclass
class KMZMonitorConfig:
    """KMZ监控配置"""
    watch_directory: str                    # 监控目录
    output_directory: str = "output"        # 输出目录
    check_interval: int = 30                # 检查间隔(秒)
    file_stable_time: int = 5               # 文件稳定时间(秒)
    enable_fuzzy_matching: bool = True      # 启用模糊匹配
    confidence_threshold: float = 0.4       # 置信度阈值
    auto_categorize: bool = True            # 自动分类文件
    generate_reports: bool = True           # 生成报告
    backup_unmatched: bool = True           # 备份未匹配文件
    debug_mode: bool = False                # 调试模式


@dataclass
class KMZFileInfo:
    """KMZ文件信息"""
    filename: str
    filepath: str
    file_size: int
    modified_time: datetime
    match_result: Dict[str, Any]
    processed_time: datetime
    category: str = "unknown"
    backup_path: str = None


class KMZMonitorStats:
    """KMZ监控统计"""
    
    def __init__(self):
        self.reset()
        self._lock = Lock()
    
    def reset(self):
        """重置统计"""
        with self._lock:
            self.total_files = 0
            self.exact_matches = 0
            self.fuzzy_matches = 0
            self.failed_matches = 0
            self.processed_files = 0
            self.start_time = datetime.now()
            self.last_update = datetime.now()
    
    def update_match_result(self, match_result: Dict[str, Any]):
        """更新匹配结果统计"""
        with self._lock:
            self.total_files += 1
            self.last_update = datetime.now()
            
            if match_result['success']:
                if match_result['match_type'] == 'exact':
                    self.exact_matches += 1
                elif match_result['match_type'] == 'fuzzy':
                    self.fuzzy_matches += 1
                self.processed_files += 1
            else:
                self.failed_matches += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            runtime = datetime.now() - self.start_time
            success_rate = (self.processed_files / self.total_files * 100) if self.total_files > 0 else 0
            
            return {
                'total_files': self.total_files,
                'processed_files': self.processed_files,
                'exact_matches': self.exact_matches,
                'fuzzy_matches': self.fuzzy_matches,
                'failed_matches': self.failed_matches,
                'success_rate': success_rate,
                'exact_rate': (self.exact_matches / self.total_files * 100) if self.total_files > 0 else 0,
                'fuzzy_rate': (self.fuzzy_matches / self.total_files * 100) if self.total_files > 0 else 0,
                'runtime_seconds': runtime.total_seconds(),
                'last_update': self.last_update.isoformat()
            }


class KMZFileMonitor:
    """KMZ文件智能监控器
    
    基于实验结果的高性能KMZ文件监控系统：
    - 实时文件监控
    - 智能匹配分析（精确+模糊）
    - 自动分类和处理
    - 详细统计和报告
    """
    
    def __init__(self, config: KMZMonitorConfig):
        """初始化监控器
        
        Args:
            config: 监控配置
        """
        self.config = config
        self.matcher = KMZFileMatcher(debug=config.debug_mode)
        self.stats = KMZMonitorStats()
        self.processed_files: Dict[str, KMZFileInfo] = {}
        self.is_running = False
        self.stop_event = Event()
        
        # 创建输出目录
        self._setup_directories()
        
        # 加载已知位置
        self._load_known_locations()
        
        self._log(f"KMZ监控器初始化完成，监控目录: {config.watch_directory}")
    
    def _setup_directories(self):
        """设置目录结构"""
        dirs_to_create = [
            self.config.output_directory,
            os.path.join(self.config.output_directory, "matched"),
            os.path.join(self.config.output_directory, "unmatched"),
            os.path.join(self.config.output_directory, "reports"),
            os.path.join(self.config.output_directory, "logs")
        ]
        
        for dir_path in dirs_to_create:
            os.makedirs(dir_path, exist_ok=True)
    
    def _load_known_locations(self):
        """加载已知位置列表"""
        # 基于实验结果的已知位置
        known_locations = [
            'mahrous', 'mahmoud', 'mahros', 'mahroos',
            'taleh', 'tale', 'tal', 'tala',
            'jizi', 'jizy', 'gizi', 'gizy',
            'group3', 'group_3', 'grp3', 'g3',
            'ayn_qunay', 'ayn_quny', 'aynqunay',
            'wadi_shawqab', 'wadishawqab',
            'harrat_al_buqum', 'harratalbuqum',
            'GMAS', 'gmas'
        ]
        
        self.matcher.add_known_locations(known_locations)
        self._log(f"加载了 {len(known_locations)} 个已知位置")
    
    def start_monitoring(self, callback: Optional[Callable[[KMZFileInfo], None]] = None):
        """开始监控
        
        Args:
            callback: 文件处理回调函数
        """
        if self.is_running:
            self._log("监控器已在运行中")
            return
        
        self.is_running = True
        self.stop_event.clear()
        self.stats.reset()
        
        self._log("开始KMZ文件监控...")
        
        try:
            while not self.stop_event.is_set():
                # 扫描新文件
                new_files = self._scan_for_new_files()
                
                # 处理新文件
                for file_path in new_files:
                    if self.stop_event.is_set():
                        break
                    
                    file_info = self._process_kmz_file(file_path)
                    if file_info and callback:
                        try:
                            callback(file_info)
                        except Exception as e:
                            self._log(f"回调函数执行失败: {e}")
                
                # 生成报告
                if self.config.generate_reports and len(self.processed_files) > 0:
                    self._generate_periodic_report()
                
                # 等待下次检查
                self.stop_event.wait(self.config.check_interval)
        
        except KeyboardInterrupt:
            self._log("接收到停止信号")
        except Exception as e:
            self._log(f"监控过程中发生错误: {e}")
        finally:
            self.is_running = False
            self._log("监控器已停止")
    
    def stop_monitoring(self):
        """停止监控"""
        if self.is_running:
            self._log("正在停止监控器...")
            self.stop_event.set()
        
        # 生成最终报告
        if self.config.generate_reports:
            self._generate_final_report()
    
    def _scan_for_new_files(self) -> List[str]:
        """扫描新的KMZ文件"""
        if not os.path.exists(self.config.watch_directory):
            return []
        
        new_files = []
        current_time = datetime.now()
        
        try:
            for root, dirs, files in os.walk(self.config.watch_directory):
                for file in files:
                    if file.lower().endswith('.kmz'):
                        file_path = os.path.join(root, file)
                        
                        # 检查是否已处理过
                        if file_path in self.processed_files:
                            continue
                        
                        # 检查文件是否稳定（防止处理正在写入的文件）
                        try:
                            stat = os.stat(file_path)
                            file_age = current_time - datetime.fromtimestamp(stat.st_mtime)
                            
                            if file_age.total_seconds() >= self.config.file_stable_time:
                                new_files.append(file_path)
                        except OSError:
                            continue
        
        except Exception as e:
            self._log(f"扫描文件时发生错误: {e}")
        
        return new_files
    
    def _process_kmz_file(self, file_path: str) -> Optional[KMZFileInfo]:
        """处理单个KMZ文件"""
        try:
            filename = os.path.basename(file_path)
            stat = os.stat(file_path)
            
            self._log(f"处理文件: {filename}")
            
            # 进行匹配分析
            match_result = self.matcher.match_kmz_filename(filename)
            
            # 更新统计
            self.stats.update_match_result(match_result)
            
            # 确定分类
            category = self._determine_category(match_result)
            
            # 创建文件信息
            file_info = KMZFileInfo(
                filename=filename,
                filepath=file_path,
                file_size=stat.st_size,
                modified_time=datetime.fromtimestamp(stat.st_mtime),
                match_result=match_result,
                processed_time=datetime.now(),
                category=category
            )
            
            # 自动分类处理
            if self.config.auto_categorize:
                self._categorize_file(file_info)
            
            # 保存到已处理列表
            self.processed_files[file_path] = file_info
            
            self._log(f"文件处理完成: {filename} -> {category} (置信度: {match_result['confidence']:.3f})")
            
            return file_info
        
        except Exception as e:
            self._log(f"处理文件失败 {file_path}: {e}")
            return None
    
    def _determine_category(self, match_result: Dict[str, Any]) -> str:
        """确定文件分类"""
        if not match_result['success']:
            return "unmatched"
        
        if match_result['match_type'] == 'exact':
            return f"exact_{match_result['pattern_type']}"
        elif match_result['match_type'] == 'fuzzy':
            quality = match_result.get('quality', 'unknown')
            return f"fuzzy_{match_result['pattern_type']}_{quality}"
        
        return "unknown"
    
    def _categorize_file(self, file_info: KMZFileInfo):
        """自动分类文件"""
        category_dir = os.path.join(self.config.output_directory, "matched" if file_info.match_result['success'] else "unmatched")
        
        if file_info.match_result['success']:
            # 成功匹配的文件按类型分类
            pattern_type = file_info.match_result['pattern_type']
            category_dir = os.path.join(category_dir, pattern_type)
        
        os.makedirs(category_dir, exist_ok=True)
        
        # 创建符号链接或复制文件（根据需要）
        target_path = os.path.join(category_dir, file_info.filename)
        if not os.path.exists(target_path):
            try:
                # 在Windows上创建硬链接，其他系统创建符号链接
                if os.name == 'nt':
                    os.link(file_info.filepath, target_path)
                else:
                    os.symlink(file_info.filepath, target_path)
                
                file_info.backup_path = target_path
            except OSError:
                # 如果链接失败，记录日志但不影响处理
                self._log(f"无法创建文件链接: {file_info.filename}")
    
    def _generate_periodic_report(self):
        """生成周期性报告"""
        try:
            report_time = datetime.now()
            report_file = os.path.join(
                self.config.output_directory, 
                "reports", 
                f"kmz_monitor_report_{report_time.strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            # 收集统计信息
            stats = self.stats.get_stats()
            matcher_stats = self.matcher.get_statistics()
            
            report_data = {
                'report_time': report_time.isoformat(),
                'monitor_config': asdict(self.config),
                'statistics': stats,
                'matcher_statistics': matcher_stats,
                'processed_files_count': len(self.processed_files),
                'recent_files': [
                    {
                        'filename': info.filename,
                        'category': info.category,
                        'confidence': info.match_result['confidence'],
                        'match_type': info.match_result['match_type']
                    }
                    for info in list(self.processed_files.values())[-10:]  # 最近10个文件
                ]
            }
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            self._log(f"生成周期性报告: {report_file}")
        
        except Exception as e:
            self._log(f"生成报告失败: {e}")
    
    def _generate_final_report(self):
        """生成最终报告"""
        try:
            report_time = datetime.now()
            report_file = os.path.join(
                self.config.output_directory,
                "reports",
                f"kmz_monitor_final_report_{report_time.strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            # 详细统计
            stats = self.stats.get_stats()
            matcher_stats = self.matcher.get_statistics()
            
            # 分类统计
            category_stats = {}
            quality_stats = {}
            
            for file_info in self.processed_files.values():
                category = file_info.category
                category_stats[category] = category_stats.get(category, 0) + 1
                
                if file_info.match_result['success']:
                    quality = file_info.match_result.get('quality', 'unknown')
                    quality_stats[quality] = quality_stats.get(quality, 0) + 1
            
            # 生成详细报告
            report_data = {
                'report_time': report_time.isoformat(),
                'monitor_config': asdict(self.config),
                'overall_statistics': stats,
                'matcher_statistics': matcher_stats,
                'category_distribution': category_stats,
                'quality_distribution': quality_stats,
                'processed_files': [
                    {
                        'filename': info.filename,
                        'filepath': info.filepath,
                        'file_size': info.file_size,
                        'modified_time': info.modified_time.isoformat(),
                        'processed_time': info.processed_time.isoformat(),
                        'category': info.category,
                        'match_result': info.match_result,
                        'backup_path': info.backup_path
                    }
                    for info in self.processed_files.values()
                ]
            }
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            self._log(f"生成最终报告: {report_file}")
            
            # 生成简化的统计摘要
            summary_file = os.path.join(
                self.config.output_directory,
                "reports",
                f"kmz_monitor_summary_{report_time.strftime('%Y%m%d_%H%M%S')}.txt"
            )
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("KMZ文件监控统计摘要\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"监控时间: {stats['runtime_seconds']:.1f} 秒\n")
                f.write(f"总文件数: {stats['total_files']}\n")
                f.write(f"成功处理: {stats['processed_files']} ({stats['success_rate']:.1f}%)\n")
                f.write(f"精确匹配: {stats['exact_matches']} ({stats['exact_rate']:.1f}%)\n")
                f.write(f"模糊匹配: {stats['fuzzy_matches']} ({stats['fuzzy_rate']:.1f}%)\n")
                f.write(f"匹配失败: {stats['failed_matches']}\n\n")
                
                f.write("分类分布:\n")
                for category, count in category_stats.items():
                    f.write(f"  {category}: {count}\n")
                
                if quality_stats:
                    f.write("\n质量分布:\n")
                    for quality, count in quality_stats.items():
                        f.write(f"  {quality}: {count}\n")
            
            self._log(f"生成统计摘要: {summary_file}")
        
        except Exception as e:
            self._log(f"生成最终报告失败: {e}")
    
    def get_current_stats(self) -> Dict[str, Any]:
        """获取当前统计信息"""
        return {
            'monitor_stats': self.stats.get_stats(),
            'matcher_stats': self.matcher.get_statistics(),
            'processed_files_count': len(self.processed_files),
            'is_running': self.is_running
        }
    
    def get_processed_files(self) -> List[KMZFileInfo]:
        """获取已处理的文件列表"""
        return list(self.processed_files.values())
    
    def _log(self, message: str):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        
        if self.config.debug_mode:
            print(log_message)
        
        # 写入日志文件
        log_file = os.path.join(self.config.output_directory, "logs", "kmz_monitor.log")
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_message + "\n")
        except Exception:
            pass  # 忽略日志写入错误


# 便捷函数
def create_kmz_monitor(watch_directory: str, **kwargs) -> KMZFileMonitor:
    """创建KMZ监控器的便捷函数
    
    Args:
        watch_directory: 监控目录
        **kwargs: 其他配置参数
        
    Returns:
        KMZFileMonitor: 监控器实例
    """
    config = KMZMonitorConfig(watch_directory=watch_directory, **kwargs)
    return KMZFileMonitor(config)


def monitor_kmz_directory(watch_directory: str, 
                         duration_minutes: Optional[int] = None,
                         callback: Optional[Callable[[KMZFileInfo], None]] = None,
                         **kwargs) -> Dict[str, Any]:
    """监控KMZ目录的便捷函数
    
    Args:
        watch_directory: 监控目录
        duration_minutes: 监控持续时间(分钟)，None表示无限期
        callback: 文件处理回调函数
        **kwargs: 其他配置参数
        
    Returns:
        Dict[str, Any]: 监控统计结果
    """
    monitor = create_kmz_monitor(watch_directory, **kwargs)
    
    try:
        if duration_minutes:
            # 启动定时监控
            import threading
            stop_timer = threading.Timer(duration_minutes * 60, monitor.stop_monitoring)
            stop_timer.start()
        
        monitor.start_monitoring(callback)
        
        if duration_minutes:
            stop_timer.cancel()
    
    except KeyboardInterrupt:
        monitor.stop_monitoring()
    
    return monitor.get_current_stats()
