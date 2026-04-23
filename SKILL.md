---
name: stock-daily-analysis
description: LLM驱动的每日股票分析系统。支持A股/港股/美股自选股智能分析，生成决策仪表盘和大盘复盘报告。提供技术面分析（均线、MACD、RSI、乖离率）、趋势判断、买入信号评分。可与market-data skill集成获取更稳定的ETF数据。触发词：股票分析、分析股票、每日分析、技术面分析。
---

# Daily Stock Analysis for OpenClaw

基于 LLM 的 A/H/美股智能分析 Skill，提供技术面分析和 AI 决策建议。

## 功能特性

1. **多市场支持** - A股、港股、美股
2. **技术面分析** - MA5/10/20、MACD、RSI、乖离率
3. **趋势交易** - 多头排列判断、买入信号评分
4. **AI 决策** - 通过 OpenAI 兼容接口接入任意 LLM
5. **数据源集成** - 可选 market-data skill

## 快速使用

```python
from scripts.analyzer import analyze_stock, analyze_stocks

# 单只分析
result = analyze_stock('600519')
print(result['ai_analysis']['operation_advice'])

# 批量分析
results = analyze_stocks(['600362', '601318', '159892'])
```

## 配置

1. 复制配置模板：
```bash
cp scripts/.env.example scripts/.env
```

2. 填入 AI 配置（支持任意 OpenAI 兼容接口）：
```
LLM_API_KEY=sk-your-api-key
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=4096
```

支持的 LLM_BASE_URL 示例：
- DeepSeek: `https://api.deepseek.com/v1`
- OpenAI: `https://api.openai.com/v1`
- Ollama 本地: `http://localhost:11434/v1`
- 智谱 GLM: `https://open.bigmodel.cn/api/paas/v4`
- 其他兼容接口: 填入对应的 base_url 即可

## 返回数据

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
        'signal_score': 75
    },
    'ai_analysis': {
        'sentiment_score': 75,
        'operation_advice': '买入',
        'confidence_level': '高',
        'target_price': '1550',
        'stop_loss': '1420'
    }
}
```

## 项目信息

- **开源协议**: MIT
- **项目地址**: https://github.com/yourusername/stock-daily-analysis
- **原项目**: https://github.com/ZhuLinsen/daily_stock_analysis

---

⚠️ **免责声明**: 本项目仅供学习研究，不构成投资建议。股市有风险，投资需谨慎。
