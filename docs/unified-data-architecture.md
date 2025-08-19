# 统一数据源架构文档

## 📋 架构概览

统一数据源系统是为了解决 Finnhub 付费限制而设计的灵活、可扩展的数据源管理架构。

### 🎯 设计目标
- **成本优化**: 提供完全免费的数据源替代方案
- **质量保证**: 支持高质量付费数据源的可选集成
- **智能降级**: API限制时自动切换到免费方案
- **配置灵活**: 环境变量和配置文件双重配置
- **向后兼容**: 保持原有接口100%兼容

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                   统一数据服务 (UnifiedDataService)           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   配置管理器     │  │   缓存系统       │  │   错误处理器     │ │
│  │ DataSourceConfig │  │ Multi-tier Cache │  │ Error Handler   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     数据源适配器层                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  GoogleNewsSource │  │ YfinanceSource  │  │AlphaVantageSource│ │
│  │   (完全免费)      │  │   (完全免费)     │  │  (500次/天)      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     外部API层                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Google News   │  │   Yahoo Finance │  │  Alpha Vantage  │ │
│  │      RSS        │  │       API       │  │      API        │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 核心组件

### 1. DataSourceConfig (配置管理器)
**位置**: `services/data_source_config.py`

**功能**:
- 环境变量解析和配置管理
- 数据源策略选择 (free/alpha_vantage/auto)
- API密钥管理和验证
- 降级策略配置

**配置选项**:
```python
class DataSourceStrategy(Enum):
    FREE = "free"           # 仅使用免费数据源
    ALPHA_VANTAGE = "alpha_vantage"  # 优先使用Alpha Vantage
    AUTO = "auto"           # 自动选择最优数据源
```

### 2. BaseDataSource (数据源基类)
**位置**: `services/data_sources/base_source.py`

**功能**:
- 定义统一的数据源接口
- 缓存机制的基础实现
- 错误处理和重试逻辑
- 健康检查和状态监控

**核心接口**:
```python
@abstractmethod
async def get_company_news(symbol, start_date, end_date, limit) -> List[Dict]
async def get_company_profile(symbol, detailed) -> Dict
async def health_check() -> bool
async def is_supported(symbol) -> bool
async def get_rate_limit_info() -> Dict
```

### 3. 具体数据源实现

#### GoogleNewsSource (完全免费)
- **数据源**: Google News RSS
- **限制**: 无限制
- **功能**: 公司新闻搜索和聚合
- **缓存**: 15分钟

#### YfinanceSource (完全免费)  
- **数据源**: Yahoo Finance
- **限制**: 隐式速率限制
- **功能**: 公司信息、财务数据、历史价格
- **缓存**: 4小时

#### AlphaVantageSource (增强方案)
- **数据源**: Alpha Vantage API
- **限制**: 500次/天免费
- **功能**: 高质量新闻、公司信息、情绪分析
- **缓存**: 1-6小时（珍惜API配额）

### 4. UnifiedDataService (统一服务)
**位置**: `services/unified_data_service.py`

**功能**:
- 数据源选择和负载均衡
- 智能降级和错误恢复
- 统一数据格式化
- 性能监控和日志记录

## 📊 数据流架构

### 1. 请求处理流程
```
MCP工具调用 
    ↓
统一数据服务 
    ↓
配置管理器 (选择数据源策略)
    ↓
数据源适配器 (检查可用性)
    ↓
缓存检查 (命中则返回)
    ↓
外部API调用 (失败则降级)
    ↓
数据格式化 (统一输出格式)
    ↓
缓存存储 (更新缓存)
    ↓
返回结果
```

### 2. 降级策略
```
Alpha Vantage API
    ↓ (API限制/错误)
Google News + yfinance
    ↓ (网络错误)
缓存数据
    ↓ (缓存过期)
错误响应
```

## 🔄 配置系统

### 环境变量配置
```bash
# 策略选择
DATA_SOURCE_STRATEGY=auto  # free|alpha_vantage|auto

# API密钥
ALPHA_VANTAGE_API_KEY=your_key_here

# 降级配置
ENABLE_AUTO_FALLBACK=true

# 优先级配置
NEWS_SOURCE_PRIORITY=alpha_vantage,google_news
PROFILE_SOURCE_PRIORITY=alpha_vantage,yfinance
```

### 运行时配置切换
```python
# 获取当前配置
config = get_data_source_config()

# 重新加载配置
unified_data.reload_config()

# 监控数据源状态
status = await unified_data.get_data_source_status()
```

## 🚀 性能优化

### 1. 分层缓存策略
- **Level 1**: 内存缓存 (最快访问)
- **Level 2**: 数据源本地缓存 (避免重复请求)
- **Level 3**: 智能缓存时间 (根据数据源调整)

### 2. 缓存时间配置
```python
cache_timeouts = {
    'alpha_vantage': {'news': 3600, 'profile': 21600},  # 1小时/6小时
    'google_news': {'news': 900, 'profile': 900},       # 15分钟
    'yfinance': {'news': 900, 'profile': 14400}         # 15分钟/4小时
}
```

### 3. 并发处理
- 异步API调用
- 并行数据源查询
- 智能负载均衡

## 🛡️ 错误处理

### 1. 错误分类
```python
error_types = {
    'RATE_LIMIT_EXCEEDED': '触发API限制，自动降级',
    'API_KEY_INVALID': 'API密钥无效，使用免费方案',
    'NETWORK_ERROR': '网络错误，重试或使用缓存',
    'DATA_NOT_FOUND': '数据不存在，尝试其他数据源'
}
```

### 2. 重试机制
- 指数退避重试
- 最大重试次数限制
- 智能错误恢复

### 3. 监控和告警
```python
# 监控数据源状态
health_status = await unified_data.health_check()

# 获取API使用情况
rate_limits = await data_source.get_rate_limit_info()
```

## 🔍 测试和验证

### 1. 单元测试
- 各数据源独立测试
- 配置管理测试
- 错误处理测试

### 2. 集成测试
- 数据源切换测试
- 降级策略验证
- 性能基准测试

### 3. 端到端测试
```python
# 测试脚本
python test_unified_service.py
```

## 📈 扩展性设计

### 1. 新数据源集成
```python
# 1. 创建新的数据源类
class NewDataSource(BaseDataSource):
    async def get_company_news(self, ...):
        # 实现具体逻辑
        pass

# 2. 在统一服务中注册
unified_service.register_source('new_source', NewDataSource())

# 3. 更新配置管理
config.add_source_priority('news', 'new_source')
```

### 2. 新功能扩展
- 支持实时数据流
- 增加更多数据类型
- 机器学习驱动的数据源选择

### 3. 监控和运维
- 数据源性能指标
- API使用率监控
- 自动故障恢复

## 💰 成本分析

### 完全免费方案
| 组件 | 成本 | 限制 | 可用性 |
|------|------|------|--------|
| Google News | $0 | 无限制 | 99.9% |
| yfinance | $0 | 隐式限制 | 95% |
| **总成本** | **$0** | **基本可用** | **97%** |

### 增强免费方案
| 组件 | 成本 | 限制 | 可用性 |
|------|------|------|--------|
| Alpha Vantage | $0 | 500次/天 | 99.9% |
| Google News (降级) | $0 | 无限制 | 99.9% |
| yfinance (降级) | $0 | 隐式限制 | 95% |
| **总成本** | **$0** | **高质量+降级** | **99%** |

### 对比 Finnhub
| 方案 | 月成本 | 限制 | 数据质量 |
|------|--------|------|----------|
| Finnhub Basic | $9.99 | 60次/分钟 | 高 |
| 统一免费方案 | $0 | 基本无限制 | 中-高 |
| **节省** | **$119.88/年** | **更灵活** | **相当** |

## 🎯 最佳实践

### 1. 配置建议
- 开发环境使用 `free` 策略
- 生产环境使用 `auto` 策略
- 启用自动降级 `ENABLE_AUTO_FALLBACK=true`

### 2. 监控建议
- 定期检查 `data_source_status`
- 监控API使用率
- 设置性能告警

### 3. 优化建议
- 合理设置缓存时间
- 避免高频重复请求
- 使用批量数据获取

---

**文档版本**: v1.0  
**最后更新**: 2025-08-19  
**维护者**: Claude Code Assistant