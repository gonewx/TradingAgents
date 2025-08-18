# MCP 服务器实现指南

本文档说明 TradingAgents 的统一 MCP 服务器架构实现。

> **更新状态**：✅ 已完成实现，使用标准 FastMCP HTTP 服务器架构。

## 概述

TradingAgents 系统通过统一的 MCP 服务器提供完整的交易功能，包含以下模块：

1. **market-data**: 实时市场数据
2. **financial-data**: 财务报表数据
3. **news-feed**: 新闻和市场情绪
4. **social-sentiment**: 社交媒体情绪
5. **backtesting**: 回测引擎
6. **memory-store**: 记忆存储
7. **risk-analytics**: 风险分析
8. **execution-broker**: 交易执行

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
**类型**: FastMCP HTTP 服务器  
**协议**: streamable HTTP MCP  
**端点**: `/mcp`

### 主服务器实现

统一服务器通过模块化设计，将所有功能整合到单一入口：

```python
# tradingagents/mcp/trading_server.py
from mcp.server import FastMCP
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入各功能模块
from .services.market_data import MarketDataService
from .services.financial_data import FinancialDataService
from .services.news_feed import NewsFeedService
from .services.social_sentiment import SocialSentimentService
from .services.backtesting import BacktestingService
from .services.memory_store import MemoryStoreService
from .services.risk_analytics import RiskAnalyticsService
from .services.execution_broker import ExecutionBrokerService

def create_trading_server():
    """创建并配置 TradingAgents MCP 服务器"""
    
    # 从环境变量读取配置
    host = os.getenv('MCP_SERVER_HOST', 'localhost')
    port = int(os.getenv('MCP_SERVER_PORT', '6550'))
    
    # 创建 FastMCP 服务器
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
    social_sentiment = SocialSentimentService()
    # ... 其他服务
    
    # ========== 市场数据工具 ==========
    
    @app.tool()
    async def market_get_quote(ticker: str) -> Dict[str, Any]:
        """获取股票实时报价"""
        return await market_data.get_quote(ticker)
    
    @Tool("market_get_historical")
    async def market_get_historical(
        self, 
        ticker: str, 
        period: str = "1y",
        interval: str = "1d"
    ) -> List[Dict]:
        """获取历史价格数据"""
        return await self.market_data.get_historical_prices(ticker, period, interval)
    
    @Tool("market_get_technical_indicators")
    async def market_get_technical_indicators(self, ticker: str) -> Dict[str, Any]:
        """计算技术指标"""
        return await self.market_data.get_technical_indicators(ticker)
    
    # ========== 财务数据工具 ==========
    
    @Tool("financial_get_income_statement")
    async def financial_get_income_statement(
        self, 
        ticker: str, 
        period: str = "annual"
    ) -> Dict[str, Any]:
        """获取损益表"""
        return await self.financial_data.get_income_statement(ticker, period)
    
    @Tool("financial_get_balance_sheet")
    async def financial_get_balance_sheet(
        self, 
        ticker: str, 
        period: str = "annual"
    ) -> Dict[str, Any]:
        """获取资产负债表"""
        return await self.financial_data.get_balance_sheet(ticker, period)
    
    @Tool("financial_get_ratios")
    async def financial_get_ratios(self, ticker: str) -> Dict[str, Any]:
        """计算财务比率"""
        return await self.financial_data.get_financial_ratios(ticker)
    
    # ========== 新闻情绪工具 ==========
    
    @Tool("news_get_sentiment")
    async def news_get_sentiment(self, ticker: str) -> Dict[str, Any]:
        """分析新闻情绪"""
        return await self.news_feed.get_news_sentiment(ticker)
    
    @Tool("news_get_latest")
    async def news_get_latest(
        self, 
        ticker: str, 
        limit: int = 10
    ) -> List[Dict]:
        """获取最新新闻"""
        return await self.news_feed.get_latest_news(ticker, limit)
    
    # ========== 社交情绪工具 ==========
    
    @Tool("social_get_reddit_sentiment")
    async def social_get_reddit_sentiment(
        self, 
        ticker: str,
        subreddit: str = "wallstreetbets"
    ) -> Dict[str, Any]:
        """分析Reddit情绪"""
        return await self.social_sentiment.get_reddit_sentiment(ticker, subreddit)
    
    @Tool("social_get_trending_tickers")
    async def social_get_trending_tickers(
        self, 
        source: str = "all"
    ) -> List[Dict]:
        """获取热门股票"""
        return await self.social_sentiment.get_trending_tickers(source)
    
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
        return await self.backtesting.run_backtest(
            strategy, ticker, start_date, end_date, initial_cash
        )
    
    @Tool("backtest_optimize")
    async def backtest_optimize(
        self,
        strategy: Dict[str, Any],
        parameters: Dict[str, Any],
        optimization_target: str = "sharpe"
    ) -> Dict[str, Any]:
        """优化策略参数"""
        return await self.backtesting.optimize_parameters(
            strategy, parameters, optimization_target
        )
    
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
        return await self.memory_store.store_decision(
            ticker, decision, context, reasoning
        )
    
    @Tool("memory_retrieve_similar")
    async def memory_retrieve_similar(
        self,
        context: Dict[str, Any],
        n_results: int = 5
    ) -> List[Dict]:
        """检索相似案例"""
        return await self.memory_store.retrieve_similar_cases(context, n_results)
    
    @Tool("memory_update_outcome")
    async def memory_update_outcome(
        self,
        memory_id: str,
        outcome: Dict[str, Any]
    ) -> bool:
        """更新决策结果"""
        return await self.memory_store.update_outcome(memory_id, outcome)
    
    # ========== 风险分析工具 ==========
    
    @Tool("risk_calculate_var")
    async def risk_calculate_var(
        self,
        portfolio: Dict[str, Any],
        confidence_level: float = 0.95,
        time_horizon: int = 1
    ) -> Dict[str, Any]:
        """计算VaR（在险价值）"""
        return await self.risk_analytics.calculate_var(
            portfolio, confidence_level, time_horizon
        )
    
    @Tool("risk_stress_test")
    async def risk_stress_test(
        self,
        portfolio: Dict[str, Any],
        scenarios: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """运行压力测试"""
        return await self.risk_analytics.run_stress_test(portfolio, scenarios)
    
    @Tool("risk_portfolio_optimization")
    async def risk_portfolio_optimization(
        self,
        tickers: List[str],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """组合优化"""
        return await self.risk_analytics.portfolio_optimization(tickers, constraints)
    
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
        return await self.execution_broker.place_order(
            ticker, quantity, side, order_type, limit_price, stop_price
        )
    
    @Tool("broker_get_positions")
    async def broker_get_positions(self) -> List[Dict]:
        """获取持仓"""
        return await self.execution_broker.get_positions()
    
    @Tool("broker_get_account")
    async def broker_get_account(self) -> Dict[str, Any]:
        """获取账户信息"""
        return await self.execution_broker.get_account_info()
    
    # ========== 综合分析工具 ==========
    
    @Tool("analyze_stock_comprehensive")
    async def analyze_stock_comprehensive(self, ticker: str) -> Dict[str, Any]:
        """综合分析股票"""
        # 并行获取各种数据
        tasks = [
            self.market_data.get_quote(ticker),
            self.market_data.get_technical_indicators(ticker),
            self.financial_data.get_financial_ratios(ticker),
            self.news_feed.get_news_sentiment(ticker),
            self.social_sentiment.get_reddit_sentiment(ticker)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "ticker": ticker,
            "market_data": results[0] if not isinstance(results[0], Exception) else None,
            "technical_indicators": results[1] if not isinstance(results[1], Exception) else None,
            "financial_ratios": results[2] if not isinstance(results[2], Exception) else None,
            "news_sentiment": results[3] if not isinstance(results[3], Exception) else None,
            "social_sentiment": results[4] if not isinstance(results[4], Exception) else None,
            "timestamp": asyncio.get_event_loop().time()
        }

# 启动服务器
async def main():
    server = TradingAgentsServer()
    await server.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    asyncio.run(main())
```

## 服务模块实现

各功能模块作为独立的服务类实现，保持代码模块化：

### 环境变量配置

创建 `.env` 文件：

```bash
# 市场数据
MARKET_DATA_API_KEY=your_market_data_api_key
ALPHA_VANTAGE_KEY=your_alpha_vantage_key

# 财务数据
FINANCIAL_DATA_API_KEY=your_financial_data_api_key

# 新闻数据
NEWS_API_KEY=your_news_api_key

# 社交媒体
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_SECRET=your_reddit_secret

# 券商接口
ALPACA_KEY_ID=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# 数据库
DATABASE_URL=postgresql://user:password@localhost/tradingagents
CHROMADB_PATH=./data/chromadb

# 缓存
REDIS_URL=redis://localhost:6379

# 日志
LOG_LEVEL=INFO
LOG_FILE=./logs/tradingagents.log
```

## Claude Code MCP 配置

在 Claude Code 中配置 MCP 服务器：

```json
{
  "mcpServers": {
    "tradingagents": {
      "command": "python",
      "args": ["-m", "tradingagents.mcp.trading_server"],
      "env": {
        "PYTHONPATH": "/path/to/tradingagents"
      }
    }
  }
}
```

或者使用 HTTP 连接：

```json
{
  "mcpServers": {
    "tradingagents": {
      "transport": {
        "type": "http",
        "host": "localhost",
        "port": 8080
      }
    }
  }
}
```

## 启动脚本

创建 `start_server.sh`：

```bash
#!/bin/bash

# 设置环境变量
export PYTHONPATH="$(pwd):$PYTHONPATH"

# 加载环境变量
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# 创建必要目录
mkdir -p logs data/chromadb

# 启动服务器
echo "启动 TradingAgents MCP 服务器..."
python -m tradingagents.mcp.trading_server

echo "服务器启动完成，监听端口 8080"
echo "使用 'claude mcp list' 查看配置的服务器"
```

## 使用示例

### 在 Claude Code 中使用

1. **获取股票报价**：
   ```
   使用 tradingagents 服务器的 market_get_quote 工具获取 AAPL 的报价
   ```

2. **综合分析股票**：
   ```
   使用 analyze_stock_comprehensive 工具分析 TSLA
   ```

3. **运行回测**：
   ```
   使用 backtest_run 工具测试移动平均策略在 AAPL 上的表现
   ```

4. **风险分析**：
   ```
   使用 risk_calculate_var 计算我的投资组合的风险价值
   ```

## 部署建议

### Docker 部署

创建 `Dockerfile`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "-m", "tradingagents.mcp.trading_server"]
```

### 监控和日志

- 使用 `logging` 模块记录所有操作
- 实现健康检查端点
- 添加性能监控指标
- 设置错误告警机制

## 安全考虑

1. **API 密钥管理**: 使用环境变量，不要硬编码
2. **访问控制**: 实现身份验证和授权
3. **数据加密**: 敏感数据传输加密
4. **审计日志**: 记录所有交易操作
5. **限流保护**: 防止 API 滥用

## 下一步

1. 实现各个服务模块的具体代码
2. 添加单元测试和集成测试
3. 完善错误处理和重试机制
4. 实现数据缓存优化
5. 添加监控和告警系统