# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ 重要提醒

**本项目仅用于研究 Claude Code 技术实现，严禁用于实际金融投资！**

- 🔬 **技术研究目的**：探索 Claude Code 的 MCP、subagents、slash commands 等功能
- 🚫 **禁止投资行为**：所有分析结果仅供技术演示，不得作为投资依据
- 📚 **学习用途**：专注于 Claude Code 平台能力的学习和实践
- ⚖️ **免责声明**：任何投资损失与项目开发者无关

## 项目概述

灵感来源于原 `TradingAgents` 项目，在 `claude code` 中重新实现类似的量化交易分析功能。基于 `claude code` 的能力，如 `slash command`、`subagents`、`mcp` 等功能来实现。

`claude code`的说明见这个目录中的文档: @docs/cc/ 

要完全掌握 [TradingAgents](https://github.com/TauricResearch/TradingAgents) 的细节请 use mcp deepwiki工具完成

最终产出是 `claude code` 相关的文件，包括 `slash command`、`subagents`、`mcp` 等。目标是利用这些能力实现与原 `TradingAgents` 相似的量化交易分析功能。

### 🆕 重大更新：统一数据源系统
项目已实现完整的 **Finnhub 免费替代方案**：
- ✅ **完全免费方案**: Google News + yfinance (无限制)
- ✅ **增强免费方案**: Alpha Vantage API (500次/天)  
- ✅ **智能降级**: API限制时自动切换免费方案
- ✅ **配置灵活**: 环境变量一键切换数据源
- ✅ **向后兼容**: 保持原有Finnhub接口可用

## 环境设置和启动

### 虚拟环境管理
项目使用 `uv` 管理 Python 环境，虚拟环境位于 `.venv/`：
```bash
# 激活虚拟环境
source .venv/bin/activate

# 安装依赖（推荐使用 uv）
uv pip install -r requirements.txt

# 传统方式
pip install -r requirements.txt
```

### 环境变量配置
复制 `.env.example` 为 `.env` 并配置API密钥：
```bash
# 🆕 推荐配置（统一数据源）
DATA_SOURCE_STRATEGY=free  # free|alpha_vantage|auto
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here  # 可选，500次/天免费
ENABLE_AUTO_FALLBACK=true  # API限制时自动降级

# 传统配置（保持兼容）  
FINNHUB_API_KEY=your_finnhub_api_key_here

# 可选配置  
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret

# 企业网络代理配置
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=http://proxy.company.com:8080
```

详细配置说明见 `docs/environment-setup.md`

### 启动MCP服务器
```bash
# 使用启动脚本（推荐）
./start_server.sh

# 直接启动
python -m tradingagents.mcp.trading_server

# 健康检查
python -c "import asyncio; from tradingagents.mcp.trading_server import TradingAgentsServer; asyncio.run(TradingAgentsServer().health_check())"
```

### MCP 服务器配置
MCP 服务器已修复为标准的 FastMCP Streamable HTTP 服务器。正确的配置：
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

服务器状态：✅ **已正常工作**
- 使用 FastMCP 实现标准 Streamable HTTP MCP 服务器
- 支持 Streamable HTTP 传输协议（推荐的生产模式）
- 在端口 6550 提供服务，路径 `/mcp`
- 与 Claude Code 完全兼容，支持会话管理和断线重连

## 架构概览

### 核心组件
- **MCP 服务器** (`tradingagents/mcp/trading_server.py`) - 统一的 MCP 接口，聚合所有服务
- **数据服务层** (`tradingagents/mcp/services/`) - 各类数据源的抽象层
- **代理配置** (`services/proxy_config.py`) - 企业网络环境支持

### 主要服务模块
- `market_data.py` - Yahoo Finance 市场数据和技术指标
- `finnhub_data.py` - Finnhub 金融数据和新闻
- `news_feed.py` - Google News 新闻聚合  
- `reddit_data.py` - Reddit 社交媒体数据
- `technical_indicators.py` - 技术指标计算
- `social_sentiment.py` - 社交媒体情绪分析

### 数据流架构
1. **外部API** → **服务模块** → **缓存层** → **MCP工具接口**
2. 支持异步处理和并行数据获取
3. 统一的错误处理和重试机制
4. 智能缓存减少API调用次数

## 开发常用命令

### 测试和调试
```bash
# 运行健康检查
./start_server.sh  # 选择选项3

# 运行快速演示
./start_server.sh  # 选择选项2

# 启用调试日志
export LOG_LEVEL=DEBUG
python -m tradingagents.mcp.trading_server
```

### 依赖管理
```bash
# 检查依赖是否齐全
python -c "import sys; required=['pandas','numpy','yfinance','requests','feedparser','stockstats','textblob','finnhub','praw']; missing=[m for m in required if __import__(m) or True]; print('✅ 依赖检查通过' if not missing else f'❌ 缺少: {missing}')"

# 更新依赖
uv pip install -r requirements.txt --upgrade
```

### 代理网络测试
```bash
# 在Python中测试代理配置
python -c "
from tradingagents.mcp.services.proxy_config import get_proxy_config
config = get_proxy_config()
print('代理配置:', config.get_proxies())
print('连接测试:', config.test_proxy_connection())
"
```

## 项目结构

```
tradingagents/
├── .env                       # 环境变量配置文件
├── .env.example              # 环境变量配置示例
├── requirements.txt          # Python依赖
├── start_server.sh          # 服务器启动脚本
├── quick_start.py           # 快速演示脚本
├── docs/                    # 项目文档
│   ├── environment-setup.md # 环境配置指南
│   ├── architecture.md      # 架构设计文档
│   └── cc/                  # Claude Code相关文档
└── tradingagents/mcp/       # MCP服务器实现
    ├── trading_server.py    # 主服务器文件
    └── services/            # 各类数据服务
        ├── market_data.py   # 市场数据服务
        ├── finnhub_data.py  # Finnhub数据服务
        ├── news_feed.py     # 新闻数据服务
        ├── reddit_data.py   # Reddit数据服务
        └── proxy_config.py  # 代理配置服务
```

## 主要MCP工具

### 🆕 统一数据源工具 (推荐)
- `company_news_unified` - 统一公司新闻接口（支持多数据源）
- `company_profile_unified` - 统一公司信息接口（支持多数据源）
- `data_source_status` - 数据源状态监控  
- `data_source_config_reload` - 配置热重载

### 数据分析工具
- `analyze_stock_comprehensive` - 股票综合分析（推荐入口）
- `market_get_quote` - 实时股价
- `technical_calculate_indicators` - 技术指标计算
- `reddit_get_sentiment_summary` - Reddit情绪分析

### 传统工具（保持兼容）
- `finnhub_company_news` - Finnhub公司新闻
- `finnhub_company_profile` - Finnhub公司信息

### 系统工具  
- `health_check` - 系统健康检查
- `proxy_get_config` - 获取代理配置
- `proxy_test_connection` - 测试代理连接

### 使用模式
```python
# 🆕 推荐：统一数据源
company_news_unified("AAPL", "2024-01-01", "2024-01-31", source="auto")
company_profile_unified("AAPL", source="auto", detailed=True)
data_source_status()  # 监控数据源状态

# 传统方式
analyze_stock_comprehensive("AAPL")
market_get_quote("AAPL")
reddit_get_sentiment_summary("AAPL")
```

## 修复完成的问题

### ✅ MCP服务器实现问题（已解决）
- **问题**：原实现使用临时的 MCPServer 类，不是真正的 HTTP MCP 服务器
- **解决方案**：
  1. 使用标准 `mcp>=1.13.0` 库的 FastMCP 实现
  2. 修复工具注册，使用正确的 `@app.tool()` 装饰器语法
  3. 配置 Streamable HTTP 传输协议（代替 SSE）
  4. 服务器在端口 6550 正确监听，路径 `/mcp`

### ✅ 环境变量加载问题（已解决）
- **问题**：服务器启动时无法正确加载 `.env` 文件中的环境变量
- **解决方案**：在服务器代码中添加 `load_dotenv()` 调用，确保环境变量正确加载

### ✅ 工具注册和连接问题（已解决）
- **问题**：Claude Code 无法连接到 MCP 服务器或调用工具
- **解决方案**：
  1. 修复 FastMCP 工具装饰器语法
  2. 从 SSE 传输切换到 Streamable HTTP 传输
  3. 更新 `.mcp.json` 配置为 `type: "http"` 和 `/mcp` 端点
  4. 配置 Claude Code 的 settings 以识别自定义服务器

## 开发最佳实践

### 错误处理
- 所有MCP工具都有统一的错误处理格式
- 网络错误会自动重试，API限制会返回友好错误信息  
- 使用 `health_check` 工具诊断系统状态

### 缓存策略
- 市场数据缓存5分钟 (`DATA_CACHE_TTL`)
- 新闻数据缓存15分钟 (`NEWS_CACHE_TTL`)
- Reddit数据缓存5分钟
- 通过环境变量调整缓存时间

### 代理网络支持
项目原生支持企业代理网络：
- 自动检测环境变量中的代理配置
- 统一配置所有HTTP请求的代理
- 提供代理连接测试工具

