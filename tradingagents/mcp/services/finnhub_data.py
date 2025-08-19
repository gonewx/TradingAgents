"""
Finnhub 数据服务模块
提供公司新闻、内部交易情绪和交易数据
"""

import os
import asyncio
import logging
import finnhub
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
from .proxy_config import get_proxy_config
from .exchange_compatibility import ExchangeCompatibilityChecker, DataSource

logger = logging.getLogger(__name__)

class FinnhubDataService:
    """Finnhub 数据服务"""
    
    def __init__(self):
        self.api_key = os.getenv("FINNHUB_API_KEY")
        self.proxy_config = get_proxy_config()
        
        if not self.api_key:
            logger.warning("FINNHUB_API_KEY not found in environment variables")
            self.client = None
        else:
            # 使用代理配置设置 Finnhub 客户端
            self.client = self.proxy_config.setup_finnhub_client(self.api_key)
            if self.client is None:
                self.client = finnhub.Client(api_key=self.api_key)
            logger.info("Finnhub 客户端初始化完成（支持代理）")
        
        self.cache = {}
        # 从环境变量读取数据缓存超时，Finnhub数据变化较慢，默认30分钟
        self.cache_timeout = int(os.getenv('DATA_CACHE_TTL', '1800'))
    
    async def health_check(self) -> bool:
        """健康检查"""
        if not self.client:
            return False
        
        try:
            # 测试基础 API 调用
            profile = self.client.company_profile2(symbol='AAPL')
            return bool(profile.get('name'))
        except Exception as e:
            logger.error(f"Finnhub health check failed: {e}")
            return False
    
    async def get_company_news(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str
    ) -> List[Dict[str, Any]]:
        """获取公司新闻"""
        if not self.client:
            logger.error("Finnhub client not initialized")
            return [{
                "error": "FINNHUB_NOT_INITIALIZED",
                "message": "Finnhub客户端未初始化，请检查API密钥配置"
            }]
        
        # 检查兼容性
        if not ExchangeCompatibilityChecker.is_supported(symbol, DataSource.FINNHUB):
            _, exchange = ExchangeCompatibilityChecker.parse_symbol(symbol)
            return [{
                "error": "EXCHANGE_NOT_SUPPORTED",
                "message": f"Finnhub不支持交易所 {exchange.value if exchange else 'UNKNOWN'}的股票代码格式",
                "original_symbol": symbol,
                "suggestion": "请使用news_feed服务的Google News获取该股票的新闻"
            }]
        
        # 格式化为Finnhub要求的格式
        finnhub_symbol = ExchangeCompatibilityChecker.format_for_finnhub(symbol)
        if not finnhub_symbol:
            return [{
                "error": "SYMBOL_FORMAT_ERROR",
                "message": f"无法将代码 {symbol} 转换为Finnhub格式"
            }]
        
        try:
            cache_key = f"news_{finnhub_symbol}_{start_date}_{end_date}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            # 转换日期格式
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            # Finnhub API 需要 Unix 时间戳
            start_timestamp = int(start_dt.timestamp())
            end_timestamp = int(end_dt.timestamp())
            
            logger.info(f"获取公司新闻: {symbol} -> {finnhub_symbol}")
            news_data = self.client.company_news(
                symbol=finnhub_symbol,
                _from=start_timestamp,
                to=end_timestamp
            )
            
            # 格式化新闻数据
            formatted_news = []
            for article in news_data[:20]:  # 限制返回前20条
                formatted_news.append({
                    "id": article.get("id"),
                    "headline": article.get("headline", ""),
                    "summary": article.get("summary", ""),
                    "source": article.get("source", ""),
                    "url": article.get("url", ""),
                    "datetime": datetime.fromtimestamp(
                        article.get("datetime", 0)
                    ).strftime("%Y-%m-%d %H:%M:%S"),
                    "related": article.get("related", ""),
                    "image": article.get("image", ""),
                    "category": article.get("category", "")
                })
            
            # 缓存结果
            self._cache_data(cache_key, formatted_news)
            
            return formatted_news
            
        except Exception as e:
            logger.error(f"Failed to get company news for {symbol}: {e}")
            return []
    
    async def get_insider_sentiment(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str
    ) -> Dict[str, Any]:
        """获取内部交易情绪"""
        if not self.client:
            logger.error("Finnhub client not initialized")
            return {}
        
        try:
            cache_key = f"insider_sentiment_{symbol}_{start_date}_{end_date}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            sentiment_data = self.client.stock_insider_sentiment(
                symbol=symbol,
                _from=start_date,
                to=end_date
            )
            
            if not sentiment_data or 'data' not in sentiment_data:
                return {}
            
            # 处理情绪数据
            processed_data = {
                "symbol": symbol,
                "period": f"{start_date} to {end_date}",
                "data": []
            }
            
            for item in sentiment_data['data']:
                processed_data["data"].append({
                    "year": item.get("year"),
                    "month": item.get("month"),
                    "change": item.get("change", 0),
                    "mspr": item.get("mspr", 0),  # Monthly Share Purchase Ratio
                    "mspr_percentile": item.get("mspr_percentile", 0)
                })
            
            # 缓存结果
            self._cache_data(cache_key, processed_data)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Failed to get insider sentiment for {symbol}: {e}")
            return {}
    
    async def get_insider_transactions(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str
    ) -> List[Dict[str, Any]]:
        """获取内部交易数据"""
        if not self.client:
            logger.error("Finnhub client not initialized")
            return []
        
        try:
            cache_key = f"insider_transactions_{symbol}_{start_date}_{end_date}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            transactions_data = self.client.stock_insider_transactions(
                symbol=symbol,
                _from=start_date,
                to=end_date
            )
            
            if not transactions_data or 'data' not in transactions_data:
                return []
            
            # 格式化交易数据
            formatted_transactions = []
            for transaction in transactions_data['data'][:50]:  # 限制返回前50条
                formatted_transactions.append({
                    "name": transaction.get("name", ""),
                    "share": transaction.get("share", 0),
                    "change": transaction.get("change", 0),
                    "filing_date": transaction.get("filingDate", ""),
                    "transaction_date": transaction.get("transactionDate", ""),
                    "transaction_code": transaction.get("transactionCode", ""),
                    "transaction_price": transaction.get("transactionPrice", 0)
                })
            
            # 缓存结果
            self._cache_data(cache_key, formatted_transactions)
            
            return formatted_transactions
            
        except Exception as e:
            logger.error(f"Failed to get insider transactions for {symbol}: {e}")
            return []
    
    async def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """获取公司基本信息"""
        if not self.client:
            logger.error("Finnhub client not initialized")
            return {
                "error": "FINNHUB_NOT_INITIALIZED",
                "message": "Finnhub客户端未初始化，请检查API密钥配置"
            }
        
        # 检查兼容性
        if not ExchangeCompatibilityChecker.is_supported(symbol, DataSource.FINNHUB):
            _, exchange = ExchangeCompatibilityChecker.parse_symbol(symbol)
            return {
                "error": "EXCHANGE_NOT_SUPPORTED",
                "message": f"Finnhub不支持交易所 {exchange.value if exchange else 'UNKNOWN'}的股票代码格式",
                "original_symbol": symbol,
                "supported_exchanges": ["NASDAQ", "NYSE", "HK (正确格式)", "TSX"],
                "suggestion": "请使用market_data服务获取该股票的基本信息"
            }
        
        # 格式化为Finnhub要求的格式
        finnhub_symbol = ExchangeCompatibilityChecker.format_for_finnhub(symbol)
        if not finnhub_symbol:
            return {
                "error": "SYMBOL_FORMAT_ERROR",
                "message": f"无法将代码 {symbol} 转换为Finnhub格式",
                "original_symbol": symbol
            }
        
        try:
            cache_key = f"profile_{finnhub_symbol}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            logger.info(f"获取公司资料: {symbol} -> {finnhub_symbol}")
            profile = self.client.company_profile2(symbol=finnhub_symbol)
            
            # 检查返回数据是否为空
            if not profile or not profile.get("name"):
                return {
                    "error": "NO_DATA_FOUND",
                    "message": f"Finnhub未找到代码 {finnhub_symbol} 的公司信息",
                    "original_symbol": symbol,
                    "finnhub_symbol": finnhub_symbol,
                    "suggestion": "请检查股票代码是否正确，或该股票是否在Finnhub支持范围内"
                }
            
            # 格式化公司信息
            formatted_profile = {
                "symbol": symbol,
                "finnhub_symbol": finnhub_symbol,
                "name": profile.get("name", ""),
                "country": profile.get("country", ""),
                "currency": profile.get("currency", ""),
                "exchange": profile.get("exchange", ""),
                "industry": profile.get("finnhubIndustry", ""),
                "ipo": profile.get("ipo", ""),
                "market_cap": profile.get("marketCapitalization", 0),
                "share_outstanding": profile.get("shareOutstanding", 0),
                "logo": profile.get("logo", ""),
                "weburl": profile.get("weburl", ""),
                "phone": profile.get("phone", ""),
                "data_source": "Finnhub",
                "timestamp": datetime.now().isoformat()
            }
            
            # 缓存结果
            self._cache_data(cache_key, formatted_profile)
            
            return formatted_profile
            
        except Exception as e:
            logger.error(f"Failed to get company profile for {symbol}: {e}")
            return {
                "error": "API_ERROR",
                "message": f"获取公司信息时发生错误: {str(e)}",
                "original_symbol": symbol,
                "finnhub_symbol": finnhub_symbol if 'finnhub_symbol' in locals() else None
            }
    
    async def get_market_news(
        self, 
        category: str = "general", 
        min_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取市场新闻"""
        if not self.client:
            logger.error("Finnhub client not initialized")
            return []
        
        try:
            cache_key = f"market_news_{category}_{min_id}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            kwargs = {"category": category}
            if min_id:
                kwargs["min_id"] = min_id
            
            news_data = self.client.general_news(**kwargs)
            
            # 格式化市场新闻
            formatted_news = []
            for article in news_data[:15]:  # 限制返回前15条
                formatted_news.append({
                    "id": article.get("id"),
                    "headline": article.get("headline", ""),
                    "summary": article.get("summary", ""),
                    "source": article.get("source", ""),
                    "url": article.get("url", ""),
                    "datetime": datetime.fromtimestamp(
                        article.get("datetime", 0)
                    ).strftime("%Y-%m-%d %H:%M:%S"),
                    "image": article.get("image", ""),
                    "category": category
                })
            
            # 缓存结果
            self._cache_data(cache_key, formatted_news)
            
            return formatted_news
            
        except Exception as e:
            logger.error(f"Failed to get market news for category {category}: {e}")
            return []
    
    def _is_cache_valid(self, key: str) -> bool:
        """检查缓存是否有效"""
        if key not in self.cache:
            return False
        
        cache_time = self.cache[key]["timestamp"]
        return (datetime.now() - cache_time).seconds < self.cache_timeout
    
    def _cache_data(self, key: str, data: Any) -> None:
        """缓存数据"""
        self.cache[key] = {
            "data": data,
            "timestamp": datetime.now()
        }