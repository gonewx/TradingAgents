"""
Alpha Vantage 数据源
提供高质量的金融数据API，支持新闻和公司信息
"""

import asyncio
import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

from .base_source import BaseDataSource, DataSourceType
from ..proxy_config import get_proxy_config

logger = logging.getLogger(__name__)

class AlphaVantageSource(BaseDataSource):
    """Alpha Vantage 数据源"""
    
    def __init__(self, api_key: str):
        super().__init__("AlphaVantage", DataSourceType.NEWS)
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.cache_timeout = 3600  # 1小时缓存（节省API配额）
        self.proxy_config = get_proxy_config()
        
        # 设置会话
        self.session = self.proxy_config.setup_requests_session()
        if self.session is None:
            self.session = requests.Session()
        
        # API调用计数（简单实现）
        self.daily_calls = 0
        self.daily_limit = 500
        self.last_reset = datetime.now().date()
        
        logger.info("Alpha Vantage 数据源初始化完成")
    
    def _check_api_limit(self) -> bool:
        """检查API调用限制"""
        current_date = datetime.now().date()
        
        # 每日重置计数
        if current_date > self.last_reset:
            self.daily_calls = 0
            self.last_reset = current_date
        
        if self.daily_calls >= self.daily_limit:
            logger.warning(f"Alpha Vantage API 日调用量已达上限: {self.daily_calls}/{self.daily_limit}")
            return False
        
        return True
    
    def _increment_api_calls(self):
        """增加API调用计数"""
        self.daily_calls += 1
        logger.debug(f"Alpha Vantage API 调用: {self.daily_calls}/{self.daily_limit}")
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            if not self._check_api_limit():
                return False
            
            # 测试基本API调用
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': 'AAPL',
                'apikey': self.api_key
            }
            
            response = self.session.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self._increment_api_calls()
                
                # 检查是否有错误信息
                if 'Error Message' in data:
                    logger.error(f"Alpha Vantage API 错误: {data['Error Message']}")
                    return False
                
                if 'Note' in data:
                    logger.warning(f"Alpha Vantage API 提示: {data['Note']}")
                    return False
                
                return 'Global Quote' in data
            
            return False
            
        except Exception as e:
            logger.error(f"Alpha Vantage 健康检查失败: {e}")
            return False
    
    async def get_company_news(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取公司新闻"""
        try:
            if not self._check_api_limit():
                return [{
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"Alpha Vantage API 日调用量已达上限: {self.daily_calls}/{self.daily_limit}",
                    "suggestion": "请明天再试或使用免费数据源"
                }]
            
            cache_key = f"news_{symbol}_{start_date}_{end_date}_{limit}"
            cached_data = self._get_cached_data(cache_key)
            if cached_data is not None:
                return cached_data
            
            # Alpha Vantage News API
            params = {
                'function': 'NEWS_SENTIMENT',
                'tickers': symbol,
                'apikey': self.api_key,
                'limit': str(min(limit, 1000)),  # API最大限制
                'sort': 'LATEST'
            }
            
            # 添加时间过滤
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                
                # Alpha Vantage 使用 YYYYMMDDTHHMM 格式
                params['time_from'] = start_dt.strftime("%Y%m%dT0000")
                params['time_to'] = end_dt.strftime("%Y%m%dT2359")
            except ValueError:
                logger.warning(f"日期格式错误: {start_date}, {end_date}")
            
            response = self.session.get(self.base_url, params=params, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Alpha Vantage API 请求失败: {response.status_code}")
                return []
            
            data = response.json()
            self._increment_api_calls()
            
            # 检查错误
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage API 错误: {data['Error Message']}")
                return []
            
            if 'Note' in data:
                logger.warning(f"Alpha Vantage API 限制: {data['Note']}")
                return [{
                    "error": "RATE_LIMIT_EXCEEDED", 
                    "message": data['Note'],
                    "suggestion": "请稍后再试或使用免费数据源"
                }]
            
            # 解析新闻数据
            articles = []
            feed_data = data.get('feed', [])
            
            for item in feed_data[:limit]:
                try:
                    # 解析时间
                    time_published = item.get('time_published', '')
                    pub_date = datetime.now()
                    
                    if time_published:
                        try:
                            # Alpha Vantage 时间格式: YYYYMMDDTHHMMSS
                            pub_date = datetime.strptime(time_published, "%Y%m%dT%H%M%S")
                        except ValueError:
                            try:
                                pub_date = datetime.strptime(time_published[:8], "%Y%m%d")
                            except ValueError:
                                pass
                    
                    # 处理情绪数据
                    sentiment_score = 0
                    sentiment_label = "neutral"
                    
                    overall_sentiment = item.get('overall_sentiment_score')
                    if overall_sentiment is not None:
                        try:
                            sentiment_score = float(overall_sentiment)
                            if sentiment_score > 0.15:
                                sentiment_label = "positive"
                            elif sentiment_score < -0.15:
                                sentiment_label = "negative"
                        except (ValueError, TypeError):
                            pass
                    
                    article = {
                        "id": f"alpha_vantage_{item.get('url', '').split('/')[-1] or hash(item.get('title', ''))}",
                        "headline": item.get('title', ''),
                        "summary": item.get('summary', ''),
                        "source": item.get('source', 'Alpha Vantage'),
                        "url": item.get('url', ''),
                        "datetime": pub_date.strftime("%Y-%m-%d %H:%M:%S"),
                        "related": symbol,
                        "image": item.get('banner_image', ''),
                        "category": "business",
                        "sentiment_score": sentiment_score,
                        "sentiment_label": sentiment_label,
                        "authors": item.get('authors', []),
                        "topics": item.get('topics', []),
                        "data_source": "alpha_vantage"
                    }
                    
                    articles.append(article)
                    
                except Exception as e:
                    logger.warning(f"处理新闻条目失败: {e}")
                    continue
            
            # 缓存结果
            self._cache_data(cache_key, articles)
            
            return articles
            
        except Exception as e:
            logger.error(f"Alpha Vantage 获取新闻失败 {symbol}: {e}")
            return []
    
    async def get_company_profile(
        self, 
        symbol: str, 
        detailed: bool = False
    ) -> Dict[str, Any]:
        """获取公司信息"""
        try:
            if not self._check_api_limit():
                return {
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"Alpha Vantage API 日调用量已达上限: {self.daily_calls}/{self.daily_limit}",
                    "suggestion": "请明天再试或使用 yfinance 数据源"
                }
            
            cache_key = f"profile_{symbol}_{detailed}"
            cached_data = self._get_cached_data(cache_key)
            if cached_data is not None:
                return cached_data
            
            # Alpha Vantage Company Overview API
            params = {
                'function': 'OVERVIEW',
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = self.session.get(self.base_url, params=params, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Alpha Vantage API 请求失败: {response.status_code}")
                return {
                    "error": "API_ERROR",
                    "message": f"Alpha Vantage API 请求失败: {response.status_code}",
                    "symbol": symbol
                }
            
            data = response.json()
            self._increment_api_calls()
            
            # 检查错误
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage API 错误: {data['Error Message']}")
                return {
                    "error": "SYMBOL_NOT_FOUND",
                    "message": data['Error Message'],
                    "symbol": symbol
                }
            
            if 'Note' in data:
                logger.warning(f"Alpha Vantage API 限制: {data['Note']}")
                return {
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": data['Note'],
                    "suggestion": "请稍后再试或使用免费数据源"
                }
            
            # 检查数据是否为空
            if not data or not data.get('Symbol'):
                return {
                    "error": "NO_DATA_FOUND",
                    "message": f"Alpha Vantage 未找到股票代码 {symbol} 的信息",
                    "symbol": symbol
                }
            
            # 解析公司信息
            profile = {
                "symbol": symbol,
                "alpha_vantage_symbol": data.get('Symbol', symbol),
                "name": data.get('Name', ''),
                "description": data.get('Description', ''),
                "country": data.get('Country', ''),
                "currency": data.get('Currency', ''),
                "exchange": data.get('Exchange', ''),
                "industry": data.get('Industry', ''),
                "sector": data.get('Sector', ''),
                "address": data.get('Address', ''),
                "fiscal_year_end": data.get('FiscalYearEnd', ''),
                "latest_quarter": data.get('LatestQuarter', ''),
                "market_cap": self._safe_float(data.get('MarketCapitalization')),
                "ebitda": self._safe_float(data.get('EBITDA')),
                "pe_ratio": self._safe_float(data.get('PERatio')),
                "peg_ratio": self._safe_float(data.get('PEGRatio')),
                "book_value": self._safe_float(data.get('BookValue')),
                "dividend_per_share": self._safe_float(data.get('DividendPerShare')),
                "dividend_yield": self._safe_float(data.get('DividendYield')),
                "eps": self._safe_float(data.get('EPS')),
                "revenue_per_share": self._safe_float(data.get('RevenuePerShareTTM')),
                "profit_margin": self._safe_float(data.get('ProfitMargin')),
                "operating_margin": self._safe_float(data.get('OperatingMarginTTM')),
                "return_on_assets": self._safe_float(data.get('ReturnOnAssetsTTM')),
                "return_on_equity": self._safe_float(data.get('ReturnOnEquityTTM')),
                "revenue": self._safe_float(data.get('RevenueTTM')),
                "gross_profit": self._safe_float(data.get('GrossProfitTTM')),
                "diluted_eps": self._safe_float(data.get('DilutedEPSTTM')),
                "quarterly_earnings_growth": self._safe_float(data.get('QuarterlyEarningsGrowthYOY')),
                "quarterly_revenue_growth": self._safe_float(data.get('QuarterlyRevenueGrowthYOY')),
                "analyst_target_price": self._safe_float(data.get('AnalystTargetPrice')),
                "trailing_pe": self._safe_float(data.get('TrailingPE')),
                "forward_pe": self._safe_float(data.get('ForwardPE')),
                "price_to_sales": self._safe_float(data.get('PriceToSalesRatioTTM')),
                "price_to_book": self._safe_float(data.get('PriceToBookRatio')),
                "ev_to_revenue": self._safe_float(data.get('EVToRevenue')),
                "ev_to_ebitda": self._safe_float(data.get('EVToEBITDA')),
                "beta": self._safe_float(data.get('Beta')),
                "week_52_high": self._safe_float(data.get('52WeekHigh')),
                "week_52_low": self._safe_float(data.get('52WeekLow')),
                "moving_average_50": self._safe_float(data.get('50DayMovingAverage')),
                "moving_average_200": self._safe_float(data.get('200DayMovingAverage')),
                "shares_outstanding": self._safe_float(data.get('SharesOutstanding')),
                "data_source": "alpha_vantage",
                "timestamp": datetime.now().isoformat()
            }
            
            # 缓存结果
            self._cache_data(cache_key, profile)
            
            return profile
            
        except Exception as e:
            logger.error(f"Alpha Vantage 获取公司信息失败 {symbol}: {e}")
            return {
                "error": "API_ERROR",
                "message": f"Alpha Vantage 获取公司信息时发生错误: {str(e)}",
                "symbol": symbol
            }
    
    async def is_supported(self, symbol: str) -> bool:
        """检查是否支持该股票代码"""
        try:
            if not self._check_api_limit():
                return True  # 假设支持，避免浪费API调用
            
            # 简单检查 - 尝试获取基本信息
            profile = await self.get_company_profile(symbol, detailed=False)
            return not profile.get('error')
        except:
            return False
    
    async def get_rate_limit_info(self) -> Dict[str, Any]:
        """获取API限制信息"""
        reset_time = datetime.combine(
            datetime.now().date() + timedelta(days=1),
            datetime.min.time()
        ).isoformat()
        
        return {
            "source": "alpha_vantage",
            "daily_limit": self.daily_limit,
            "daily_calls_used": self.daily_calls,
            "remaining_calls": max(0, self.daily_limit - self.daily_calls),
            "reset_time": reset_time,
            "is_free": True,
            "per_minute_limit": 5
        }
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """安全转换为浮点数"""
        if value is None or value == 'None' or value == '':
            return None
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def __str__(self) -> str:
        return f"AlphaVantageSource(500次/天, 已用: {self.daily_calls})"