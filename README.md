# Daily Stock Analysis for OpenClaw

> 基于 LLM 的股票智能分析 Skill，为 OpenClaw 提供 A股/港股/美股 技术面分析和 AI 决策建议。

## 🎯 项目定位

本项目是 [ZhuLinsen/daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis) 的 **OpenClaw Skill 适配版**，fork 自 [chjm-ai/stock-daily-analysis-skill](https://github.com/chjm-ai/stock-daily-analysis-skill) 并进行了增强。

与原版相比，本项目的特点：
- ✅ **OpenClaw 原生集成** - 直接作为 Skill 调用
- ✅ **模块化设计** - 可独立使用或与 market-data skill 配合
- ✅ **简化依赖** - 核心功能零配置即可运行
- ✅ **开源友好** - MIT 协议，欢迎贡献

## 📢 本 Fork 的改进

相比原项目 [chjm-ai/stock-daily-analysis-skill](https://github.com/chjm-ai/stock-daily-analysis-skill)，主要做了以下改进：

### 1. 数据获取周期优化（60天 → 20天）

将技术指标的计算周期从 60 个交易日缩短为 20 个交易日，更高效、更聚焦近期行情：

| 参数 | 原值 | 新值 | 说明 |
|------|------|------|------|
| MACD 慢线周期 | 26 | 20 | 适配短周期数据 |
| RSI 长周期 | 24 | 20 | 适配短周期数据 |
| MA60 均线窗口 | rolling(60) | rolling(20) | 适配短周期数据 |
| 默认获取天数 | 60 | 20 | 减少数据请求量，提升效率 |

### 2. 数据源切换：财新数据平台

原项目使用 `akshare` 获取行情数据，本项目改用 [财新数据平台](https://yun.ccxe.com.cn/) 的 **stock-market-information skill** 作为数据源：

- 通过财新数据 API 获取 A 股日行情数据（仅使用 getStkDayQuoByCond-G 接口）
- 数据更稳定，接口响应更快
- 支持通过环境变量 `SKI_STOCK_MARKET_INFO_PATH` 自定义数据源 skill 路径

### 3. 精简数据源，移除冗余代码

- 仅使用 `getStkDayQuoByCond-G`（日行情）接口获取所有需要的数据，不再调用换手率、市值等接口
- 删除未使用的 `market_data_bridge.py`、`StockQuote`、`ChipDistribution` 等死代码
- 股票名称从日行情数据中直接提取，不再单独请求

### 4. Prompt 模板外置

将 AI 分析的提示词从 Python 代码中抽离为独立的 Markdown 模板文件：

- 提示词模板位于 `scripts/prompts/analysis_prompt.md`，使用 `{{变量名}}` 占位符
- 无需修改 Python 代码即可调整 AI 分析的提示词、输出格式和分析维度
- 模板文件不存在时自动回退到内联 prompt，兼容无模板环境

### 5. AI 分析模块重构：统一 OpenAI 兼容接口

原项目硬编码了 Gemini、OpenAI、Ollama、MLX 四个 provider 分支，每个分支有独立的初始化和调用逻辑。本次重构统一为通用的 OpenAI 兼容接口：

- **删除 `provider` 字段**，不再区分 Gemini/Ollama/OpenAI/MLX
- 只需配置 `api_key` + `base_url` + `model` 即可接入任意 LLM
- 删除 `_analyze_with_gemini()`、`_analyze_with_ollama()`、`_analyze_with_openai()` 三个独立方法
- 必须配置 AI 才能正常使用，未配置时技术分析结果不完整

### 6. 新增完整报告生成

新增 `generate_report()` 内部函数，自动整合行情数据、技术分析和 AI 分析，生成完整的 Markdown 报告：

- **行情数据是必须的** — 获取失败直接返回错误，不会生成残缺报告
- Skill 被调用时内部自动调用，无需外部直接调用
- 报告包含：核心结论、最新行情、技术指标、支撑压力位、近 N 日行情走势表、AI 决策建议

## 🚀 快速开始

### 安装

```bash
cd ~/workspace/skills/
git clone https://github.com/hongyue0102/stock-daily-analysis-skill.git

# 安装依赖
pip3 install pandas numpy requests openai python-dotenv
```

### 数据源安装

本项目依赖 [财新数据平台的 stock-market-information skill](https://yun.ccxe.com.cn/) 获取行情数据：

```bash
cd ~/workspace/skills/
mkdir -p wh
cd wh
# 将 stock-market-information skill 放置在此目录
```

目录结构应为：
```
workspace/skills/
├── wh/
│   └── stock-market-information/   # 财新数据源 skill
└── stock-daily-analysis-skill/     # 本项目
```

### 配置

```bash
cp config.example.json config.json
# 编辑 config.json 填入你的 API Key
```

### 使用

```python
from scripts.analyzer import analyze_stock, analyze_stocks

# 分析单只股票
result = analyze_stock('600519')
print(result['ai_analysis']['operation_advice'])  # 买入/持有/观望

# 分析多只股票
results = analyze_stocks(['600519', 'AAPL', '00700'])
```

## 📊 功能特性

| 功能 | 状态 | 说明 |
|------|------|------|
| A股分析 | ✅ | 支持个股、ETF |
| 港股分析 | ✅ | 支持港股通标的 |
| 美股分析 | ✅ | 基础行情获取 |
| 技术面分析 | ✅ | MA/MACD/RSI/乖离率 |
| AI 决策建议 | ✅ | OpenAI 兼容接口（任意 LLM） |
| 市场数据源集成 | ✅ | [stock-market-information skill](https://yun.ccxe.com.cn/) |

## 🏗️ 项目结构

```
stock-daily-analysis-skill/
├── SKILL.md                 # OpenClaw Skill 定义
├── README.md                # 项目文档
├── LICENSE                  # MIT 许可证
├── config.example.json      # 配置示例
├── config.json              # 用户配置 (gitignore)
├── requirements.txt         # Python 依赖
├── 300502_分析报告.md        # 📄 示例报告（新易盛）
└── scripts/
    ├── analyzer.py          # 主入口
    ├── data_fetcher.py      # 财新数据源获取（stock-market-information skill）
    ├── trend_analyzer.py    # 技术分析引擎
    ├── ai_analyzer.py       # AI 分析模块
    ├── notifier.py          # 报告输出
    └── prompts/
        └── analysis_prompt.md  # AI 分析提示词模板
```

> 📄 **示例报告**: [300502_分析报告.md](300502_分析报告.md) — 新易盛（300502）完整分析报告，包含技术面分析、AI 决策建议和近 20 日行情走势，供参考报告输出效果。

## 🔧 配置说明

### AI 模型配置

通过 OpenAI 兼容接口接入任意 LLM，只需配置 `api_key`、`base_url`、`model` 三个字段：

```json
{
  "ai": {
    "api_key": "sk-your-api-key",
    "base_url": "https://api.deepseek.com/v1",
    "model": "deepseek-chat",
    "temperature": 0.3,
    "max_tokens": 4096
  }
}
```

**支持的 base_url 示例：**

| 提供商 | base_url | 说明 |
|--------|----------|------|
| DeepSeek | `https://api.deepseek.com/v1` | 推荐，国内可用 |
| OpenAI | `https://api.openai.com/v1` | 需代理 |
| 智谱 | `https://open.bigmodel.cn/api/paas/v4` | 国内可用 |
| Ollama 本地 | `http://localhost:11434/v1` | 免费本地部署 |
| 其他 | 对应的 OpenAI 兼容接口 | 只要兼容 OpenAI API 即可 |

### 数据源配置

通过环境变量自定义数据源 skill 路径：
```bash
export SKI_STOCK_MARKET_INFO_PATH=/path/to/stock-market-information
```

默认路径为 `../../wh/stock-market-information`。

## 🤝 与 stock-market-information skill 集成

本项目使用 [财新数据平台](https://yun.ccxe.com.cn/) 的 stock-market-information skill 获取 A 股行情数据，仅调用 `getStkDayQuoByCond-G`（日行情）接口。

## 📈 返回数据格式

```python
{
    'code': '600519',
    'name': '贵州茅台',
    'technical_indicators': {
        'trend_status': '强势多头',
        'ma5': 1500.0,
        'ma10': 1480.0,
        'ma20': 1450.0,
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
        'trend_prediction': '强势多头',
        'operation_advice': '买入',
        'confidence_level': '高',
        'analysis_summary': '多头排列 | MACD金叉 | 量能配合',
        'target_price': '1550',
        'stop_loss': '1420'
    }
}
```

## 🛠️ 开发计划

- [ ] 支持更多数据源 (Tushare, Baostock)
- [ ] 添加板块分析功能
- [ ] 支持自定义策略回测
- [ ] WebUI 管理界面
- [ ] 支持更多推送渠道

## 🤝 贡献指南

欢迎提交 Issue 和 PR！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## ⚠️ 免责声明

本项目仅供学习研究使用，不构成任何投资建议。股市有风险，投资需谨慎。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- 原项目：[chjm-ai/stock-daily-analysis-skill](https://github.com/chjm-ai/stock-daily-analysis-skill)
- 灵感来源：[ZhuLinsen/daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis)
- 数据来源：[财新数据平台](https://yun.ccxe.com.cn/)
- 平台支持：[OpenClaw](https://openclaw.ai)

---

**Made with ❤️ for OpenClaw**
