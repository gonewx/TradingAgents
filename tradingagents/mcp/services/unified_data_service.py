"""
统一数据服务
整合多个数据源，提供统一的数据接口，支持自动降级和负载均衡
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Type
from datetime import datetime

from .data_source_config import get_data_source_config, DataSourceStrategy
from .data_sources import (
    BaseDataSource, 
    GoogleNewsSource, 
    YfinanceSource, 
    AlphaVantageSource
)

logger = logging.getLogger(__name__)

class UnifiedDataService:
    """统一数据服务"""
    
    def __init__(self):
        self.config = get_data_source_config()
        self.data_sources: Dict[str, BaseDataSource] = {}
        self._initialize_sources()
        
        logger.info("统一数据服务初始化完成")
    
    def _initialize_sources(self):
        """初始化数据源"""
        try:
            # 初始化 Google News
            self.data_sources['google_news'] = GoogleNewsSource()
            
            # 初始化 yfinance
            self.data_sources['yfinance'] = YfinanceSource()
            
            # 初始化 Alpha Vantage (如果有API密钥)
            alpha_key = self.config.get_api_key('alpha_vantage')
            if alpha_key:
                self.data_sources['alpha_vantage'] = AlphaVantageSource(alpha_key)
                logger.info("Alpha Vantage 数据源已启用")
            else:
                logger.info("Alpha Vantage API密钥未配置，使用免费数据源")
                
        except Exception as e:
            logger.error(f"数据源初始化失败: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查所有数据源"""
        health_status = {}
        
        for source_name, source in self.data_sources.items():
            try:
                is_healthy = await source.health_check()
                health_status[source_name] = "healthy" if is_healthy else "unhealthy"
            except Exception as e:
                logger.error(f"{source_name} 健康检查失败: {e}")
                health_status[source_name] = f"error: {str(e)}"
        
        return {
            "unified_service": "healthy",
            "data_sources": health_status,
            "config": self.config.to_dict(),
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_company_news_unified(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str,
        source: str = "auto",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """统一的公司新闻接口"""
        try:
            # 确定数据源优先级
            sources_to_try = self._get_sources_for_news(source)
            
            last_error = None
            
            for source_name in sources_to_try:
                try:
                    if source_name not in self.data_sources:
                        continue
                    
                    data_source = self.data_sources[source_name]
                    
                    # 检查是否支持
                    if not await data_source.is_supported(symbol):
                        continue
                    
                    logger.info(f"使用 {source_name} 获取 {symbol} 的新闻")
                    result = await data_source.get_company_news(symbol, start_date, end_date, limit)
                    
                    # 检查结果是否有效
                    if result and not self._is_error_result(result):
                        # 添加数据源标识
                        for item in result:
                            if isinstance(item, dict):
                                item['unified_source'] = source_name
                        return result
                    
                    # 检查是否需要降级
                    if result and self._should_fallback(result, source_name):
                        logger.warning(f"{source_name} 返回错误，尝试降级")
                        continue
                        
                except Exception as e:
                    logger.error(f"{source_name} 获取新闻失败: {e}")
                    last_error = e
                    continue
            
            # 所有数据源都失败
            return [{
                "error": "ALL_SOURCES_FAILED",
                "message": "所有数据源都无法获取新闻",
                "last_error": str(last_error) if last_error else "未知错误",
                "symbol": symbol,
                "attempted_sources": sources_to_try
            }]
            
        except Exception as e:
            logger.error(f"统一新闻服务失败: {e}")
            return [{
                "error": "UNIFIED_SERVICE_ERROR",
                "message": f"统一服务内部错误: {str(e)}",
                "symbol": symbol
            }]
    
    async def get_company_profile_unified(
        self, 
        symbol: str,
        source: str = "auto",
        detailed: bool = False
    ) -> Dict[str, Any]:
        """统一的公司信息接口"""
        try:
            # 确定数据源优先级
            sources_to_try = self._get_sources_for_profile(source)
            
            last_error = None
            
            for source_name in sources_to_try:
                try:
                    if source_name not in self.data_sources:
                        continue
                    
                    data_source = self.data_sources[source_name]
                    
                    # 检查是否支持
                    if not await data_source.is_supported(symbol):
                        continue
                    
                    logger.info(f"使用 {source_name} 获取 {symbol} 的公司信息")
                    result = await data_source.get_company_profile(symbol, detailed)
                    
                    # 检查结果是否有效
                    if result and not result.get('error'):
                        result['unified_source'] = source_name
                        return result
                    
                    # 检查是否需要降级
                    if result and self._should_fallback([result], source_name):
                        logger.warning(f"{source_name} 返回错误，尝试降级")
                        continue
                        
                except Exception as e:
                    logger.error(f"{source_name} 获取公司信息失败: {e}")
                    last_error = e
                    continue
            
            # 所有数据源都失败
            return {
                "error": "ALL_SOURCES_FAILED",
                "message": "所有数据源都无法获取公司信息",
                "last_error": str(last_error) if last_error else "未知错误",
                "symbol": symbol,
                "attempted_sources": sources_to_try
            }
            
        except Exception as e:
            logger.error(f"统一公司信息服务失败: {e}")
            return {
                "error": "UNIFIED_SERVICE_ERROR",
                "message": f"统一服务内部错误: {str(e)}",
                "symbol": symbol
            }
    
    def _get_sources_for_news(self, requested_source: str) -> List[str]:
        """获取新闻数据源优先级"""
        if requested_source != "auto":
            # 指定数据源
            if requested_source in self.data_sources:
                return [requested_source]
            else:
                logger.warning(f"请求的数据源 {requested_source} 不可用，使用自动选择")
        
        # 自动选择
        sources = self.config.get_news_sources().copy()
        
        # 过滤不可用的数据源
        available_sources = [s for s in sources if s in self.data_sources]
        
        if not available_sources:
            available_sources = ['google_news']  # 默认降级
        
        return available_sources
    
    def _get_sources_for_profile(self, requested_source: str) -> List[str]:
        """获取公司信息数据源优先级"""
        if requested_source != "auto":
            # 指定数据源
            if requested_source in self.data_sources:
                return [requested_source]
            else:
                logger.warning(f"请求的数据源 {requested_source} 不可用，使用自动选择")
        
        # 自动选择
        sources = self.config.get_profile_sources().copy()
        
        # 过滤不可用的数据源
        available_sources = [s for s in sources if s in self.data_sources]
        
        if not available_sources:
            available_sources = ['yfinance']  # 默认降级
        
        return available_sources
    
    def _is_error_result(self, result: List[Dict[str, Any]]) -> bool:
        """检查结果是否为错误"""
        if not result:
            return True
        
        if len(result) == 1 and isinstance(result[0], dict) and result[0].get('error'):
            return True
        
        return False
    
    def _should_fallback(self, result: List[Dict[str, Any]], source_name: str) -> bool:
        """判断是否应该降级到其他数据源"""
        if not self.config.fallback_enabled:
            return False
        
        if not result:
            return True
        
        # 检查是否有错误需要降级
        for item in result:
            if isinstance(item, dict) and item.get('error'):
                error_type = item.get('error')
                if error_type in ['RATE_LIMIT_EXCEEDED', 'QUOTA_EXCEEDED', 'API_KEY_INVALID']:
                    return True
        
        return False
    
    async def get_data_source_status(self) -> Dict[str, Any]:
        """获取数据源状态"""
        status = {}
        
        for source_name, source in self.data_sources.items():
            try:
                rate_limit_info = await source.get_rate_limit_info()
                health = await source.health_check()
                
                status[source_name] = {
                    "healthy": health,
                    "rate_limit": rate_limit_info,
                    "type": source.source_type.value,
                    "description": str(source)
                }
            except Exception as e:
                status[source_name] = {
                    "healthy": False,
                    "error": str(e)
                }
        
        return status
    
    def get_available_sources(self) -> Dict[str, List[str]]:
        """获取可用的数据源"""
        return {
            "news": [name for name, source in self.data_sources.items() 
                    if hasattr(source, 'get_company_news')],
            "profile": [name for name, source in self.data_sources.items() 
                       if hasattr(source, 'get_company_profile')]
        }
    
    def reload_config(self):
        """重新加载配置"""
        try:
            from .data_source_config import reload_config
            self.config = reload_config()
            
            # 重新初始化数据源
            self.data_sources.clear()
            self._initialize_sources()
            
            logger.info("配置重新加载完成")
        except Exception as e:
            logger.error(f"重新加载配置失败: {e}")


# 全局统一服务实例
_global_service = None

def get_unified_data_service() -> UnifiedDataService:
    """获取全局统一数据服务"""
    global _global_service
    if _global_service is None:
        _global_service = UnifiedDataService()
    return _global_service