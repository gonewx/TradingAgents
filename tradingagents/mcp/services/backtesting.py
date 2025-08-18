"""
回测服务模块
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import yfinance as yf

logger = logging.getLogger(__name__)

class BacktestingService:
    """回测服务"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 3600  # 1小时缓存
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 检查pandas等依赖是否正常
            return True
        except Exception as e:
            logger.error(f"Backtesting health check failed: {e}")
            return False
    
    async def run_backtest(
        self,
        strategy: Dict[str, Any],
        ticker: str,
        start_date: str,
        end_date: str,
        initial_cash: float = 100000
    ) -> Dict[str, Any]:
        """运行策略回测"""
        try:
            cache_key = f"backtest_{ticker}_{start_date}_{end_date}_{hash(str(strategy))}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            # 获取历史数据
            data = await self._get_price_data(ticker, start_date, end_date)
            if data.empty:
                raise ValueError(f"No price data available for {ticker}")
            
            # 根据策略类型执行回测
            strategy_type = strategy.get("type", "simple_ma")
            
            if strategy_type == "simple_ma":
                result = await self._backtest_simple_ma(data, strategy, initial_cash)
            elif strategy_type == "rsi":
                result = await self._backtest_rsi(data, strategy, initial_cash)
            elif strategy_type == "bollinger":
                result = await self._backtest_bollinger(data, strategy, initial_cash)
            else:
                result = await self._backtest_buy_hold(data, initial_cash)
            
            # 添加基准比较
            benchmark_result = await self._backtest_buy_hold(data, initial_cash)
            result["benchmark"] = {
                "total_return": benchmark_result["total_return"],
                "final_value": benchmark_result["final_value"]
            }
            
            result.update({
                "ticker": ticker,
                "start_date": start_date,
                "end_date": end_date,
                "strategy": strategy,
                "timestamp": datetime.now().isoformat()
            })
            
            # 缓存结果
            self._cache_data(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Backtest failed for {ticker}: {e}")
            raise
    
    async def optimize_parameters(
        self,
        strategy: Dict[str, Any],
        parameters: Dict[str, Any],
        optimization_target: str = "sharpe"
    ) -> Dict[str, Any]:
        """优化策略参数"""
        try:
            ticker = strategy.get("ticker", "AAPL")
            start_date = strategy.get("start_date", "2023-01-01")
            end_date = strategy.get("end_date", "2024-01-01")
            
            best_params = None
            best_score = -float('inf')
            optimization_results = []
            
            # 生成参数组合
            param_combinations = self._generate_param_combinations(parameters)
            
            for params in param_combinations[:20]:  # 限制测试数量
                test_strategy = {**strategy, **params}
                
                try:
                    result = await self.run_backtest(
                        test_strategy, ticker, start_date, end_date
                    )
                    
                    # 计算优化目标得分
                    if optimization_target == "sharpe":
                        score = result.get("sharpe_ratio", 0)
                    elif optimization_target == "return":
                        score = result.get("total_return", 0)
                    elif optimization_target == "max_drawdown":
                        score = -result.get("max_drawdown", 0)  # 负号因为要最小化
                    else:
                        score = result.get("total_return", 0)
                    
                    optimization_results.append({
                        "parameters": params,
                        "score": score,
                        "total_return": result.get("total_return", 0),
                        "sharpe_ratio": result.get("sharpe_ratio", 0),
                        "max_drawdown": result.get("max_drawdown", 0)
                    })
                    
                    if score > best_score:
                        best_score = score
                        best_params = params
                        
                except Exception as e:
                    logger.warning(f"Parameter optimization failed for {params}: {e}")
                    continue
            
            return {
                "best_parameters": best_params,
                "best_score": best_score,
                "optimization_target": optimization_target,
                "all_results": sorted(optimization_results, key=lambda x: x["score"], reverse=True),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Parameter optimization failed: {e}")
            raise
    
    async def _get_price_data(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取价格数据"""
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(start=start_date, end=end_date)
            return data
        except Exception as e:
            logger.error(f"Failed to get price data: {e}")
            return pd.DataFrame()
    
    async def _backtest_simple_ma(
        self, 
        data: pd.DataFrame, 
        strategy: Dict[str, Any], 
        initial_cash: float
    ) -> Dict[str, Any]:
        """简单移动平均策略回测"""
        short_window = strategy.get("short_window", 20)
        long_window = strategy.get("long_window", 50)
        
        # 计算移动平均
        data['MA_short'] = data['Close'].rolling(window=short_window).mean()
        data['MA_long'] = data['Close'].rolling(window=long_window).mean()
        
        # 生成信号
        data['Signal'] = 0
        data.loc[data['MA_short'] > data['MA_long'], 'Signal'] = 1
        data.loc[data['MA_short'] < data['MA_long'], 'Signal'] = -1
        
        # 计算持仓变化
        data['Position'] = data['Signal'].shift(1)
        data['Position'].fillna(0, inplace=True)
        
        # 计算收益
        data['Returns'] = data['Close'].pct_change()
        data['Strategy_Returns'] = data['Position'] * data['Returns']
        
        # 计算累计收益
        data['Cumulative_Returns'] = (1 + data['Strategy_Returns']).cumprod()
        
        return self._calculate_performance_metrics(data, initial_cash)
    
    async def _backtest_rsi(
        self, 
        data: pd.DataFrame, 
        strategy: Dict[str, Any], 
        initial_cash: float
    ) -> Dict[str, Any]:
        """RSI策略回测"""
        rsi_period = strategy.get("rsi_period", 14)
        oversold = strategy.get("oversold", 30)
        overbought = strategy.get("overbought", 70)
        
        # 计算RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        # 生成信号
        data['Signal'] = 0
        data.loc[data['RSI'] < oversold, 'Signal'] = 1  # 买入
        data.loc[data['RSI'] > overbought, 'Signal'] = -1  # 卖出
        
        # 计算持仓
        data['Position'] = data['Signal'].shift(1)
        data['Position'].fillna(0, inplace=True)
        
        # 计算收益
        data['Returns'] = data['Close'].pct_change()
        data['Strategy_Returns'] = data['Position'] * data['Returns']
        data['Cumulative_Returns'] = (1 + data['Strategy_Returns']).cumprod()
        
        return self._calculate_performance_metrics(data, initial_cash)
    
    async def _backtest_bollinger(
        self, 
        data: pd.DataFrame, 
        strategy: Dict[str, Any], 
        initial_cash: float
    ) -> Dict[str, Any]:
        """布林带策略回测"""
        period = strategy.get("period", 20)
        std_dev = strategy.get("std_dev", 2)
        
        # 计算布林带
        data['MA'] = data['Close'].rolling(window=period).mean()
        data['STD'] = data['Close'].rolling(window=period).std()
        data['Upper'] = data['MA'] + (data['STD'] * std_dev)
        data['Lower'] = data['MA'] - (data['STD'] * std_dev)
        
        # 生成信号
        data['Signal'] = 0
        data.loc[data['Close'] < data['Lower'], 'Signal'] = 1  # 买入
        data.loc[data['Close'] > data['Upper'], 'Signal'] = -1  # 卖出
        
        # 计算持仓
        data['Position'] = data['Signal'].shift(1)
        data['Position'].fillna(0, inplace=True)
        
        # 计算收益
        data['Returns'] = data['Close'].pct_change()
        data['Strategy_Returns'] = data['Position'] * data['Returns']
        data['Cumulative_Returns'] = (1 + data['Strategy_Returns']).cumprod()
        
        return self._calculate_performance_metrics(data, initial_cash)
    
    async def _backtest_buy_hold(self, data: pd.DataFrame, initial_cash: float) -> Dict[str, Any]:
        """买入持有策略"""
        data['Returns'] = data['Close'].pct_change()
        data['Strategy_Returns'] = data['Returns']  # 始终持有
        data['Cumulative_Returns'] = (1 + data['Strategy_Returns']).cumprod()
        
        return self._calculate_performance_metrics(data, initial_cash)
    
    def _calculate_performance_metrics(self, data: pd.DataFrame, initial_cash: float) -> Dict[str, Any]:
        """计算性能指标"""
        try:
            # 基本收益指标
            final_value = initial_cash * data['Cumulative_Returns'].iloc[-1]
            total_return = (final_value - initial_cash) / initial_cash * 100
            
            # 年化收益率
            days = len(data)
            years = days / 252  # 假设252个交易日/年
            annualized_return = ((final_value / initial_cash) ** (1/years) - 1) * 100 if years > 0 else 0
            
            # 波动率
            strategy_returns = data['Strategy_Returns'].dropna()
            volatility = strategy_returns.std() * np.sqrt(252) * 100  # 年化波动率
            
            # 夏普比率
            risk_free_rate = 0.02  # 假设无风险利率2%
            excess_return = annualized_return - risk_free_rate * 100
            sharpe_ratio = excess_return / volatility if volatility > 0 else 0
            
            # 最大回撤
            cumulative = data['Cumulative_Returns']
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min() * 100
            
            # 胜率
            winning_trades = (strategy_returns > 0).sum()
            total_trades = len(strategy_returns[strategy_returns != 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # 交易次数（信号变化次数）
            if 'Position' in data.columns:
                trades = (data['Position'].diff() != 0).sum()
            else:
                trades = 0
            
            return {
                "initial_cash": initial_cash,
                "final_value": final_value,
                "total_return": total_return,
                "annualized_return": annualized_return,
                "volatility": volatility,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "win_rate": win_rate,
                "total_trades": trades,
                "trading_days": days
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate performance metrics: {e}")
            return {
                "error": str(e),
                "initial_cash": initial_cash,
                "final_value": initial_cash,
                "total_return": 0
            }
    
    def _generate_param_combinations(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成参数组合"""
        try:
            import itertools
            
            param_names = list(parameters.keys())
            param_values = list(parameters.values())
            
            # 如果参数值是列表，直接使用；否则生成范围
            processed_values = []
            for values in param_values:
                if isinstance(values, list):
                    processed_values.append(values)
                elif isinstance(values, dict) and 'min' in values and 'max' in values:
                    step = values.get('step', 1)
                    processed_values.append(list(range(values['min'], values['max'] + 1, step)))
                else:
                    processed_values.append([values])
            
            combinations = list(itertools.product(*processed_values))
            
            return [
                dict(zip(param_names, combo))
                for combo in combinations
            ]
            
        except Exception as e:
            logger.error(f"Failed to generate parameter combinations: {e}")
            return [{}]
    
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