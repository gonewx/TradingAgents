"""
代理配置模块
提供统一的代理设置和网络配置管理
"""

import os
import logging
from typing import Dict, Optional, Any
import urllib.parse

logger = logging.getLogger(__name__)

class ProxyConfig:
    """代理配置管理类"""
    
    def __init__(self):
        """初始化代理配置"""
        self.http_proxy = os.getenv('HTTP_PROXY') or os.getenv('http_proxy')
        self.https_proxy = os.getenv('HTTPS_PROXY') or os.getenv('https_proxy')
        self.no_proxy = os.getenv('NO_PROXY') or os.getenv('no_proxy')
        self.proxy_username = os.getenv('PROXY_USERNAME')
        self.proxy_password = os.getenv('PROXY_PASSWORD')
        
        # 从环境变量构建代理 URL
        self._setup_proxy_urls()
        
        logger.info(f"代理配置初始化: HTTP={bool(self.http_proxy)}, HTTPS={bool(self.https_proxy)}")
    
    def _setup_proxy_urls(self):
        """设置完整的代理 URL（包含认证信息）"""
        if self.proxy_username and self.proxy_password:
            auth = f"{self.proxy_username}:{self.proxy_password}@"
            
            if self.http_proxy and not self.http_proxy.startswith('http://'):
                self.http_proxy = f"http://{auth}{self.http_proxy}"
            elif self.http_proxy and '://' in self.http_proxy:
                # 如果已有协议，插入认证信息
                scheme, rest = self.http_proxy.split('://', 1)
                self.http_proxy = f"{scheme}://{auth}{rest}"
            
            if self.https_proxy and not self.https_proxy.startswith('http'):
                self.https_proxy = f"http://{auth}{self.https_proxy}"
            elif self.https_proxy and '://' in self.https_proxy:
                scheme, rest = self.https_proxy.split('://', 1)
                self.https_proxy = f"{scheme}://{auth}{rest}"
    
    def get_proxies(self) -> Dict[str, str]:
        """获取代理字典，用于 requests 库"""
        proxies = {}
        
        if self.http_proxy:
            proxies['http'] = self.http_proxy
        
        if self.https_proxy:
            proxies['https'] = self.https_proxy
        
        return proxies
    
    def get_urllib_proxy_handler(self):
        """获取 urllib 代理处理器"""
        import urllib.request
        
        proxies = self.get_proxies()
        if proxies:
            return urllib.request.ProxyHandler(proxies)
        return None
    
    def get_aiohttp_connector(self):
        """获取 aiohttp 连接器（支持代理）"""
        try:
            import aiohttp
            
            if self.https_proxy or self.http_proxy:
                # 使用第一个可用的代理
                proxy_url = self.https_proxy or self.http_proxy
                return aiohttp.TCPConnector()
            
            return aiohttp.TCPConnector()
        except ImportError:
            logger.warning("aiohttp 未安装，跳过 aiohttp 代理配置")
            return None
    
    def setup_requests_session(self, session=None):
        """配置 requests 会话的代理设置"""
        import requests
        
        if session is None:
            session = requests.Session()
        
        # 设置代理
        proxies = self.get_proxies()
        if proxies:
            session.proxies.update(proxies)
            logger.debug(f"为 requests 会话设置代理: {proxies}")
        
        # 设置其他网络配置
        session.timeout = float(os.getenv('REQUEST_TIMEOUT', '30'))
        session.headers.update({
            'User-Agent': os.getenv('USER_AGENT', 'TradingAgents/1.0')
        })
        
        return session
    
    def setup_finnhub_client(self, api_key: str):
        """配置 Finnhub 客户端的代理设置"""
        try:
            import finnhub
            
            # Finnhub 客户端本身不直接支持代理，但底层使用 requests
            # 我们需要修改 requests 的默认适配器
            client = finnhub.Client(api_key=api_key)
            
            # 为 finnhub 客户端的 session 设置代理
            if hasattr(client, '_session'):
                self.setup_requests_session(client._session)
            
            return client
        except ImportError:
            logger.error("finnhub-python 未安装")
            return None
    
    def setup_yfinance_session(self):
        """配置 yfinance 的会话代理"""
        try:
            import yfinance as yf
            
            # yfinance 使用 requests-cache 和 requests
            session = self.setup_requests_session()
            
            # 如果 yfinance 支持自定义会话，使用它
            # 注意：这取决于 yfinance 的版本
            return session
        except ImportError:
            logger.error("yfinance 未安装")
            return None
    
    def setup_praw_config(self, client_id: str, client_secret: str, user_agent: str):
        """配置 PRAW (Reddit) 的代理设置"""
        try:
            import praw
            
            # PRAW 配置字典
            config = {
                'client_id': client_id,
                'client_secret': client_secret,
                'user_agent': user_agent
            }
            
            # 添加代理配置
            proxies = self.get_proxies()
            if proxies:
                # PRAW 使用 requestor_kwargs 传递代理
                config['requestor_kwargs'] = {'proxies': proxies}
                logger.debug(f"为 PRAW 设置代理: {proxies}")
            
            return config
        except ImportError:
            logger.error("praw 未安装")
            return None
    
    def should_use_proxy_for_url(self, url: str) -> bool:
        """检查某个 URL 是否应该使用代理"""
        if not self.no_proxy:
            return True
        
        # 解析 no_proxy 环境变量
        no_proxy_list = [host.strip() for host in self.no_proxy.split(',')]
        
        try:
            parsed_url = urllib.parse.urlparse(url)
            hostname = parsed_url.hostname
            
            for no_proxy_host in no_proxy_list:
                if no_proxy_host == '*':
                    return False
                if hostname and (hostname == no_proxy_host or hostname.endswith('.' + no_proxy_host)):
                    return False
            
        except Exception as e:
            logger.warning(f"解析 URL 失败 {url}: {e}")
        
        return True
    
    def test_proxy_connection(self) -> Dict[str, Any]:
        """测试代理连接"""
        import requests
        
        test_results = {
            'proxy_configured': bool(self.get_proxies()),
            'http_proxy_working': False,
            'https_proxy_working': False,
            'errors': []
        }
        
        if not test_results['proxy_configured']:
            test_results['errors'].append("未配置代理")
            return test_results
        
        session = self.setup_requests_session()
        
        # 测试 HTTP 代理
        try:
            response = session.get('http://httpbin.org/ip', timeout=10)
            if response.status_code == 200:
                test_results['http_proxy_working'] = True
                test_results['http_ip'] = response.json().get('origin')
        except Exception as e:
            test_results['errors'].append(f"HTTP 代理测试失败: {e}")
        
        # 测试 HTTPS 代理
        try:
            response = session.get('https://httpbin.org/ip', timeout=10)
            if response.status_code == 200:
                test_results['https_proxy_working'] = True
                test_results['https_ip'] = response.json().get('origin')
        except Exception as e:
            test_results['errors'].append(f"HTTPS 代理测试失败: {e}")
        
        return test_results

# 全局代理配置实例
_proxy_config = None

def get_proxy_config() -> ProxyConfig:
    """获取全局代理配置实例"""
    global _proxy_config
    if _proxy_config is None:
        _proxy_config = ProxyConfig()
    return _proxy_config

def setup_global_proxy():
    """设置全局代理（影响所有网络请求）"""
    proxy_config = get_proxy_config()
    proxies = proxy_config.get_proxies()
    
    if proxies:
        # 设置环境变量，影响所有使用标准库的网络请求
        for scheme, proxy_url in proxies.items():
            os.environ[f'{scheme.upper()}_PROXY'] = proxy_url
        
        logger.info(f"已设置全局代理: {list(proxies.keys())}")
    else:
        logger.info("未配置代理")