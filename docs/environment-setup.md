# TradingAgents for Claude Code 环境配置指南

> 灵感来源于原 [TradingAgents](https://github.com/TauricResearch/TradingAgents) 项目，感谢原团队的贡献。

## ⚠️ 使用前必读

> **🔬 纯技术研究项目 - 禁止用于实际投资**
>
> - **仅限学习用途**：本项目专门用于学习和研究 Claude Code 的技术能力
> - **技术演示目的**：所有金融数据分析功能仅为展示 MCP、subagents 等技术特性
> - **投资风险警告**：任何使用本项目进行实际投资决策的行为，风险自负
> - **免责条款**：项目开发者不对任何投资损失承担责任
>
> **请确保您理解并同意以上条款后再进行配置和使用！**

## 概述

本文档描述了本项目在 Claude Code 环境中所需的环境变量配置和依赖项安装。

## 环境变量配置

### 🆕 推荐配置 (统一数据源系统)

#### 1. 统一数据源配置
```bash
# 数据源策略选择
export DATA_SOURCE_STRATEGY="free"  # free|alpha_vantage|auto

# Alpha Vantage API (推荐 - 500次/天免费)
export ALPHA_VANTAGE_API_KEY="your_alpha_vantage_key_here"

# 自动降级策略
export ENABLE_AUTO_FALLBACK="true"
```

**配置说明：**
- `free`: 使用完全免费方案 (Google News + yfinance)
- `alpha_vantage`: 使用 Alpha Vantage 增强方案 (需要API密钥)
- `auto`: 智能选择最优数据源

**获取 Alpha Vantage API 密钥：**
1. 访问 [Alpha Vantage](https://www.alphavantage.co/)
2. 注册免费账户
3. 获取 API 密钥 (500次/天免费)

### 传统配置 (保持兼容)

#### Finnhub API 密钥 (可选)
```bash
export FINNHUB_API_KEY="your_finnhub_api_key_here"
```

**注意：** Finnhub 已被免费方案替换，但保持向后兼容

#### 2. OpenAI API 密钥（可选）
```bash
export OPENAI_API_KEY="your_openai_api_key_here"
```

**用途：**
- Claude Code subagents 使用
- 可选的增强分析功能

### 可选的环境变量

#### Reddit API 配置（用于社交媒体数据）
```bash
export REDDIT_CLIENT_ID="your_reddit_client_id"
export REDDIT_CLIENT_SECRET="your_reddit_client_secret"
export REDDIT_USER_AGENT="TradingAgents/1.0"
```

**获取方式：**
1. 访问 [Reddit Apps](https://www.reddit.com/prefs/apps)
2. 创建新的应用程序
3. 获取客户端 ID 和密钥

#### 代理配置（企业网络环境）
```bash
export HTTP_PROXY="http://proxy.company.com:8080"
export HTTPS_PROXY="http://proxy.company.com:8080"
export NO_PROXY="localhost,127.0.0.1,.local"

# 如果代理需要认证
export PROXY_USERNAME="your_username"
export PROXY_PASSWORD="your_password"
```

**代理配置说明：**
- `HTTP_PROXY` / `HTTPS_PROXY`: 代理服务器地址
- `NO_PROXY`: 不使用代理的地址列表（逗号分隔）
- `PROXY_USERNAME` / `PROXY_PASSWORD`: 代理认证凭据

## .env 文件配置示例

创建 `.env` 文件在项目根目录：

```bash
# ========== 🆕 统一数据源配置 (推荐) ==========
# 数据源策略选择 (free|alpha_vantage|auto)
DATA_SOURCE_STRATEGY=free

# Alpha Vantage API - 高质量金融数据（500次/天免费）
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here

# 自动降级策略 - 当API限制时自动切换到免费方案
ENABLE_AUTO_FALLBACK=true

# 数据源优先级设置
NEWS_SOURCE_PRIORITY=google_news
PROFILE_SOURCE_PRIORITY=yfinance

# 当配置Alpha Vantage时的优先级
# NEWS_SOURCE_PRIORITY=alpha_vantage,google_news
# PROFILE_SOURCE_PRIORITY=alpha_vantage,yfinance

# ========== 传统配置 (保持兼容) ==========
FINNHUB_API_KEY=your_finnhub_api_key_here

# ========== 可选配置 ==========
OPENAI_API_KEY=your_openai_api_key_here

# Reddit 配置
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=TradingAgents/1.0

# 代理配置（企业网络环境）
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=http://proxy.company.com:8080
NO_PROXY=localhost,127.0.0.1,.local
PROXY_USERNAME=your_proxy_username
PROXY_PASSWORD=your_proxy_password

# ========== 高级配置 ==========
# MCP 服务器配置
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=6550

# 数据缓存配置
DATA_CACHE_TTL=1800  # 30分钟
NEWS_CACHE_TTL=900   # 15分钟

# 日志级别
LOG_LEVEL=INFO
```

## Python 依赖项

### 使用 uv 管理环境

推荐使用 [uv](https://github.com/astral-sh/uv) 来管理 Python 虚拟环境和依赖项，它比传统的 pip/venv 更快更可靠。

#### 安装 uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 或使用 pip
pip install uv
```

#### 创建虚拟环境并安装依赖

```bash
# 创建虚拟环境
uv venv

# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

# 方法1: 使用 pyproject.toml 安装（推荐）
uv pip install -e .

# 方法2: 使用 requirements.txt
uv pip install -r requirements.txt

# 方法3: 手动安装核心依赖
uv pip install pandas numpy yfinance finnhub-python stockstats feedparser beautifulsoup4 requests python-dotenv praw textblob
```

**注意**: `sqlite3`, `asyncio`, `json`, `os` 等是 Python 标准库模块，无需单独安装。

### 传统方式（不推荐）

```bash
# 使用传统 pip（不推荐）
pip install -r requirements.txt
```

### 核心依赖说明

| 依赖包 | 版本要求 | 用途 |
|--------|----------|------|
| `yfinance` | >=0.2.0 | Yahoo Finance 市场数据 |
| `finnhub-python` | >=2.4.0 | Finnhub 金融数据 API |
| `stockstats` | >=0.6.0 | 技术指标计算 |
| `feedparser` | >=6.0.0 | RSS 新闻解析 |
| `beautifulsoup4` | >=4.12.0 | HTML 内容解析 |
| `pandas` | >=1.5.0 | 数据处理 |
| `numpy` | >=1.24.0 | 数值计算 |
| `requests` | >=2.31.0 | HTTP 请求 |

### 可选依赖

```bash
# 用于更多功能的可选依赖（推荐使用 uv）
uv pip install chromadb>=0.4.0  # 向量数据库
uv pip install praw>=7.7.0      # Reddit API
uv pip install transformers>=4.30.0  # AI 模型
uv pip install scikit-learn>=1.3.0   # 机器学习
```

## 数据源说明

### 🆕 统一数据源系统

#### 1. 完全免费方案
- **Google News**: 新闻搜索和聚合，无限制访问
- **yfinance**: 股票价格、历史数据、公司基本信息
- **优势**: 100%免费，无需API密钥，无限制使用
- **配置**: 默认启用，无需特殊配置

#### 2. Alpha Vantage 增强方案 
- **用途**: 高质量金融数据和新闻
- **限制**: 500次/天免费（NASDAQ官方合作伙伴）
- **配置**: 需要 `ALPHA_VANTAGE_API_KEY`
- **优势**: 数据质量更高，官方支持

#### 3. 智能降级策略
- **自动切换**: API限制时自动使用免费方案
- **配置**: `ENABLE_AUTO_FALLBACK=true`
- **监控**: 通过 `data_source_status` 工具监控状态

### 传统数据源 (保持兼容)

#### Yahoo Finance (免费)
- **用途**: 股票价格、历史数据、基本市场信息
- **限制**: 无需 API 密钥，但有速率限制
- **配置**: 无需特殊配置

#### Finnhub (已替换)
- **状态**: 已被免费方案替换，但保持向后兼容
- **用途**: 公司新闻、内部交易数据、公司基本信息
- **配置**: 可选的 `FINNHUB_API_KEY`

#### Reddit API (免费，需注册)
- **用途**: 社交媒体情绪分析
- **限制**: 免费层有速率限制
- **配置**: 需要 Reddit 应用程序凭据

## MCP 服务器配置

### Claude Code 配置文件

在 Claude Code 中配置 MCP 服务器（.mcp.json）：

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

**配置说明：**
- `type: "http"`: 使用 Streamable HTTP 协议，支持会话管理和断线重连
- `url`: 服务器 Streamable HTTP 端点地址（`/mcp` 路径）
- 服务器端口可通过环境变量 `MCP_SERVER_PORT` 自定义（默认 6550）
- **注意**: 服务器名称必须在 Claude Code 的 settings 中正确配置才能被识别

### 启动服务器

```bash
# 开发模式启动
python -m tradingagents.mcp.trading_server

# 或使用启动脚本
chmod +x start_server.sh
./start_server.sh
```

## 故障排除

### 常见问题

#### 1. API 密钥错误
```
Error: FINNHUB_API_KEY not found in environment variables
```
**解决方案**: 确保在 `.env` 文件中设置了正确的 API 密钥，并重新启动服务。

#### 2. 依赖包导入错误
```
ModuleNotFoundError: No module named 'finnhub'
```
**解决方案**: 
- 使用 uv: `uv pip install finnhub-python`
- 或传统方式: `pip install finnhub-python`

#### 3. 网络连接问题
```
Error: Failed to get Google News: HTTPSConnectionPool...
```
**解决方案**: 检查网络连接和防火墙设置。

#### 4. 数据服务健康检查失败
**解决方案**: 
1. 检查 API 密钥是否有效
2. 验证网络连接
3. 查看服务器日志获取详细错误信息

#### 5. 代理连接问题
```
Error: ProxyError: HTTPSConnectionPool(host='api.finnhub.io', port=443)
```
**解决方案**:
1. 验证代理设置: `proxy_get_config` 工具
2. 测试代理连接: `proxy_test_connection` 工具
3. 检查代理认证凭据
4. 确认目标网站不在 NO_PROXY 列表中

#### 6. 企业防火墙问题
**解决方案**:
1. 配置正确的代理服务器地址
2. 添加必要的域名到防火墙白名单:
   - `api.finnhub.io`
   - `query1.finance.yahoo.com`
   - `news.google.com`
   - `oauth.reddit.com`
3. 使用公司提供的代理配置

### 日志调试

启用详细日志：
```bash
export LOG_LEVEL=DEBUG
python -m tradingagents.mcp.trading_server
```

## 生产环境注意事项

### 1. API 速率限制
- Finnhub 免费层: 60 requests/分钟
- Yahoo Finance: 建议间隔 1-2 秒
- Google News: 通常无严格限制

### 2. 缓存策略
- 市场数据: 5-10 分钟缓存
- 新闻数据: 15-30 分钟缓存
- 技术指标: 5-10 分钟缓存

### 3. 错误处理
- 实现自动重试机制
- 设置合理的超时时间
- 监控 API 配额使用情况

### 4. 安全考虑
- 不要在代码中硬编码 API 密钥
- 使用环境变量或安全的密钥管理系统
- 定期轮换 API 密钥