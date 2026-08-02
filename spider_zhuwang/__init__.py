# spider_zhuwang/__init__.py
"""
养猪网数据爬虫模块
"""

from .pig_spider import PigPriceSpider, PigSpiderConfig
from .corn_spider import CornPriceSpider

__all__ = [
    'PigPriceSpider',
    'PigSpiderConfig',
    'CornPriceSpider'
]