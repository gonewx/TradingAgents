"""
市场数据服务模块
"""

import os
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Any
import asyncio
import logging
from datetime import datetime, timedelta
import requests
from .proxy_config import get_proxy_config

logger = logging.getLogger(__name__)

class MarketDataService:
    """市场数据服务"""
    
    def __init__(self):
        self.cache = {}
        # 从环境变量读取缓存超时，默认5分钟
        self.cache_timeout = int(os.getenv('DATA_CACHE_TTL', '300'))
        self.proxy_config = get_proxy_config()
        self._setup_yfinance_proxy()
        
    def _setup_yfinance_proxy(self):
        """为 yfinance 设置代理"""
        try:
            proxies = self.proxy_config.get_proxies()
            if proxies:
                # yfinance 内部使用 requests，我们可以通过修改默认会话来设置代理
                session = self.proxy_config.setup_requests_session()
                
                # 尝试为 yfinance 设置自定义会话
                # 这需要 yfinance 版本支持
                try:
                    # 某些版本的 yfinance 允许自定义会话
                    if hasattr(yf, 'session'):
                        yf.session = session
                except AttributeError:
                    pass
                
                logger.info("yfinance 代理配置完成")
            else:
                logger.info("yfinance 使用直连（无代理）")
        except Exception as e:
            logger.warning(f"yfinance 代理配置失败: {e}")
    
    def _get_ticker_with_proxy(self, symbol: str):
        """获取带代理配置的 ticker 对象"""
        try:
            ticker = yf.Ticker(symbol)
            
            # 如果需要，可以为每个 ticker 实例设置代理会话
            proxies = self.proxy_config.get_proxies()
            if proxies and hasattr(ticker, 'session'):
                ticker.session = self.proxy_config.setup_requests_session()
            
            return ticker
        except Exception as e:
            logger.error(f"创建 ticker 失败 {symbol}: {e}")
            return yf.Ticker(symbol)  # 回退到基本实现
        
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 尝试获取一个简单的股票报价
            stock = self._get_ticker_with_proxy("AAPL")
            info = stock.info
            return bool(info.get("symbol"))
        except Exception as e:
            logger.error(f"Market data health check failed: {e}")
            return False
    
    async def get_quote(self, ticker: str) -> Dict[str, Any]:
        """获取股票实时报价"""
        try:
            # 检查缓存
            cache_key = f"quote_{ticker}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            # 获取股票信息
            stock = self._get_ticker_with_proxy(ticker)
            info = stock.info
            # 获取至少2天的数据以计算涨跌幅
            hist = stock.history(period="5d")
            
            if hist.empty:
                raise ValueError(f"No data found for ticker {ticker}")
            
            latest = hist.iloc[-1]
            
            # 获取前一交易日收盘价
            previous_close = float(latest["Open"])  # 当日开盘价作为基准
            if len(hist) > 1:
                previous_close = float(hist.iloc[-2]["Close"])  # 前一交易日收盘价
            elif 'previousClose' in info:
                previous_close = float(info['previousClose'])  # 从info获取前一日收盘价
            
            current_price = float(latest["Close"])
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100 if previous_close != 0 else 0.0
            
            quote_data = {
                "ticker": ticker,
                "price": current_price,
                "open": float(latest["Open"]),
                "high": float(latest["High"]),
                "low": float(latest["Low"]),
                "volume": int(latest["Volume"]),
                "previous_close": previous_close,
                "change": change,
                "change_percent": change_percent,
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "eps": info.get("trailingEps"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "dividend_yield": info.get("dividendYield"),
                "timestamp": datetime.now().isoformat()
            }
            
            # 缓存结果
            self._cache_data(cache_key, quote_data)
            
            return quote_data
            
        except Exception as e:
            logger.error(f"Failed to get quote for {ticker}: {e}")
            raise
    
    async def get_historical_prices(
        self, 
        ticker: str, 
        period: str = "1y",
        interval: str = "1d"
    ) -> List[Dict]:
        """获取历史价格数据"""
        try:
            cache_key = f"historical_{ticker}_{period}_{interval}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            stock = self._get_ticker_with_proxy(ticker)
            hist = stock.history(period=period, interval=interval)
            
            if hist.empty:
                raise ValueError(f"No historical data found for ticker {ticker}")
            
            # 转换为字典列表
            historical_data = []
            for date, row in hist.iterrows():
                historical_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                    "ticker": ticker
                })
            
            # 缓存结果
            self._cache_data(cache_key, historical_data)
            
            return historical_data
            
        except Exception as e:
            logger.error(f"Failed to get historical data for {ticker}: {e}")
            raise
    
    async def get_technical_indicators(self, ticker: str) -> Dict[str, Any]:
        """计算技术指标"""
        try:
            cache_key = f"technical_{ticker}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            # 获取历史数据
            stock = self._get_ticker_with_proxy(ticker)
            hist = stock.history(period="6mo")  # 6个月数据用于计算指标
            
            if hist.empty or len(hist) < 50:
                raise ValueError(f"Insufficient data for technical analysis of {ticker}")
            
            close_prices = hist["Close"]
            high_prices = hist["High"]
            low_prices = hist["Low"]
            volume = hist["Volume"]
            
            # 计算各种技术指标
            indicators = {
                "ticker": ticker,
                "timestamp": datetime.now().isoformat(),
                
                # 移动平均线
                "sma_20": float(close_prices.rolling(window=20).mean().iloc[-1]),
                "sma_50": float(close_prices.rolling(window=50).mean().iloc[-1]),
                "ema_12": float(close_prices.ewm(span=12).mean().iloc[-1]),
                "ema_26": float(close_prices.ewm(span=26).mean().iloc[-1]),
                
                # RSI
                "rsi": self._calculate_rsi(close_prices),
                
                # MACD
                "macd": self._calculate_macd(close_prices),
                
                # 布林带
                "bollinger": self._calculate_bollinger_bands(close_prices),
                
                # 成交量指标
                "volume_sma_20": float(volume.rolling(window=20).mean().iloc[-1]),
                "volume_ratio": float(volume.iloc[-1] / volume.rolling(window=20).mean().iloc[-1]),
                
                # 支撑阻力位
                "support_resistance": self._calculate_support_resistance(high_prices, low_prices),
                
                # 波动率
                "volatility": self._calculate_volatility(close_prices),
                
                # 当前价格相对位置
                "price_position": self._calculate_price_position(close_prices, high_prices, low_prices)
            }
            
            # 缓存结果
            self._cache_data(cache_key, indicators)
            
            return indicators
            
        except Exception as e:
            logger.error(f"Failed to calculate technical indicators for {ticker}: {e}")
            raise
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])
    
    def _calculate_macd(self, prices: pd.Series) -> Dict[str, float]:
        """计算MACD指标"""
        ema_12 = prices.ewm(span=12).mean()
        ema_26 = prices.ewm(span=26).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9).mean()
        histogram = macd_line - signal_line
        
        return {
            "macd_line": float(macd_line.iloc[-1]),
            "signal_line": float(signal_line.iloc[-1]),
            "histogram": float(histogram.iloc[-1])
        }
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20) -> Dict[str, float]:
        """计算布林带"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper_band = sma + (std * 2)
        lower_band = sma - (std * 2)
        
        return {
            "upper_band": float(upper_band.iloc[-1]),
            "middle_band": float(sma.iloc[-1]),
            "lower_band": float(lower_band.iloc[-1]),
            "bandwidth": float((upper_band.iloc[-1] - lower_band.iloc[-1]) / sma.iloc[-1] * 100)
        }
    
    def _calculate_support_resistance(self, highs: pd.Series, lows: pd.Series) -> Dict[str, float]:
        """计算支撑阻力位"""
        # 简单的支撑阻力位计算
        recent_highs = highs.tail(20)
        recent_lows = lows.tail(20)
        
        resistance = float(recent_highs.max())
        support = float(recent_lows.min())
        
        return {
            "resistance": resistance,
            "support": support,
            "range_percent": ((resistance - support) / support) * 100
        }
    
    def _calculate_volatility(self, prices: pd.Series, period: int = 20) -> float:
        """计算波动率（年化）"""
        returns = prices.pct_change().dropna()
        volatility = returns.rolling(window=period).std().iloc[-1]
        # 年化波动率
        annualized_volatility = volatility * np.sqrt(252)
        return float(annualized_volatility * 100)
    
    def _calculate_price_position(self, close: pd.Series, high: pd.Series, low: pd.Series, period: int = 52) -> Dict[str, float]:
        """计算价格在一定周期内的相对位置"""
        recent_data = pd.DataFrame({
            "close": close.tail(period),
            "high": high.tail(period),
            "low": low.tail(period)
        })
        
        max_high = recent_data["high"].max()
        min_low = recent_data["low"].min()
        current_price = close.iloc[-1]
        
        position_percent = ((current_price - min_low) / (max_high - min_low)) * 100
        
        return {
            "position_percent": float(position_percent),
            "period_high": float(max_high),
            "period_low": float(min_low),
            "current_price": float(current_price)
        }
    
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