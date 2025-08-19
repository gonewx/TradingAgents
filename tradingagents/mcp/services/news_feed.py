"""
新闻聚合服务模块
整合 Google News、Reddit 和其他新闻源
"""

import os
import asyncio
import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import feedparser
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .proxy_config import get_proxy_config

logger = logging.getLogger(__name__)

class NewsFeedService:
    """新闻聚合服务"""
    
    def __init__(self):
        self.cache = {}
        # 从环境变量读取新闻缓存超时，默认15分钟
        self.cache_timeout = int(os.getenv('NEWS_CACHE_TTL', '900'))
        self.proxy_config = get_proxy_config()
        
        # 使用代理配置设置 requests 会话
        self.session = self.proxy_config.setup_requests_session()
        if self.session is None:
            self.session = requests.Session()
        
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        logger.info("新闻服务初始化完成（支持代理）")
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 测试 Google News RSS
            response = self.session.get(
                "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZ4ZERBU0FtVnVHZ0pWVXlnQVAB",
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"News feed health check failed: {e}")
            return False
    
    async def get_google_news(
        self, 
        query: str = None, 
        language: str = "en",
        country: str = "US",
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """获取 Google News 数据"""
        try:
            cache_key = f"google_news_{query}_{language}_{country}_{max_results}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            if query:
                # 搜索特定主题
                encoded_query = quote_plus(query)
                url = f"https://news.google.com/rss/search?q={encoded_query}&hl={language}&gl={country}&ceid={country}:{language}"
            else:
                # 获取热门新闻
                url = f"https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZ4ZERBU0FtVnVHZ0pWVXlnQVAB?hl={language}&gl={country}&ceid={country}:{language}"
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # 解析 RSS 内容
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
                    
                    articles.append({
                        "title": title,
                        "description": description,
                        "url": entry.link if hasattr(entry, 'link') else "",
                        "source": entry.source.title if hasattr(entry, 'source') and hasattr(entry.source, 'title') else "Google News",
                        "published": pub_date.strftime("%Y-%m-%d %H:%M:%S"),
                        "category": "business" if query else "general"
                    })
                    
                except Exception as e:
                    logger.warning(f"Error processing news entry: {e}")
                    continue
            
            # 缓存结果
            self._cache_data(cache_key, articles)
            
            return articles
            
        except Exception as e:
            logger.error(f"Failed to get Google News: {e}")
            return []
    
    async def get_financial_news(
        self, 
        symbols: List[str] = None,
        keywords: List[str] = None
    ) -> List[Dict[str, Any]]:
        """获取金融相关新闻"""
        try:
            cache_key = f"financial_news_{'-'.join(symbols or [])}_{'-'.join(keywords or [])}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            all_articles = []
            
            # 构建搜索查询
            queries = []
            
            if symbols:
                for symbol in symbols:
                    queries.append(f"{symbol} stock")
                    queries.append(f"{symbol} earnings")
            
            if keywords:
                queries.extend(keywords)
            
            if not queries:
                queries = ["stock market", "trading", "finance"]
            
            # 获取每个查询的新闻
            for query in queries[:3]:  # 限制查询数量
                try:
                    articles = await self.get_google_news(query=query, max_results=10)
                    all_articles.extend(articles)
                except Exception as e:
                    logger.warning(f"Failed to get news for query '{query}': {e}")
                    continue
            
            # 去重和排序
            unique_articles = self._deduplicate_articles(all_articles)
            sorted_articles = sorted(
                unique_articles,
                key=lambda x: x['published'],
                reverse=True
            )
            
            # 缓存结果
            self._cache_data(cache_key, sorted_articles[:30])
            
            return sorted_articles[:30]
            
        except Exception as e:
            logger.error(f"Failed to get financial news: {e}")
            return []
    
    def _deduplicate_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去除重复文章"""
        seen_titles = set()
        unique_articles = []
        
        for article in articles:
            title_lower = article['title'].lower()
            
            # 简单的重复检测
            is_duplicate = False
            for seen_title in seen_titles:
                if self._calculate_similarity(title_lower, seen_title) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_titles.add(title_lower)
                unique_articles.append(article)
        
        return unique_articles
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    async def get_latest_news(self, ticker: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取股票相关的最新新闻"""
        try:
            # 获取股票相关新闻
            articles = await self.get_financial_news(symbols=[ticker])
            
            # 限制数量并返回
            return articles[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get latest news for {ticker}: {e}")
            return [{
                "error": str(e),
                "ticker": ticker,
                "timestamp": datetime.now().isoformat()
            }]
    
    async def get_news_sentiment(self, ticker: str) -> Dict[str, Any]:
        """获取股票相关新闻情感分析"""
        try:
            cache_key = f"news_sentiment_{ticker}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            # 获取股票相关新闻
            articles = await self.get_financial_news(symbols=[ticker])
            
            if not articles:
                sentiment_result = {
                    "ticker": ticker,
                    "sentiment_score": 0.0,
                    "sentiment_label": "neutral",
                    "confidence": 0.0,
                    "article_count": 0,
                    "positive_count": 0,
                    "negative_count": 0,
                    "neutral_count": 0,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # 简单的情感分析（基于关键词）
                positive_keywords = ["gains", "up", "rise", "bullish", "buy", "positive", "growth", "increase", "strong", "high"]
                negative_keywords = ["losses", "down", "fall", "bearish", "sell", "negative", "decline", "decrease", "weak", "low"]
                
                sentiment_scores = []
                for article in articles:
                    text = f"{article['title']} {article['description']}".lower()
                    
                    positive_count = sum(1 for word in positive_keywords if word in text)
                    negative_count = sum(1 for word in negative_keywords if word in text)
                    
                    if positive_count > negative_count:
                        sentiment_scores.append(1)
                    elif negative_count > positive_count:
                        sentiment_scores.append(-1)
                    else:
                        sentiment_scores.append(0)
                
                # 计算整体情感
                avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
                positive_count = sum(1 for s in sentiment_scores if s > 0)
                negative_count = sum(1 for s in sentiment_scores if s < 0)
                neutral_count = len(sentiment_scores) - positive_count - negative_count
                
                if avg_sentiment > 0.1:
                    sentiment_label = "positive"
                elif avg_sentiment < -0.1:
                    sentiment_label = "negative"
                else:
                    sentiment_label = "neutral"
                
                confidence = abs(avg_sentiment)
                
                sentiment_result = {
                    "ticker": ticker,
                    "sentiment_score": avg_sentiment,
                    "sentiment_label": sentiment_label,
                    "confidence": confidence,
                    "article_count": len(articles),
                    "positive_count": positive_count,
                    "negative_count": negative_count,
                    "neutral_count": neutral_count,
                    "timestamp": datetime.now().isoformat(),
                    "recent_articles": articles[:5]  # 包含最近5篇文章
                }
            
            # 缓存结果
            self._cache_data(cache_key, sentiment_result)
            
            return sentiment_result
            
        except Exception as e:
            logger.error(f"Failed to get news sentiment for {ticker}: {e}")
            return {
                "ticker": ticker,
                "sentiment_score": 0.0,
                "sentiment_label": "neutral",
                "confidence": 0.0,
                "article_count": 0,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
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