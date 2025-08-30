# -*- coding: utf-8 -*-
"""
验证器类型定义
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from .enums import ValidatorType, ValidationLevel
from .base import BaseConfig


class Validator(ABC):
    """验证器抽象基类 - 来自 validators/common.py"""
    
    @abstractmethod
    def validate(self, value: str) -> bool:
        """验证字符串
        
        Args:
            value: 要验证的字符串
            
        Returns:
            bool: 是否有效
        """
        pass
    
    @abstractmethod
    def get_error_message(self) -> str:
        """获取错误信息"""
        pass


@dataclass
class ValidationResult:
    """验证结果类"""
    is_valid: bool = False
    error_message: str = ""
    suggestions: List[str] = field(default_factory=list)
    validated_value: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidatorDefinition(BaseConfig):
    """验证器定义类"""
    validator_type: ValidatorType = ValidatorType.CUSTOM
    validation_level: ValidationLevel = ValidationLevel.BASIC
    validator_class: Optional[type] = None
    validator_function: Optional[Callable[[str], bool]] = None
    config_params: Dict[str, Any] = field(default_factory=dict)
    error_messages: Dict[str, str] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """验证定义的有效性"""
        if self.validator_class is None and self.validator_function is None:
            return False
        return True


@dataclass
class ValidationRule:
    """验证规则类"""
    rule_name: str
    validator_type: ValidatorType
    parameters: Dict[str, Any] = field(default_factory=dict)
    required: bool = True
    error_message: str = ""
    
    def apply(self, value: str) -> ValidationResult:
        """应用验证规则"""
        # 这里应该根据 validator_type 创建相应的验证器并执行验证
        # 目前返回一个默认结果
        return ValidationResult(
            is_valid=True,
            validated_value=value
        )


@dataclass
class ValidationSchema:
    """验证模式类"""
    schema_name: str
    rules: List[ValidationRule] = field(default_factory=list)
    strict_mode: bool = False
    stop_on_first_error: bool = False
    
    def validate_value(self, value: str) -> List[ValidationResult]:
        """根据模式验证值"""
        results = []
        
        for rule in self.rules:
            result = rule.apply(value)
            results.append(result)
            
            if not result.is_valid and self.stop_on_first_error:
                break
                
        return results
    
    def is_valid(self, value: str) -> bool:
        """检查值是否通过所有验证"""
        results = self.validate_value(value)
        
        if self.strict_mode:
            return all(r.is_valid for r in results)
        else:
            # 非严格模式下，只要有一个required规则通过即可
            required_results = [r for r, rule in zip(results, self.rules) if rule.required]
            if required_results:
                return any(r.is_valid for r in required_results)
            else:
                return any(r.is_valid for r in results)
