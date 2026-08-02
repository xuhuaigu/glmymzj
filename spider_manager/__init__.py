# spider_manager/__init__.py
"""
爬虫管理模块
"""

from .spider_core import SpiderCore, SpiderTask

# 创建全局实例
spider_core = SpiderCore()

__all__ = [
    'SpiderCore',
    'SpiderTask',
    'spider_core'
]