"""
社交媒体情绪分析服务模块
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import os
import re
from collections import Counter

logger = logging.getLogger(__name__)

class SocialSentimentService:
    """社交媒体情绪分析服务"""
    
    def __init__(self):
        self.cache = {}
        # 从环境变量读取新闻缓存超时，默认15分钟
        self.cache_timeout = int(os.getenv('NEWS_CACHE_TTL', '900'))
        
        # Reddit API配置
        self.reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
        self.reddit_secret = os.getenv("REDDIT_SECRET")
        
        # 情绪分析词典
        self.bullish_terms = {
            'moon', 'rocket', 'diamond hands', 'hodl', 'buy the dip', 'to the moon',
            'bullish', 'calls', 'yolo', 'stonks', 'apes', 'tendies', 'green',
            'pump', 'squeeze', 'gains', 'lambo', 'bull', 'strong buy'
        }
        
        self.bearish_terms = {
            'crash', 'dump', 'red', 'puts', 'short', 'sell', 'drop', 'fall',
            'bearish', 'panic', 'loss', 'rip', 'dead', 'bag holder', 'bear',
            'correction', 'bubble', 'overvalued'
        }
        
        # 常见股票术语
        self.stock_terms = {
            'dd', 'due diligence', 'earnings', 'options', 'calls', 'puts',
            'strike', 'expiry', 'volume', 'float', 'market cap', 'pe ratio'
        }
        
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 检查配置是否完整
            return True  # 即使没有API密钥也可以提供基本功能
        except Exception as e:
            logger.error(f"Social sentiment health check failed: {e}")
            return False
    
    async def get_reddit_sentiment(
        self, 
        ticker: str, 
        subreddit: str = "wallstreetbets"
    ) -> Dict[str, Any]:
        """分析Reddit情绪"""
        try:
            cache_key = f"reddit_{ticker}_{subreddit}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            # 模拟Reddit数据获取（实际应用中需要使用PRAW库）
            posts = await self._fetch_reddit_posts(ticker, subreddit)
            
            if not posts:
                return {
                    "ticker": ticker,
                    "subreddit": subreddit,
                    "sentiment_score": 0.5,
                    "bullish_ratio": 0.5,
                    "post_count": 0,
                    "comment_count": 0,
                    "trending_score": 0,
                    "sentiment_distribution": {"bullish": 0, "neutral": 0, "bearish": 0},
                    "timestamp": datetime.now().isoformat()
                }
            
            # 分析情绪
            sentiment_analysis = self._analyze_reddit_sentiment(posts, ticker)
            
            result = {
                "ticker": ticker,
                "subreddit": subreddit,
                "sentiment_score": sentiment_analysis["sentiment_score"],
                "bullish_ratio": sentiment_analysis["bullish_ratio"],
                "post_count": len(posts),
                "comment_count": sum(post.get("num_comments", 0) for post in posts),
                "trending_score": sentiment_analysis["trending_score"],
                "sentiment_distribution": sentiment_analysis["distribution"],
                "top_posts": posts[:5],  # 前5个热门帖子
                "popular_terms": sentiment_analysis["popular_terms"],
                "timestamp": datetime.now().isoformat()
            }
            
            # 缓存结果
            self._cache_data(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze Reddit sentiment for {ticker}: {e}")
            return {
                "ticker": ticker,
                "subreddit": subreddit,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_trending_tickers(self, source: str = "all") -> List[Dict[str, Any]]:
        """获取热门股票"""
        try:
            cache_key = f"trending_{source}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            trending_data = []
            
            if source in ["reddit", "all"]:
                reddit_trending = await self._get_reddit_trending()
                trending_data.extend(reddit_trending)
            
            if source in ["twitter", "all"]:
                twitter_trending = await self._get_twitter_trending()
                trending_data.extend(twitter_trending)
            
            # 合并和排序
            merged_tickers = self._merge_trending_data(trending_data)
            
            # 缓存结果
            self._cache_data(cache_key, merged_tickers)
            
            return merged_tickers
            
        except Exception as e:
            logger.error(f"Failed to get trending tickers: {e}")
            return [{"error": str(e)}]
    
    async def _fetch_reddit_posts(self, ticker: str, subreddit: str) -> List[Dict[str, Any]]:
        """获取Reddit帖子（模拟数据）"""
        try:
            # 实际应用中应该使用PRAW库连接Reddit API
            # 这里提供模拟数据用于演示
            
            sample_posts = [
                {
                    "title": f"{ticker} DD - Why this is going to moon 🚀",
                    "score": 1250,
                    "num_comments": 300,
                    "created_utc": datetime.now().timestamp(),
                    "selftext": f"Deep dive analysis on {ticker}. Strong fundamentals, great management team.",
                    "url": f"https://reddit.com/r/{subreddit}/sample1",
                    "author": "sample_user1"
                },
                {
                    "title": f"YOLO {ticker} calls 💎🙌",
                    "score": 800,
                    "num_comments": 150,
                    "created_utc": (datetime.now() - timedelta(hours=2)).timestamp(),
                    "selftext": f"All in on {ticker} options. Diamond hands!",
                    "url": f"https://reddit.com/r/{subreddit}/sample2",
                    "author": "sample_user2"
                },
                {
                    "title": f"{ticker} earnings play - thoughts?",
                    "score": 450,
                    "num_comments": 80,
                    "created_utc": (datetime.now() - timedelta(hours=4)).timestamp(),
                    "selftext": f"Thinking about playing {ticker} earnings. What do you think?",
                    "url": f"https://reddit.com/r/{subreddit}/sample3",
                    "author": "sample_user3"
                }
            ]
            
            return sample_posts
            
        except Exception as e:
            logger.warning(f"Failed to fetch Reddit posts: {e}")
            return []
    
    def _analyze_reddit_sentiment(self, posts: List[Dict], ticker: str) -> Dict[str, Any]:
        """分析Reddit帖子情绪"""
        try:
            bullish_count = 0
            bearish_count = 0
            neutral_count = 0
            total_score = 0
            all_text = ""
            
            for post in posts:
                title = post.get("title", "").lower()
                content = post.get("selftext", "").lower()
                text = f"{title} {content}"
                all_text += f" {text}"
                
                # 计算情绪得分
                bullish_words = sum(1 for term in self.bullish_terms if term in text)
                bearish_words = sum(1 for term in self.bearish_terms if term in text)
                
                post_score = post.get("score", 0)
                total_score += post_score
                
                # 根据关键词和得分判断情绪
                if bullish_words > bearish_words:
                    bullish_count += 1
                elif bearish_words > bullish_words:
                    bearish_count += 1
                else:
                    neutral_count += 1
            
            total_posts = len(posts)
            if total_posts == 0:
                return {
                    "sentiment_score": 0.5,
                    "bullish_ratio": 0.5,
                    "trending_score": 0,
                    "distribution": {"bullish": 0, "neutral": 0, "bearish": 0},
                    "popular_terms": []
                }
            
            bullish_ratio = bullish_count / total_posts
            sentiment_score = (bullish_count + 0.5 * neutral_count) / total_posts
            trending_score = total_score / total_posts  # 平均得分作为热度指标
            
            # 提取热门词汇
            popular_terms = self._extract_popular_terms(all_text)
            
            return {
                "sentiment_score": sentiment_score,
                "bullish_ratio": bullish_ratio,
                "trending_score": trending_score,
                "distribution": {
                    "bullish": bullish_count,
                    "neutral": neutral_count,
                    "bearish": bearish_count
                },
                "popular_terms": popular_terms
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze Reddit sentiment: {e}")
            return {
                "sentiment_score": 0.5,
                "bullish_ratio": 0.5,
                "trending_score": 0,
                "distribution": {"bullish": 0, "neutral": 0, "bearish": 0},
                "popular_terms": []
            }
    
    async def _get_reddit_trending(self) -> List[Dict[str, Any]]:
        """获取Reddit热门股票"""
        try:
            # 模拟热门股票数据
            trending_tickers = [
                {"ticker": "AAPL", "mentions": 1500, "sentiment": 0.75, "source": "reddit"},
                {"ticker": "TSLA", "mentions": 1200, "sentiment": 0.85, "source": "reddit"},
                {"ticker": "GME", "mentions": 800, "sentiment": 0.90, "source": "reddit"},
                {"ticker": "NVDA", "mentions": 600, "sentiment": 0.70, "source": "reddit"},
                {"ticker": "AMD", "mentions": 450, "sentiment": 0.65, "source": "reddit"}
            ]
            
            return trending_tickers
            
        except Exception as e:
            logger.warning(f"Failed to get Reddit trending: {e}")
            return []
    
    async def _get_twitter_trending(self) -> List[Dict[str, Any]]:
        """获取Twitter热门股票"""
        try:
            # 模拟Twitter数据
            trending_tickers = [
                {"ticker": "AAPL", "mentions": 800, "sentiment": 0.60, "source": "twitter"},
                {"ticker": "MSFT", "mentions": 600, "sentiment": 0.70, "source": "twitter"},
                {"ticker": "GOOGL", "mentions": 400, "sentiment": 0.65, "source": "twitter"},
                {"ticker": "META", "mentions": 350, "sentiment": 0.55, "source": "twitter"},
                {"ticker": "AMZN", "mentions": 300, "sentiment": 0.60, "source": "twitter"}
            ]
            
            return trending_tickers
            
        except Exception as e:
            logger.warning(f"Failed to get Twitter trending: {e}")
            return []
    
    def _merge_trending_data(self, trending_data: List[Dict]) -> List[Dict[str, Any]]:
        """合并多个来源的热门数据"""
        try:
            ticker_data = {}
            
            for item in trending_data:
                ticker = item["ticker"]
                if ticker not in ticker_data:
                    ticker_data[ticker] = {
                        "ticker": ticker,
                        "total_mentions": 0,
                        "weighted_sentiment": 0,
                        "sources": []
                    }
                
                ticker_data[ticker]["total_mentions"] += item["mentions"]
                ticker_data[ticker]["weighted_sentiment"] += item["sentiment"] * item["mentions"]
                ticker_data[ticker]["sources"].append(item["source"])
            
            # 计算加权平均情绪
            for ticker_info in ticker_data.values():
                if ticker_info["total_mentions"] > 0:
                    ticker_info["avg_sentiment"] = ticker_info["weighted_sentiment"] / ticker_info["total_mentions"]
                else:
                    ticker_info["avg_sentiment"] = 0.5
                
                # 清理临时字段
                del ticker_info["weighted_sentiment"]
            
            # 按提及次数排序
            sorted_tickers = sorted(
                ticker_data.values(),
                key=lambda x: x["total_mentions"],
                reverse=True
            )
            
            return sorted_tickers[:20]  # 返回前20个
            
        except Exception as e:
            logger.error(f"Failed to merge trending data: {e}")
            return []
    
    def _extract_popular_terms(self, text: str) -> List[str]:
        """提取热门词汇"""
        try:
            # 清理文本
            text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
            words = text.split()
            
            # 过滤常见词
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
                'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be',
                'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                'would', 'could', 'should', 'may', 'might', 'can', 'this',
                'that', 'these', 'those'
            }
            
            # 过滤并统计词频
            filtered_words = [
                word for word in words 
                if len(word) > 2 and word not in stop_words
            ]
            
            word_counts = Counter(filtered_words)
            
            # 返回前10个高频词
            return [word for word, count in word_counts.most_common(10)]
            
        except Exception as e:
            logger.warning(f"Failed to extract popular terms: {e}")
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