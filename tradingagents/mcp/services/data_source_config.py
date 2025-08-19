"""
数据源配置管理
支持环境变量和配置文件的灵活配置
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class DataSourceStrategy(Enum):
    """数据源策略"""
    FREE = "free"           # 仅使用免费数据源
    ALPHA_VANTAGE = "alpha_vantage"  # 优先使用Alpha Vantage
    AUTO = "auto"           # 自动选择最优数据源

class DataSourceConfig:
    """数据源配置管理器"""
    
    def __init__(self):
        self.strategy = self._get_strategy()
        self.fallback_enabled = self._get_fallback_enabled()
        self.api_keys = self._load_api_keys()
        self.source_priorities = self._load_source_priorities()
        self.rate_limits = self._load_rate_limits()
        
    def _get_strategy(self) -> DataSourceStrategy:
        """获取数据源策略"""
        strategy_str = os.getenv('DATA_SOURCE_STRATEGY', 'free').lower()
        try:
            return DataSourceStrategy(strategy_str)
        except ValueError:
            logger.warning(f"未知的数据源策略: {strategy_str}, 使用默认策略: free")
            return DataSourceStrategy.FREE
    
    def _get_fallback_enabled(self) -> bool:
        """获取自动降级设置"""
        return os.getenv('ENABLE_AUTO_FALLBACK', 'true').lower() == 'true'
    
    def _load_api_keys(self) -> Dict[str, str]:
        """加载API密钥"""
        return {
            'alpha_vantage': os.getenv('ALPHA_VANTAGE_API_KEY', ''),
            'finnhub': os.getenv('FINNHUB_API_KEY', ''),  # 保持兼容性
        }
    
    def _load_source_priorities(self) -> Dict[str, List[str]]:
        """加载数据源优先级"""
        defaults = {
            'news': ['google_news'],
            'profile': ['yfinance']
        }
        
        # 根据策略调整默认优先级
        if self.strategy == DataSourceStrategy.ALPHA_VANTAGE:
            if self.api_keys.get('alpha_vantage'):
                defaults['news'] = ['alpha_vantage', 'google_news']
                defaults['profile'] = ['alpha_vantage', 'yfinance']
        elif self.strategy == DataSourceStrategy.AUTO:
            if self.api_keys.get('alpha_vantage'):
                defaults['news'] = ['alpha_vantage', 'google_news']
                defaults['profile'] = ['alpha_vantage', 'yfinance']
        
        # 从环境变量覆盖
        news_priority = os.getenv('NEWS_SOURCE_PRIORITY')
        if news_priority:
            defaults['news'] = [s.strip() for s in news_priority.split(',')]
            
        profile_priority = os.getenv('PROFILE_SOURCE_PRIORITY')
        if profile_priority:
            defaults['profile'] = [s.strip() for s in profile_priority.split(',')]
        
        return defaults
    
    def _load_rate_limits(self) -> Dict[str, Dict[str, Any]]:
        """加载API限制配置"""
        return {
            'alpha_vantage': {
                'daily_limit': 500,
                'per_minute_limit': 5,
                'tracking_enabled': True
            },
            'google_news': {
                'daily_limit': -1,  # 无限制
                'per_minute_limit': -1,
                'tracking_enabled': False
            },
            'yfinance': {
                'daily_limit': -1,  # 无限制
                'per_minute_limit': 60,  # 估算限制
                'tracking_enabled': False
            }
        }
    
    def get_news_sources(self) -> List[str]:
        """获取新闻数据源优先级列表"""
        return self.source_priorities.get('news', ['google_news'])
    
    def get_profile_sources(self) -> List[str]:
        """获取公司信息数据源优先级列表"""
        return self.source_priorities.get('profile', ['yfinance'])
    
    def get_api_key(self, source: str) -> Optional[str]:
        """获取指定数据源的API密钥"""
        key = self.api_keys.get(source, '')
        return key if key else None
    
    def is_source_available(self, source: str) -> bool:
        """检查数据源是否可用"""
        if source in ['google_news', 'yfinance']:
            return True  # 免费数据源总是可用
        
        if source == 'alpha_vantage':
            return bool(self.get_api_key('alpha_vantage'))
        
        return False
    
    def get_fallback_source(self, data_type: str) -> str:
        """获取指定数据类型的降级数据源"""
        fallback_map = {
            'news': 'google_news',
            'profile': 'yfinance'
        }
        return fallback_map.get(data_type, 'google_news')
    
    def should_use_fallback(self, source: str, error_type: str = None) -> bool:
        """判断是否应该使用降级策略"""
        if not self.fallback_enabled:
            return False
        
        # API限制错误时启用降级
        if error_type in ['rate_limit', 'quota_exceeded', 'api_key_invalid']:
            return True
        
        # 数据源不可用时启用降级
        if not self.is_source_available(source):
            return True
        
        return False
    
    def get_cache_timeout(self, source: str, data_type: str) -> int:
        """获取缓存超时时间(秒)"""
        cache_config = {
            'alpha_vantage': {'news': 3600, 'profile': 21600},  # 1小时/6小时
            'google_news': {'news': 900, 'profile': 900},       # 15分钟
            'yfinance': {'news': 900, 'profile': 14400}         # 15分钟/4小时
        }
        
        source_config = cache_config.get(source, {})
        return source_config.get(data_type, 900)  # 默认15分钟
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'strategy': self.strategy.value,
            'fallback_enabled': self.fallback_enabled,
            'api_keys_configured': {
                source: bool(key) for source, key in self.api_keys.items()
            },
            'source_priorities': self.source_priorities,
            'available_sources': {
                'alpha_vantage': self.is_source_available('alpha_vantage'),
                'google_news': self.is_source_available('google_news'),
                'yfinance': self.is_source_available('yfinance')
            }
        }
    
    def __str__(self) -> str:
        return f"DataSourceConfig(strategy={self.strategy.value}, fallback={self.fallback_enabled})"


# 全局配置实例
_global_config = None

def get_data_source_config() -> DataSourceConfig:
    """获取全局数据源配置"""
    global _global_config
    if _global_config is None:
        _global_config = DataSourceConfig()
    return _global_config

def reload_config() -> DataSourceConfig:
    """重新加载配置"""
    global _global_config
    _global_config = DataSourceConfig()
    return _global_config