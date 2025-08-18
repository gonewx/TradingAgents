# MCP 服务器实现指南

本文档说明本项目在 Claude Code 中的统一 MCP 服务器架构实现。

> 灵感来源于原 [TradingAgents](https://github.com/TauricResearch/TradingAgents) 项目，感谢原团队的设计思路。

> **更新状态**：✅ **已完成实现**，使用标准 FastMCP Streamable HTTP 服务器架构。

## 概述

本系统参考原 TradingAgents 的设计，通过统一的 MCP 服务器提供完整的金融数据分析功能，包含以下模块：

1. **market-data**: 实时市场数据
2. **financial-data**: 财务报表数据
3. **news-feed**: 新闻和市场情绪
4. **social-sentiment**: 社交媒体情绪
5. **finnhub-data**: Finnhub 金融数据
6. **technical-indicators**: 技术指标计算
7. **reddit-data**: Reddit 社交数据
8. **proxy-config**: 代理配置支持

## 架构优势

### 统一服务器架构的优点
- **简化部署**: 单一进程，一个端口配置
- **降低延迟**: 减少网络调用，提高响应速度
- **数据共享**: 模块间可直接共享状态和缓存
- **配置简单**: Claude Code 只需配置一个 MCP 连接
- **资源高效**: 共享进程资源，降低系统开销

## 统一服务器实现

### 核心架构

**端口**: 6550  
**类型**: FastMCP Streamable HTTP 服务器  
**协议**: Streamable HTTP MCP（推荐的生产模式）  
**端点**: `/mcp`

### 主服务器实现

使用标准 FastMCP 库实现，支持 Claude Code 原生集成：

```python
# tradingagents/mcp/trading_server.py
from mcp.server import FastMCP
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

def create_trading_server():
    """创建并配置 TradingAgents MCP 服务器"""
    
    # 从环境变量读取配置
    host = os.getenv('MCP_SERVER_HOST', 'localhost')
    port = int(os.getenv('MCP_SERVER_PORT', '6550'))
    
    # 创建 FastMCP 服务器（在模块级别初始化）
    app = FastMCP(
        name="TradingAgents",
        host=host,
        port=port,
        debug=log_level == 'DEBUG'
    )
    
    # 初始化各功能服务
    market_data = MarketDataService()
    financial_data = FinancialDataService()
    news_feed = NewsFeedService()
    # ... 其他服务
    
    # ========== 主要 MCP 工具 ==========
    
    @app.tool()
    async def health_check() -> Dict[str, Any]:
        """系统健康检查"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {...}
        }
    
    @app.tool()
    async def market_get_quote(ticker: str) -> Dict[str, Any]:
        """获取股票实时报价"""
        return await market_data.get_quote(ticker)
    
    @app.tool()
    async def analyze_stock_comprehensive(ticker: str) -> Dict[str, Any]:
        """综合分析股票 - 推荐入口工具"""
        # 并行获取各种数据
        tasks = [
            market_data.get_quote(ticker),
            market_data.get_technical_indicators(ticker),
            financial_data.get_financial_ratios(ticker),
            news_feed.get_news_sentiment(ticker),
            reddit_data.get_sentiment_summary(ticker)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "ticker": ticker,
            "market_data": results[0],
            "technical_indicators": results[1],
            "financial_ratios": results[2],
            "news_sentiment": results[3],
            "reddit_sentiment": results[4],
            "timestamp": datetime.now().isoformat()
        }
    
    @app.tool()
    async def technical_calculate_indicators(
        symbol: str,
        indicators: Optional[List[str]] = None,
        period: str = "6mo"
    ) -> Dict[str, Any]:
        """计算技术指标"""
        return await technical_indicators.calculate_indicators(
            symbol, indicators, period
        )
    
    @app.tool()
    async def finnhub_company_news(
        symbol: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """获取公司新闻"""
        return await finnhub_data.get_company_news(symbol, start_date, end_date)
    
    @app.tool()
    async def reddit_get_sentiment_summary(symbol: str) -> Dict[str, Any]:
        """获取股票 Reddit 情感分析摘要"""
        return await reddit_data.get_sentiment_summary(symbol)
    
    @app.tool()
    async def proxy_get_config() -> Dict[str, Any]:
        """获取当前代理配置"""
        return proxy_config.get_proxy_status()
    
    return app

# 启动服务器
def main():
    """启动服务器主函数"""
    app = create_trading_server()
    app.run(transport="streamable-http")

if __name__ == "__main__":
    main()
```

## 环境变量配置

创建 `.env` 文件：

```bash
# ========== MCP 服务器配置 ==========
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=6550

# ========== 必需配置 ==========
# Finnhub API - 金融数据、新闻、内部交易信息
FINNHUB_API_KEY=your_finnhub_api_key_here

# ========== 可选配置 ==========
# Reddit API - 社交媒体情绪分析
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=TradingAgents/1.0

# ========== 代理配置（企业网络环境） ==========
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=http://proxy.company.com:8080
NO_PROXY=localhost,127.0.0.1,.local

# ========== 数据缓存配置 ==========
DATA_CACHE_TTL=300   # 5分钟
NEWS_CACHE_TTL=900   # 15分钟

# ========== 日志配置 ==========
LOG_LEVEL=INFO
```

## Claude Code MCP 配置

在项目根目录的 `.mcp.json` 文件中配置：

```json
{
  "mcpServers": {
    "trading": {
      "type": "http",
      "url": "http://localhost:6550/mcp"
    }
  }
}
```

**重要注意**：服务器名称必须在 Claude Code 的 settings 中正确配置才能被识别。

## 启动和使用

### 启动服务器

```bash
# 使用启动脚本（推荐）
./start_server.sh

# 或直接启动
source .venv/bin/activate
python -m tradingagents.mcp.trading_server
```

### 验证连接

```bash
# 检查 MCP 服务器状态
claude mcp list

# 查看 tradingagents 服务器详情
claude mcp get tradingagents
```

## 主要工具使用

### 1. 系统健康检查
```python
# 在 Claude Code 中使用
health_check()
```

### 2. 股票综合分析（推荐入口）
```python
# 分析单只股票的完整信息
analyze_stock_comprehensive("AAPL")
```

### 3. 技术指标分析
```python
# 计算特定技术指标
technical_calculate_indicators("AAPL", ["RSI", "MACD", "SMA"], "3mo")
```

### 4. 新闻和社交媒体分析
```python
# Finnhub 公司新闻
finnhub_company_news("AAPL", "2025-01-01", "2025-01-31")

# Reddit 情绪分析
reddit_get_sentiment_summary("AAPL")
```

### 5. 代理配置检查（企业环境）
```python
# 检查代理配置
proxy_get_config()
```

## 部署建议

### 生产环境部署

1. **使用虚拟环境**：
   ```bash
   # 推荐使用 uv
   uv venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```

2. **配置环境变量**：
   - 确保所有必需的 API 密钥已配置
   - 设置适当的缓存时间
   - 配置代理（如果在企业网络中）

3. **启动服务器**：
   ```bash
   # 后台运行
   nohup python -m tradingagents.mcp.trading_server &
   
   # 或使用 systemd 服务
   sudo systemctl start tradingagents-mcp
   ```

### 监控和日志

- **健康检查**：使用 `health_check()` 工具定期检查系统状态
- **日志级别**：生产环境建议使用 `LOG_LEVEL=INFO`
- **错误监控**：所有工具都有统一的错误处理格式

## 故障排除

### 常见问题

1. **连接失败**：
   - 检查端口 6550 是否被占用
   - 验证 `.mcp.json` 配置是否正确
   - 确认服务器已启动

2. **API 错误**：
   - 验证 API 密钥是否有效
   - 检查网络连接和代理配置
   - 使用 `proxy_get_config()` 诊断代理问题

3. **数据获取失败**：
   - 检查股票代码格式是否正确
   - 验证日期范围是否有效
   - 查看服务器日志获取详细错误信息

### 调试命令

```bash
# 启用详细日志
export LOG_LEVEL=DEBUG
python -m tradingagents.mcp.trading_server

# 测试代理连接
python -c "from tradingagents.mcp.services.proxy_config import get_proxy_config; print(get_proxy_config().test_proxy_connection())"

# 检查依赖
python -c "import pandas, numpy, yfinance, finnhub, requests; print('✅ 所有依赖已安装')"
```

## 技术特性

### 已实现功能

- ✅ **标准 MCP 协议支持**：完全兼容 Claude Code
- ✅ **异步并发处理**：高性能数据获取
- ✅ **智能缓存系统**：减少 API 调用次数
- ✅ **企业代理支持**：支持复杂网络环境
- ✅ **统一错误处理**：一致的错误响应格式
- ✅ **健康检查机制**：实时监控系统状态

### 性能优化

- **缓存策略**：市场数据缓存 5 分钟，新闻数据缓存 15 分钟
- **并行处理**：`analyze_stock_comprehensive` 并行获取多种数据
- **连接池**：复用 HTTP 连接，减少网络开销
- **错误重试**：自动重试失败的网络请求

## 下一步

1. **扩展功能**：添加更多技术指标和数据源
2. **性能优化**：实现更高级的缓存策略
3. **监控集成**：添加 Prometheus 指标支持
4. **安全增强**：实现 API 密钥轮换机制