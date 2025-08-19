"""
yfinance 数据源
基于 yfinance 提供免费的股票信息和市场数据
"""

import asyncio
import logging
import yfinance as yf
from typing import Dict, List, Any
from datetime import datetime, timedelta

from .base_source import BaseDataSource, DataSourceType
from ..proxy_config import get_proxy_config

logger = logging.getLogger(__name__)

class YfinanceSource(BaseDataSource):
    """yfinance 数据源"""
    
    def __init__(self):
        super().__init__("yfinance", DataSourceType.PROFILE)
        self.cache_timeout = 14400  # 4小时缓存
        self.proxy_config = get_proxy_config()
        self._setup_yfinance_proxy()
        
        logger.info("yfinance 数据源初始化完成")
    
    def _setup_yfinance_proxy(self):
        """为 yfinance 设置代理"""
        try:
            proxies = self.proxy_config.get_proxies()
            if proxies:
                session = self.proxy_config.setup_requests_session()
                
                # 尝试为 yfinance 设置自定义会话
                try:
                    if hasattr(yf, 'session'):
                        yf.session = session
                except AttributeError:
                    pass
                
                logger.info("yfinance 代理配置完成")
            else:
                logger.info("yfinance 使用直连（无代理）")
        except Exception as e:
            logger.warning(f"yfinance 代理配置失败: {e}")
    
    def _get_ticker_with_proxy(self, symbol: str):
        """获取带代理配置的 ticker 对象"""
        try:
            ticker = yf.Ticker(symbol)
            
            # 如果需要，可以为每个 ticker 实例设置代理会话
            proxies = self.proxy_config.get_proxies()
            if proxies and hasattr(ticker, 'session'):
                ticker.session = self.proxy_config.setup_requests_session()
            
            return ticker
        except Exception as e:
            logger.error(f"创建 ticker 失败 {symbol}: {e}")
            return yf.Ticker(symbol)  # 回退到基本实现
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            stock = self._get_ticker_with_proxy("AAPL")
            info = stock.info
            return bool(info.get("symbol"))
        except Exception as e:
            logger.error(f"yfinance 健康检查失败: {e}")
            return False
    
    async def get_company_news(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """yfinance 不支持新闻查询"""
        return [{
            "error": "NOT_SUPPORTED",
            "message": "yfinance 数据源不支持新闻查询",
            "suggestion": "请使用 google_news 或 alpha_vantage 数据源"
        }]
    
    async def get_company_profile(
        self, 
        symbol: str, 
        detailed: bool = False
    ) -> Dict[str, Any]:
        """获取公司信息"""
        try:
            cache_key = f"profile_{symbol}_{detailed}"
            cached_data = self._get_cached_data(cache_key)
            if cached_data is not None:
                return cached_data
            
            # 获取股票信息
            stock = self._get_ticker_with_proxy(symbol)
            info = stock.info
            
            if not info or not info.get("symbol"):
                return {
                    "error": "NO_DATA_FOUND",
                    "message": f"未找到股票代码 {symbol} 的信息",
                    "original_symbol": symbol,
                    "data_source": "yfinance"
                }
            
            # 基础公司信息
            profile = {
                "symbol": symbol,
                "yfinance_symbol": info.get("symbol", symbol),
                "name": info.get("longName", info.get("shortName", "")),
                "country": info.get("country", ""),
                "currency": info.get("currency", ""),
                "exchange": info.get("exchange", ""),
                "industry": info.get("industry", ""),
                "sector": info.get("sector", ""),
                "website": info.get("website", ""),
                "business_summary": info.get("longBusinessSummary", ""),
                "employees": info.get("fullTimeEmployees"),
                "market_cap": info.get("marketCap"),
                "enterprise_value": info.get("enterpriseValue"),
                "shares_outstanding": info.get("sharesOutstanding"),
                "float_shares": info.get("floatShares"),
                "data_source": "yfinance",
                "timestamp": datetime.now().isoformat()
            }
            
            # 详细信息
            if detailed:
                profile.update({
                    # 财务指标
                    "trailing_pe": info.get("trailingPE"),
                    "forward_pe": info.get("forwardPE"),
                    "peg_ratio": info.get("pegRatio"),
                    "price_to_sales": info.get("priceToSalesTrailing12Months"),
                    "price_to_book": info.get("priceToBook"),
                    "enterprise_to_revenue": info.get("enterpriseToRevenue"),
                    "enterprise_to_ebitda": info.get("enterpriseToEbitda"),
                    
                    # 盈利能力
                    "profit_margins": info.get("profitMargins"),
                    "gross_margins": info.get("grossMargins"),
                    "operating_margins": info.get("operatingMargins"),
                    "return_on_assets": info.get("returnOnAssets"),
                    "return_on_equity": info.get("returnOnEquity"),
                    
                    # 财务健康
                    "total_cash": info.get("totalCash"),
                    "total_debt": info.get("totalDebt"),
                    "debt_to_equity": info.get("debtToEquity"),
                    "current_ratio": info.get("currentRatio"),
                    "quick_ratio": info.get("quickRatio"),
                    
                    # 股息信息
                    "dividend_rate": info.get("dividendRate"),
                    "dividend_yield": info.get("dividendYield"),
                    "payout_ratio": info.get("payoutRatio"),
                    
                    # 增长指标
                    "revenue_growth": info.get("revenueGrowth"),
                    "earnings_growth": info.get("earningsGrowth"),
                    
                    # 价格信息
                    "current_price": info.get("currentPrice"),
                    "target_high_price": info.get("targetHighPrice"),
                    "target_low_price": info.get("targetLowPrice"),
                    "target_mean_price": info.get("targetMeanPrice"),
                    "recommendation_mean": info.get("recommendationMean"),
                    
                    # 52周价格范围
                    "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                    "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                    
                    # 交易量
                    "volume": info.get("volume"),
                    "average_volume": info.get("averageVolume"),
                    "average_volume_10days": info.get("averageVolume10days"),
                    
                    # Beta
                    "beta": info.get("beta"),
                })
            
            # 缓存结果
            self._cache_data(cache_key, profile)
            
            return profile
            
        except Exception as e:
            logger.error(f"获取公司信息失败 {symbol}: {e}")
            return {
                "error": "API_ERROR",
                "message": f"yfinance 获取公司信息时发生错误: {str(e)}",
                "original_symbol": symbol,
                "data_source": "yfinance"
            }
    
    async def is_supported(self, symbol: str) -> bool:
        """检查是否支持该股票代码"""
        try:
            stock = self._get_ticker_with_proxy(symbol)
            info = stock.info
            return bool(info and info.get("symbol"))
        except:
            return False
    
    async def get_rate_limit_info(self) -> Dict[str, Any]:
        """获取API限制信息"""
        return {
            "source": "yfinance",
            "daily_limit": -1,  # 无明确限制
            "remaining_calls": -1,
            "reset_time": None,
            "is_free": True,
            "note": "yfinance 基于网页抓取，存在隐式限制"
        }
    
    async def get_financial_data(self, symbol: str) -> Dict[str, Any]:
        """获取财务数据（额外功能）"""
        try:
            cache_key = f"financial_{symbol}"
            cached_data = self._get_cached_data(cache_key)
            if cached_data is not None:
                return cached_data
            
            stock = self._get_ticker_with_proxy(symbol)
            
            # 获取财务报表
            financials = {}
            
            try:
                # 年度财务数据
                income_stmt = stock.financials
                balance_sheet = stock.balance_sheet
                cash_flow = stock.cashflow
                
                if not income_stmt.empty:
                    financials['income_statement'] = income_stmt.to_dict()
                if not balance_sheet.empty:
                    financials['balance_sheet'] = balance_sheet.to_dict() 
                if not cash_flow.empty:
                    financials['cash_flow'] = cash_flow.to_dict()
                    
            except Exception as e:
                logger.warning(f"获取财务报表失败: {e}")
            
            result = {
                "symbol": symbol,
                "financials": financials,
                "data_source": "yfinance",
                "timestamp": datetime.now().isoformat()
            }
            
            # 缓存结果
            self._cache_data(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"获取财务数据失败 {symbol}: {e}")
            return {
                "error": "API_ERROR",
                "message": f"获取财务数据时发生错误: {str(e)}",
                "symbol": symbol
            }
    
    def __str__(self) -> str:
        return "YfinanceSource(免费无限制)"