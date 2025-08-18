"""
技术指标服务模块
基于 stockstats 库提供各种技术指标计算
"""

import os
import asyncio
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import yfinance as yf
from stockstats import StockDataFrame
from .proxy_config import get_proxy_config

logger = logging.getLogger(__name__)

class TechnicalIndicatorsService:
    """技术指标服务"""
    
    def __init__(self):
        self.cache = {}
        # 从环境变量读取数据缓存超时，默认10分钟
        self.cache_timeout = int(os.getenv('DATA_CACHE_TTL', '600'))
        self.proxy_config = get_proxy_config()
        self._setup_yfinance_proxy()
    
    def _setup_yfinance_proxy(self):
        """为 yfinance 设置代理"""
        try:
            proxies = self.proxy_config.get_proxies()
            if proxies:
                # 设置全局代理环境变量，影响 yfinance
                for scheme, proxy_url in proxies.items():
                    os.environ[f'{scheme.upper()}_PROXY'] = proxy_url
                logger.info("技术指标服务 yfinance 代理配置完成")
        except Exception as e:
            logger.warning(f"技术指标服务代理配置失败: {e}")
    
    def _get_ticker_with_proxy(self, symbol: str):
        """获取带代理配置的 ticker 对象"""
        try:
            ticker = yf.Ticker(symbol)
            proxies = self.proxy_config.get_proxies()
            if proxies and hasattr(ticker, 'session'):
                ticker.session = self.proxy_config.setup_requests_session()
            return ticker
        except Exception as e:
            logger.error(f"创建 ticker 失败 {symbol}: {e}")
            return yf.Ticker(symbol)
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 测试基础功能
            test_data = pd.DataFrame({
                'open': [100, 101, 102],
                'high': [105, 106, 107],
                'low': [99, 100, 101],
                'close': [104, 105, 106],
                'volume': [1000, 1100, 1200]
            })
            
            stock_df = StockDataFrame.retype(test_data)
            _ = stock_df['rsi_14']
            return True
        except Exception as e:
            logger.error(f"Technical indicators health check failed: {e}")
            return False
    
    async def get_market_data(
        self, 
        symbol: str, 
        period: str = "6mo",
        interval: str = "1d"
    ) -> pd.DataFrame:
        """获取市场数据用于技术指标计算"""
        try:
            cache_key = f"market_data_{symbol}_{period}_{interval}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            ticker = self._get_ticker_with_proxy(symbol)
            hist = ticker.history(period=period, interval=interval)
            
            if hist.empty:
                raise ValueError(f"No market data found for {symbol}")
            
            # 标准化列名
            hist.columns = hist.columns.str.lower()
            hist = hist.reset_index()
            if 'date' in hist.columns:
                hist['date'] = pd.to_datetime(hist['date'])
            
            # 缓存结果
            self._cache_data(cache_key, hist)
            
            return hist
            
        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {e}")
            return pd.DataFrame()
    
    async def calculate_indicators(
        self, 
        symbol: str, 
        indicators: List[str] = None,
        period: str = "6mo"
    ) -> Dict[str, Any]:
        """计算技术指标"""
        if indicators is None:
            indicators = [
                'rsi_14', 'macd', 'boll', 'sma_20', 'sma_50', 
                'ema_12', 'ema_26', 'atr_14', 'stoch_k', 'stoch_d'
            ]
        
        try:
            cache_key = f"indicators_{symbol}_{'-'.join(sorted(indicators))}_{period}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            # 获取市场数据
            df = await self.get_market_data(symbol, period)
            if df.empty:
                return {}
            
            # 转换为 StockDataFrame
            stock_df = StockDataFrame.retype(df.copy())
            
            # 计算指标
            results = {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "indicators": {},
                "latest_values": {},
                "signals": {}
            }
            
            for indicator in indicators:
                try:
                    if indicator == 'macd':
                        results["indicators"]["macd"] = self._calculate_macd(stock_df)
                        results["latest_values"]["macd"] = results["indicators"]["macd"]["latest"]
                        results["signals"]["macd"] = results["indicators"]["macd"]["signal"]
                    
                    elif indicator == 'boll':
                        results["indicators"]["bollinger"] = self._calculate_bollinger(stock_df)
                        results["latest_values"]["bollinger"] = results["indicators"]["bollinger"]["latest"]
                        results["signals"]["bollinger"] = results["indicators"]["bollinger"]["signal"]
                    
                    elif indicator.startswith('rsi'):
                        period = int(indicator.split('_')[1]) if '_' in indicator else 14
                        results["indicators"][f"rsi_{period}"] = self._calculate_rsi(stock_df, period)
                        results["latest_values"][f"rsi_{period}"] = results["indicators"][f"rsi_{period}"]["latest"]
                        results["signals"][f"rsi_{period}"] = results["indicators"][f"rsi_{period}"]["signal"]
                    
                    elif indicator.startswith('sma'):
                        period = int(indicator.split('_')[1]) if '_' in indicator else 20
                        results["indicators"][f"sma_{period}"] = self._calculate_sma(stock_df, period)
                        results["latest_values"][f"sma_{period}"] = results["indicators"][f"sma_{period}"]["latest"]
                        results["signals"][f"sma_{period}"] = results["indicators"][f"sma_{period}"]["signal"]
                    
                    elif indicator.startswith('ema'):
                        period = int(indicator.split('_')[1]) if '_' in indicator else 12
                        results["indicators"][f"ema_{period}"] = self._calculate_ema(stock_df, period)
                        results["latest_values"][f"ema_{period}"] = results["indicators"][f"ema_{period}"]["latest"]
                        results["signals"][f"ema_{period}"] = results["indicators"][f"ema_{period}"]["signal"]
                    
                    elif indicator.startswith('atr'):
                        period = int(indicator.split('_')[1]) if '_' in indicator else 14
                        results["indicators"][f"atr_{period}"] = self._calculate_atr(stock_df, period)
                        results["latest_values"][f"atr_{period}"] = results["indicators"][f"atr_{period}"]["latest"]
                    
                    elif indicator in ['stoch_k', 'stoch_d']:
                        if 'stochastic' not in results["indicators"]:
                            results["indicators"]["stochastic"] = self._calculate_stochastic(stock_df)
                            results["latest_values"]["stochastic"] = results["indicators"]["stochastic"]["latest"]
                            results["signals"]["stochastic"] = results["indicators"]["stochastic"]["signal"]
                
                except Exception as e:
                    logger.warning(f"Failed to calculate {indicator} for {symbol}: {e}")
                    continue
            
            # 缓存结果
            self._cache_data(cache_key, results)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to calculate indicators for {symbol}: {e}")
            return {}
    
    def _calculate_macd(self, df: StockDataFrame) -> Dict[str, Any]:
        """计算 MACD 指标"""
        try:
            macd = df['macd']
            macd_signal = df['macds']
            macd_hist = df['macdh']
            
            latest_macd = float(macd.iloc[-1])
            latest_signal = float(macd_signal.iloc[-1])
            latest_hist = float(macd_hist.iloc[-1])
            
            # 生成信号
            signal = "neutral"
            if latest_macd > latest_signal and latest_hist > 0:
                signal = "bullish"
            elif latest_macd < latest_signal and latest_hist < 0:
                signal = "bearish"
            
            return {
                "latest": {
                    "macd": latest_macd,
                    "signal": latest_signal,
                    "histogram": latest_hist
                },
                "signal": signal,
                "description": "MACD 动量指标显示趋势变化"
            }
        except Exception as e:
            logger.error(f"MACD calculation error: {e}")
            return {}
    
    def _calculate_bollinger(self, df: StockDataFrame) -> Dict[str, Any]:
        """计算布林带"""
        try:
            boll_upper = df['boll_ub']
            boll_lower = df['boll_lb']
            boll_mid = df['boll']
            current_price = df['close'].iloc[-1]
            
            latest_upper = float(boll_upper.iloc[-1])
            latest_lower = float(boll_lower.iloc[-1])
            latest_mid = float(boll_mid.iloc[-1])
            
            # 生成信号
            signal = "neutral"
            if current_price > latest_upper:
                signal = "overbought"
            elif current_price < latest_lower:
                signal = "oversold"
            
            return {
                "latest": {
                    "upper": latest_upper,
                    "middle": latest_mid,
                    "lower": latest_lower,
                    "current_price": float(current_price)
                },
                "signal": signal,
                "description": "布林带显示价格波动区间"
            }
        except Exception as e:
            logger.error(f"Bollinger Bands calculation error: {e}")
            return {}
    
    def _calculate_rsi(self, df: StockDataFrame, period: int = 14) -> Dict[str, Any]:
        """计算 RSI 指标"""
        try:
            rsi = df[f'rsi_{period}']
            latest_rsi = float(rsi.iloc[-1])
            
            # 生成信号
            signal = "neutral"
            if latest_rsi > 70:
                signal = "overbought"
            elif latest_rsi < 30:
                signal = "oversold"
            
            return {
                "latest": latest_rsi,
                "signal": signal,
                "description": f"RSI({period}) 相对强弱指标"
            }
        except Exception as e:
            logger.error(f"RSI calculation error: {e}")
            return {}
    
    def _calculate_sma(self, df: StockDataFrame, period: int = 20) -> Dict[str, Any]:
        """计算简单移动平均线"""
        try:
            sma = df[f'close_{period}_sma']
            current_price = df['close'].iloc[-1]
            latest_sma = float(sma.iloc[-1])
            
            # 生成信号
            signal = "neutral"
            if current_price > latest_sma:
                signal = "bullish"
            elif current_price < latest_sma:
                signal = "bearish"
            
            return {
                "latest": latest_sma,
                "current_price": float(current_price),
                "signal": signal,
                "description": f"SMA({period}) 简单移动平均线"
            }
        except Exception as e:
            logger.error(f"SMA calculation error: {e}")
            return {}
    
    def _calculate_ema(self, df: StockDataFrame, period: int = 12) -> Dict[str, Any]:
        """计算指数移动平均线"""
        try:
            ema = df[f'close_{period}_ema']
            current_price = df['close'].iloc[-1]
            latest_ema = float(ema.iloc[-1])
            
            # 生成信号
            signal = "neutral"
            if current_price > latest_ema:
                signal = "bullish"
            elif current_price < latest_ema:
                signal = "bearish"
            
            return {
                "latest": latest_ema,
                "current_price": float(current_price),
                "signal": signal,
                "description": f"EMA({period}) 指数移动平均线"
            }
        except Exception as e:
            logger.error(f"EMA calculation error: {e}")
            return {}
    
    def _calculate_atr(self, df: StockDataFrame, period: int = 14) -> Dict[str, Any]:
        """计算平均真实波幅"""
        try:
            atr = df[f'atr_{period}']
            latest_atr = float(atr.iloc[-1])
            
            return {
                "latest": latest_atr,
                "description": f"ATR({period}) 平均真实波幅，衡量价格波动性"
            }
        except Exception as e:
            logger.error(f"ATR calculation error: {e}")
            return {}
    
    def _calculate_stochastic(self, df: StockDataFrame) -> Dict[str, Any]:
        """计算随机指标"""
        try:
            k_percent = df['rsv_9']  # %K
            d_percent = df['rsv_9_3_sma']  # %D
            
            latest_k = float(k_percent.iloc[-1])
            latest_d = float(d_percent.iloc[-1])
            
            # 生成信号
            signal = "neutral"
            if latest_k > 80 and latest_d > 80:
                signal = "overbought"
            elif latest_k < 20 and latest_d < 20:
                signal = "oversold"
            
            return {
                "latest": {
                    "k_percent": latest_k,
                    "d_percent": latest_d
                },
                "signal": signal,
                "description": "随机指标显示超买超卖状态"
            }
        except Exception as e:
            logger.error(f"Stochastic calculation error: {e}")
            return {}
    
    async def get_indicator_summary(self, symbol: str) -> Dict[str, Any]:
        """获取指标汇总"""
        try:
            indicators = await self.calculate_indicators(symbol)
            if not indicators:
                return {}
            
            signals = indicators.get("signals", {})
            
            # 统计信号
            bullish_count = sum(1 for signal in signals.values() if signal == "bullish")
            bearish_count = sum(1 for signal in signals.values() if signal == "bearish")
            total_signals = len([s for s in signals.values() if s != "neutral"])
            
            overall_signal = "neutral"
            if total_signals > 0:
                if bullish_count > bearish_count:
                    overall_signal = "bullish"
                elif bearish_count > bullish_count:
                    overall_signal = "bearish"
            
            return {
                "symbol": symbol,
                "overall_signal": overall_signal,
                "bullish_signals": bullish_count,
                "bearish_signals": bearish_count,
                "total_signals": total_signals,
                "detailed_signals": signals,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get indicator summary for {symbol}: {e}")
            return {}
    
    def _is_cache_valid(self, key: str) -> bool:
        """检查缓存是否有效"""
        if key not in self.cache:
            return False
        
        cache_time = self.cache[key]["timestamp"]
        return (datetime.now() - cache_time).seconds < self.cache_timeout
    
    def _cache_data(self, key: str, data: Any) -> None:
        """缓存数据"""
        self.cache[key] = {
            "data": data,
            "timestamp": datetime.now()
        }