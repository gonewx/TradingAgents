"""
TradingAgents for Claude Code - 统一 MCP 服务器
灵感来源于原 TradingAgents 项目，感谢原团队的设计理念

⚠️ 重要免责声明：
本项目仅用于研究和学习 Claude Code 的技术实现，严禁用于任何实际的股票交易或金融投资！
所有金融数据分析功能仅供技术演示，不构成任何投资建议。
任何因使用本项目进行投资决策造成的损失，开发者概不负责。
请仅将此项目用于 Claude Code 技术学习和研究目的。
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 正确的 MCP 框架导入
from mcp.server import FastMCP

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

logger = logging.getLogger(__name__)

# 创建 FastMCP 服务器实例
# 从环境变量读取配置
host = os.getenv('MCP_SERVER_HOST', 'localhost')
port = int(os.getenv('MCP_SERVER_PORT', '6550'))

app = FastMCP(
    name="TradingAgents",
    host=host,
    port=port,
    debug=log_level == 'DEBUG'
)

def create_trading_server():
    """初始化 TradingAgents MCP 服务器"""
    
    logger.info(f"初始化 TradingAgents MCP 服务器: {host}:{port}")
    
    # 初始化代理配置
    proxy_config = get_proxy_config()
    
    # 初始化各功能服务
    try:
        market_data = MarketDataService()
        financial_data = FinancialDataService()
        news_feed = NewsFeedService()
        social_sentiment = SocialSentimentService()
        backtesting = BacktestingService()
        memory_store = MemoryStoreService()
        risk_analytics = RiskAnalyticsService()
        execution_broker = ExecutionBrokerService()
        finnhub_data = FinnhubDataService()
        technical_indicators = TechnicalIndicatorsService()
        reddit_data = RedditDataService()
        
        logger.info("TradingAgents 服务组件初始化完成")
    except Exception as e:
        logger.error(f"服务器初始化失败: {e}")
        raise
    
    # ========== 健康检查工具 ==========
    
    @app.tool()
    async def health_check() -> Dict[str, Any]:
        """系统健康检查"""
        try:
            # 简化的健康检查，避免循环依赖
            status = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "services": {
                    "market_data": "healthy",
                    "financial_data": "healthy", 
                    "news_feed": "healthy",
                    "social_sentiment": "healthy",
                    "backtesting": "healthy",
                    "memory_store": "healthy",
                    "risk_analytics": "healthy",
                    "execution_broker": "healthy",
                    "finnhub_data": "healthy",
                    "technical_indicators": "healthy",
                    "reddit_data": "healthy",
                }
            }
            return status
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    # ========== 市场数据工具 ==========
    
    @app.tool()
    async def market_get_quote(ticker: str) -> Dict[str, Any]:
        """获取股票实时报价"""
        try:
            # 标准化股票代码格式
            normalized_ticker = _normalize_ticker_symbol(ticker)
            if normalized_ticker != ticker:
                logger.info(f"股票代码标准化: {ticker} -> {normalized_ticker}")
                ticker = normalized_ticker
            
            return await market_data.get_quote(ticker)
        except Exception as e:
            logger.error(f"获取报价失败 {ticker}: {e}")
            return {"error": str(e), "ticker": ticker}
    
    @app.tool()
    async def market_get_historical(
        ticker: str, 
        period: str = "1y",
        interval: str = "1d"
    ) -> List[Dict]:
        """获取历史价格数据"""
        try:
            # 标准化股票代码格式
            normalized_ticker = _normalize_ticker_symbol(ticker)
            if normalized_ticker != ticker:
                logger.info(f"股票代码标准化: {ticker} -> {normalized_ticker}")
                ticker = normalized_ticker
                
            return await market_data.get_historical_prices(ticker, period, interval)
        except Exception as e:
            logger.error(f"获取历史数据失败 {ticker}: {e}")
            return [{"error": str(e), "ticker": ticker}]
    
    @app.tool()
    async def market_get_technical_indicators(ticker: str) -> Dict[str, Any]:
        """计算技术指标"""
        try:
            # 标准化股票代码格式
            normalized_ticker = _normalize_ticker_symbol(ticker)
            if normalized_ticker != ticker:
                logger.info(f"股票代码标准化: {ticker} -> {normalized_ticker}")
                ticker = normalized_ticker
                
            return await market_data.get_technical_indicators(ticker)
        except Exception as e:
            logger.error(f"计算技术指标失败 {ticker}: {e}")
            return {"error": str(e), "ticker": ticker}
    
    # ========== 财务数据工具 ==========
    
    @app.tool()
    async def financial_get_income_statement(
        ticker: str, 
        period: str = "annual"
    ) -> Dict[str, Any]:
        """获取损益表"""
        try:
            # 标准化股票代码格式
            normalized_ticker = _normalize_ticker_symbol(ticker)
            if normalized_ticker != ticker:
                logger.info(f"股票代码标准化: {ticker} -> {normalized_ticker}")
                ticker = normalized_ticker
                
            return await financial_data.get_income_statement(ticker, period)
        except Exception as e:
            logger.error(f"获取损益表失败 {ticker}: {e}")
            return {"error": str(e), "ticker": ticker}
    
    @app.tool()
    async def financial_get_balance_sheet(
        ticker: str, 
        period: str = "annual"
    ) -> Dict[str, Any]:
        """获取资产负债表"""
        try:
            # 标准化股票代码格式
            normalized_ticker = _normalize_ticker_symbol(ticker)
            if normalized_ticker != ticker:
                logger.info(f"股票代码标准化: {ticker} -> {normalized_ticker}")
                ticker = normalized_ticker
                
            return await financial_data.get_balance_sheet(ticker, period)
        except Exception as e:
            logger.error(f"获取资产负债表失败 {ticker}: {e}")
            return {"error": str(e), "ticker": ticker}
    
    @app.tool()
    async def financial_get_ratios(ticker: str) -> Dict[str, Any]:
        """计算财务比率"""
        try:
            # 标准化股票代码格式
            normalized_ticker = _normalize_ticker_symbol(ticker)
            if normalized_ticker != ticker:
                logger.info(f"股票代码标准化: {ticker} -> {normalized_ticker}")
                ticker = normalized_ticker
                
            return await financial_data.get_financial_ratios(ticker)
        except Exception as e:
            logger.error(f"计算财务比率失败 {ticker}: {e}")
            return {"error": str(e), "ticker": ticker}
    
    # ========== 新闻情绪工具 ==========
    
    @app.tool()
    async def news_get_sentiment(ticker: str) -> Dict[str, Any]:
        """分析新闻情绪"""
        try:
            # 标准化股票代码格式
            normalized_ticker = _normalize_ticker_symbol(ticker)
            if normalized_ticker != ticker:
                logger.info(f"股票代码标准化: {ticker} -> {normalized_ticker}")
                ticker = normalized_ticker
                
            return await news_feed.get_news_sentiment(ticker)
        except Exception as e:
            logger.error(f"分析新闻情绪失败 {ticker}: {e}")
            return {"error": str(e), "ticker": ticker}
    
    @app.tool()
    async def news_get_latest(
        ticker: str, 
        limit: int = 10
    ) -> List[Dict]:
        """获取最新新闻"""
        try:
            # 标准化股票代码格式
            normalized_ticker = _normalize_ticker_symbol(ticker)
            if normalized_ticker != ticker:
                logger.info(f"股票代码标准化: {ticker} -> {normalized_ticker}")
                ticker = normalized_ticker
                
            return await news_feed.get_latest_news(ticker, limit)
        except Exception as e:
            logger.error(f"获取最新新闻失败 {ticker}: {e}")
            return [{"error": str(e), "ticker": ticker}]
    
    # ========== 社交情绪工具 ==========
    
    @app.tool()
    async def social_get_reddit_sentiment(
        ticker: str,
        subreddit: str = "wallstreetbets"
    ) -> Dict[str, Any]:
        """分析Reddit情绪"""
        try:
            # 标准化股票代码格式
            normalized_ticker = _normalize_ticker_symbol(ticker)
            if normalized_ticker != ticker:
                logger.info(f"股票代码标准化: {ticker} -> {normalized_ticker}")
                ticker = normalized_ticker
                
            return await social_sentiment.get_reddit_sentiment(ticker, subreddit)
        except Exception as e:
            logger.error(f"分析Reddit情绪失败 {ticker}: {e}")
            return {"error": str(e), "ticker": ticker}
    
    @app.tool()
    async def social_get_trending_tickers(
        source: str = "all"
    ) -> List[Dict]:
        """获取热门股票"""
        try:
            return await social_sentiment.get_trending_tickers(source)
        except Exception as e:
            logger.error(f"获取热门股票失败: {e}")
            return [{"error": str(e)}]
    
    # ========== 综合分析工具 ==========
    
    @app.tool()
    async def analyze_stock_comprehensive(ticker: str) -> Dict[str, Any]:
        """综合分析股票"""
        logger.info(f"开始综合分析股票: {ticker}")
        
        # 标准化股票代码格式
        normalized_ticker = _normalize_ticker_symbol(ticker)
        if normalized_ticker != ticker:
            logger.info(f"股票代码标准化: {ticker} -> {normalized_ticker}")
            ticker = normalized_ticker
        
        # 首先验证股票代码是否有效
        try:
            logger.info(f"验证股票代码: {ticker}")
            quote_data = await market_data.get_quote(ticker)
            if not quote_data or 'error' in str(quote_data):
                logger.error(f"股票代码 {ticker} 无效或无法获取数据，停止分析")
                return {
                    "ticker": ticker,
                    "error": f"Invalid ticker symbol: {ticker}. No market data found.",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"股票代码验证失败 {ticker}: {e}")
            return {
                "ticker": ticker,
                "error": f"Failed to validate ticker symbol: {ticker}. Error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        
        # 股票代码有效，继续并行获取其他数据
        logger.info(f"股票代码验证通过，开始全面分析: {ticker}")
        tasks = [
            market_data.get_technical_indicators(ticker),
            financial_data.get_financial_ratios(ticker),
            news_feed.get_news_sentiment(ticker),
            social_sentiment.get_reddit_sentiment(ticker),
            reddit_data.get_sentiment_summary(ticker)
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
                "analysis_summary": _generate_analysis_summary(results, ticker)
            }
            
            logger.info(f"完成综合分析股票: {ticker}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"综合分析失败 {ticker}: {e}")
            return {
                "ticker": ticker,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    # ========== Finnhub 数据工具 ==========
    
    @app.tool()
    async def finnhub_company_news(
        symbol: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """获取公司新闻"""
        try:
            # 标准化股票代码格式
            normalized_symbol = _normalize_ticker_symbol(symbol)
            if normalized_symbol != symbol:
                logger.info(f"股票代码标准化: {symbol} -> {normalized_symbol}")
                symbol = normalized_symbol
                
            return await finnhub_data.get_company_news(symbol, start_date, end_date)
        except Exception as e:
            logger.error(f"获取 {symbol} 公司新闻失败: {e}")
            return []
    
    @app.tool()
    async def finnhub_company_profile(symbol: str) -> Dict[str, Any]:
        """获取公司基本信息"""
        try:
            # 标准化股票代码格式
            normalized_symbol = _normalize_ticker_symbol(symbol)
            if normalized_symbol != symbol:
                logger.info(f"股票代码标准化: {symbol} -> {normalized_symbol}")
                symbol = normalized_symbol
                
            return await finnhub_data.get_company_profile(symbol)
        except Exception as e:
            logger.error(f"获取 {symbol} 公司信息失败: {e}")
            return {}
    
    # ========== 技术指标工具 ==========
    
    @app.tool()
    async def technical_calculate_indicators(
        symbol: str,
        indicators: Optional[List[str]] = None,
        period: str = "6mo"
    ) -> Dict[str, Any]:
        """计算技术指标"""
        try:
            # 标准化股票代码格式
            normalized_symbol = _normalize_ticker_symbol(symbol)
            if normalized_symbol != symbol:
                logger.info(f"股票代码标准化: {symbol} -> {normalized_symbol}")
                symbol = normalized_symbol
                
            return await technical_indicators.calculate_indicators(
                symbol, indicators, period
            )
        except Exception as e:
            logger.error(f"计算 {symbol} 技术指标失败: {e}")
            return {}
    
    @app.tool()
    async def technical_indicator_summary(symbol: str) -> Dict[str, Any]:
        """获取技术指标汇总"""
        try:
            # 标准化股票代码格式
            normalized_symbol = _normalize_ticker_symbol(symbol)
            if normalized_symbol != symbol:
                logger.info(f"股票代码标准化: {symbol} -> {normalized_symbol}")
                symbol = normalized_symbol
                
            return await technical_indicators.get_indicator_summary(symbol)
        except Exception as e:
            logger.error(f"获取 {symbol} 技术指标汇总失败: {e}")
            return {}
    
    # ========== Reddit 社交数据工具 ==========
    
    @app.tool()
    async def reddit_get_stock_mentions(
        symbol: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取股票在 Reddit 上的提及"""
        try:
            # 标准化股票代码格式
            normalized_symbol = _normalize_ticker_symbol(symbol)
            if normalized_symbol != symbol:
                logger.info(f"股票代码标准化: {symbol} -> {normalized_symbol}")
                symbol = normalized_symbol
                
            return await reddit_data.get_stock_mentions(symbol, limit)
        except Exception as e:
            logger.error(f"获取 {symbol} Reddit 提及失败: {e}")
            return []
    
    @app.tool()
    async def reddit_get_sentiment_summary(symbol: str) -> Dict[str, Any]:
        """获取股票 Reddit 情感分析摘要"""
        try:
            # 标准化股票代码格式
            normalized_symbol = _normalize_ticker_symbol(symbol)
            if normalized_symbol != symbol:
                logger.info(f"股票代码标准化: {symbol} -> {normalized_symbol}")
                symbol = normalized_symbol
                
            return await reddit_data.get_sentiment_summary(symbol)
        except Exception as e:
            logger.error(f"获取 {symbol} Reddit 情感摘要失败: {e}")
            return {}
    
    # ========== 代理配置工具 ==========
    
    @app.tool()
    async def proxy_test_connection() -> Dict[str, Any]:
        """测试代理连接"""
        try:
            return proxy_config.test_proxy_connection()
        except Exception as e:
            logger.error(f"代理连接测试失败: {e}")
            return {"error": str(e)}
    
    @app.tool()
    async def proxy_get_config() -> Dict[str, Any]:
        """获取当前代理配置"""
        try:
            proxies = proxy_config.get_proxies()
            return {
                "proxy_configured": bool(proxies),
                "http_proxy": bool(proxy_config.http_proxy),
                "https_proxy": bool(proxy_config.https_proxy),
                "no_proxy": proxy_config.no_proxy,
                "proxy_urls": {k: v[:20] + "..." if len(v) > 20 else v for k, v in proxies.items()},
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取代理配置失败: {e}")
            return {"error": str(e)}
    
    # 服务器配置完成，app 已在模块级别创建

def _normalize_ticker_symbol(ticker: str) -> str:
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

def _generate_analysis_summary(results: List, ticker: str) -> Dict[str, Any]:
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
        logger.warning(f"生成分析摘要失败: {e}")
        
    return summary

# 启动服务器的主函数
def main():
    """启动服务器主函数"""
    import asyncio
    import sys
    
    try:
        # 初始化服务器配置
        create_trading_server()
        logger.info("TradingAgents MCP 服务器启动中...")
        
        # 检查是否通过 stdio 启动（被 Claude Code 调用）
        if '--stdio' in sys.argv or os.getenv('MCP_TRANSPORT') == 'stdio':
            logger.info("启动 STDIO 模式")
            app.run(transport="stdio")
        else:
            # 启动 Streamable HTTP 服务器模式
            logger.info("启动 Streamable HTTP 服务器模式")
            app.run(transport="streamable-http")
            
    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except asyncio.CancelledError:
        logger.info("服务器异步任务已取消")
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        raise

if __name__ == "__main__":
    main()