"""
Google News 数据源
基于 Google News RSS 提供免费的新闻数据
"""

import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
import requests
import feedparser
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

from .base_source import BaseDataSource, DataSourceType
from ..proxy_config import get_proxy_config

logger = logging.getLogger(__name__)

class GoogleNewsSource(BaseDataSource):
    """Google News 数据源"""
    
    def __init__(self):
        super().__init__("GoogleNews", DataSourceType.NEWS)
        self.cache_timeout = 900  # 15分钟缓存
        self.proxy_config = get_proxy_config()
        
        # 设置会话
        self.session = self.proxy_config.setup_requests_session()
        if self.session is None:
            self.session = requests.Session()
        
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        logger.info("Google News 数据源初始化完成")
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 使用更简单和稳定的 Google News RSS URL
            test_urls = [
                "https://news.google.com/rss?hl=en&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=AAPL&hl=en&gl=US&ceid=US:en",
                "https://news.google.com/news/rss"
            ]
            
            for url in test_urls:
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        # 检查是否是有效的 RSS 内容
                        if '<?xml' in response.text or '<rss' in response.text:
                            logger.info(f"Google News 健康检查成功，使用 URL: {url}")
                            return True
                except Exception as e:
                    logger.debug(f"URL {url} 测试失败: {e}")
                    continue
            
            logger.warning("所有 Google News URL 都无法访问")
            return False
            
        except Exception as e:
            logger.error(f"Google News 健康检查失败: {e}")
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
            cache_key = f"news_{symbol}_{start_date}_{end_date}_{limit}"
            cached_data = self._get_cached_data(cache_key)
            if cached_data is not None:
                return cached_data
            
            # 构建智能搜索查询
            queries = self._build_smart_queries(symbol)
            
            all_articles = []
            
            for query in queries:
                try:
                    articles = await self._search_google_news(query, limit//len(queries) + 3)
                    all_articles.extend(articles)
                except Exception as e:
                    logger.warning(f"Google News 搜索失败 {query}: {e}")
                    continue
            
            # 去重和排序
            unique_articles = self._deduplicate_articles(all_articles)
            
            # 按时间过滤
            filtered_articles = self._filter_by_date(unique_articles, start_date, end_date)
            
            # 限制数量
            result = filtered_articles[:limit]
            
            # 缓存结果
            self._cache_data(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"获取公司新闻失败 {symbol}: {e}")
            return []
    
    async def get_company_profile(
        self, 
        symbol: str, 
        detailed: bool = False
    ) -> Dict[str, Any]:
        """Google News 不支持公司信息"""
        return {
            "error": "NOT_SUPPORTED",
            "message": "Google News 数据源不支持公司信息查询",
            "suggestion": "请使用 yfinance 或 alpha_vantage 数据源"
        }
    
    async def is_supported(self, symbol: str) -> bool:
        """检查是否支持该股票代码"""
        # Google News 支持任何股票代码的新闻搜索
        return True
    
    async def get_rate_limit_info(self) -> Dict[str, Any]:
        """获取API限制信息"""
        return {
            "source": "google_news",
            "daily_limit": -1,  # 无限制
            "remaining_calls": -1,
            "reset_time": None,
            "is_free": True
        }
    
    async def _search_google_news(
        self, 
        query: str, 
        max_results: int = 10,
        language: str = "en",
        country: str = "US"
    ) -> List[Dict[str, Any]]:
        """搜索 Google News"""
        try:
            encoded_query = quote_plus(query)
            url = f"https://news.google.com/rss/search?q={encoded_query}&hl={language}&gl={country}&ceid={country}:{language}"
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # 解析 RSS
            feed = feedparser.parse(response.content)
            
            articles = []
            for entry in feed.entries[:max_results]:
                try:
                    # 解析发布时间
                    pub_date = datetime.now()
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    
                    # 清理标题和描述
                    title = entry.title if hasattr(entry, 'title') else ""
                    description = entry.summary if hasattr(entry, 'summary') else ""
                    
                    # 移除 HTML 标签
                    if title:
                        title = BeautifulSoup(title, 'html.parser').get_text()
                    if description:
                        description = BeautifulSoup(description, 'html.parser').get_text()
                    
                    article = {
                        "id": f"google_news_{hash(entry.link if hasattr(entry, 'link') else title)}",
                        "headline": title,
                        "summary": description,
                        "source": entry.source.title if hasattr(entry, 'source') and hasattr(entry.source, 'title') else "Google News",
                        "url": entry.link if hasattr(entry, 'link') else "",
                        "datetime": pub_date.strftime("%Y-%m-%d %H:%M:%S"),
                        "related": query,
                        "image": "",
                        "category": "business",
                        "data_source": "google_news"
                    }
                    
                    articles.append(article)
                    
                except Exception as e:
                    logger.warning(f"处理新闻条目失败: {e}")
                    continue
            
            return articles
            
        except Exception as e:
            logger.error(f"Google News 搜索失败: {e}")
            return []
    
    def _deduplicate_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重新闻文章"""
        seen_urls = set()
        seen_titles = set()
        unique_articles = []
        
        for article in articles:
            url = article.get('url', '')
            title = article.get('headline', '')
            
            # 基于URL和标题去重
            if url and url not in seen_urls and title not in seen_titles:
                seen_urls.add(url)
                seen_titles.add(title)
                unique_articles.append(article)
        
        return unique_articles
    
    def _build_smart_queries(self, symbol: str) -> List[str]:
        """构建智能搜索查询，减少混淆"""
        queries = []
        
        # 检测股票交易所和格式
        if '.HK' in symbol.upper():
            # 香港股票 - 使用更精确的查询
            base_symbol = symbol.split('.')[0]
            queries.extend([
                f'"{symbol}" stock Hong Kong',  # 精确匹配带引号
                f'"{base_symbol}.HK" earnings',
                f'"{symbol}" HKEX',  # 香港交易所
                f'{base_symbol} HK stock news',
                f'Hong Kong stock {base_symbol}'
            ])
        elif '.SS' in symbol.upper() or '.SZ' in symbol.upper():
            # 中国A股
            queries.extend([
                f'"{symbol}" stock Shanghai',
                f'"{symbol}" stock Shenzhen', 
                f'"{symbol}" A股',
                f'{symbol} 股票'
            ])
        elif len(symbol) == 4 and symbol.isdigit():
            # 可能是日本股票代码，需要明确指定
            queries.extend([
                f'"{symbol}" stock Japan TSE',
                f'TSE:{symbol}',
                f'Tokyo stock {symbol}'
            ])
        else:
            # 美股或其他
            queries.extend([
                f'"{symbol}" stock',
                f'"{symbol}" earnings',
                f'"{symbol}" news',
                f'{symbol} stock market'
            ])
        
        # 限制查询数量避免过度搜索
        return queries[:4]
    
    def _filter_by_date(
        self, 
        articles: List[Dict[str, Any]], 
        start_date: str, 
        end_date: str
    ) -> List[Dict[str, Any]]:
        """按日期过滤新闻（放宽日期限制）"""
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  # 包含结束日期
            
            # 📈 Google News 经常返回较旧的新闻，因此放宽日期范围
            # 如果请求范围小于7天，则扩展到30天前
            date_range_days = (end_dt - start_dt).days
            if date_range_days <= 7:
                start_dt = start_dt - timedelta(days=30)
                logger.info(f"放宽日期过滤范围到 {start_dt.strftime('%Y-%m-%d')} - {end_dt.strftime('%Y-%m-%d')}")
            
            filtered = []
            no_date_articles = []
            
            for article in articles:
                try:
                    article_dt = datetime.strptime(article['datetime'], "%Y-%m-%d %H:%M:%S")
                    if start_dt <= article_dt <= end_dt:
                        filtered.append(article)
                    else:
                        logger.debug(f"文章日期 {article['datetime']} 超出范围 {start_dt} - {end_dt}")
                except (ValueError, KeyError):
                    # 日期解析失败，保留文章但放在后面
                    logger.debug(f"无法解析文章日期: {article.get('datetime', 'N/A')}")
                    no_date_articles.append(article)
            
            # 如果严格过滤后没有结果，包含一些无日期的文章
            if not filtered and no_date_articles:
                logger.info("严格日期过滤无结果，包含部分无日期文章")
                filtered.extend(no_date_articles[:5])  # 最多包含5篇无日期文章
            
            # 按时间倒序排序
            filtered.sort(key=lambda x: x.get('datetime', ''), reverse=True)
            return filtered
            
        except Exception as e:
            logger.warning(f"日期过滤失败: {e}，返回所有文章")
            return articles
    
    def __str__(self) -> str:
        return "GoogleNewsSource(免费无限制)"