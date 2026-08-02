# data_processing/__init__.py
"""
数据处理模块
提供数据加载、清洗、转换、分析等功能的统一接口
"""

from .data_loader import DataLoader
from .data_cleaner import DataCleaner
from .data_transformer import DataTransformer
from .data_analyzer import DataAnalyzer
from .data_export import DataExporter

# 创建全局实例
data_loader = DataLoader()
data_cleaner = DataCleaner()
data_transformer = DataTransformer()
data_analyzer = DataAnalyzer()
data_exporter = DataExporter()

__all__ = [
    'DataLoader',
    'DataCleaner', 
    'DataTransformer',
    'DataAnalyzer',
    'DataExporter',
    'data_loader',
    'data_cleaner',
    'data_transformer',
    'data_analyzer',
    'data_exporter'
]