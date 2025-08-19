# TradingAgents for Claude Code

## ⚠️ 重要免责声明

> **本项目纯粹用于研究和学习 Claude Code 的技术实现，严禁用于任何实际的股票交易或金融投资！**
>
> - 🔬 **仅用于技术研究**：本项目是为了探索和学习 Claude Code 的 MCP、subagents、slash commands 等技术能力
> - 🚫 **禁止投资用途**：所有数据分析、技术指标、情绪分析等功能仅供技术演示，不构成任何投资建议
> - ⚖️ **使用者责任**：任何因使用本项目进行投资决策造成的损失，开发者概不负责
> - 📚 **教育目的**：项目提供的所有金融数据和分析结果仅用于教学和技术展示
>
> **请在充分理解上述声明的前提下使用本项目！**

---

灵感来源于原 [TradingAgents](https://github.com/TauricResearch/TradingAgents) 多智能体交易系统，感谢原项目的创新设计。本项目专为 Claude Code 环境设计，通过 **slash commands** 和 **subagents** 团队协作，提供结构化的金融分析体验。

> **实现状态**: ✅ **核心功能完整**。包含 13 个专业 subagents、6 个 slash commands、SQLite 记忆系统，以及基于 FastMCP 的 HTTP 服务器，与 Claude Code 完全集成。

## 🚀 核心特性

### 🤖 专业 Subagents 团队 (13个)
- ✅ **分析师团队**: market-analyst, fundamentals-analyst, news-analyst, social-analyst
- ✅ **研究团队**: bull-researcher, bear-researcher, research-manager
- ✅ **决策团队**: trader, risk-manager, portfolio-manager
- ✅ **风险评估**: safe-analyst, risky-analyst, neutral-analyst

### 🎮 Slash Commands (6个)
- ✅ `/trade-analyze [ticker]` - 完整交易分析流程
- ✅ `/market-scan [sector]` - 市场扫描和机会识别
- ✅ `/portfolio-review` - 投资组合评审
- ✅ `/risk-assessment [ticker]` - 风险评估分析
- ✅ `/backtest [strategy]` - 策略回测
- ✅ `/memory-train [data]` - 记忆系统训练

### 🧠 智能协作系统
- ✅ **多角度分析**: 看涨看跌研究员自动辩论
- ✅ **风险管理**: 三层风险评估团队协作
- ✅ **决策流程**: 从分析→研究→风险评估→最终决策
- ✅ **记忆学习**: SQLite 数据库存储历史决策

### 📊 统一数据源系统 (🆕 免费替代方案)
- ✅ **完全免费方案**: Google News + yfinance (无限制)
- ✅ **增强免费方案**: Alpha Vantage API (500次/天)
- ✅ **智能降级**: API限制时自动切换免费方案
- ✅ **灵活配置**: 环境变量一键切换数据源
- ✅ Reddit (社交媒体情绪、热门股票)
- ⚠️ Finnhub (已替换，但保持兼容)

## 🎯 如何使用

### 🚀 核心工作流

#### 📈 完整股票分析
```
> /trade-analyze AAPL
```
自动调用完整的分析师团队：
1. **market-analyst** 进行技术分析
2. **fundamentals-analyst** 分析财务数据
3. **news-analyst** 分析新闻影响
4. **social-analyst** 分析社媒情绪
5. **bull/bear-researcher** 进行多角度辩论
6. **risk-manager** 评估风险等级
7. **trader** 给出交易建议
8. **portfolio-manager** 做出最终决策

#### 🔍 市场扫描
```
> /market-scan technology
> /market-scan healthcare
```

#### 📋 投资组合管理
```
> /portfolio-review
> /risk-assessment TSLA
```

### 💬 自然语言交互

你也可以通过自然语言与专业团队协作：

```
> 请分析 NVDA 的技术指标，重点关注 RSI 和 MACD

> 组织投资团队对苹果公司进行全面的投资研究和辩论

> 评估特斯拉股票的当前风险水平

> 搜索半导体行业的最新新闻和市场动向
```

## 📦 快速开始

### 1. 安装依赖

推荐使用 `uv` 管理环境：
```bash
# 激活虚拟环境
source .venv/bin/activate

# 使用 uv 安装依赖（推荐）
uv pip install -r requirements.txt

# 或使用传统方式
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：
```bash
# 🆕 统一数据源配置 (推荐)
DATA_SOURCE_STRATEGY=free  # free|alpha_vantage|auto
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here  # 可选，500次/天免费
ENABLE_AUTO_FALLBACK=true  # API限制时自动降级

# 传统配置 (保持兼容)
FINNHUB_API_KEY=your_finnhub_api_key_here

# 可选配置
OPENAI_API_KEY=your_openai_api_key_here
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret

# 代理配置（企业网络环境）
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=http://proxy.company.com:8080
PROXY_USERNAME=your_proxy_username
PROXY_PASSWORD=your_proxy_password
```

详细配置说明请参考：[环境配置指南](docs/environment-setup.md)

### 3. 启动服务器

使用提供的启动脚本：
```bash
chmod +x start_server.sh
./start_server.sh
```

或直接启动：
```bash
python -m tradingagents.mcp.trading_server
```

启动脚本提供多个选项：
- **MCP 服务器** - 用于 Claude Code 集成
- **快速演示** - 展示主要功能
- **健康检查** - 验证系统状态

### 4. 在 Claude Code 中使用

启动 Claude Code：
```bash
# 在项目目录中
claude
```

系统会自动加载 `.mcp.json` 配置，你可以立即使用：

```
> /help                    # 查看所有可用命令
> /trade-analyze AAPL      # 分析苹果股票
> 请检查系统健康状态        # 验证服务运行正常
```

## 🏗️ 系统架构

### 🎭 Subagents 协作流程

```
用户请求 → Slash Commands → 自动调用相关 Subagents
                           ↓
┌─────────────────────────────────────────────────┐
│              分析师团队 (Analysts)               │
│  📊 market-analyst    📈 fundamentals-analyst  │
│  📰 news-analyst     📱 social-analyst         │
└─────────────────┬───────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────┐
│              研究团队 (Researchers)              │
│  🐂 bull-researcher  🐻 bear-researcher        │
│           📝 research-manager                   │
└─────────────────┬───────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────┐
│              决策团队 (Decision Team)            │
│  💼 trader  ⚖️ risk-manager  🏛️ portfolio-mgr   │
│  🛡️ safe-analyst  🎲 risky-analyst  ⚖️ neutral │
└─────────────────┬───────────────────────────────┘
                  ↓
              最终投资建议
```

### 🔄 数据流架构
- **外部API** → **服务模块** → **缓存层** → **MCP工具接口** → **Subagents**
- 支持异步处理和并行数据获取
- 统一的错误处理和重试机制

## 📝 实际应用案例

### 🎯 典型工作流程

#### 📈 新股票调研
```
1. > /trade-analyze NVDA
   → 自动调用完整分析师团队进行综合分析

2. > /risk-assessment NVDA  
   → 风险管理团队进行多角度风险评估

3. > 请研究团队对 NVDA 进行看涨看跌辩论
   → bull/bear-researcher 进行深度辩论

4. > 请投资组合经理基于所有分析做出最终决策
   → portfolio-manager 综合所有意见给出建议
```

#### 🔍 每日市场扫描
```
1. > /market-scan technology
   → 扫描科技板块投资机会

2. > 搜索今日重要科技股新闻
   → news-analyst 分析市场动向

3. > 获取热门讨论的科技股票
   → social-analyst 监控社媒情绪

4. > /portfolio-review
   → portfolio-manager 评估组合表现
```

#### 💼 风险管理
```
1. > /risk-assessment TSLA
   → 完整的三层风险评估体系

2. > 请风险管理团队分析当前市场的主要风险点
   → 多个风险分析师协作评估

3. > 基于风险分析调整投资组合建议
   → portfolio-manager 提供调整方案
```

## 📚 文档资源

- **使用指南**: [详细使用方法和最佳实践](docs/usage-guide.md) 📖
- **环境配置**: [完整的环境设置指南](docs/environment-setup.md) ⚙️
- **系统架构**: [技术架构和设计文档](docs/architecture.md) 🏗️
- **Claude Code 文档**: [docs/cc/](docs/cc/) - Claude Code 平台相关资料

## 🔧 故障排除

### 常见问题
```
> 请检查系统健康状态，确保所有服务正常运行
> 检查代理配置是否正确设置（企业网络环境）
> 测试网络连接和 API 配置
```

### 性能优化
- 智能缓存减少 API 调用次数
- 异步处理提高响应速度  
- 企业代理环境完全支持  

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出改进建议！

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 发起 Pull Request

## 🙏 致谢

本项目的灵感来源于原 [TradingAgents](https://github.com/TauricResearch/TradingAgents) 项目，感谢原团队的开创性工作和设计理念。本项目专为 Claude Code 环境重新设计和实现，展示了现代 AI 开发平台的强大能力。

## 📄 许可证

本项目采用 MIT 许可证。详情请参见 [LICENSE](LICENSE) 文件。

```
MIT License

Copyright (c) 2025 gonewx

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```