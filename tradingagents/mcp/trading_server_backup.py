"""
TradingAgents 统一 MCP 服务器
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# MCP 框架相关导入 (需要安装对应的 MCP 库)
try:
    from mcp import MCPServer, Tool
except ImportError:
    # 临时替代方案，用于演示
    class MCPServer:
        def __init__(self):
            self.tools = {}
            
        async def run(self, host="0.0.0.0", port=8080):
            print(f"TradingAgents MCP 服务器启动在 {host}:{port}")
            while True:
                await asyncio.sleep(1)
    
    def Tool(name):
        def decorator(func):
            func.tool_name = name
            return func
        return decorator

# 导入各功能模块
from .services.market_data import MarketDataService
from .services.financial_data import FinancialDataService
from .services.news_feed import NewsFeedService
from .services.social_sentiment import SocialSentimentService
from .services.backtesting import BacktestingService
from .services.memory_store import MemoryStoreService
from .services.risk_analytics import RiskAnalyticsService
from .services.execution_broker import ExecutionBrokerService
from .services.finnhub_data import FinnhubDataService
from .services.technical_indicators import TechnicalIndicatorsService
from .services.reddit_data import RedditDataService
from .services.proxy_config import get_proxy_config

# 配置日志
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class TradingAgentsServer(MCPServer):
    """TradingAgents 统一 MCP 服务器"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 初始化代理配置
        self.proxy_config = get_proxy_config()
        
        # 初始化各功能服务
        try:
            self.market_data = MarketDataService()
            self.financial_data = FinancialDataService()
            self.news_feed = NewsFeedService()
            self.social_sentiment = SocialSentimentService()
            self.backtesting = BacktestingService()
            self.memory_store = MemoryStoreService()
            self.risk_analytics = RiskAnalyticsService()
            self.execution_broker = ExecutionBrokerService()
            self.finnhub_data = FinnhubDataService()
            self.technical_indicators = TechnicalIndicatorsService()
            self.reddit_data = RedditDataService()
            
            self.logger.info("TradingAgents MCP 服务器初始化完成")
        except Exception as e:
            self.logger.error(f"服务器初始化失败: {e}")
            raise
    
    # ========== 健康检查 ==========
    
    @Tool("health_check")
    async def health_check(self) -> Dict[str, Any]:
        """系统健康检查"""
        try:
            status = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "services": {
                    "market_data": await self._check_service_health(self.market_data),
                    "financial_data": await self._check_service_health(self.financial_data),
                    "news_feed": await self._check_service_health(self.news_feed),
                    "social_sentiment": await self._check_service_health(self.social_sentiment),
                    "backtesting": await self._check_service_health(self.backtesting),
                    "memory_store": await self._check_service_health(self.memory_store),
                    "risk_analytics": await self._check_service_health(self.risk_analytics),
                    "execution_broker": await self._check_service_health(self.execution_broker),
                    "finnhub_data": await self._check_service_health(self.finnhub_data),
                    "technical_indicators": await self._check_service_health(self.technical_indicators),
                    "reddit_data": await self._check_service_health(self.reddit_data),
                }
            }
            return status
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_service_health(self, service) -> str:
        """检查单个服务健康状态"""
        try:
            if hasattr(service, 'health_check'):
                await service.health_check()
            return "healthy"
        except Exception as e:
            self.logger.warning(f"服务健康检查失败: {e}")
            return "unhealthy"
    
    # ========== 市场数据工具 ==========
    
    @Tool("market_get_quote")
    async def market_get_quote(self, ticker: str) -> Dict[str, Any]:
        """获取股票实时报价"""
        try:
            return await self.market_data.get_quote(ticker)
        except Exception as e:
            self.logger.error(f"获取报价失败 {ticker}: {e}")
            return {"error": str(e), "ticker": ticker}
    
    @Tool("market_get_historical")
    async def market_get_historical(
        self, 
        ticker: str, 
        period: str = "1y",
        interval: str = "1d"
    ) -> List[Dict]:
        """获取历史价格数据"""
        try:
            return await self.market_data.get_historical_prices(ticker, period, interval)
        except Exception as e:
            self.logger.error(f"获取历史数据失败 {ticker}: {e}")
            return [{"error": str(e), "ticker": ticker}]
    
    @Tool("market_get_technical_indicators")
    async def market_get_technical_indicators(self, ticker: str) -> Dict[str, Any]:
        """计算技术指标"""
        try:
            return await self.market_data.get_technical_indicators(ticker)
        except Exception as e:
            self.logger.error(f"计算技术指标失败 {ticker}: {e}")
            return {"error": str(e), "ticker": ticker}
    
    # ========== 财务数据工具 ==========
    
    @Tool("financial_get_income_statement")
    async def financial_get_income_statement(
        self, 
        ticker: str, 
        period: str = "annual"
    ) -> Dict[str, Any]:
        """获取损益表"""
        try:
            return await self.financial_data.get_income_statement(ticker, period)
        except Exception as e:
            self.logger.error(f"获取损益表失败 {ticker}: {e}")
            return {"error": str(e), "ticker": ticker}
    
    @Tool("financial_get_balance_sheet")
    async def financial_get_balance_sheet(
        self, 
        ticker: str, 
        period: str = "annual"
    ) -> Dict[str, Any]:
        """获取资产负债表"""
        try:
            return await self.financial_data.get_balance_sheet(ticker, period)
        except Exception as e:
            self.logger.error(f"获取资产负债表失败 {ticker}: {e}")
            return {"error": str(e), "ticker": ticker}
    
    @Tool("financial_get_ratios")
    async def financial_get_ratios(self, ticker: str) -> Dict[str, Any]:
        """计算财务比率"""
        try:
            return await self.financial_data.get_financial_ratios(ticker)
        except Exception as e:
            self.logger.error(f"计算财务比率失败 {ticker}: {e}")
            return {"error": str(e), "ticker": ticker}
    
    # ========== 新闻情绪工具 ==========
    
    @Tool("news_get_sentiment")
    async def news_get_sentiment(self, ticker: str) -> Dict[str, Any]:
        """分析新闻情绪"""
        try:
            return await self.news_feed.get_news_sentiment(ticker)
        except Exception as e:
            self.logger.error(f"分析新闻情绪失败 {ticker}: {e}")
            return {"error": str(e), "ticker": ticker}
    
    @Tool("news_get_latest")
    async def news_get_latest(
        self, 
        ticker: str, 
        limit: int = 10
    ) -> List[Dict]:
        """获取最新新闻"""
        try:
            return await self.news_feed.get_latest_news(ticker, limit)
        except Exception as e:
            self.logger.error(f"获取最新新闻失败 {ticker}: {e}")
            return [{"error": str(e), "ticker": ticker}]
    
    # ========== 社交情绪工具 ==========
    
    @Tool("social_get_reddit_sentiment")
    async def social_get_reddit_sentiment(
        self, 
        ticker: str,
        subreddit: str = "wallstreetbets"
    ) -> Dict[str, Any]:
        """分析Reddit情绪"""
        try:
            return await self.social_sentiment.get_reddit_sentiment(ticker, subreddit)
        except Exception as e:
            self.logger.error(f"分析Reddit情绪失败 {ticker}: {e}")
            return {"error": str(e), "ticker": ticker}
    
    @Tool("social_get_trending_tickers")
    async def social_get_trending_tickers(
        self, 
        source: str = "all"
    ) -> List[Dict]:
        """获取热门股票"""
        try:
            return await self.social_sentiment.get_trending_tickers(source)
        except Exception as e:
            self.logger.error(f"获取热门股票失败: {e}")
            return [{"error": str(e)}]
    
    # ========== 回测工具 ==========
    
    @Tool("backtest_run")
    async def backtest_run(
        self,
        strategy: Dict[str, Any],
        ticker: str,
        start_date: str,
        end_date: str,
        initial_cash: float = 100000
    ) -> Dict[str, Any]:
        """运行策略回测"""
        try:
            return await self.backtesting.run_backtest(
                strategy, ticker, start_date, end_date, initial_cash
            )
        except Exception as e:
            self.logger.error(f"回测失败 {ticker}: {e}")
            return {"error": str(e), "ticker": ticker}
    
    @Tool("backtest_optimize")
    async def backtest_optimize(
        self,
        strategy: Dict[str, Any],
        parameters: Dict[str, Any],
        optimization_target: str = "sharpe"
    ) -> Dict[str, Any]:
        """优化策略参数"""
        try:
            return await self.backtesting.optimize_parameters(
                strategy, parameters, optimization_target
            )
        except Exception as e:
            self.logger.error(f"参数优化失败: {e}")
            return {"error": str(e)}
    
    # ========== 记忆存储工具 ==========
    
    @Tool("memory_store_decision")
    async def memory_store_decision(
        self,
        ticker: str,
        decision: str,
        context: Dict[str, Any],
        reasoning: str
    ) -> str:
        """存储交易决策"""
        try:
            return await self.memory_store.store_decision(
                ticker, decision, context, reasoning
            )
        except Exception as e:
            self.logger.error(f"存储决策失败 {ticker}: {e}")
            return f"error:{str(e)}"
    
    @Tool("memory_retrieve_similar")
    async def memory_retrieve_similar(
        self,
        context: Dict[str, Any],
        n_results: int = 5
    ) -> List[Dict]:
        """检索相似案例"""
        try:
            return await self.memory_store.retrieve_similar_cases(context, n_results)
        except Exception as e:
            self.logger.error(f"检索相似案例失败: {e}")
            return [{"error": str(e)}]
    
    @Tool("memory_update_outcome")
    async def memory_update_outcome(
        self,
        memory_id: str,
        outcome: Dict[str, Any]
    ) -> bool:
        """更新决策结果"""
        try:
            return await self.memory_store.update_outcome(memory_id, outcome)
        except Exception as e:
            self.logger.error(f"更新决策结果失败 {memory_id}: {e}")
            return False
    
    # ========== 风险分析工具 ==========
    
    @Tool("risk_calculate_var")
    async def risk_calculate_var(
        self,
        portfolio: Dict[str, Any],
        confidence_level: float = 0.95,
        time_horizon: int = 1
    ) -> Dict[str, Any]:
        """计算VaR（在险价值）"""
        try:
            return await self.risk_analytics.calculate_var(
                portfolio, confidence_level, time_horizon
            )
        except Exception as e:
            self.logger.error(f"计算VaR失败: {e}")
            return {"error": str(e)}
    
    @Tool("risk_stress_test")
    async def risk_stress_test(
        self,
        portfolio: Dict[str, Any],
        scenarios: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """运行压力测试"""
        try:
            return await self.risk_analytics.run_stress_test(portfolio, scenarios)
        except Exception as e:
            self.logger.error(f"压力测试失败: {e}")
            return {"error": str(e)}
    
    @Tool("risk_portfolio_optimization")
    async def risk_portfolio_optimization(
        self,
        tickers: List[str],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """组合优化"""
        try:
            return await self.risk_analytics.portfolio_optimization(tickers, constraints)
        except Exception as e:
            self.logger.error(f"组合优化失败: {e}")
            return {"error": str(e)}
    
    # ========== 交易执行工具 ==========
    
    @Tool("broker_place_order")
    async def broker_place_order(
        self,
        ticker: str,
        quantity: int,
        side: str,  # 'buy' or 'sell'
        order_type: str = "market",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """下单"""
        try:
            return await self.execution_broker.place_order(
                ticker, quantity, side, order_type, limit_price, stop_price
            )
        except Exception as e:
            self.logger.error(f"下单失败 {ticker}: {e}")
            return {"error": str(e), "ticker": ticker}
    
    @Tool("broker_get_positions")
    async def broker_get_positions(self) -> List[Dict]:
        """获取持仓"""
        try:
            return await self.execution_broker.get_positions()
        except Exception as e:
            self.logger.error(f"获取持仓失败: {e}")
            return [{"error": str(e)}]
    
    @Tool("broker_get_account")
    async def broker_get_account(self) -> Dict[str, Any]:
        """获取账户信息"""
        try:
            return await self.execution_broker.get_account_info()
        except Exception as e:
            self.logger.error(f"获取账户信息失败: {e}")
            return {"error": str(e)}
    
    # ========== 综合分析工具 ==========
    
    @Tool("analyze_stock_comprehensive")
    async def analyze_stock_comprehensive(self, ticker: str) -> Dict[str, Any]:
        """综合分析股票"""
        self.logger.info(f"开始综合分析股票: {ticker}")
        
        # 标准化股票代码格式
        normalized_ticker = self._normalize_ticker_symbol(ticker)
        if normalized_ticker != ticker:
            self.logger.info(f"股票代码标准化: {ticker} -> {normalized_ticker}")
            ticker = normalized_ticker
        
        # 首先验证股票代码是否有效
        try:
            self.logger.info(f"验证股票代码: {ticker}")
            quote_data = await self.market_data.get_quote(ticker)
            if not quote_data or 'error' in str(quote_data):
                self.logger.error(f"股票代码 {ticker} 无效或无法获取数据，停止分析")
                return {
                    "ticker": ticker,
                    "error": f"Invalid ticker symbol: {ticker}. No market data found.",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            self.logger.error(f"股票代码验证失败 {ticker}: {e}")
            return {
                "ticker": ticker,
                "error": f"Failed to validate ticker symbol: {ticker}. Error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        
        # 股票代码有效，继续并行获取其他数据
        self.logger.info(f"股票代码验证通过，开始全面分析: {ticker}")
        tasks = [
            self.market_data.get_technical_indicators(ticker),
            self.financial_data.get_financial_ratios(ticker),
            self.news_feed.get_news_sentiment(ticker),
            self.social_sentiment.get_reddit_sentiment(ticker),
            self.reddit_data.get_sentiment_summary(ticker)
        ]
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # 在结果前插入已验证的quote_data
            results.insert(0, quote_data)
            
            analysis_result = {
                "ticker": ticker,
                "market_data": results[0] if not isinstance(results[0], Exception) else {"error": str(results[0])},
                "technical_indicators": results[1] if not isinstance(results[1], Exception) else {"error": str(results[1])},
                "financial_ratios": results[2] if not isinstance(results[2], Exception) else {"error": str(results[2])},
                "news_sentiment": results[3] if not isinstance(results[3], Exception) else {"error": str(results[3])},
                "social_sentiment": results[4] if not isinstance(results[4], Exception) else {"error": str(results[4])},
                "reddit_sentiment": results[5] if not isinstance(results[5], Exception) else {"error": str(results[5])},
                "timestamp": datetime.now().isoformat(),
                "analysis_summary": self._generate_analysis_summary(results, ticker)
            }
            
            self.logger.info(f"完成综合分析股票: {ticker}")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"综合分析失败 {ticker}: {e}")
            return {
                "ticker": ticker,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_analysis_summary(self, results: List, ticker: str) -> Dict[str, Any]:
        """生成分析摘要"""
        summary = {
            "overall_sentiment": "neutral",
            "risk_level": "medium",
            "recommendation": "hold",
            "key_insights": []
        }
        
        try:
            # 基于各模块结果生成摘要
            if not isinstance(results[0], Exception) and results[0]:
                summary["key_insights"].append(f"当前价格: ${results[0].get('price', 'N/A')}")
            
            if not isinstance(results[3], Exception) and results[3]:
                news_sentiment = results[3].get('overall_sentiment', 'neutral')
                summary["key_insights"].append(f"新闻情绪: {news_sentiment}")
                
            if not isinstance(results[4], Exception) and results[4]:
                social_sentiment = results[4].get('sentiment_score', 0)
                if social_sentiment > 0.6:
                    summary["overall_sentiment"] = "positive"
                elif social_sentiment < 0.4:
                    summary["overall_sentiment"] = "negative"
                    
        except Exception as e:
            self.logger.warning(f"生成分析摘要失败: {e}")
            
        return summary
    
    def _normalize_ticker_symbol(self, ticker: str) -> str:
        """标准化股票代码格式"""
        ticker = ticker.upper().strip()
        
        # 港股代码处理：纯数字代码添加.HK后缀
        if ticker.isdigit() and len(ticker) == 4:
            return f"{ticker}.HK"
        
        # 中国A股代码处理：6位数字代码
        if ticker.isdigit() and len(ticker) == 6:
            # 沪市：60开头 -> .SS
            if ticker.startswith('60'):
                return f"{ticker}.SS"
            # 深市：00开头或30开头 -> .SZ  
            elif ticker.startswith(('00', '30')):
                return f"{ticker}.SZ"
        
        # 其他情况保持原样
        return ticker
    
    # ========== Finnhub 数据工具 ==========
    
    @Tool("finnhub_company_news")
    async def finnhub_company_news(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """获取公司新闻"""
        try:
            return await self.finnhub_data.get_company_news(symbol, start_date, end_date)
        except Exception as e:
            self.logger.error(f"获取 {symbol} 公司新闻失败: {e}")
            return []
    
    @Tool("finnhub_insider_sentiment")
    async def finnhub_insider_sentiment(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """获取内部交易情绪"""
        try:
            return await self.finnhub_data.get_insider_sentiment(symbol, start_date, end_date)
        except Exception as e:
            self.logger.error(f"获取 {symbol} 内部交易情绪失败: {e}")
            return {}
    
    @Tool("finnhub_insider_transactions")
    async def finnhub_insider_transactions(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """获取内部交易数据"""
        try:
            return await self.finnhub_data.get_insider_transactions(symbol, start_date, end_date)
        except Exception as e:
            self.logger.error(f"获取 {symbol} 内部交易数据失败: {e}")
            return []
    
    @Tool("finnhub_company_profile")
    async def finnhub_company_profile(self, symbol: str) -> Dict[str, Any]:
        """获取公司基本信息"""
        try:
            return await self.finnhub_data.get_company_profile(symbol)
        except Exception as e:
            self.logger.error(f"获取 {symbol} 公司信息失败: {e}")
            return {}
    
    @Tool("finnhub_market_news")
    async def finnhub_market_news(
        self,
        category: str = "general",
        min_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取市场新闻"""
        try:
            return await self.finnhub_data.get_market_news(category, min_id)
        except Exception as e:
            self.logger.error(f"获取市场新闻失败 (category: {category}): {e}")
            return []
    
    # ========== 技术指标工具 ==========
    
    @Tool("technical_calculate_indicators")
    async def technical_calculate_indicators(
        self,
        symbol: str,
        indicators: Optional[List[str]] = None,
        period: str = "6mo"
    ) -> Dict[str, Any]:
        """计算技术指标"""
        try:
            return await self.technical_indicators.calculate_indicators(
                symbol, indicators, period
            )
        except Exception as e:
            self.logger.error(f"计算 {symbol} 技术指标失败: {e}")
            return {}
    
    @Tool("technical_indicator_summary")
    async def technical_indicator_summary(self, symbol: str) -> Dict[str, Any]:
        """获取技术指标汇总"""
        try:
            return await self.technical_indicators.get_indicator_summary(symbol)
        except Exception as e:
            self.logger.error(f"获取 {symbol} 技术指标汇总失败: {e}")
            return {}
    
    @Tool("news_google_search")
    async def news_google_search(
        self,
        query: Optional[str] = None,
        language: str = "en",
        country: str = "US",
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """搜索 Google 新闻"""
        try:
            return await self.news_feed.get_google_news(query, language, country, max_results)
        except Exception as e:
            self.logger.error(f"搜索 Google 新闻失败 (query: {query}): {e}")
            return []
    
    @Tool("news_financial_search")
    async def news_financial_search(
        self,
        symbols: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """搜索金融相关新闻"""
        try:
            return await self.news_feed.get_financial_news(symbols, keywords)
        except Exception as e:
            self.logger.error(f"搜索金融新闻失败: {e}")
            return []

    # ========== Reddit 社交数据工具 ==========
    
    @Tool("reddit_get_stock_mentions")
    async def reddit_get_stock_mentions(
        self,
        symbol: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取股票在 Reddit 上的提及"""
        try:
            return await self.reddit_data.get_stock_mentions(symbol, limit)
        except Exception as e:
            self.logger.error(f"获取 {symbol} Reddit 提及失败: {e}")
            return []
    
    @Tool("reddit_get_sentiment_summary")
    async def reddit_get_sentiment_summary(self, symbol: str) -> Dict[str, Any]:
        """获取股票 Reddit 情感分析摘要"""
        try:
            return await self.reddit_data.get_sentiment_summary(symbol)
        except Exception as e:
            self.logger.error(f"获取 {symbol} Reddit 情感摘要失败: {e}")
            return {}
    
    @Tool("reddit_get_trending_stocks")
    async def reddit_get_trending_stocks(
        self,
        subreddit_name: str = "stocks",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取 Reddit 热门股票讨论"""
        try:
            return await self.reddit_data.get_trending_stocks(subreddit_name, limit)
        except Exception as e:
            self.logger.error(f"获取 Reddit 热门股票失败 (subreddit: {subreddit_name}): {e}")
            return []

    # ========== 代理配置工具 ==========
    
    @Tool("proxy_test_connection")
    async def proxy_test_connection(self) -> Dict[str, Any]:
        """测试代理连接"""
        try:
            return self.proxy_config.test_proxy_connection()
        except Exception as e:
            self.logger.error(f"代理连接测试失败: {e}")
            return {"error": str(e)}
    
    @Tool("proxy_get_config")
    async def proxy_get_config(self) -> Dict[str, Any]:
        """获取当前代理配置"""
        try:
            proxies = self.proxy_config.get_proxies()
            return {
                "proxy_configured": bool(proxies),
                "http_proxy": bool(self.proxy_config.http_proxy),
                "https_proxy": bool(self.proxy_config.https_proxy),
                "no_proxy": self.proxy_config.no_proxy,
                "proxy_urls": {k: v[:20] + "..." if len(v) > 20 else v for k, v in proxies.items()},
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"获取代理配置失败: {e}")
            return {"error": str(e)}
    
    async def close(self):
        """关闭服务器和所有服务"""
        self.logger.info("开始关闭 TradingAgents 服务器...")
        
        # 关闭所有需要清理的服务
        services_to_close = [
            ("reddit_data", self.reddit_data),
            ("news_feed", self.news_feed),
            ("market_data", self.market_data),
            ("financial_data", self.financial_data),
            ("social_sentiment", self.social_sentiment),
            ("backtesting", self.backtesting),
            ("memory_store", self.memory_store),
            ("risk_analytics", self.risk_analytics),
            ("execution_broker", self.execution_broker),
            ("finnhub_data", self.finnhub_data),
            ("technical_indicators", self.technical_indicators),
        ]
        
        for service_name, service in services_to_close:
            try:
                if hasattr(service, 'close'):
                    await service.close()
                    self.logger.info(f"已关闭 {service_name} 服务")
            except Exception as e:
                self.logger.warning(f"关闭 {service_name} 服务时出错: {e}")
        
        self.logger.info("TradingAgents 服务器已完全关闭")


# 启动服务器
async def main():
    """启动服务器主函数"""
    try:
        # 从环境变量读取配置
        host = os.getenv('MCP_SERVER_HOST', '0.0.0.0')
        port = int(os.getenv('MCP_SERVER_PORT', '8080'))
        
        server = TradingAgentsServer()
        await server.run(host=host, port=port)
    except KeyboardInterrupt:
        logging.info("服务器已停止")
    except Exception as e:
        logging.error(f"服务器启动失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())