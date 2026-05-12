---
name: stock-daily-analysis
description: A股技术面分析系统。获取A股日线行情，计算技术指标（均线、MACD、RSI、乖离率、量能），输出技术面评分和AI结论。触发词：股票分析、分析股票、每日分析、技术面分析。
---

# 执行标准程序 (Recommended Workflow)

当用户要求分析股票时，按以下步骤执行：

## Step 1: 调用分析脚本获取技术指标

使用以下命令获取股票的技术面分析数据：

```bash
cd ~/.openclaw/workspace/skills/stock-daily-analysis-skill && .venv/bin/python3 -c "from scripts.analyzer import analyze_stock; import json; r=analyze_stock('{股票代码}'); print(json.dumps(r, ensure_ascii=False, indent=2, default=str))"
```

将 `{股票代码}` 替换为6位数字代码，例如 `600519`、`301292`。

脚本会自动完成：获取行情数据 → 计算技术指标 → 输出 JSON 结果。

## Step 2: 你（Agent LLM）必须亲自解读技术指标

**⚠️ 重要：这一步是你（Agent LLM）必须执行的分析工作，不要跳过，不要直接使用 ai_analysis 字段的内容。**

Step 1 返回的 JSON 中，`ai_analysis` 字段只是技术指标的简单字符串拼接，不包含任何智能判断。你必须基于 `technical_indicators` 中的数据，自己进行分析和解读。

### 你需要完成的分析：

1. **AI结论**：看多 / 继续跟踪 / 观望 / 看空（结合所有指标综合判断，不是直接取 operation_advice）
2. **目标价**：基于支撑压力位、均线位置、近期高点推算
3. **止损价**：基于关键支撑位（MA20、近期低点）设定
4. **关键观察点**：接下来 1-3 个交易日需要关注什么
5. **每个技术指标下写 AI 解读**：不要只列数据，要说明含义和后续走势预判
6. **看多理由**：基于 signal_reasons 结合近 20 日行情走势做综合分析
7. **风险提示**：基于 risk_factors 结合近 20 日行情走势做综合分析

### 你需要重点关注的字段：

- `signal_score`：综合评分（0-100），>=60 偏积极，<45 偏谨慎
- `trend_status`：趋势判断（强势多头/多头排列/弱势多头/盘整/弱势空头/空头排列/强势空头）
- `bias_ma5`：乖离率，绝对值 >5% 提示短期偏离过大
- `macd_status`：金叉/死叉/多头/空头
- `rsi_status`：超买(>70)/强势看多/中性/弱势/超卖(<30)
- `volume_status`：放量上涨/缩量回调/放量下跌 等
- `signal_reasons`：看多理由列表（参考但不照搬）
- `risk_factors`：风险因素列表（参考但不照搬）

## Step 3: 生成完整报告并保存

将 Step 1 的技术指标数据和 Step 2 你自己的分析整合为完整的 Markdown 报告。

报告格式：

```markdown
# {代码} {名称} 股票分析报告

> 生成时间: {日期} | 数据来源: 财新数据平台 | 分析工具: stock-daily-analysis-skill + AI 分析

---

## 核心结论

| 项目 | 结果 |
|------|------|
| **AI结论** | {你在 Step 2 的综合结论} |
| **综合评分** | {signal_score}/100 |
| **趋势判断** | {trend_status}（{你的补充说明}） |
| **置信度** | {你判断的高/中/低} |

**一句话结论**: {你的一句话核心结论}

---

## 最新行情

{从 technical_indicators 中提取 current_price 等}

---

## 技术面分析

### 均线系统
{ma5/ma10/ma20 + 乖离率}
- **AI 解读**: {你对均线走势的判断}

### MACD 指标
{macd_status + macd_signal}
- **AI 解读**: {你对 MACD 信号的判断}

### RSI 指标
{rsi_6/rsi_12/rsi_24 + rsi_status}
- **AI 解读**: {你对 RSI 状态的判断}

### 量能分析
{volume_status + volume_ratio_5d}
- **AI 解读**: {你对量能配合的判断}

---

## 支撑与压力位

| 类型 | 价位 | 依据 |
|------|------|------|
| 强支撑 | {价位} | {依据} |
| 短支撑 | {价位} | {依据} |
| 第一压力 | {价位} | {依据} |
| 强压力 | {价位} | {依据} |

---

## AI 结论

| 项目 | 内容 |
|------|------|
| **合理价值区间** | {AI 生成的合理价值区间} |
| **风险警示区间** | {AI 生成的风险警示区间} |
| **关键观察点** | {你认为需要关注的要点} |

### 看多理由
{你基于技术指标和行情走势的综合分析}

### 风险提示
{你基于技术指标和行情走势的风险分析}

---

## 近{N}日行情走势

{从 Step 1 返回数据中提取近 20 日行情表}

---

*免责声明: 本报告技术指标由 stock-daily-analysis-skill 自动生成，AI 分析部分基于技术面数据，仅供学习研究参考，不构成任何投资建议。股市有风险，投资需谨慎。*
```

**报告保存位置**: `{项目根目录}/stock-analysis/{代码}_{名称}_分析报告_{日期}.md`

---

# 配置说明

## 数据源
本技能依赖 `wh/stock-market-information` skill 获取 A 股行情数据。

**必须先安装数据源 skill**：前往 https://yun.ccxe.com.cn/data/Skills 下载 `stock-market-information`，放置到 `wh/stock-market-information` 目录。未安装时调用分析会返回安装提示。

## 可选参数
通过环境变量配置（`scripts/.env`）：
```
DATA_DAYS=20
ANALYSIS_BIAS_THRESHOLD=5.0
ANALYSIS_VOLUME_SHRINK_RATIO=0.7
ANALYSIS_VOLUME_HEAVY_RATIO=1.5
```

---

# 故障排除

- **数据源未安装**: 需要先下载 stock-market-information skill → 前往 https://yun.ccxe.com.cn/data/Skills 下载，放置到 `wh/stock-market-information` 目录
- **ModuleNotFoundError**: 需要安装依赖 → `.venv/bin/pip install pandas numpy requests python-dotenv`
- **数据获取失败**: 检查 `wh/stock-market-information` skill 是否存在，`.env` 中是否配置了 `CXDA_USER_KEY` 和 `BASE_URL`
- **只支持 A 股**: 港股/美股代码会返回"数据获取失败"

---

# 返回数据格式参考

```python
{
    'code': '600519',
    'name': '贵州茅台',
    'technical_indicators': {
        'trend_status': '强势多头',
        'ma5': 1500.0, 'ma10': 1480.0, 'ma20': 1450.0,
        'bias_ma5': 2.5,
        'macd_status': '金叉',
        'rsi_status': '强势看多',
        'buy_signal': '看多',
        'signal_score': 75,
        'signal_reasons': [...],
        'risk_factors': [...]
    },
    'ai_analysis': {
        'sentiment_score': 75,
        'operation_advice': '看多',
        'confidence_level': '高',
        'analysis_summary': '...',
        'buy_reason': '...',
        'risk_warning': '...'
    }
}
```
