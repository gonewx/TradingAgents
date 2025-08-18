# TradingAgents for Claude Code 使用指南

> 灵感来源于原 [TradingAgents](https://github.com/TauricResearch/TradingAgents) 项目，感谢原团队的设计理念。

## ⚠️ 研究使用声明

> **🔬 Claude Code 技术研究专用**
>
> - **学术研究**：本项目专门用于研究 Claude Code 平台的 MCP、subagents、slash commands 等技术特性
> - **技术演示**：所有金融分析功能仅为展示技术实现，不提供投资建议
> - **教育用途**：适合用于学习现代 AI 开发平台的实际应用
> - **严禁投资**：任何将本项目用于实际金融投资的行为，后果自负
>
> **请始终牢记：这是一个技术研究项目，不是投资工具！**

## 系统概述

本系统参考原 TradingAgents 的设计，在 Claude Code 环境中通过 slash commands 和 subagents 提供完整的金融数据分析功能。系统集成 Yahoo Finance、Finnhub、Reddit、Google News 等多个数据源，通过专业的分析师团队（subagents）协作，为用户提供结构化的投资研究体验。

## 快速开始

### 1. 环境准备

```bash
# 进入项目目录
cd /path/to/tradingagents

# 激活虚拟环境
source .venv/bin/activate

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入必要的 API 密钥（至少需要 FINNHUB_API_KEY）

# 启动 MCP 服务器
./start_server.sh
```

### 2. 在 Claude Code 中使用

```bash
# 在项目目录中打开 Claude Code
claude

# 查看可用的 slash commands
/help
```

### 3. 验证系统状态

```
> 请检查系统健康状态，确保所有服务正常运行

> 获取 AAPL 的基本报价信息测试连接
```

## 核心功能

### 📊 股票分析

#### 完整股票分析流程

使用主要的交易分析命令进行全面的股票研究：

```
> /trade-analyze AAPL
```

这个命令会自动调用所有相关的 subagents：
1. **market-analyst** - 技术分析和价格趋势
2. **fundamentals-analyst** - 财务报表和基本面分析  
3. **news-analyst** - 新闻和宏观经济分析
4. **social-analyst** - 社交媒体情绪分析
5. **bull-researcher** - 看涨论点研究
6. **bear-researcher** - 看跌论点研究
7. **research-manager** - 投资研究总结
8. **trader** - 最终交易决策
9. **risk-manager** - 风险评估
10. **portfolio-manager** - 投资组合管理决策

#### 分专业领域分析

您也可以通过自然语言请求特定的分析：

```
> 请分析 AAPL 的技术指标，重点关注 RSI 和 MACD

> 获取 AAPL 最近的财务报表数据

> 分析 AAPL 的新闻情绪和社交媒体讨论

> 搜索苹果公司相关的最新新闻
```

### 🔍 市场扫描和数据获取

#### 市场扫描

使用市场扫描命令发现投资机会：

```
> /market-scan technology

> /market-scan healthcare

> /market-scan energy
```

#### 批量股票分析

通过自然语言请求进行批量分析：

```
> 请分析科技股 AAPL、MSFT、GOOGL 的投资价值对比

> 获取当前市场上的热门讨论股票

> 搜索半导体行业 2024 年第四季度财报相关新闻
```

### 💼 投资组合和风险管理

#### 投资组合评审

使用专门的投资组合命令：

```
> /portfolio-review
```

此命令会调用 portfolio-manager subagent 进行全面的投资组合分析。

#### 风险评估分析

```
> /risk-assessment TSLA

> /risk-assessment NVDA
```

此命令会调用风险分析团队（risk-manager, safe-analyst, risky-analyst, neutral-analyst）进行多角度风险评估。

#### 多维度对比分析

通过自然语言进行复杂分析：

```
> 请对比分析 AAPL 和 MSFT 的投资价值，包括技术面、基本面和风险因素

> 分析科技股板块的整体表现和未来前景

> 综合多个数据源分析 NVDA 的投资机会和风险
```

### ⚠️ 技术分析与指标

#### 专业技术分析

系统会自动调用 market-analyst subagent 进行技术分析：

```
> 请对 AAPL 进行技术分析，包括 RSI、MACD、布林带等指标

> 分析 TSLA 过去 6 个月的技术指标变化趋势

> 获取 NVDA 的全部技术指标分析
```

#### 技术信号解读

```
> 基于 AAPL 的技术指标分析当前的买卖时机

> 分析 TSLA 的价格趋势和关键支撑阻力位

> 评估 NVDA 的价格波动性和技术风险水平
```

### 📈 新闻与情绪分析

#### 新闻情绪分析

系统会自动调用 news-analyst 和 social-analyst subagents：

```
> 分析 AAPL 最近一个月的新闻情绪

> 搜索人工智能相关股票的最新消息

> 获取 2025 年 2 月股市前景的新闻分析
```

#### 社交媒体情绪

```
> 分析 TSLA 在 Reddit 上的讨论情绪

> 获取当前 wallstreetbets 上的热门讨论股票

> 分析投资论坛上对 AAPL 的看法
```

### 🧠 系统管理与配置

#### 系统状态检查

```
> 请检查系统健康状态，确保所有服务正常运行

> 检查代理配置是否正确设置

> 测试网络连接和代理设置
```

#### 数据缓存管理

```
> 清理数据缓存并重新获取 AAPL 的最新信息

> 检查当前缓存的数据是否为最新
```

## 高级功能

### 🤖 策略回测和记忆训练

#### 策略回测

使用回测命令验证投资策略：

```
> /backtest momentum-strategy 2024-01-01 2024-12-31

> /backtest value-investing 2023-01-01 2024-12-31
```

#### 记忆系统训练

通过记忆训练命令改进分析质量：

```
> /memory-train AAPL-analysis-results

> /memory-train portfolio-performance-data
```

#### 智能协作分析

系统会自动协调多个 subagents 进行协作分析：

```
> 请组织投资团队对 NVDA 进行全面的投资研究和辩论

> 召集分析师团队对科技股板块进行深度研究
```

### 📊 实际应用案例

#### 投资决策支持

```
# 新股票研究流程
> /trade-analyze META
> 请基于分析结果评估 META 的增长前景和风险因素
> 综合技术面和基本面给出投资建议

# 持仓评估流程
> /portfolio-review
> 分析当前持股是否需要调整仓位
> 识别新的投资机会和风险点
```

#### 市场监控

```
# 每日市场扫描流程
> /market-scan all
> 搜索今日重要市场新闻
> 分析市场热点和潜在风险信号

# 特定事件影响分析
> 搜索相关新闻事件的最新进展
> 分析事件对相关股票和板块的影响
> 评估由此产生的投资机会或风险
```

### 📊 数据分析和报告

#### 结构化数据分析

```
# 获取和分析结构化数据
> 获取 AAPL 的实时报价数据
> 计算 AAPL 的技术指标并生成图表
> 将分析结果格式化为 CSV 格式以便导出

# 历史数据分析
> 获取 AAPL 过去一年的历史价格数据
> 分析价格趋势和技术指标变化
> 生成投资分析报告
```

#### 自动化监控

```
# 定期监控流程
> 请设置每日检查系统状态
> 对我的关注列表股票进行定期分析
> 生成投资组合表现报告

# 预警系统
> 监控特定股票的技术指标异常
> 当 RSI 超买或超卖时发出提醒
> 新闻情绪发生重大变化时通知
```

## 工作流示例

### 🌅 每日分析流程

```
1. 系统健康检查
> 请检查系统健康状态

2. 市场扫描
> /market-scan all

3. 搜索市场新闻
> 搜索今日重要股市新闻

4. 分析重点股票
> /trade-analyze [热门股票]

5. 技术指标确认
> 请分析今日关注股票的技术指标变化
```

### 📈 新股票调研流程

```
1. 完整股票分析
> /trade-analyze [TICKER]

2. 风险评估
> /risk-assessment [TICKER]

3. 深入研究
> 请组织研究团队对 [TICKER] 进行看涨看跌辩论

4. 最终决策
> 请交易团队基于所有分析给出最终投资建议
```

### 🔄 投资组合管理流程

```
1. 系统状态检查
> 请检查系统健康状态

2. 投资组合评审
> /portfolio-review

3. 重要新闻扫描
> 搜索可能影响投资组合的重大新闻

4. 持仓股票更新
> 请分析我的持仓股票的最新状况

5. 风险信号识别
> 分析市场是否出现新的风险信号

6. 调整建议
> 基于分析结果提供投资组合调整建议
```

## 最佳实践

### 🎯 使用 Slash Commands 的最佳实践

1. **从核心命令开始**：使用 `/trade-analyze` 作为主要分析入口
2. **组合使用命令**：结合 `/market-scan` 和 `/risk-assessment` 进行全面分析
3. **利用记忆功能**：使用 `/memory-train` 改进分析质量
4. **定期组合评审**：使用 `/portfolio-review` 定期检查投资组合

### ⚙️ 与 Subagents 协作

1. **信任专业分工**：让不同的 subagents 处理各自专长领域
2. **鼓励团队辩论**：通过自然语言请求让 bull-researcher 和 bear-researcher 进行辩论
3. **重视最终决策**：portfolio-manager 的最终决策融合了所有团队的意见
4. **关注风险管理**：确保 risk-manager 的建议得到充分考虑

### 📊 系统使用技巧

1. **定期健康检查**：通过自然语言请求检查系统状态
2. **自然语言交互**：使用自然、具体的语言描述分析需求
3. **结果解读**：正确理解各个 subagents 提供的专业分析
4. **数据时效性**：了解数据缓存机制，必要时请求最新数据

## 常见问题

### Q: 为什么有些数据获取失败？

A: 可能的原因和解决方案：
```
> 请检查系统健康状态，确保所有服务正常运行

> 检查代理配置是否正确设置（企业网络环境）

> 测试网络连接和 API 配置

> 验证 .env 文件中的 FINNHUB_API_KEY 等配置
```

### Q: 如何获取最新数据？

A: 系统有缓存机制，如需最新数据：
```
> 请清理缓存并获取最新的市场数据

# 或重启 MCP 服务器
./start_server.sh
```

### Q: Slash Commands 没有响应怎么办？

A: 
1. 确认 MCP 服务器正在运行
2. 检查 `.mcp.json` 配置是否正确
3. 使用 `/help` 查看可用命令
4. 尝试通过自然语言请求相同功能

### Q: 如何理解 Subagents 的分析结果？

A: 
```
> 请详细解释各个分析师团队对 AAPL 的分析结论

> 对比说明看涨和看跌研究员的不同观点

> 分析风险管理团队提出的主要风险点

> 解释最终交易决策的依据和理由
```

## 主要 Slash Commands 参考

### 核心交易命令
- `/trade-analyze [ticker]` - 完整交易分析流程（核心命令）
- `/market-scan [sector]` - 市场扫描和机会识别
- `/portfolio-review` - 投资组合评审
- `/risk-assessment [ticker]` - 风险评估分析
- `/backtest [strategy] [start] [end]` - 策略回测
- `/memory-train [data]` - 记忆系统训练

### 专业 Subagents 团队

#### 分析师团队
- **market-analyst** - 技术分析和市场趋势专家
- **fundamentals-analyst** - 财务报表和基本面分析师
- **news-analyst** - 全球新闻和宏观经济分析师
- **social-analyst** - 社交媒体情绪分析师

#### 研究团队
- **bull-researcher** - 看涨研究员，寻找投资机会的积极面
- **bear-researcher** - 看跌研究员，识别投资风险和问题
- **research-manager** - 研究经理，协调和综合不同观点

#### 决策团队
- **trader** - 资深交易员，制定最终交易决策
- **risk-manager** - 风险管理专家，评估交易风险
- **portfolio-manager** - 投资组合经理，批准或拒绝交易提案
- **safe-analyst** - 保守风险分析师，强调风险控制
- **risky-analyst** - 激进风险分析师，关注高风险高回报
- **neutral-analyst** - 中性风险分析师，提供平衡观点

## 技术支持

- 📖 项目文档: 查看项目 `docs/` 目录
- 🔧 配置文件: `.env.example` 和 `CLAUDE.md`
- 🐛 问题报告: 在项目 GitHub 仓库提交 Issue

---

**免责声明**: 本系统仅供研究和教育目的。投资有风险，请谨慎决策。所有数据和分析结果仅供参考，不构成投资建议。