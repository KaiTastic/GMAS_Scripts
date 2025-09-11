# 配置管理器改进计划

## 当前实现状态

### ✅ 已实现的核心功能
- [x] **单例模式设计** - 使用线程安全的单例实现
- [x] **YAML配置文件加载与解析** - 支持UTF-8编码，完整错误处理
- [x] **点号路径访问** - 完整实现嵌套配置访问 (`logging.default.level`)
- [x] **配置验证框架** - 基础结构验证 + 自定义验证规则系统
- [x] **配置缓存机制** - 带TTL的缓存 (默认5分钟)，支持智能缓存清理
- [x] **热重载** - 使用watchdog监控文件变化，自动重载配置
- [x] **观察者模式** - 完整的配置变更通知系统
- [x] **变量展开和配置引用** - 支持 `{key.subkey}` 语法，防循环引用
- [x] **线程安全保护** - 使用 RLock 保护所有关键操作
- [x] **配置保存功能** - 支持保存修改后的配置到文件
- [x] **错误处理与日志集成** - 自定义ConfigError异常，完整日志记录
- [x] **🆕 平台特定配置支持** - 自动检测平台，支持平台特定路径管理
- [x] **🆕 智能变量展开** - 支持平台特定变量引用 (`{platform.workspace}`)
- [x] **🆕 路径标准化** - 自动处理不同平台的路径分隔符差异

### 🔍 实现细节分析
- **缓存策略**: 使用 `_cache` 和 `_cache_ttl` 双重字典实现TTL缓存
- **变量展开**: 支持递归展开，最大深度保护，特殊变量处理，**新增平台特定变量支持**
- **文件监控**: 实时监控 `.yaml/.yml` 文件变化
- **验证规则**: 支持类型检查、必需字段、自定义验证函数
- **🆕 平台检测**: 自动检测 Windows/macOS/Linux，提供平台特定配置
- **🆕 路径处理**: 智能路径标准化，保持平台兼容性

## 🚀 待实现的改进功能

### 优先级1 - 高优先级 (建议优先实现)

#### 1. 多环境支持 🌍
**描述**: 实现开发、测试、生产等不同环境的配置管理

**当前状态**: ✅ **已完成** - 平台特定配置已实现，为多环境支持奠定基础

**已实现功能**:
- ✅ 平台自动检测 (Windows/macOS/Linux)
- ✅ 平台特定配置文件结构 (`platform.workspace.{platform}`)
- ✅ 平台特定变量展开 (`{platform.workspace}`)
- ✅ 默认配置回退机制
- ✅ 路径标准化处理

**剩余工作** (环境特定配置):
- [ ] 环境特定配置文件 (`settings.dev.yaml`, `settings.prod.yaml`)
- [ ] 环境变量检测 (`GMAS_ENV`)
- [ ] 环境与平台的组合配置支持

**测试状态**: ✅ 已通过完整测试

**实现要点**:
- 环境特定配置文件 (`settings.dev.yaml`, `settings.prod.yaml`)
- 环境变量检测 (`GMAS_ENV` 或 `ENVIRONMENT`)
- 深度配置合并机制 (覆盖基础配置)
- 环境隔离验证

**具体实现方案**:
```python
def __init__(self, config_file: Optional[str] = None, environment: Optional[str] = None):
    if self._config is None:
        with self._lock:
            if self._config is None:
                self.logger = get_logger('config')
                # ... 现有初始化代码 ...
                self._environment = environment or os.getenv('GMAS_ENV', 'production')
                
                self._load_config(config_file)
                self._load_environment_config()  # 新增：加载环境配置
                self._validate_config()
                # ... 其余代码 ...

def _load_environment_config(self):
    """加载环境特定的配置覆盖"""
    env_config_file = self._config_file.parent / f"settings.{self._environment}.yaml"
    if env_config_file.exists():
        try:
            with open(env_config_file, 'r', encoding='utf-8') as f:
                env_config = yaml.safe_load(f) or {}
            self._deep_merge(self._config, env_config)
            self.logger.info(f"环境配置加载成功: {env_config_file}")
        except Exception as e:
            self.logger.warning(f"环境配置加载失败: {e}")

def _deep_merge(self, base: dict, override: dict):
    """深度合并字典配置"""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            self._deep_merge(base[key], value)
        else:
            base[key] = value
```

**影响模块**: `ConfigManager.__init__()`, `_load_config()`, 新增环境处理方法  
**测试要求**: 环境配置加载、配置合并、环境变量检测

---

#### 2. 配置备份管理 💾
**描述**: 自动备份机制和备份文件管理

**当前状态**: ⚠️ 部分实现 (已有backup目录和手动备份，缺乏自动化管理)

**实现要点**:
- 配置保存时自动创建备份
- 备份文件命名规范 (时间戳 + 版本号)
- 旧备份自动清理 (保留策略：最近N个 + 时间策略)
- 备份恢复功能
- 备份完整性验证

**具体实现方案**:
```python
def save_config(self, file_path: Optional[str] = None, create_backup: bool = True):
    """保存配置并创建备份"""
    target_file = Path(file_path) if file_path else self._config_file
    
    # 创建备份
    if create_backup and target_file.exists():
        backup_info = self._create_backup(target_file)
        if backup_info:
            self.logger.info(f"配置备份已创建: {backup_info['file']}")
    
    # 保存配置
    try:
        # 先保存到临时文件，验证成功后替换
        temp_file = target_file.with_suffix('.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
        
        # 验证保存的配置
        self._validate_saved_config(temp_file)
        
        # 替换原文件
        temp_file.replace(target_file)
        self.logger.info(f"配置已保存到: {target_file}")
        
    except Exception as e:
        if temp_file.exists():
            temp_file.unlink()
        self.logger.error(f"保存配置失败: {e}")
        raise ConfigError(f"保存配置失败: {e}")

def _create_backup(self, config_file: Path) -> Optional[Dict[str, Any]]:
    """创建配置备份"""
    backup_dir = config_file.parent / 'backups'
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = backup_dir / f"{config_file.stem}_backup_{timestamp}{config_file.suffix}"
    
    try:
        import shutil
        shutil.copy2(config_file, backup_file)
        
        # 计算文件哈希用于完整性验证
        import hashlib
        with open(backup_file, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        
        # 清理旧备份
        self._cleanup_old_backups(backup_dir, keep=10)
        
        return {
            'file': backup_file,
            'hash': file_hash,
            'timestamp': timestamp,
            'original_size': config_file.stat().st_size
        }
    except Exception as e:
        self.logger.warning(f"创建配置备份失败: {e}")
        return None

def _cleanup_old_backups(self, backup_dir: Path, keep: int = 10):
    """清理旧的备份文件"""
    backup_files = sorted(
        backup_dir.glob('*_backup_*.yaml'), 
        key=lambda p: p.stat().st_mtime, 
        reverse=True
    )
    
    for backup_file in backup_files[keep:]:
        try:
            backup_file.unlink()
            self.logger.debug(f"删除旧备份: {backup_file}")
        except Exception as e:
            self.logger.warning(f"删除备份文件失败: {e}")

def restore_from_backup(self, backup_file: str) -> bool:
    """从备份恢复配置"""
    backup_path = Path(backup_file)
    if not backup_path.exists():
        raise ConfigError(f"备份文件不存在: {backup_file}")
    
    try:
        # 验证备份文件
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_config = yaml.safe_load(f)
        
        # 创建当前配置的备份
        current_backup = self._create_backup(self._config_file)
        
        # 恢复配置
        self._config = backup_config
        self.save_config(create_backup=False)
        
        # 清除缓存并重新验证
        self.clear_cache()
        self._validate_config()
        
        self.logger.info(f"配置已从备份恢复: {backup_file}")
        self._notify_observers('__config_restored__', None, self._config)
        
        return True
    except Exception as e:
        self.logger.error(f"从备份恢复配置失败: {e}")
        raise ConfigError(f"恢复配置失败: {e}")

def list_backups(self) -> List[Dict[str, Any]]:
    """列出所有可用备份"""
    backup_dir = self._config_file.parent / 'backups'
    if not backup_dir.exists():
        return []
    
    backups = []
    for backup_file in sorted(backup_dir.glob('*_backup_*.yaml'), reverse=True):
        try:
            stat = backup_file.stat()
            backups.append({
                'file': str(backup_file),
                'name': backup_file.name,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'age_days': (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days
            })
        except Exception:
            continue
    
    return backups
```

**影响模块**: `save_config()`, 新增备份管理方法  
**测试要求**: 备份创建、清理、恢复、完整性验证

---

### 优先级2 - 中等优先级

#### 3. 性能监控与统计 📊
**描述**: 监控配置管理器性能，提供运行时统计信息

**当前状态**: ❌ 未实现 (需要新增功能)

**实现要点**:
- 方法执行时间监控
- 缓存命中率统计 
- 配置访问频率分析
- 内存使用监控
- 性能报告生成

**具体实现方案**:
```python
from functools import wraps
import sys

def performance_monitor(func):
    """性能监控装饰器"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        start_time = time.time()
        result = func(self, *args, **kwargs)
        elapsed_time = time.time() - start_time
        
        # 记录性能数据
        if not hasattr(self, '_perf_stats'):
            self._perf_stats = {}
        
        func_name = func.__name__
        if func_name not in self._perf_stats:
            self._perf_stats[func_name] = {
                'call_count': 0,
                'total_time': 0,
                'max_time': 0,
                'min_time': float('inf')
            }
        
        stats = self._perf_stats[func_name]
        stats['call_count'] += 1
        stats['total_time'] += elapsed_time
        stats['max_time'] = max(stats['max_time'], elapsed_time)
        stats['min_time'] = min(stats['min_time'], elapsed_time)
        
        # 性能警告
        if elapsed_time > 0.1:  # 超过100ms记录警告
            self.logger.warning(f"{func_name} 执行时间过长: {elapsed_time:.3f}秒")
        
        return result
    return wrapper

class ConfigManager:
    # 在现有方法上添加性能监控
    @performance_monitor
    def get(self, key: str, default: Any = None, use_cache: bool = True, expand_vars: bool = True) -> Any:
        # 现有实现保持不变
        
        # 新增：缓存命中率统计
        if not hasattr(self, '_cache_stats'):
            self._cache_stats = {'hits': 0, 'misses': 0}
        
        cache_key = f"{key}_{expand_vars}" if expand_vars else key
        if use_cache and cache_key in self._cache:
            if cache_key not in self._cache_ttl or time.time() < self._cache_ttl[cache_key]:
                self._cache_stats['hits'] += 1
                # ... 现有返回逻辑
            else:
                self._cache_stats['misses'] += 1
        else:
            self._cache_stats['misses'] += 1
        
        # ... 现有实现
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        stats = {
            'cache_stats': getattr(self, '_cache_stats', {'hits': 0, 'misses': 0}),
            'cache_size': len(self._cache),
            'cache_memory_usage': sum(sys.getsizeof(v) for v in self._cache.values()),
            'observer_count': len(self._observers),
            'validation_rules_count': len(self._validation_rules),
            'config_memory_usage': sys.getsizeof(self._config),
            'method_performance': getattr(self, '_perf_stats', {})
        }
        
        # 计算缓存命中率
        cache_stats = stats['cache_stats']
        total_requests = cache_stats['hits'] + cache_stats['misses']
        stats['cache_hit_rate'] = cache_stats['hits'] / total_requests if total_requests > 0 else 0
        
        # 计算平均执行时间
        for method, perf in stats['method_performance'].items():
            if perf['call_count'] > 0:
                perf['avg_time'] = perf['total_time'] / perf['call_count']
        
        return stats
    
    def generate_performance_report(self) -> str:
        """生成性能报告"""
        stats = self.get_performance_stats()
        
        report = [
            "=== 配置管理器性能报告 ===",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "📊 缓存统计:",
            f"  • 缓存命中率: {stats['cache_hit_rate']:.2%}",
            f"  • 缓存条目数: {stats['cache_size']}",
            f"  • 缓存内存使用: {stats['cache_memory_usage']} bytes",
            "",
            "⚡ 方法性能:",
        ]
        
        for method, perf in stats['method_performance'].items():
            report.append(f"  • {method}:")
            report.append(f"    - 调用次数: {perf['call_count']}")
            report.append(f"    - 平均耗时: {perf.get('avg_time', 0):.4f}s")
            report.append(f"    - 最大耗时: {perf['max_time']:.4f}s")
        
        report.extend([
            "",
            "🔧 系统信息:",
            f"  • 观察者数量: {stats['observer_count']}",
            f"  • 验证规则数量: {stats['validation_rules_count']}",
            f"  • 配置内存使用: {stats['config_memory_usage']} bytes"
        ])
        
        return "\n".join(report)
    
    def reset_performance_stats(self):
        """重置性能统计"""
        self._perf_stats = {}
        self._cache_stats = {'hits': 0, 'misses': 0}
        self.logger.info("性能统计已重置")
```

**影响模块**: 核心方法添加监控装饰器，新增统计接口  
**测试要求**: 性能数据收集准确性、报告生成、统计重置

---

#### 4. 配置导入导出功能 🔄
**描述**: 支持配置的导入导出，便于配置迁移和共享

**当前状态**: ❌ 未实现 (需要新增功能)

**实现要点**:
- 多格式支持 (YAML, JSON, INI)
- 敏感信息脱敏处理
- 配置合并选项 (覆盖/合并/仅新增)
- 导入验证和安全检查
- 配置差异对比

**具体实现方案**:
```python
def export_config(self, format: str = 'yaml', include_sensitive: bool = False, 
                 sections: Optional[List[str]] = None) -> str:
    """导出配置为指定格式"""
    # 获取要导出的配置
    if sections:
        export_config = {}
        for section in sections:
            if section in self._config:
                export_config[section] = self._config[section]
    else:
        export_config = self._config.copy()
    
    # 处理敏感信息
    if not include_sensitive:
        export_config = self._mask_sensitive_fields(export_config)
    
    # 添加元数据
    metadata = {
        'export_time': datetime.now().isoformat(),
        'export_version': '1.0',
        'config_file': str(self._config_file),
        'environment': getattr(self, '_environment', 'unknown')
    }
    
    # 根据格式导出
    if format.lower() == 'yaml':
        result = f"# GMAS配置导出\n# {metadata['export_time']}\n\n"
        result += yaml.dump(export_config, default_flow_style=False, allow_unicode=True)
        result += f"\n# 元数据\n_metadata: {yaml.dump(metadata)}"
        return result
        
    elif format.lower() == 'json':
        import json
        export_data = {
            '_metadata': metadata,
            'config': export_config
        }
        return json.dumps(export_data, ensure_ascii=False, indent=2)
        
    elif format.lower() == 'ini':
        import configparser
        config_parser = configparser.ConfigParser()
        self._dict_to_configparser(export_config, config_parser)
        
        from io import StringIO
        output = StringIO()
        config_parser.write(output)
        return output.getvalue()
    else:
        raise ValueError(f"不支持的导出格式: {format}")

def import_config(self, data: Union[str, dict], format: str = 'yaml', 
                 merge_strategy: str = 'merge', validate: bool = True) -> Dict[str, Any]:
    """导入配置数据"""
    # 解析数据
    if isinstance(data, str):
        if format.lower() == 'yaml':
            imported_data = yaml.safe_load(data)
        elif format.lower() == 'json':
            import json
            imported_data = json.loads(data)
        elif format.lower() == 'ini':
            import configparser
            config_parser = configparser.ConfigParser()
            config_parser.read_string(data)
            imported_data = self._configparser_to_dict(config_parser)
        else:
            raise ValueError(f"不支持的导入格式: {format}")
    else:
        imported_data = data
    
    # 提取配置和元数据
    if '_metadata' in imported_data:
        metadata = imported_data.pop('_metadata')
        config_data = imported_data.get('config', imported_data)
    else:
        metadata = {}
        config_data = imported_data
    
    # 安全检查
    if validate:
        self._validate_import_data(config_data, metadata)
    
    # 备份当前配置
    backup_info = self._create_backup(self._config_file)
    
    try:
        # 根据合并策略处理
        old_config = self._config.copy()
        
        if merge_strategy == 'replace':
            self._config = config_data
        elif merge_strategy == 'merge':
            self._deep_merge(self._config, config_data)
        elif merge_strategy == 'add_only':
            self._merge_new_keys_only(self._config, config_data)
        else:
            raise ValueError(f"不支持的合并策略: {merge_strategy}")
        
        # 验证新配置
        self._validate_config()
        
        # 清除缓存
        self.clear_cache()
        
        # 通知变更
        changes = self._calculate_config_diff(old_config, self._config)
        self._notify_observers('__config_imported__', old_config, self._config)
        
        self.logger.info(f"配置导入成功，变更项数: {len(changes)}")
        return {
            'success': True,
            'changes': changes,
            'metadata': metadata,
            'backup_info': backup_info
        }
        
    except Exception as e:
        # 恢复原配置
        self._config = old_config
        self.logger.error(f"配置导入失败，已恢复原配置: {e}")
        raise ConfigError(f"配置导入失败: {e}")

def _mask_sensitive_fields(self, config: dict, sensitive_keys: List[str] = None) -> dict:
    """脱敏敏感配置字段"""
    if sensitive_keys is None:
        sensitive_keys = ['password', 'secret', 'key', 'token', 'api_key', 'auth']
    
    masked_config = {}
    for key, value in config.items():
        if isinstance(value, dict):
            masked_config[key] = self._mask_sensitive_fields(value, sensitive_keys)
        elif any(sensitive in key.lower() for sensitive in sensitive_keys):
            if isinstance(value, str) and len(value) > 4:
                masked_config[key] = value[:2] + '*' * (len(value) - 4) + value[-2:]
            else:
                masked_config[key] = '***'
        else:
            masked_config[key] = value
    
    return masked_config

def _calculate_config_diff(self, old_config: dict, new_config: dict) -> List[Dict[str, Any]]:
    """计算配置差异"""
    changes = []
    
    def compare_dict(old_dict, new_dict, path=""):
        for key in set(old_dict.keys()) | set(new_dict.keys()):
            current_path = f"{path}.{key}" if path else key
            
            if key not in old_dict:
                changes.append({
                    'type': 'added',
                    'path': current_path,
                    'new_value': new_dict[key]
                })
            elif key not in new_dict:
                changes.append({
                    'type': 'removed',
                    'path': current_path,
                    'old_value': old_dict[key]
                })
            elif old_dict[key] != new_dict[key]:
                if isinstance(old_dict[key], dict) and isinstance(new_dict[key], dict):
                    compare_dict(old_dict[key], new_dict[key], current_path)
                else:
                    changes.append({
                        'type': 'modified',
                        'path': current_path,
                        'old_value': old_dict[key],
                        'new_value': new_dict[key]
                    })
    
    compare_dict(old_config, new_config)
    return changes
```

**影响模块**: 新增导入导出接口，增强配置管理功能  
**测试要求**: 多格式转换、敏感信息处理、合并策略、差异计算

---

### 优先级3 - 低优先级 (可选实现)

#### 5. 配置加密支持 🔐
**描述**: 对敏感配置进行加密存储和访问

**当前状态**: ❌ 未实现 (需要额外依赖)

**实现要点**:
- 敏感字段自动加密存储
- 密钥管理策略 (环境变量/密钥文件/机器指纹)
- 透明解密访问 (用户无感知)
- 安全密钥派生和轮换
- 加密字段标识和管理

**具体实现方案**:
```python
# 需要新增依赖: cryptography>=3.4.8

import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class ConfigManager:
    def __init__(self, config_file: Optional[str] = None, enable_encryption: bool = False):
        # ... 现有初始化代码 ...
        self._encryption_enabled = enable_encryption
        if enable_encryption:
            self._setup_encryption()
    
    def _setup_encryption(self):
        """设置加密组件"""
        # 获取加密密钥
        key_source = (
            os.getenv('GMAS_CONFIG_KEY') or          # 环境变量
            self._load_key_from_file() or            # 密钥文件
            self._generate_machine_key()             # 机器指纹
        )
        
        if isinstance(key_source, str):
            key_source = key_source.encode()
        
        # 使用PBKDF2派生密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'gmas_config_salt',  # 在生产环境中应使用随机盐
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(key_source))
        self._cipher = Fernet(key)
        
        self.logger.info("配置加密已启用")
    
    def _load_key_from_file(self) -> Optional[bytes]:
        """从密钥文件加载密钥"""
        key_file = Path.home() / '.gmas' / 'config.key'
        if key_file.exists():
            try:
                return key_file.read_bytes()
            except Exception as e:
                self.logger.warning(f"读取密钥文件失败: {e}")
        return None
    
    def _generate_machine_key(self) -> bytes:
        """基于机器指纹生成密钥"""
        import platform
        import hashlib
        
        # 收集机器信息
        machine_info = [
            platform.node(),                    # 主机名
            platform.machine(),                 # 架构
            platform.processor(),               # 处理器
            str(os.getlogin() if hasattr(os, 'getlogin') else 'unknown')  # 用户名
        ]
        
        # 生成指纹
        fingerprint = '|'.join(machine_info).encode()
        return hashlib.sha256(fingerprint).digest()
    
    def _encrypt_value(self, value: str) -> str:
        """加密配置值"""
        if not hasattr(self, '_cipher'):
            return value
        
        try:
            encrypted = self._cipher.encrypt(value.encode())
            return f"ENC:{base64.urlsafe_b64encode(encrypted).decode()}"
        except Exception as e:
            self.logger.error(f"配置值加密失败: {e}")
            return value
    
    def _decrypt_value(self, value: str) -> str:
        """解密配置值"""
        if not isinstance(value, str) or not value.startswith('ENC:'):
            return value
            
        if not hasattr(self, '_cipher'):
            self.logger.warning("尝试解密配置值但加密未启用")
            return value
        
        try:
            encrypted_data = base64.urlsafe_b64decode(value[4:].encode())
            decrypted = self._cipher.decrypt(encrypted_data)
            return decrypted.decode()
        except Exception as e:
            self.logger.error(f"配置值解密失败: {e}")
            return value  # 返回原值，避免系统崩溃
    
    def get(self, key: str, default: Any = None, use_cache: bool = True, expand_vars: bool = True) -> Any:
        """获取配置值（自动解密）"""
        # ... 现有get方法逻辑 ...
        
        # 在返回值之前解密
        if isinstance(value, str) and value.startswith('ENC:'):
            value = self._decrypt_value(value)
        elif isinstance(value, dict):
            value = self._decrypt_dict_values(value)
        elif isinstance(value, list):
            value = [self._decrypt_value(v) if isinstance(v, str) else v for v in value]
        
        # ... 现有缓存和返回逻辑 ...
    
    def _decrypt_dict_values(self, data: dict) -> dict:
        """递归解密字典中的值"""
        result = {}
        for k, v in data.items():
            if isinstance(v, str) and v.startswith('ENC:'):
                result[k] = self._decrypt_value(v)
            elif isinstance(v, dict):
                result[k] = self._decrypt_dict_values(v)
            elif isinstance(v, list):
                result[k] = [self._decrypt_value(item) if isinstance(item, str) else item for item in v]
            else:
                result[k] = v
        return result
    
    def encrypt_sensitive_config(self, sensitive_keys: List[str] = None):
        """加密配置中的敏感字段"""
        if not self._encryption_enabled:
            raise ConfigError("加密功能未启用")
        
        if sensitive_keys is None:
            sensitive_keys = ['password', 'secret', 'key', 'token', 'api_key']
        
        def encrypt_recursive(data: dict, path: str = ""):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                
                if isinstance(value, dict):
                    encrypt_recursive(value, current_path)
                elif isinstance(value, str) and not value.startswith('ENC:'):
                    # 检查是否为敏感字段
                    if any(sensitive in key.lower() for sensitive in sensitive_keys):
                        encrypted_value = self._encrypt_value(value)
                        data[key] = encrypted_value
                        self.logger.info(f"已加密敏感配置: {current_path}")
        
        encrypt_recursive(self._config)
        self.clear_cache()  # 清除缓存，确保使用加密后的值
    
    def list_encrypted_fields(self) -> List[str]:
        """列出所有加密字段"""
        encrypted_fields = []
        
        def find_encrypted_recursive(data: dict, path: str = ""):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                
                if isinstance(value, dict):
                    find_encrypted_recursive(value, current_path)
                elif isinstance(value, str) and value.startswith('ENC:'):
                    encrypted_fields.append(current_path)
        
        find_encrypted_recursive(self._config)
        return encrypted_fields
```

**安全考虑**:
- 密钥不应硬编码在代码中
- 生产环境建议使用外部密钥管理系统
- 定期轮换加密密钥
- 加密字段审计和监控

**影响模块**: `get()`, `set()`, 配置加载保存流程，新增加密管理接口  
**测试要求**: 加密解密准确性、密钥管理、性能影响评估

---

### 优先级4 - 扩展功能 (长期规划)

#### 6. 配置模板和继承 📋
**描述**: 支持配置模板和继承机制，简化配置管理

**实现要点**:
- 配置模板定义
- 模板继承和覆盖
- 占位符替换
- 模板验证

#### 7. 配置可视化界面 🖥️
**描述**: Web界面或GUI工具进行配置管理

**实现要点**:
- 配置项可视化编辑
- 实时配置预览
- 配置历史查看
- 批量配置管理

#### 8. 分布式配置同步 🌐
**描述**: 支持多实例间的配置同步

**实现要点**:
- 配置版本控制
- 节点间同步机制
- 冲突解决策略
- 配置一致性保证

---

## 📋 实施计划

### 阶段1: 基础功能完善 (短期 - 1-2周) 🎯
**目标**: 完善核心配置管理功能

- [ ] **多环境支持** (高优先级)
  - [ ] 实现环境配置文件加载
  - [ ] 深度配置合并机制
  - [ ] 环境变量检测和设置
  - [ ] 环境隔离验证测试

- [ ] **配置备份管理** (高优先级)  
  - [ ] 自动备份机制
  - [ ] 备份文件管理和清理
  - [ ] 备份恢复功能
  - [ ] 备份完整性验证

- [ ] **单元测试覆盖**
  - [ ] 环境配置加载测试
  - [ ] 备份创建和恢复测试
  - [ ] 异常情况处理测试

**成功标准**: 通过所有测试用例，功能稳定运行

---

### 阶段2: 增强功能开发 (中期 - 2-3周) 🚀
**目标**: 添加高级配置管理功能

- [ ] **性能监控系统** (中等优先级)
  - [ ] 方法执行时间监控
  - [ ] 缓存命中率统计
  - [ ] 性能报告生成
  - [ ] 性能警告机制

- [ ] **配置导入导出** (中等优先级)
  - [ ] 多格式支持 (YAML/JSON/INI)
  - [ ] 敏感信息脱敏
  - [ ] 配置差异对比
  - [ ] 安全验证机制

- [ ] **缓存策略优化**
  - [ ] 智能缓存预热
  - [ ] 缓存分层策略
  - [ ] 内存使用优化

**成功标准**: 性能提升明显，导入导出功能完整

---

### 阶段3: 安全和扩展 (长期 - 按需实现) 🔒
**目标**: 提供企业级安全和扩展功能

- [ ] **配置加密支持** (低优先级)
  - [ ] 敏感字段加密
  - [ ] 密钥管理策略
  - [ ] 透明解密访问
  - [ ] 加密字段审计

- [ ] **高级功能探索**
  - [ ] 配置模板和继承
  - [ ] 配置可视化界面
  - [ ] 分布式配置同步

**成功标准**: 安全性达到企业级要求，扩展功能可用

---

## 🔧 技术依赖和兼容性

### 现有依赖项 ✅
```yaml
# 已在项目中使用
watchdog>=2.1.0        # 文件监控
PyYAML>=6.0            # YAML解析  
pathlib                # 路径处理 (Python标准库)
threading               # 线程安全 (Python标准库)
datetime                # 时间处理 (Python标准库)
```

### 新增依赖项 📦
```yaml
# 阶段2需要
configparser            # INI格式支持 (Python标准库)

# 阶段3需要  
cryptography>=3.4.8     # 配置加密支持
flask>=2.0.0            # Web界面 (可选)
```

### Python版本兼容性
- **最低要求**: Python 3.8+ 
- **推荐版本**: Python 3.9+
- **测试覆盖**: Python 3.8, 3.9, 3.10, 3.11

---

## 📝 开发规范和注意事项

### 代码质量要求 ✨
1. **向后兼容性**: 
   - 所有新功能必须保持与现有API的100%兼容
   - 废弃功能需要提供迁移指南和过渡期

2. **测试覆盖率**: 
   - 新功能测试覆盖率 ≥ 90%
   - 包含单元测试、集成测试、异常测试
   - 性能基准测试

3. **文档要求**:
   - 所有公共方法需要完整的docstring
   - 代码注释说明复杂逻辑
   - 更新用户使用文档

4. **性能要求**:
   - 新功能不能显著影响现有性能 (< 5%性能损失)
   - 内存使用增长可控
   - 启动时间不超过现有基准的110%

### 安全考虑 🔐
1. **输入验证**: 所有外部输入必须验证
2. **错误处理**: 避免敏感信息泄露到日志
3. **权限控制**: 配置文件访问权限检查
4. **加密存储**: 敏感配置加密存储

### 日志规范 📊
1. **日志级别使用**:
   - `DEBUG`: 详细调试信息
   - `INFO`: 关键操作成功信息
   - `WARNING`: 非致命性问题
   - `ERROR`: 需要关注的错误

2. **日志内容要求**:
   - 包含操作上下文
   - 避免记录敏感信息
   - 提供足够的故障排查信息

---

## 🧪 测试策略

### 单元测试覆盖范围 ✅
- [ ] **多环境配置**
  - [ ] 环境配置文件加载
  - [ ] 配置合并逻辑
  - [ ] 环境变量处理
  - [ ] 异常情况处理

- [ ] **备份管理**
  - [ ] 备份创建和命名
  - [ ] 备份恢复验证
  - [ ] 备份清理策略
  - [ ] 完整性检查

- [ ] **性能监控**
  - [ ] 统计数据准确性
  - [ ] 报告生成正确性
  - [ ] 性能数据重置

- [ ] **导入导出**
  - [ ] 多格式转换准确性
  - [ ] 敏感信息脱敏
  - [ ] 配置合并策略
  - [ ] 差异计算正确性

- [ ] **配置加密**
  - [ ] 加密解密准确性
  - [ ] 密钥管理安全性
  - [ ] 性能影响评估
  - [ ] 兼容性验证

### 集成测试场景 🔄
- [ ] **完整配置生命周期**
  - [ ] 加载 → 修改 → 保存 → 重载
  - [ ] 多环境配置切换
  - [ ] 备份和恢复流程

- [ ] **并发访问测试**
  - [ ] 多线程同时读写配置
  - [ ] 缓存一致性验证
  - [ ] 死锁检测

- [ ] **异常场景恢复**
  - [ ] 配置文件损坏恢复
  - [ ] 网络中断处理
  - [ ] 权限问题处理

### 性能基准测试 📈
- [ ] **基础性能指标**
  - [ ] 配置加载时间 (< 100ms)
  - [ ] 配置获取时间 (< 1ms)
  - [ ] 内存使用量 (< 10MB基础)
  - [ ] 缓存命中率 (> 90%)

- [ ] **压力测试**
  - [ ] 大配置文件处理 (>1MB)
  - [ ] 高频配置访问 (>1000 QPS)
  - [ ] 长期运行稳定性 (24小时+)

---

## 📊 项目跟踪

### 当前进度概览
```
总体进度: ████████████░░ 85%

✅ 已完成 (85%):
- 核心配置管理功能
- 缓存和热重载机制  
- 变量展开和验证
- 线程安全和异常处理
- 🆕 平台特定配置支持
- 🆕 智能变量展开
- 🆕 路径标准化

🚧 进行中 (0%):
- 无

⏳ 待开始 (15%):
- 环境特定配置完善
- 配置备份管理
- 性能监控
- 导入导出功能
- 配置加密
```

### 里程碑时间表
| 阶段 | 开始时间 | 预计完成 | 状态 |
|------|----------|----------|------|
| 阶段1: 基础功能 | 待定 | +2周 | ⏳ 未开始 |
| 阶段2: 增强功能 | 待定 | +3周 | ⏳ 未开始 |  
| 阶段3: 安全扩展 | 待定 | 按需 | ⏳ 未开始 |

---

**最后更新**: 2025年9月11日  
**创建人**: Kai Cao
**版本**: v1.0.0 (基于实际代码分析优化)  
