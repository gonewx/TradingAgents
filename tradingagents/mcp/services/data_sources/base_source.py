"""
数据源基类
定义统一的数据源接口
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class DataSourceType(Enum):
    """数据源类型"""
    NEWS = "news"
    PROFILE = "profile"
    MARKET = "market"

class BaseDataSource(ABC):
    """数据源基类"""
    
    def __init__(self, name: str, source_type: DataSourceType):
        self.name = name
        self.source_type = source_type
        self.cache = {}
        self.cache_timeout = 300  # 默认5分钟缓存
        
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass
    
    @abstractmethod
    async def get_company_news(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取公司新闻"""
        pass
    
    @abstractmethod 
    async def get_company_profile(
        self, 
        symbol: str, 
        detailed: bool = False
    ) -> Dict[str, Any]:
        """获取公司信息"""
        pass
    
    @abstractmethod
    async def is_supported(self, symbol: str) -> bool:
        """检查是否支持该股票代码"""
        pass
        
    @abstractmethod
    async def get_rate_limit_info(self) -> Dict[str, Any]:
        """获取API限制信息"""
        pass
    
    def _is_cache_valid(self, key: str) -> bool:
        """检查缓存是否有效"""
        if key not in self.cache:
            return False
        
        from datetime import datetime
        cache_time = self.cache[key]["timestamp"]
        return (datetime.now() - cache_time).seconds < self.cache_timeout
    
    def _cache_data(self, key: str, data: Any) -> None:
        """缓存数据"""
        from datetime import datetime
        self.cache[key] = {
            "data": data,
            "timestamp": datetime.now()
        }
        
    def _get_cached_data(self, key: str) -> Any:
        """获取缓存数据"""
        if self._is_cache_valid(key):
            return self.cache[key]["data"]
        return None
    
    def __str__(self) -> str:
        return f"{self.name}DataSource({self.source_type.value})"
    
    def __repr__(self) -> str:
        return self.__str__()