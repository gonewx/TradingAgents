"""
Reddit数据服务模块
提供Reddit社交媒体数据获取和情感分析功能
"""

import asyncio
import asyncpraw
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import aiohttp
from textblob import TextBlob
import os
import sys
from .proxy_config import get_proxy_config

logger = logging.getLogger(__name__)

class RedditDataService:
    """Reddit数据服务类"""
    
    def __init__(self):
        """初始化Reddit API客户端"""
        self.reddit = None
        self.cache = {}
        self.cache_timeout = 300  # 5分钟缓存
        self.proxy_config = get_proxy_config()
        self._reddit_initialized = False
        self._custom_session = None  # 用于跟踪自定义会话
    
    async def _test_network_connectivity(self) -> Dict[str, Any]:
        """测试网络连接"""
        results = {}
        
        # 测试基本网络连接
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get('https://httpbin.org/ip') as response:
                    if response.status == 200:
                        results['basic_internet'] = True
                        ip_info = await response.json()
                        results['external_ip'] = ip_info.get('origin', 'unknown')
                    else:
                        results['basic_internet'] = False
        except Exception as e:
            results['basic_internet'] = False
            results['basic_internet_error'] = str(e)
        
        # 测试Reddit连接
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get('https://www.reddit.com/api/v1/me') as response:
                    results['reddit_reachable'] = response.status in [200, 401, 403]  # 401/403说明能连接但未认证
                    results['reddit_status'] = response.status
        except Exception as e:
            results['reddit_reachable'] = False
            results['reddit_error'] = str(e)
        
        # 测试OAuth端点
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get('https://www.reddit.com/api/v1/access_token') as response:
                    results['oauth_reachable'] = response.status in [400, 401, 405]  # 这些状态码说明端点可达
                    results['oauth_status'] = response.status
        except Exception as e:
            results['oauth_reachable'] = False
            results['oauth_error'] = str(e)
        
        return results
    
    async def _test_reddit_api_direct(self, client_id: str, client_secret: str) -> Dict[str, Any]:
        """直接测试Reddit API连接（不使用AsyncPRAW）"""
        import base64
        
        results = {}
        
        try:
            # 准备认证信息
            auth_string = f"{client_id}:{client_secret}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                'Authorization': f'Basic {auth_b64}',
                'User-Agent': 'TradingAgents/1.0'
            }
            
            data = {
                'grant_type': 'client_credentials'
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.post(
                    'https://www.reddit.com/api/v1/access_token',
                    headers=headers,
                    data=data
                ) as response:
                    results['status_code'] = response.status
                    results['headers'] = dict(response.headers)
                    
                    if response.status == 200:
                        token_data = await response.json()
                        results['success'] = True
                        results['token_type'] = token_data.get('token_type')
                        results['access_token_present'] = 'access_token' in token_data
                    else:
                        results['success'] = False
                        try:
                            error_data = await response.text()
                            results['error_response'] = error_data
                        except:
                            results['error_response'] = 'Unable to read response'
                            
        except Exception as e:
            results['success'] = False
            results['exception'] = f"{type(e).__name__}: {e}"
        
        return results
    
    async def _initialize_reddit(self):
        """异步初始化Reddit客户端"""
        try:
            client_id = os.getenv('REDDIT_CLIENT_ID')
            client_secret = os.getenv('REDDIT_CLIENT_SECRET')
            user_agent = os.getenv('REDDIT_USER_AGENT', 'TradingAgents/1.0')
            
            if not client_id or not client_secret:
                logger.warning("Reddit API credentials not configured")
                return
            
            # 基本配置
            reddit_config = {
                'client_id': client_id,
                'client_secret': client_secret,
                'user_agent': user_agent
            }
            
            # 创建Reddit实例并添加网络诊断
            try:
                # 设置全局代理环境变量（确保AsyncPRAW能使用）
                from .proxy_config import setup_global_proxy
                setup_global_proxy()
                
                # 确认代理设置
                proxies = self.proxy_config.get_proxies()
                if proxies:
                    logger.info(f"设置代理配置: {list(proxies.keys())}")
                    # 确保环境变量被正确设置
                    for scheme, proxy_url in proxies.items():
                        env_var = f'{scheme.upper()}_PROXY'
                        os.environ[env_var] = proxy_url
                        logger.info(f"设置环境变量 {env_var} = {proxy_url}")
                else:
                    logger.info("未检测到代理配置，使用直连")
                
                # 创建配置了代理的aiohttp会话
                session_kwargs = {}
                proxies = self.proxy_config.get_proxies()
                if proxies:
                    # 创建支持代理的连接器
                    connector = aiohttp.TCPConnector()
                    
                    # 创建配置了代理的ClientSession
                    session = aiohttp.ClientSession(
                        connector=connector,
                        timeout=aiohttp.ClientTimeout(total=30)
                    )
                    
                    # 设置代理到session（通过monkey patch）
                    original_request = session._request
                    
                    async def patched_request(*args, **kwargs):
                        # 为每个请求添加代理
                        if 'proxy' not in kwargs:
                            kwargs['proxy'] = proxies.get('https') or proxies.get('http')
                        return await original_request(*args, **kwargs)
                    
                    session._request = patched_request
                    
                    # 保存session引用以便后续清理
                    self._custom_session = session
                    
                    # 通过requestor_kwargs传递自定义session
                    reddit_config['requestor_kwargs'] = {'session': session}
                    logger.info(f"为AsyncPRAW配置代理会话: {list(proxies.keys())}")
                else:
                    logger.info("未配置代理，使用默认会话")
                
                self.reddit = asyncpraw.Reddit(**reddit_config)
                logger.info("Reddit API 初始化完成（增强代理配置）")
            except Exception as e:
                logger.error(f"Reddit API 初始化失败: {type(e).__name__}: {e}")
                self.reddit = None
                return
            
            # 测试连接 - 使用更简单的测试方法
            try:
                # 尝试获取Reddit用户信息（只需要基本API访问权限）
                user = await self.reddit.user.me()
                # client_credentials 模式下 user.me() 返回 None 是正常的
                if user:
                    logger.info(f"Reddit API initialized successfully, authenticated as user: {user}")
                else:
                    logger.info("Reddit API initialized successfully with application-level authentication (client_credentials mode)")
                
                # 进一步测试：尝试获取一个帖子来验证完整功能
                try:
                    subreddit = await self.reddit.subreddit('announcements')
                    async for submission in subreddit.hot(limit=1):
                        logger.info(f"Reddit content access test successful: {submission.title[:50]}...")
                        break
                    self._reddit_initialized = True
                    logger.info("Reddit API 完全功能测试通过")
                except Exception as content_error:
                    logger.warning(f"Reddit content access limited: {content_error}")
                    # 即使内容访问受限，基本API仍可用
                    self._reddit_initialized = True
                
            except Exception as e:
                # 如果用户信息获取失败，尝试简单的subreddit访问
                try:
                    subreddit = await self.reddit.subreddit('announcements')
                    logger.info("Reddit API initialized successfully (read-only mode)")
                    self._reddit_initialized = True
                except Exception as e2:
                    logger.error(f"Reddit API test failed - Primary error: {type(e).__name__}: {e}")
                    logger.error(f"Reddit API test failed - Secondary error: {type(e2).__name__}: {e2}")
                    logger.error(f"Reddit API credentials check - Client ID: {'set' if os.getenv('REDDIT_CLIENT_ID') else 'not set'}")
                    logger.error(f"Reddit API credentials check - Client Secret: {'set' if os.getenv('REDDIT_CLIENT_SECRET') else 'not set'}")
                    
                    # 进行网络连接诊断
                    logger.info("Starting network connectivity diagnosis...")
                    try:
                        network_results = await self._test_network_connectivity()
                        logger.error(f"Network diagnosis results: {network_results}")
                    except Exception as diag_e:
                        logger.error(f"Network diagnosis failed: {diag_e}")
                    
                    # 添加环境信息诊断
                    logger.error(f"Environment info - Python: {sys.version}")
                    logger.error(f"Environment info - AsyncPRAW: {asyncpraw.__version__}")
                    logger.error(f"Environment info - aiohttp: {aiohttp.__version__}")
                    
                    # 检查代理设置
                    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
                    proxy_info = {var: os.environ.get(var, 'not set') for var in proxy_vars}
                    logger.error(f"Proxy environment variables: {proxy_info}")
                    
                    # 进行直接API测试
                    if client_id and client_secret:
                        logger.info("Testing Reddit API directly (bypassing AsyncPRAW)...")
                        try:
                            direct_test_results = await self._test_reddit_api_direct(client_id, client_secret)
                            logger.error(f"Direct API test results: {direct_test_results}")
                        except Exception as direct_e:
                            logger.error(f"Direct API test failed: {direct_e}")
                    
                    if self.reddit:
                        await self.reddit.close()
                    self.reddit = None
                
        except Exception as e:
            logger.error(f"Failed to initialize Reddit API: {type(e).__name__}: {e}")
            self.reddit = None
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            await self._ensure_reddit_initialized()
            if not self.reddit:
                return False
            # 简单测试 - 尝试获取一个subreddit
            subreddit = await self.reddit.subreddit('all')
            # 测试完成后不关闭连接，因为其他功能可能还需要使用
            return True
        except Exception as e:
            logger.error(f"Reddit health check failed: {e}")
            return False
    
    async def _ensure_reddit_initialized(self):
        """确保Reddit客户端已初始化"""
        if not self._reddit_initialized:
            await self._initialize_reddit()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self.cache:
            return False
        
        cache_time = self.cache[cache_key].get('timestamp', 0)
        return (datetime.now().timestamp() - cache_time) < self.cache_timeout
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """从缓存获取数据"""
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        return None
    
    def _set_cache(self, cache_key: str, data: Any):
        """设置缓存数据"""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now().timestamp()
        }
    
    def _analyze_sentiment(self, text: str) -> Dict[str, float]:
        """分析文本情感"""
        try:
            blob = TextBlob(text)
            return {
                'polarity': blob.sentiment.polarity,  # -1 to 1 (负面到正面)
                'subjectivity': blob.sentiment.subjectivity  # 0 to 1 (客观到主观)
            }
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {'polarity': 0.0, 'subjectivity': 0.5}
    
    async def get_stock_mentions(self, symbol: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取股票相关的Reddit提及"""
        try:
            await self._ensure_reddit_initialized()
            if not self.reddit:
                logger.warning("Reddit API not available, returning empty results")
                return []
        except Exception as e:
            logger.warning(f"Reddit API initialization failed: {e}")
            return []
        
        cache_key = f"reddit_mentions_{symbol}_{limit}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        try:
            mentions = []
            
            # 搜索相关subreddit
            relevant_subreddits = [
                'stocks', 'investing', 'SecurityAnalysis', 'ValueInvesting',
                'StockMarket', 'pennystocks', 'options', 'wallstreetbets'
            ]
            
            for subreddit_name in relevant_subreddits:
                try:
                    subreddit = await self.reddit.subreddit(subreddit_name)
                    
                    # 搜索包含股票符号的帖子（添加超时和错误处理）
                    search_queries = [symbol, f"${symbol}", f"{symbol} stock"]
                    
                    for query in search_queries:
                        try:
                            search_results = subreddit.search(query, time_filter='day', limit=10)
                            async for submission in search_results:
                                try:
                                    # 分析帖子内容
                                    content = f"{submission.title} {submission.selftext}"
                                    sentiment = self._analyze_sentiment(content)
                                    
                                    mention = {
                                        'id': submission.id,
                                        'subreddit': subreddit_name,
                                        'title': submission.title,
                                        'content': submission.selftext[:500],  # 限制内容长度
                                        'score': submission.score,
                                        'num_comments': submission.num_comments,
                                        'created_utc': submission.created_utc,
                                        'url': f"https://reddit.com{submission.permalink}",
                                        'sentiment': sentiment,
                                        'symbol': symbol
                                    }
                                    
                                    mentions.append(mention)
                                    
                                    if len(mentions) >= limit:
                                        break
                            
                                except Exception as e:
                                    logger.error(f"Error processing submission {submission.id}: {e}")
                                    continue
                                    
                                if len(mentions) >= limit:
                                    break
                        except Exception as search_error:
                            logger.warning(f"Search failed for query '{query}' in {subreddit_name}: {search_error}")
                            continue
                        
                        if len(mentions) >= limit:
                            break
                    
                    if len(mentions) >= limit:
                        break
                        
                except Exception as e:
                    logger.error(f"Error accessing subreddit {subreddit_name}: {e}")
                    continue
            
            # 按分数排序
            mentions.sort(key=lambda x: x['score'], reverse=True)
            result = mentions[:limit]
            
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"Error getting Reddit mentions for {symbol}: {e}")
            return []
    
    async def get_sentiment_summary(self, symbol: str) -> Dict[str, Any]:
        """获取股票的Reddit情感分析摘要"""
        try:
            mentions = await self.get_stock_mentions(symbol, limit=100)
        except Exception as e:
            logger.warning(f"Failed to get Reddit mentions for {symbol}: {e}")
            mentions = []
        
        if not mentions:
            return {
                'symbol': symbol,
                'total_mentions': 0,
                'average_sentiment': 0.0,
                'sentiment_distribution': {'positive': 0, 'neutral': 0, 'negative': 0},
                'engagement_score': 0.0,
                'trending_score': 0.0,
                'status': 'no_data_available'
            }
        
        # 计算平均情感
        sentiments = [m['sentiment']['polarity'] for m in mentions]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
        
        # 情感分布
        positive = len([s for s in sentiments if s > 0.1])
        negative = len([s for s in sentiments if s < -0.1])
        neutral = len(sentiments) - positive - negative
        
        # 参与度分数 (基于分数和评论数)
        total_score = sum(m['score'] for m in mentions)
        total_comments = sum(m['num_comments'] for m in mentions)
        engagement_score = (total_score + total_comments) / len(mentions) if mentions else 0
        
        # 趋势分数 (最近24小时的活动)
        recent_mentions = [
            m for m in mentions 
            if datetime.fromtimestamp(m['created_utc']) > datetime.now() - timedelta(hours=24)
        ]
        trending_score = len(recent_mentions) / len(mentions) if mentions else 0
        
        return {
            'symbol': symbol,
            'total_mentions': len(mentions),
            'average_sentiment': round(avg_sentiment, 3),
            'sentiment_distribution': {
                'positive': positive,
                'neutral': neutral,
                'negative': negative
            },
            'engagement_score': round(engagement_score, 2),
            'trending_score': round(trending_score, 3),
            'top_mentions': mentions[:5]  # 前5个最高分的提及
        }
    
    async def get_trending_stocks(self, subreddit_name: str = 'stocks', limit: int = 20) -> List[Dict[str, Any]]:
        """获取热门股票讨论"""
        try:
            await self._ensure_reddit_initialized()
            if not self.reddit:
                logger.warning("Reddit API not available, returning empty results")
                return []
        except Exception as e:
            logger.warning(f"Reddit API initialization failed: {e}")
            return []
        
        cache_key = f"reddit_trending_{subreddit_name}_{limit}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        try:
            subreddit = await self.reddit.subreddit(subreddit_name)
            trending_stocks = {}
            
            # 获取热门帖子
            async for submission in subreddit.hot(limit=limit * 2):
                try:
                    content = f"{submission.title} {submission.selftext}"
                    
                    # 简单的股票符号提取 (假设格式为 $SYMBOL 或 SYMBOL)
                    import re
                    symbols = re.findall(r'\$([A-Z]{1,5})\b|\b([A-Z]{2,5})\b', content.upper())
                    
                    for match in symbols:
                        symbol = match[0] or match[1]
                        if len(symbol) >= 2 and symbol.isalpha():
                            if symbol not in trending_stocks:
                                trending_stocks[symbol] = {
                                    'symbol': symbol,
                                    'mentions': 0,
                                    'total_score': 0,
                                    'total_comments': 0,
                                    'posts': []
                                }
                            
                            trending_stocks[symbol]['mentions'] += 1
                            trending_stocks[symbol]['total_score'] += submission.score
                            trending_stocks[symbol]['total_comments'] += submission.num_comments
                            trending_stocks[symbol]['posts'].append({
                                'title': submission.title,
                                'score': submission.score,
                                'comments': submission.num_comments,
                                'url': f"https://reddit.com{submission.permalink}"
                            })
                
                except Exception as e:
                    logger.error(f"Error processing trending submission: {e}")
                    continue
            
            # 转换为列表并按提及次数排序
            result = []
            for symbol, data in trending_stocks.items():
                if data['mentions'] >= 2:  # 至少被提及2次
                    data['average_score'] = data['total_score'] / data['mentions']
                    data['average_comments'] = data['total_comments'] / data['mentions']
                    result.append(data)
            
            result.sort(key=lambda x: x['mentions'], reverse=True)
            result = result[:limit]
            
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"Error getting trending stocks from {subreddit_name}: {e}")
            return []
    
    async def close(self):
        """关闭Reddit连接"""
        try:
            # 首先关闭自定义会话
            if self._custom_session and not self._custom_session.closed:
                await self._custom_session.close()
                logger.info("Custom aiohttp session closed")
                self._custom_session = None
            
            # 然后关闭Reddit实例
            if self.reddit:
                await self.reddit.close()
                logger.info("Reddit API connection closed")
                
        except Exception as e:
            logger.warning(f"Error closing Reddit connection: {e}")
        finally:
            self.reddit = None
            self._reddit_initialized = False
            self._custom_session = None