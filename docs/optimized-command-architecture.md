# 交易分析命令优化架构设计

## 问题诊断

### 当前架构问题
1. **基础验证缺失** - 直接假设股票代码对应公司，无验证机制
2. **数据割裂** - 各subagents独立工作，基础事实不一致
3. **质量控制缺失** - 无最终验证环节检查关键信息准确性
4. **错误传播** - 初始错误在整个分析链中被放大
5. **MCP工具利用不充分** - 未充分提取和验证结构化数据

## 优化架构设计

### 新执行流程 (5+1阶段)

```
Phase 0: 基础验证阶段 (NEW)
    ↓
Phase 1: 标准化数据收集
    ↓  
Phase 2: 交叉验证阶段 (NEW)
    ↓
Phase 3: 分析阶段
    ↓
Phase 4: 质量检查阶段 (NEW)
    ↓
Phase 5: 最终输出
```

### Phase 0: 基础验证阶段 (NEW)

**目标**: 建立可靠的"事实基础"
**执行者**: `data-validator` subagent (新增)

**关键任务**:
1. 验证股票代码有效性和格式
2. 获取官方公司信息（名称、行业、基本描述）
3. 建立标准化的"基础事实档案"
4. 设定分析边界和预期结果格式

**MCP工具调用顺序**:
```python
# 1. 基础验证
quote_data = market_get_quote(ticker)
company_info = finnhub_company_profile(ticker) 
comprehensive_data = analyze_stock_comprehensive(ticker)

# 2. 提取关键标识信息
company_name = extract_company_name(quote_data, company_info, news_data)
industry_sector = extract_industry_info(company_info)
business_description = extract_business_summary(company_info, news_data)

# 3. 建立事实基础
fact_base = {
    "ticker": verified_ticker,
    "company_name": verified_company_name,
    "industry": verified_industry,
    "market": market_info,
    "business_type": business_description
}
```

**输出**: 标准化基础事实档案 (JSON格式)

### Phase 1: 标准化数据收集

**目标**: 基于验证事实收集多维数据
**执行者**: `market-analyst`, `fundamentals-analyst`, `news-analyst`, `social-analyst`

**关键改进**:
1. 所有agents必须使用Phase 0的基础事实档案
2. 每个agent在开始时验证公司信息一致性
3. 标准化数据格式和字段命名
4. 增加数据来源和置信度标记

**Agent协议**:
```python
class StandardizedAnalysisProtocol:
    def __init__(self, fact_base):
        self.fact_base = fact_base
        self.verify_consistency()
    
    def verify_consistency(self):
        # 验证获取的数据与fact_base一致
        assert self.data.company_name == self.fact_base.company_name
    
    def format_output(self):
        # 标准化输出格式
        return {
            "agent_type": self.agent_type,
            "fact_base_verified": True,
            "data_source_confidence": self.confidence_score,
            "analysis_results": self.results,
            "timestamp": self.timestamp
        }
```

### Phase 2: 交叉验证阶段 (NEW)

**目标**: 确保数据一致性和准确性
**执行者**: `cross-validator` subagent (新增)

**关键任务**:
1. 比较各agents的基础事实提取
2. 检测和标记数据冲突
3. 解决不一致性问题
4. 生成数据可靠性报告

**验证矩阵**:
```python
validation_matrix = {
    "company_name": [market_analyst.company_name, fundamental_analyst.company_name, news_analyst.company_name],
    "industry_sector": [fundamental_analyst.industry, news_analyst.industry],
    "business_type": [fundamental_analyst.business_type, news_analyst.business_type],
    "market_cap_range": [market_analyst.market_cap, fundamental_analyst.market_cap]
}

# 一致性检查
for key, values in validation_matrix.items():
    consistency_score = calculate_consistency(values)
    if consistency_score < 0.8:
        raise DataInconsistencyError(f"{key} inconsistency detected")
```

### Phase 3: 分析阶段

**目标**: 基于验证数据进行深度分析
**执行者**: `bull-researcher`, `bear-researcher`, `research-manager`

**关键改进**:
1. 使用经过验证的标准化数据
2. 分析过程中保持事实一致性
3. 增加分析可信度评估
4. 改进协作和数据共享机制

### Phase 4: 质量检查阶段 (NEW)

**目标**: 最终验证分析结果准确性
**执行者**: `quality-controller` subagent (新增)

**关键任务**:
1. 验证最终报告中的基础事实准确性
2. 检查分析逻辑一致性
3. 确认数据引用正确性
4. 生成质量评估报告

**检查清单**:
```python
quality_checklist = {
    "basic_facts": {
        "company_name_consistent": True/False,
        "industry_classification_correct": True/False,
        "financial_data_reasonable": True/False
    },
    "analysis_logic": {
        "conclusions_supported_by_data": True/False,
        "risk_assessment_balanced": True/False,
        "recommendations_justified": True/False
    },
    "data_integrity": {
        "source_citations_accurate": True/False,
        "numerical_data_consistent": True/False,
        "timeline_consistency": True/False
    }
}
```

## 新增Subagents规格

### 1. data-validator

**职责**: 基础数据验证和事实档案建立
**工具权限**: 所有MCP trading工具
**输出格式**: 标准化事实档案JSON

**Prompt模板**:
```
你是数据验证专家，负责为股票{ticker}建立可靠的基础事实档案。

必须完成的任务：
1. 使用MCP工具验证股票代码有效性
2. 获取官方公司名称、行业分类、业务描述
3. 交叉验证多个数据源的一致性
4. 建立标准化的基础事实档案

如果发现任何基础信息不一致，必须明确报告并尝试解决。
```

### 2. cross-validator

**职责**: 跨agent数据一致性验证
**输入**: 所有data collection agents的输出
**输出**: 一致性验证报告

### 3. quality-controller

**职责**: 最终质量检查和事实核实
**输入**: 所有分析结果
**输出**: 质量评估报告和修正建议

## MCP工具使用优化

### 1. 工具调用策略改进
```python
# 当前问题：单次调用，数据未充分利用
old_approach = single_tool_call(ticker)

# 优化方案：多工具组合验证
new_approach = {
    "basic_data": market_get_quote(ticker),
    "company_profile": finnhub_company_profile(ticker),
    "comprehensive": analyze_stock_comprehensive(ticker),
    "news_sample": news_get_latest(ticker, limit=5)
}
# 从多个来源提取和验证公司基础信息
```

### 2. 数据解析增强
```python
def extract_company_identity(multi_source_data):
    """从多个MCP工具返回数据中提取和验证公司身份"""
    
    # 从不同来源提取公司名
    names_from_news = extract_names_from_news_titles(news_data)
    name_from_profile = company_profile.get('name')
    name_from_quote = quote_data.get('longName')
    
    # 一致性验证
    if not all_names_consistent([names_from_news, name_from_profile, name_from_quote]):
        raise CompanyIdentityInconsistency()
    
    return verified_company_info
```

## 错误处理和恢复机制

### 1. 错误分类
- **Level 1**: 基础事实错误 (致命，必须修复)
- **Level 2**: 数据不一致 (警告，尝试解决)  
- **Level 3**: 分析偏差 (提醒，记录但继续)

### 2. 自动恢复策略
```python
def error_recovery_protocol(error_type, error_context):
    if error_type == "company_identity_mismatch":
        # 重新验证基础数据
        return restart_from_phase_0()
    elif error_type == "data_inconsistency":
        # 标记不确定数据，继续分析
        return mark_uncertain_and_continue()
    elif error_type == "analysis_logic_error":
        # 重新调用相关agent
        return retry_analysis_phase()
```

## 数据共享协议

### 1. 标准化数据交换格式
```json
{
  "phase": "data_collection",
  "agent_id": "market-analyst", 
  "fact_base_version": "v1.0",
  "fact_base_verified": true,
  "confidence_score": 0.95,
  "data": {
    "company_identity": {
      "ticker": "6855.HK",
      "official_name": "Ascentage Pharma Group International",
      "verified_sources": ["market_data", "news_titles", "company_profile"]
    },
    "analysis_results": {...}
  },
  "metadata": {
    "timestamp": "2025-08-19T10:00:00Z",
    "data_sources": ["yfinance", "finnhub"],
    "verification_status": "passed"
  }
}
```

### 2. Agent间通信协议
- **Phase 0结果** → 所有后续agents
- **Phase 1结果** → Phase 2 cross-validator
- **Phase 2验证报告** → Phase 3 analysis agents
- **Phase 3分析结果** → Phase 4 quality-controller

## 实施计划

### 第一步：架构重构 (立即)
1. 修改 `/trade-analyze` command 执行逻辑
2. 添加Phase 0和Phase 2验证步骤
3. 创建新的subagents配置

### 第二步：Subagents开发 (优先)
1. 开发 `data-validator` subagent
2. 开发 `cross-validator` subagent  
3. 开发 `quality-controller` subagent

### 第三步：现有Agents优化 (同步)
1. 更新所有analysis agents使用标准化协议
2. 增强MCP工具调用和数据解析逻辑
3. 添加一致性验证机制

### 第四步：测试和调优 (最后)
1. 使用多个股票代码测试新流程
2. 验证错误检测和恢复机制
3. 优化性能和用户体验

## 成功指标

1. **基础事实准确率**: 100% (不允许公司识别错误)
2. **数据一致性**: >95% 跨agent数据一致性
3. **错误检测率**: >90% 自动检测分析中的事实错误
4. **分析质量**: 提高分析可信度和实用性
5. **用户体验**: 保持响应速度，提升结果可靠性

这个优化架构将从根本上解决当前系统的设计缺陷，确保类似的重大失误不再发生。