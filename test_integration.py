#!/usr/bin/env python3
"""
TradingAgents for Claude Code 数据流集成测试脚本
灵感来源于原 TradingAgents 项目，测试各个数据源服务的基本功能
"""

import asyncio
import os
import sys
import logging
from datetime import datetime, timedelta

# 添加项目根目录到 Python 路径
sys.path.insert(0, '/mnt/disk0/project/quant/tradingagents')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_basic_imports():
    """测试基本导入"""
    logger.info("测试基本导入...")
    
    try:
        # 测试 Yahoo Finance
        import yfinance as yf
        logger.info("✅ yfinance 导入成功")
        
        # 测试基本数据获取
        ticker = yf.Ticker("AAPL")
        info = ticker.info
        logger.info(f"✅ Yahoo Finance 数据获取成功: {info.get('symbol', 'AAPL')}")
        
    except Exception as e:
        logger.error(f"❌ Yahoo Finance 测试失败: {e}")
    
    try:
        # 测试 Finnhub（如果有 API key）
        if os.getenv('FINNHUB_API_KEY'):
            import finnhub
            finnhub_client = finnhub.Client(api_key=os.getenv('FINNHUB_API_KEY'))
            profile = finnhub_client.company_profile2(symbol='AAPL')
            logger.info("✅ Finnhub 连接成功")
        else:
            logger.warning("⚠️ FINNHUB_API_KEY 未设置，跳过 Finnhub 测试")
            
    except Exception as e:
        logger.error(f"❌ Finnhub 测试失败: {e}")
    
    try:
        # 测试 StockStats
        import stockstats
        logger.info("✅ StockStats 导入成功")
        
    except Exception as e:
        logger.error(f"❌ StockStats 导入失败: {e}")
    
    try:
        # 测试 Reddit（如果有配置）
        if os.getenv('REDDIT_CLIENT_ID') and os.getenv('REDDIT_CLIENT_SECRET'):
            import praw
            reddit = praw.Reddit(
                client_id=os.getenv('REDDIT_CLIENT_ID'),
                client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                user_agent='TradingAgents/1.0'
            )
            # 简单测试
            subreddit = reddit.subreddit('all')
            logger.info("✅ Reddit API 连接成功")
        else:
            logger.warning("⚠️ Reddit API 配置未设置，跳过 Reddit 测试")
            
    except Exception as e:
        logger.error(f"❌ Reddit API 测试失败: {e}")

async def test_data_services():
    """测试数据服务模块"""
    logger.info("测试数据服务模块...")
    
    try:
        # 测试技术指标服务
        from tradingagents.mcp.services.technical_indicators import TechnicalIndicatorsService
        tech_service = TechnicalIndicatorsService()
        
        # 获取简单的技术指标
        indicators = await tech_service.calculate_indicators("AAPL", ["RSI", "MACD"], "1mo")
        logger.info(f"✅ 技术指标服务测试成功: {list(indicators.keys())}")
        
    except Exception as e:
        logger.error(f"❌ 技术指标服务测试失败: {e}")
    
    try:
        # 测试新闻服务
        from tradingagents.mcp.services.news_feed import NewsFeedService
        news_service = NewsFeedService()
        
        # 获取谷歌新闻
        news = await news_service.get_google_news("Apple stock", max_results=5)
        logger.info(f"✅ 新闻服务测试成功: 获取到 {len(news)} 条新闻")
        
    except Exception as e:
        logger.error(f"❌ 新闻服务测试失败: {e}")
    
    try:
        # 测试 Finnhub 服务（如果有 API key）
        if os.getenv('FINNHUB_API_KEY'):
            from tradingagents.mcp.services.finnhub_data import FinnhubDataService
            finnhub_service = FinnhubDataService()
            
            # 获取公司信息
            profile = await finnhub_service.get_company_profile("AAPL")
            logger.info(f"✅ Finnhub 服务测试成功: {profile.get('name', 'Apple Inc.')}")
        else:
            logger.warning("⚠️ 跳过 Finnhub 服务测试（无 API key）")
            
    except Exception as e:
        logger.error(f"❌ Finnhub 服务测试失败: {e}")
    
    try:
        # 测试 Reddit 服务（如果有配置）
        if os.getenv('REDDIT_CLIENT_ID') and os.getenv('REDDIT_CLIENT_SECRET'):
            from tradingagents.mcp.services.reddit_data import RedditDataService
            reddit_service = RedditDataService()
            
            # 获取股票提及（限制数量以减少测试时间）
            mentions = await reddit_service.get_stock_mentions("AAPL", limit=5)
            logger.info(f"✅ Reddit 服务测试成功: 获取到 {len(mentions)} 个提及")
        else:
            logger.warning("⚠️ 跳过 Reddit 服务测试（无 API 配置）")
            
    except Exception as e:
        logger.error(f"❌ Reddit 服务测试失败: {e}")

async def test_mcp_server_initialization():
    """测试 MCP 服务器初始化"""
    logger.info("测试 MCP 服务器初始化...")
    
    try:
        from tradingagents.mcp.trading_server import TradingAgentsServer
        
        # 创建服务器实例
        server = TradingAgentsServer()
        logger.info("✅ MCP 服务器初始化成功")
        
        # 测试健康检查
        health = await server.health_check()
        logger.info(f"✅ 健康检查完成: {health['status']}")
        
        # 显示服务状态
        if 'services' in health:
            for service_name, status in health['services'].items():
                status_icon = "✅" if status == "healthy" else "❌"
                logger.info(f"  {status_icon} {service_name}: {status}")
        
    except Exception as e:
        logger.error(f"❌ MCP 服务器测试失败: {e}")

async def test_comprehensive_analysis():
    """测试综合分析功能"""
    logger.info("测试综合分析功能...")
    
    try:
        from tradingagents.mcp.trading_server import TradingAgentsServer
        
        server = TradingAgentsServer()
        
        # 进行综合分析（使用 AAPL 作为测试股票）
        analysis = await server.analyze_stock_comprehensive("AAPL")
        
        logger.info("✅ 综合分析完成")
        logger.info(f"  📊 市场数据: {'✅' if 'error' not in analysis.get('market_data', {}) else '❌'}")
        logger.info(f"  📈 技术指标: {'✅' if 'error' not in analysis.get('technical_indicators', {}) else '❌'}")
        logger.info(f"  📰 新闻情绪: {'✅' if 'error' not in analysis.get('news_sentiment', {}) else '❌'}")
        logger.info(f"  🗣️ 社交情绪: {'✅' if 'error' not in analysis.get('social_sentiment', {}) else '❌'}")
        logger.info(f"  💬 Reddit 情绪: {'✅' if 'error' not in analysis.get('reddit_sentiment', {}) else '❌'}")
        
    except Exception as e:
        logger.error(f"❌ 综合分析测试失败: {e}")

async def main():
    """主测试函数"""
    logger.info("=== TradingAgents 数据流集成测试开始 ===")
    
    # 显示环境配置状态
    logger.info("环境配置状态:")
    logger.info(f"  FINNHUB_API_KEY: {'✅ 已配置' if os.getenv('FINNHUB_API_KEY') else '❌ 未配置'}")
    logger.info(f"  REDDIT_CLIENT_ID: {'✅ 已配置' if os.getenv('REDDIT_CLIENT_ID') else '❌ 未配置'}")
    logger.info(f"  REDDIT_CLIENT_SECRET: {'✅ 已配置' if os.getenv('REDDIT_CLIENT_SECRET') else '❌ 未配置'}")
    logger.info("")
    
    # 运行各项测试
    await test_basic_imports()
    logger.info("")
    
    await test_data_services()
    logger.info("")
    
    await test_mcp_server_initialization()
    logger.info("")
    
    await test_comprehensive_analysis()
    logger.info("")
    
    logger.info("=== TradingAgents 数据流集成测试完成 ===")

if __name__ == "__main__":
    asyncio.run(main())