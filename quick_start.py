#!/usr/bin/env python3
"""
TradingAgents for Claude Code 快速入门脚本
灵感来源于原 TradingAgents 项目，演示主要功能的使用方法

⚠️ 重要声明：本脚本仅用于 Claude Code 技术学习和演示，严禁用于实际投资！
所有金融数据分析功能仅供技术展示，不构成任何投资建议。
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def quick_start_demo():
    """快速入门演示"""
    print("🚀 TradingAgents Claude Code 快速入门演示")
    print("⚠️  重要提醒：本项目仅用于 Claude Code 技术研究，严禁用于实际投资！")
    print("🔬 技术学习用途：探索 MCP、subagents、slash commands 等功能")
    print("🚫 投资风险提醒：任何投资损失与项目开发者无关")
    print("=" * 70)
    
    try:
        # 导入服务器
        from tradingagents.mcp.trading_server import TradingAgentsServer
        
        # 初始化服务器
        print("📡 初始化 TradingAgents 服务器...")
        server = TradingAgentsServer()
        print("✅ 服务器初始化成功！")
        
        # 1. 系统健康检查
        print("\n🔍 步骤 1: 系统健康检查")
        health = await server.health_check()
        print(f"系统状态: {health['status']}")
        
        service_status = []
        for service, status in health['services'].items():
            icon = "✅" if status == "healthy" else "⚠️"
            service_status.append(f"  {icon} {service}: {status}")
        
        print("\n".join(service_status))
        
        # 2. 代理配置检查
        print("\n🌐 步骤 2: 网络和代理配置检查")
        proxy_config = await server.proxy_get_config()
        
        if proxy_config['proxy_configured']:
            print("✅ 代理已配置")
            print(f"  HTTP 代理: {'✅' if proxy_config['http_proxy'] else '❌'}")
            print(f"  HTTPS 代理: {'✅' if proxy_config['https_proxy'] else '❌'}")
        else:
            print("ℹ️ 未配置代理（直连模式）")
        
        # 3. 基础数据获取演示
        print("\n📊 步骤 3: 基础数据获取演示")
        print("获取 Apple (AAPL) 股票报价...")
        
        try:
            quote = await server.market_get_quote("AAPL")
            if 'error' not in quote:
                print(f"✅ AAPL 当前价格: ${quote.get('price', 'N/A')}")
                print(f"  涨跌幅: {quote.get('change_percent', 'N/A')}%")
            else:
                print(f"⚠️ 获取报价失败: {quote['error']}")
        except Exception as e:
            print(f"⚠️ 市场数据获取异常: {e}")
        
        # 4. 技术指标演示
        print("\n📈 步骤 4: 技术指标计算演示")
        print("计算 AAPL 的技术指标...")
        
        try:
            indicators = await server.technical_calculate_indicators(
                "AAPL", ["rsi_14", "macd"], "1mo"
            )
            if indicators and 'error' not in indicators:
                # 使用正确的数据结构访问RSI
                rsi = indicators.get('latest_values', {}).get('rsi_14', 'N/A')
                if isinstance(rsi, (int, float)):
                    print(f"✅ RSI 指标: {rsi:.2f}")
                else:
                    print(f"✅ RSI 指标: {rsi}")
                
                # 使用正确的数据结构访问MACD
                macd_signals = indicators.get('signals', {}).get('macd', 'N/A')
                print(f"  MACD 信号: {macd_signals}")
            else:
                print("⚠️ 技术指标计算失败")
        except Exception as e:
            print(f"⚠️ 技术指标异常: {e}")
        
        # 5. 新闻搜索演示
        print("\n📰 步骤 5: 新闻搜索演示")
        print("搜索 Apple 相关新闻...")
        
        try:
            news = await server.news_google_search("Apple stock", "en", "US", 5)
            if news and len(news) > 0:
                print(f"✅ 找到 {len(news)} 条新闻")
                for i, article in enumerate(news[:3], 1):
                    title = article.get('title', '无标题')[:50]
                    print(f"  {i}. {title}...")
            else:
                print("⚠️ 未找到相关新闻")
        except Exception as e:
            print(f"⚠️ 新闻搜索异常: {e}")
        
        # 6. 综合分析演示
        print("\n🎯 步骤 6: 综合分析演示")
        print("进行 AAPL 综合分析...")
        
        try:
            analysis = await server.analyze_stock_comprehensive("AAPL")
            if analysis and 'error' not in analysis:
                print("✅ 综合分析完成")
                
                # 显示关键信息
                market_data = analysis.get('market_data', {})
                if 'error' not in market_data:
                    print(f"  市场数据: ✅")
                else:
                    print(f"  市场数据: ❌ {market_data.get('error', '')}")
                
                technical = analysis.get('technical_indicators', {})
                if 'error' not in technical:
                    print(f"  技术指标: ✅")
                else:
                    print(f"  技术指标: ❌")
                
                news_sentiment = analysis.get('news_sentiment', {})
                if 'error' not in news_sentiment:
                    print(f"  新闻情绪: ✅")
                else:
                    print(f"  新闻情绪: ❌")
                
                reddit_sentiment = analysis.get('reddit_sentiment', {})
                if 'error' not in reddit_sentiment:
                    print(f"  Reddit 情绪: ✅")
                else:
                    print(f"  Reddit 情绪: ❌")
                
                # 显示分析摘要
                summary = analysis.get('analysis_summary', {})
                if summary:
                    print(f"\n📋 分析摘要:")
                    print(f"  整体情绪: {summary.get('overall_sentiment', 'N/A')}")
                    print(f"  风险等级: {summary.get('risk_level', 'N/A')}")
                    print(f"  投资建议: {summary.get('recommendation', 'N/A')}")
            else:
                print("⚠️ 综合分析失败")
        except Exception as e:
            print(f"⚠️ 综合分析异常: {e}")
        
        # 总结
        print(f"\n🎉 快速入门演示完成！")
        print(f"分析时间: {health.get('timestamp', '')}")
        
        # 下一步建议
        print(f"\n📚 下一步建议:")
        print(f"  1. 查看详细使用示例: docs/cc/usage-examples.md")
        print(f"  2. 配置 API 密钥获得完整功能")
        print(f"  3. 在 Claude Code 中集成 MCP 服务器")
        print(f"  4. 探索更多分析工具和功能")
        
        if not proxy_config['proxy_configured']:
            print(f"  5. 企业环境用户请配置代理设置")
            
        # 正确关闭服务器
        await server.close()
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保已安装所有依赖: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        print("请检查环境配置或查看详细日志")

async def interactive_demo():
    """交互式演示"""
    print("🎮 TradingAgents 交互式演示")
    print("=" * 40)
    
    # 获取用户输入
    symbol = input("请输入要分析的股票代码 (默认: AAPL): ").strip().upper()
    if not symbol:
        symbol = "AAPL"
    
    print(f"\n正在分析 {symbol}...")
    
    server = None
    try:
        from tradingagents.mcp.trading_server import TradingAgentsServer
        server = TradingAgentsServer()
        
        # 进行分析
        analysis = await server.analyze_stock_comprehensive(symbol)
        
        if analysis and 'error' not in analysis:
            print(f"\n📊 {symbol} 分析结果:")
            
            # 市场数据
            market_data = analysis.get('market_data', {})
            if 'error' not in market_data:
                price = market_data.get('price', 'N/A')
                change = market_data.get('change_percent', 'N/A')
                print(f"  当前价格: ${price}")
                print(f"  涨跌幅: {change}%")
            
            # 分析摘要
            summary = analysis.get('analysis_summary', {})
            if summary:
                print(f"  整体情绪: {summary.get('overall_sentiment', 'N/A')}")
                print(f"  投资建议: {summary.get('recommendation', 'N/A')}")
                
                insights = summary.get('key_insights', [])
                if insights:
                    print("  关键洞察:")
                    for insight in insights:
                        print(f"    • {insight}")
        else:
            print(f"❌ 分析 {symbol} 失败")
            if 'error' in analysis:
                print(f"错误: {analysis['error']}")
        
        # 正确关闭服务器
        if server:
            await server.close()
    
    except Exception as e:
        print(f"❌ 交互演示出错: {e}")
        # 确保在异常情况下也关闭服务器
        if server:
            try:
                await server.close()
            except:
                pass

def main():
    """主函数"""
    print("TradingAgents Claude Code - 快速入门")
    print("=" * 50)
    
    # 检查环境
    env_status = []
    
    # 检查关键依赖
    required_modules = [
        'pandas', 'numpy', 'yfinance', 'requests', 
        'feedparser', 'stockstats', 'textblob'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("❌ 缺少以下依赖模块:")
        for module in missing_modules:
            print(f"  - {module}")
        print("\n请运行: pip install -r requirements.txt")
        return
    
    # 检查环境变量
    api_keys = {
        'FINNHUB_API_KEY': os.getenv('FINNHUB_API_KEY'),
        'REDDIT_CLIENT_ID': os.getenv('REDDIT_CLIENT_ID'),
        'REDDIT_CLIENT_SECRET': os.getenv('REDDIT_CLIENT_SECRET'),
    }
    
    configured_apis = sum(1 for key, value in api_keys.items() if value)
    print(f"📊 环境检查:")
    print(f"  已配置 API: {configured_apis}/3")
    
    for key, value in api_keys.items():
        status = "✅" if value else "⚠️"
        print(f"  {status} {key}")
    
    if configured_apis == 0:
        print("\nℹ️ 注意: 未配置 API 密钥，某些功能可能受限")
        print("  基础功能（Yahoo Finance）仍然可用")
    
    # 选择演示模式
    print(f"\n选择演示模式:")
    print(f"  1. 自动演示 - 展示所有功能")
    print(f"  2. 交互演示 - 分析指定股票")
    print(f"  3. 退出")
    
    try:
        choice = input("\n请选择 (1-3): ").strip()
        
        if choice == "1":
            asyncio.run(quick_start_demo())
        elif choice == "2":
            asyncio.run(interactive_demo())
        elif choice == "3":
            print("👋 退出演示")
        else:
            print("❌ 无效选择")
    
    except KeyboardInterrupt:
        print("\n👋 用户中断，退出演示")
    except Exception as e:
        print(f"❌ 程序异常: {e}")

if __name__ == "__main__":
    main()