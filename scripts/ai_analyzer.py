# -*- coding: utf-8 -*-
"""
AI 分析模块 - 通过 OpenAI 兼容接口调用 LLM 进行深度分析
"""

import json
import logging
from typing import Dict, Any

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """AI 分析器 - 通过 OpenAI 兼容接口调用任意 LLM"""

    def __init__(self, config: Dict[str, Any]):
        self.model = config.get('model', 'gpt-4o-mini')
        self.temperature = config.get('temperature', 0.3)
        self.max_tokens = config.get('max_tokens', 4096)
        self.enabled = bool(config.get('api_key') or config.get('base_url'))

        if self.enabled and HAS_OPENAI:
            kwargs = {}
            if config.get('api_key'):
                kwargs['api_key'] = config['api_key']
            if config.get('base_url'):
                kwargs['base_url'] = config['base_url']
            self.client = OpenAI(**kwargs)
        else:
            self.client = None
            if not HAS_OPENAI:
                logger.warning("openai 包未安装，AI 分析不可用")
            elif not self.enabled:
                logger.info("AI 分析未配置（缺少 api_key 或 base_url），将使用技术面兜底分析")

    def analyze(self, code: str, name: str, technical_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用 AI 进行深度分析

        Args:
            code: 股票代码
            name: 股票名称
            technical_data: 技术指标数据

        Returns:
            AI 分析结果
        """
        if not self.client:
            return self._default_analysis_from_tech(technical_data)

        try:
            prompt = self._build_prompt(code, name, technical_data)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            text = response.choices[0].message.content
            return self._parse_ai_response(text, technical_data)
        except Exception as e:
            logger.error(f"AI 分析失败：{e}")
            return self._default_analysis_from_tech(technical_data)

    def _build_prompt(self, code: str, name: str, tech: Dict[str, Any]) -> str:
        """构建 AI 提示词（优先从外部 markdown 模板加载）"""
        from pathlib import Path

        template_path = Path(__file__).parent / "prompts" / "analysis_prompt.md"

        variables = {
            'code': code,
            'name': name,
            'current_price': tech.get('current_price', 'N/A'),
            'ma5': f"{tech.get('ma5', 0):.2f}",
            'bias_ma5': f"{tech.get('bias_ma5', 0):+.2f}%",
            'ma10': f"{tech.get('ma10', 0):.2f}",
            'bias_ma10': f"{tech.get('bias_ma10', 0):+.2f}%",
            'ma20': f"{tech.get('ma20', 0):.2f}",
            'trend_status': tech.get('trend_status', 'N/A'),
            'macd_status': tech.get('macd_status', 'N/A'),
            'macd_signal': tech.get('macd_signal', ''),
            'rsi_status': tech.get('rsi_status', 'N/A'),
            'rsi_signal': tech.get('rsi_signal', ''),
            'volume_status': tech.get('volume_status', 'N/A'),
            'volume_trend': tech.get('volume_trend', ''),
            'signal_score': tech.get('signal_score', 0),
            'buy_signal': tech.get('buy_signal', 'N/A'),
            'signal_reasons': ', '.join(tech.get('signal_reasons', [])),
            'risk_factors': ', '.join(tech.get('risk_factors', [])),
        }

        try:
            template = template_path.read_text(encoding='utf-8')
            for key, value in variables.items():
                template = template.replace('{{' + key + '}}', str(value))
            return template
        except FileNotFoundError:
            logger.warning("模板文件 %s 不存在，使用内联 prompt", template_path)

        return f"""你是一位专业的股票分析师，请根据以下技术指标给出投资建议。

股票：{name} ({code})

技术指标数据:
- 当前价格：{tech.get('current_price', 'N/A')}
- MA5: {tech.get('ma5', 0):.2f} (乖离率：{tech.get('bias_ma5', 0):+.2f}%)
- MA10: {tech.get('ma10', 0):.2f} (乖离率：{tech.get('bias_ma10', 0):+.2f}%)
- MA20: {tech.get('ma20', 0):.2f}
- 趋势状态：{tech.get('trend_status', 'N/A')}
- MACD: {tech.get('macd_status', 'N/A')} - {tech.get('macd_signal', '')}
- RSI: {tech.get('rsi_status', 'N/A')} - {tech.get('rsi_signal', '')}
- 量能：{tech.get('volume_status', 'N/A')} - {tech.get('volume_trend', '')}
- 技术面评分：{tech.get('signal_score', 0)}/100
- 买入信号：{tech.get('buy_signal', 'N/A')}
- 买入理由：{', '.join(tech.get('signal_reasons', []))}
- 风险因素：{', '.join(tech.get('risk_factors', []))}

请输出以下 JSON 格式的分析结果:
{{
    "sentiment_score": 0-100,
    "trend_prediction": "上涨/下跌/震荡",
    "operation_advice": "买入/持有/观望/卖出",
    "confidence_level": "高/中/低",
    "analysis_summary": "一句话核心结论",
    "buy_reason": "具体买入理由",
    "risk_warning": "风险提示",
    "target_price": "目标价",
    "stop_loss": "止损价"
}}

只输出 JSON，不要其他内容。"""

    def _parse_ai_response(self, text: str, tech: Dict[str, Any]) -> Dict[str, Any]:
        """解析 AI 响应"""
        try:
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    'sentiment_score': result.get('sentiment_score', tech.get('signal_score', 50)),
                    'trend_prediction': result.get('trend_prediction', tech.get('trend_status', '震荡')),
                    'operation_advice': result.get('operation_advice', tech.get('buy_signal', '观望')),
                    'confidence_level': result.get('confidence_level', '中'),
                    'analysis_summary': result.get('analysis_summary', ''),
                    'buy_reason': result.get('buy_reason', ''),
                    'risk_warning': result.get('risk_warning', ''),
                    'target_price': result.get('target_price', ''),
                    'stop_loss': result.get('stop_loss', '')
                }
        except Exception as e:
            logger.warning(f"解析 AI 响应失败：{e}")

        return self._default_analysis_from_tech(tech)

    def _default_analysis_from_tech(self, tech: Dict[str, Any]) -> Dict[str, Any]:
        """基于技术面的默认分析"""
        score = tech.get('signal_score', 50)
        buy_signal = tech.get('buy_signal', '观望')

        return {
            'sentiment_score': score,
            'trend_prediction': tech.get('trend_status', '震荡'),
            'operation_advice': buy_signal,
            'confidence_level': '高' if score >= 70 else '中' if score >= 50 else '低',
            'analysis_summary': ' | '.join(tech.get('signal_reasons', []))[:100],
            'buy_reason': ', '.join(tech.get('signal_reasons', [])),
            'risk_warning': ' | '.join(tech.get('risk_factors', [])),
            'target_price': '',
            'stop_loss': ''
        }
