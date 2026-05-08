---
name: stock-daily-analysis
description: A股技术面分析系统。获取A股日线行情，计算技术指标（均线、MACD、RSI、乖离率、量能），输出技术面评分和买入信号。触发词：股票分析、分析股票、每日分析、技术面分析。
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

## Step 2: 读取技术指标，给出投资建议

基于 Step 1 返回的技术指标数据，**由 AI 自己**给出以下分析：

- **操作建议**：买入 / 持有 / 观望 / 卖出
- **目标价**：基于技术面支撑压力位推算
- **止损价**：基于关键支撑位设定
- **风险提示**：基于技术指标中的风险因素
- **买入理由**：基于 signal_reasons 中的积极信号

重点关注以下字段：
- `signal_score`：综合评分（0-100），>=60 偏积极，<45 偏谨慎
- `trend_status`：趋势判断（强势多头/多头排列/弱势多头/盘整/弱势空头/空头排列/强势空头）
- `bias_ma5`：乖离率，绝对值 >5% 提示短期偏离过大
- `macd_status`：金叉/死叉/多头/空头
- `rsi_status`：超买(>70)/强势买入/中性/弱势/超卖(<30)
- `volume_status`：放量上涨/缩量回调/放量下跌 等
- `signal_reasons`：看多理由列表
- `risk_factors`：风险因素列表

## Step 3: 输出完整分析报告

将技术指标和 AI 分析建议组合为 Markdown 报告，格式如下：

```markdown
# {代码} {名称} 股票分析报告

> 生成时间: {日期} | 数据来源: 财新数据平台 | 分析工具: stock-daily-analysis-skill

---

## 核心结论

| 项目 | 结果 |
|------|------|
| **操作建议** | {AI 给出的建议} |
| **综合评分** | {signal_score}/100 |
| **趋势判断** | {trend_status} |
| **置信度** | {AI 判断的高/中/低} |

**一句话结论**: {AI 的一句核心结论}

---

## 最新行情

{从返回数据的 technical_indicators 中提取 current_price 等}

---

## 技术面分析

### 均线系统
{ma5/ma10/ma20 + 乖离率}

### MACD 指标
{macd_status + macd_signal}

### RSI 指标
{rsi_6/rsi_12/rsi_24 + rsi_status}

### 量能分析
{volume_status + volume_ratio_5d}

---

## AI 决策建议

| 项目 | 内容 |
|------|------|
| **目标价** | {AI 基于技术面推算} |
| **止损价** | {AI 基于支撑位设定} |
| **操作建议** | {AI 给出的建议} |
| **关键观察点** | {AI 认为需要关注的要点} |

### 买入理由
{AI 基于技术指标的分析}

### 风险提示
{AI 基于技术指标的风险分析}

---

*免责声明: 本报告仅供学习研究参考，不构成任何投资建议。股市有风险，投资需谨慎。*
```

---

# 配置说明

## 数据源
本技能依赖 `wh/stock-market-information` skill 获取 A 股行情数据。

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
        'rsi_status': '强势买入',
        'buy_signal': '买入',
        'signal_score': 75,
        'signal_reasons': [...],
        'risk_factors': [...]
    },
    'ai_analysis': {
        'sentiment_score': 75,
        'operation_advice': '买入',
        'confidence_level': '高',
        'analysis_summary': '...',
        'buy_reason': '...',
        'risk_warning': '...'
    }
}
```
