# -*- coding: utf-8 -*-
"""
数据获取模块 - 基于 stock-market-information 本地 API

替代 akshare 联网获取，使用本地 stock-market-information skill 的 API 接口获取 A 股行情数据。
仅使用 getStkDayQuoByCond-G（日行情）接口获取所有需要的数据。
"""

import json
import logging
import os
from datetime import datetime
from typing import Optional, Dict, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

# stock-market-information skill 路径（可通过环境变量 SKI_STOCK_MARKET_INFO_PATH 覆盖）
_default_skill_dir = os.environ.get(
    'SKI_STOCK_MARKET_INFO_PATH',
    os.path.join(os.path.dirname(__file__), '..', '..', 'wh', 'stock-market-information')
)
SKILL_DIR = os.path.normpath(_default_skill_dir)


def _call_api(api_id: str, params: Dict[str, str]) -> Optional[Dict]:
    """
    调用 stock-market-information API（直接 HTTP 请求，避免子进程开销）

    Args:
        api_id: 接口标识
        params: 请求参数字典

    Returns:
        API 返回的 JSON 数据，失败返回 None
    """
    try:
        import requests as req
        import base64
        import gzip

        # 加载配置
        env = {}
        if os.path.exists(os.path.join(SKILL_DIR, 'scripts', '.env')):
            with open(os.path.join(SKILL_DIR, 'scripts', '.env'), 'r', encoding='utf-8') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        k, v = line.strip().split('=', 1)
                        env[k.strip()] = v.strip()

        base_url = env.get('BASE_URL', '').rstrip('/')
        user_key = os.environ.get('CXDA_USER_KEY') or env.get('CXDA_USER_KEY')

        if not base_url or not user_key:
            logger.error("未找到 BASE_URL 或 USER_KEY 配置")
            return None

        # 获取/刷新 token
        token = None
        token_expire_str = env.get('AUTH_TOKEN_EXPIRE', '')
        if token_expire_str:
            try:
                from datetime import timedelta
                expire = datetime.strptime(token_expire_str, '%Y-%m-%d %H:%M:%S')
                if expire > datetime.now():
                    token = env.get('AUTH_TOKEN')
            except:
                pass

        if not token:
            resp = req.get(
                f"{base_url}/webservice/foreign_getAuthtoken.htm",
                params={"userKey": user_key},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=30
            )
            token = json.loads(resp.text).get("result")
            if not token:
                logger.error("获取 authToken 失败")
                return None

        # 构建请求参数
        request_params = {"authtoken": token}
        request_params.update(params)

        # 发送请求
        resp = req.get(
            f"{base_url}/webservice/cxdata/{api_id}.htm",
            params=request_params,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=60
        )

        # 解码解压
        data = json.loads(gzip.decompress(base64.b64decode(resp.text.strip())).decode('utf-8'))

        if data.get('code') == '10000':
            return data
        else:
            logger.error(f"API 返回错误: {data.get('msg', 'unknown')}")
            return None

    except Exception as e:
        logger.error(f"API 调用异常: {e}")
        return None


def _is_etf_code(stock_code: str) -> bool:
    """判断是否为 ETF 代码"""
    etf_prefixes = ('51', '52', '56', '58', '15', '16', '18')
    return stock_code.startswith(etf_prefixes) and len(stock_code) == 6


def normalize_code(stock_code: str) -> tuple:
    """
    标准化股票代码

    Returns:
        tuple: (market, code)
        - market: 'a', 'hk', 'us'
        - code: 标准化后的代码
    """
    code = stock_code.strip()

    if code.isdigit() and len(code) == 6:
        return 'a', code

    import re
    if re.match(r'^[A-Z]{1,5}(\.[A-Z])?$', code.upper()):
        return 'us', code.upper()

    if code.lower().startswith('hk'):
        numeric_part = code[2:]
        if numeric_part.isdigit():
            return 'hk', numeric_part.zfill(5)

    if code.isdigit() and len(code) == 5:
        return 'hk', code.zfill(5)

    return 'a', code


def get_daily_data(stock_code: str, days: int = 20) -> Optional[Tuple[pd.DataFrame, str]]:
    """
    获取股票日线数据（通过 stock-market-information 本地 API）

    Args:
        stock_code: 股票代码（仅支持 A 股）
        days: 获取天数（API 返回全量数据，此参数用于截取）

    Returns:
        (DataFrame, 股票名称) 元组，DataFrame 包含 OHLCV 数据，失败返回 None
    """
    market, code = normalize_code(stock_code)

    if market != 'a':
        logger.warning(f"stock-market-information 仅支持 A 股，{stock_code} 为 {market} 市场代码")
        return None

    # 多页请求拼接数据（API 每页返回 20 条）
    pages_needed = max(1, (days + 19) // 20)
    all_results = []

    for page in range(1, pages_needed + 1):
        data = _call_api('getStkDayQuoByCond-G', {
            'stkCode': code,
            'pageNum': str(page),
            'pageSize': '20',
        })
        if not data:
            break
        results = data.get('result', [])
        if not results:
            break
        all_results.extend(results)
        if len(results) < 20:
            break

    if not all_results:
        logger.warning(f"{stock_code} 无日行情数据")
        return None

    # 提取股票名称（取最新一条数据中的名称）
    all_results.sort(key=lambda x: x.get('TRADE_DATE', ''), reverse=True)
    name = all_results[0].get('STK_SHORT_NAME', stock_code)

    # 去重（按 TRADE_DATE）
    seen = set()
    unique = []
    for r in all_results:
        dt = r.get('TRADE_DATE', '')
        if dt not in seen:
            seen.add(dt)
            unique.append(r)

    # 转换为 DataFrame
    df = pd.DataFrame(unique)

    column_mapping = {
        'TRADE_DATE': 'date',
        'OPEN_PRICE': 'open',
        'CLOSE_PRICE': 'close',
        'HIGH_PRICE': 'high',
        'LOW_PRICE': 'low',
        'TRADE_VOL': 'volume',
        'TRADE_AMUT': 'amount',
        'PRICE_LIMIT': 'pct_chg',
        'PRE_CLOSE_PRICE': 'pre_close',
    }

    df = df.rename(columns=column_mapping)

    df['date'] = pd.to_datetime(df['date'])

    for col in ['open', 'high', 'low', 'close', 'volume', 'amount', 'pct_chg', 'pre_close']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # 删除不需要的列
    keep_cols = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'pct_chg', 'pre_close']
    df = df[[c for c in keep_cols if c in df.columns]]

    df = df.dropna(subset=['close', 'volume'])
    df = df.sort_values('date', ascending=True).reset_index(drop=True)

    if days and len(df) > days:
        df = df.tail(days).reset_index(drop=True)

    return df, name
