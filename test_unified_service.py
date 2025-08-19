#!/usr/bin/env python3
"""
统一数据服务测试脚本
验证 Finnhub 替换功能是否正常工作
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta

# 设置日志
logging.basicConfig(level=logging.INFO)

async def test_company_news():
    """测试公司新闻功能"""
    print("\n🔍 测试公司新闻功能...")
    
    from tradingagents.mcp.services.unified_data_service import get_unified_data_service
    
    unified = get_unified_data_service()
    
    # 测试参数
    symbol = "AAPL"
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    try:
        # 测试Google News数据源
        print(f"📰 测试Google News获取 {symbol} 新闻...")
        news = await unified.get_company_news_unified(
            symbol, start_date, end_date, source="google_news", limit=5
        )
        
        if news and not news[0].get('error'):
            print(f"✅ Google News 成功获取 {len(news)} 条新闻")
            for i, article in enumerate(news[:2]):
                print(f"  {i+1}. {article.get('headline', 'N/A')[:50]}...")
        else:
            print(f"⚠️ Google News 返回: {news[0] if news else 'No data'}")
    
    except Exception as e:
        print(f"❌ Google News 测试失败: {e}")
    
    try:
        # 测试自动选择数据源
        print(f"🤖 测试自动选择数据源获取 {symbol} 新闻...")
        news = await unified.get_company_news_unified(
            symbol, start_date, end_date, source="auto", limit=3
        )
        
        if news and not news[0].get('error'):
            print(f"✅ 自动选择 成功获取 {len(news)} 条新闻")
            if news:
                source_used = news[0].get('unified_source', 'unknown')
                print(f"  使用的数据源: {source_used}")
        else:
            print(f"⚠️ 自动选择 返回: {news[0] if news else 'No data'}")
    
    except Exception as e:
        print(f"❌ 自动选择测试失败: {e}")

async def test_company_profile():
    """测试公司信息功能"""
    print("\n🏢 测试公司信息功能...")
    
    from tradingagents.mcp.services.unified_data_service import get_unified_data_service
    
    unified = get_unified_data_service()
    
    symbol = "AAPL"
    
    try:
        # 测试yfinance数据源
        print(f"📊 测试yfinance获取 {symbol} 公司信息...")
        profile = await unified.get_company_profile_unified(
            symbol, source="yfinance", detailed=False
        )
        
        if profile and not profile.get('error'):
            print(f"✅ yfinance 成功获取公司信息")
            print(f"  公司名称: {profile.get('name', 'N/A')}")
            print(f"  行业: {profile.get('industry', 'N/A')}")
            print(f"  市值: {profile.get('market_cap', 'N/A')}")
        else:
            print(f"⚠️ yfinance 返回: {profile.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"❌ yfinance 测试失败: {e}")
    
    try:
        # 测试详细信息
        print(f"📈 测试yfinance获取 {symbol} 详细信息...")
        profile = await unified.get_company_profile_unified(
            symbol, source="yfinance", detailed=True
        )
        
        if profile and not profile.get('error'):
            print(f"✅ yfinance 成功获取详细信息")
            print(f"  P/E比率: {profile.get('trailing_pe', 'N/A')}")
            print(f"  股息收益率: {profile.get('dividend_yield', 'N/A')}")
            print(f"  beta: {profile.get('beta', 'N/A')}")
        else:
            print(f"⚠️ yfinance 详细信息返回: {profile.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"❌ yfinance 详细信息测试失败: {e}")

async def test_data_source_status():
    """测试数据源状态"""
    print("\n⚙️ 测试数据源状态...")
    
    from tradingagents.mcp.services.unified_data_service import get_unified_data_service
    
    unified = get_unified_data_service()
    
    try:
        status = await unified.get_data_source_status()
        print("✅ 数据源状态获取成功")
        
        for source_name, source_info in status.items():
            healthy = source_info.get('healthy', False)
            status_symbol = "✅" if healthy else "❌"
            print(f"  {status_symbol} {source_name}: {source_info.get('description', 'N/A')}")
    
    except Exception as e:
        print(f"❌ 数据源状态测试失败: {e}")

async def test_configuration():
    """测试配置功能"""
    print("\n🔧 测试配置功能...")
    
    from tradingagents.mcp.services.data_source_config import get_data_source_config
    
    try:
        config = get_data_source_config()
        print("✅ 配置加载成功")
        print(f"  策略: {config.strategy.value}")
        print(f"  自动降级: {config.fallback_enabled}")
        print(f"  新闻数据源优先级: {config.get_news_sources()}")
        print(f"  公司信息数据源优先级: {config.get_profile_sources()}")
        
        # 测试数据源可用性
        sources = ['google_news', 'yfinance', 'alpha_vantage']
        for source in sources:
            available = config.is_source_available(source)
            status_symbol = "✅" if available else "❌"
            print(f"  {status_symbol} {source}: {'可用' if available else '不可用'}")
    
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")

async def main():
    """主测试函数"""
    print("🚀 开始统一数据服务测试")
    print("=" * 50)
    
    await test_configuration()
    await test_data_source_status() 
    await test_company_profile()
    await test_company_news()
    
    print("\n" + "=" * 50)
    print("✅ 统一数据服务测试完成")
    
    # 提示如何使用
    print("\n💡 使用提示:")
    print("1. 完全免费方案: 使用 google_news + yfinance")
    print("2. 增强方案: 配置 ALPHA_VANTAGE_API_KEY 环境变量")
    print("3. 数据源可通过 source 参数灵活切换")
    print("4. 支持自动降级，API限制时自动使用免费方案")

if __name__ == "__main__":
    asyncio.run(main())