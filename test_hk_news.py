#!/usr/bin/env python3
"""
测试香港股票新闻获取问题
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 加载环境变量
load_dotenv()

from tradingagents.mcp.services.data_sources.google_news_source import GoogleNewsSource

async def test_hk_stock_news():
    """测试香港股票新闻获取"""
    print("=== 测试香港股票 1952.HK 新闻获取 ===")
    
    google_news = GoogleNewsSource()
    
    # 测试健康检查
    print("1. 健康检查...")
    health = await google_news.health_check()
    print(f"   健康状态: {health}")
    
    # 测试股票支持
    print("2. 支持检查...")
    supported = await google_news.is_supported("1952.HK")
    print(f"   支持 1952.HK: {supported}")
    
    # 测试不同的搜索查询
    test_queries = [
        "1952.HK",
        "1952 HK stock",
        "Evergrande",
        "中国恒大",
        "Evergrande Group",
        "3333.HK",  # 另一个香港股票
        "0700.HK",  # 腾讯
        "TCEHY"     # 腾讯美股代码
    ]
    
    print("3. 测试不同搜索查询...")
    for query in test_queries:
        print(f"\n   测试查询: {query}")
        try:
            articles = await google_news._search_google_news(query, 3)
            print(f"   结果数量: {len(articles)}")
            for i, article in enumerate(articles[:2]):
                print(f"     [{i+1}] {article.get('headline', 'N/A')[:80]}...")
        except Exception as e:
            print(f"   错误: {e}")
    
    # 测试完整的新闻获取
    print("\n4. 测试完整新闻获取...")
    try:
        result = await google_news.get_company_news("1952.HK", "2025-08-18", "2025-08-19", 5)
        print(f"   最终结果数量: {len(result)}")
        
        if result:
            for i, article in enumerate(result[:2]):
                print(f"     [{i+1}] {article.get('headline', 'N/A')}")
        else:
            print("   无结果返回")
            
    except Exception as e:
        print(f"   获取新闻失败: {e}")
    
    # 测试详细的过滤过程
    print("\n5. 测试详细过滤过程...")
    try:
        # 手动复制 get_company_news 的逻辑来调试
        queries = [
            "1952.HK stock",
            "1952.HK earnings", 
            "1952.HK news"
        ]
        
        all_articles = []
        for query in queries:
            print(f"   搜索查询: {query}")
            articles = await google_news._search_google_news(query, 5)
            print(f"   原始结果: {len(articles)}")
            all_articles.extend(articles)
        
        print(f"   总原始文章数: {len(all_articles)}")
        
        # 去重
        unique_articles = google_news._deduplicate_articles(all_articles)
        print(f"   去重后文章数: {len(unique_articles)}")
        
        # 日期过滤
        filtered_articles = google_news._filter_by_date(unique_articles, "2025-08-18", "2025-08-19")
        print(f"   日期过滤后文章数: {len(filtered_articles)}")
        
        # 显示一些文章的日期
        for i, article in enumerate(unique_articles[:3]):
            pub_date = article.get('datetime', 'N/A')
            print(f"     文章 {i+1} 日期: {pub_date}")
            
    except Exception as e:
        print(f"   详细测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_hk_stock_news())