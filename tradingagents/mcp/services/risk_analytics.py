"""
风险分析服务模块
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import yfinance as yf
from scipy import stats

logger = logging.getLogger(__name__)

class RiskAnalyticsService:
    """风险分析服务"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 1800  # 30分钟缓存
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 检查必要的库是否可用
            return True
        except Exception as e:
            logger.error(f"Risk analytics health check failed: {e}")
            return False
    
    async def calculate_var(
        self,
        portfolio: Dict[str, Any],
        confidence_level: float = 0.95,
        time_horizon: int = 1
    ) -> Dict[str, Any]:
        """计算VaR（在险价值）"""
        try:
            cache_key = f"var_{hash(str(portfolio))}_{confidence_level}_{time_horizon}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            # 获取组合收益率
            returns = await self._get_portfolio_returns(portfolio)
            if returns is None or len(returns) == 0:
                raise ValueError("Unable to calculate portfolio returns")
            
            portfolio_value = portfolio.get("total_value", 100000)
            
            # 计算不同方法的VaR
            var_results = {
                "portfolio_value": portfolio_value,
                "confidence_level": confidence_level,
                "time_horizon": time_horizon,
                "timestamp": datetime.now().isoformat()
            }
            
            # 1. 历史模拟法
            if len(returns) > 0:
                var_historical = np.percentile(returns, (1 - confidence_level) * 100)
                var_results["var_historical"] = {
                    "daily_var": float(var_historical),
                    "dollar_var": float(var_historical * portfolio_value),
                    "scaled_var": float(var_historical * np.sqrt(time_horizon) * portfolio_value)
                }
            
            # 2. 参数法（正态分布假设）
            if len(returns) > 1:
                mean_return = np.mean(returns)
                std_return = np.std(returns)
                z_score = stats.norm.ppf(1 - confidence_level)
                
                var_parametric = mean_return + z_score * std_return
                var_results["var_parametric"] = {
                    "daily_var": float(var_parametric),
                    "dollar_var": float(var_parametric * portfolio_value),
                    "scaled_var": float(var_parametric * np.sqrt(time_horizon) * portfolio_value)
                }
            
            # 3. 蒙特卡洛模拟（简化版）
            if len(returns) > 1:
                var_monte_carlo = await self._monte_carlo_var(
                    returns, confidence_level, time_horizon, portfolio_value
                )
                var_results["var_monte_carlo"] = var_monte_carlo
            
            # 4. 条件VaR (CVaR/Expected Shortfall)
            if len(returns) > 0:
                var_threshold = np.percentile(returns, (1 - confidence_level) * 100)
                tail_losses = returns[returns <= var_threshold]
                cvar = np.mean(tail_losses) if len(tail_losses) > 0 else var_threshold
                
                var_results["cvar"] = {
                    "daily_cvar": float(cvar),
                    "dollar_cvar": float(cvar * portfolio_value),
                    "scaled_cvar": float(cvar * np.sqrt(time_horizon) * portfolio_value)
                }
            
            # 5. 最大回撤
            cumulative_returns = (1 + pd.Series(returns)).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = drawdown.min()
            
            var_results["max_drawdown"] = {
                "max_drawdown_pct": float(max_drawdown * 100),
                "max_drawdown_dollar": float(max_drawdown * portfolio_value)
            }
            
            # 缓存结果
            self._cache_data(cache_key, var_results)
            
            return var_results
            
        except Exception as e:
            logger.error(f"Failed to calculate VaR: {e}")
            raise
    
    async def run_stress_test(
        self,
        portfolio: Dict[str, Any],
        scenarios: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """运行压力测试"""
        try:
            if scenarios is None:
                scenarios = self._get_default_scenarios()
            
            portfolio_value = portfolio.get("total_value", 100000)
            holdings = portfolio.get("holdings", {})
            
            stress_results = {
                "portfolio_value": portfolio_value,
                "scenarios": {},
                "timestamp": datetime.now().isoformat()
            }
            
            for scenario in scenarios:
                scenario_name = scenario["name"]
                scenario_impacts = scenario["impacts"]
                
                scenario_result = {
                    "description": scenario.get("description", ""),
                    "total_loss": 0,
                    "loss_percentage": 0,
                    "affected_positions": {}
                }
                
                total_scenario_loss = 0
                
                for ticker, position in holdings.items():
                    position_value = position.get("market_value", 0)
                    
                    # 查找这个股票的压力影响
                    ticker_impact = 0
                    for impact in scenario_impacts:
                        if impact.get("asset") == ticker or impact.get("asset") == "all":
                            ticker_impact = impact.get("price_change", 0)
                            break
                    
                    if ticker_impact != 0:
                        position_loss = position_value * (ticker_impact / 100)
                        total_scenario_loss += position_loss
                        
                        scenario_result["affected_positions"][ticker] = {
                            "current_value": position_value,
                            "impact_percent": ticker_impact,
                            "loss_amount": position_loss
                        }
                
                scenario_result["total_loss"] = total_scenario_loss
                scenario_result["loss_percentage"] = (total_scenario_loss / portfolio_value) * 100
                
                stress_results["scenarios"][scenario_name] = scenario_result
            
            return stress_results
            
        except Exception as e:
            logger.error(f"Failed to run stress test: {e}")
            raise
    
    async def portfolio_optimization(
        self,
        tickers: List[str],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """组合优化"""
        try:
            cache_key = f"optimization_{hash(str(tickers))}_{hash(str(constraints))}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            # 获取历史价格数据
            price_data = await self._get_price_matrix(tickers)
            if price_data.empty:
                raise ValueError("Unable to get price data for optimization")
            
            # 计算收益率
            returns = price_data.pct_change().dropna()
            
            # 计算预期收益和协方差矩阵
            mean_returns = returns.mean() * 252  # 年化
            cov_matrix = returns.cov() * 252  # 年化
            
            # 简化的均值方差优化
            num_assets = len(tickers)
            
            # 等权重作为起始点
            equal_weights = np.array([1.0 / num_assets] * num_assets)
            
            # 最小方差组合
            inv_cov = np.linalg.pinv(cov_matrix.values)
            ones = np.ones((num_assets, 1))
            min_var_weights = (inv_cov @ ones) / (ones.T @ inv_cov @ ones)
            min_var_weights = min_var_weights.flatten()
            
            # 最大夏普比率组合（简化计算）
            risk_free_rate = 0.02
            excess_returns = mean_returns - risk_free_rate
            
            try:
                sharpe_weights = inv_cov @ excess_returns.values
                sharpe_weights = sharpe_weights / np.sum(sharpe_weights)
            except:
                sharpe_weights = equal_weights
            
            # 计算组合指标
            optimization_results = {
                "tickers": tickers,
                "timestamp": datetime.now().isoformat(),
                "portfolios": {}
            }
            
            # 等权重组合
            equal_return = np.sum(equal_weights * mean_returns)
            equal_risk = np.sqrt(equal_weights.T @ cov_matrix.values @ equal_weights)
            equal_sharpe = (equal_return - risk_free_rate) / equal_risk if equal_risk > 0 else 0
            
            optimization_results["portfolios"]["equal_weight"] = {
                "weights": dict(zip(tickers, equal_weights.tolist())),
                "expected_return": float(equal_return * 100),
                "volatility": float(equal_risk * 100),
                "sharpe_ratio": float(equal_sharpe)
            }
            
            # 最小方差组合
            min_var_return = np.sum(min_var_weights * mean_returns)
            min_var_risk = np.sqrt(min_var_weights.T @ cov_matrix.values @ min_var_weights)
            min_var_sharpe = (min_var_return - risk_free_rate) / min_var_risk if min_var_risk > 0 else 0
            
            optimization_results["portfolios"]["min_variance"] = {
                "weights": dict(zip(tickers, min_var_weights.tolist())),
                "expected_return": float(min_var_return * 100),
                "volatility": float(min_var_risk * 100),
                "sharpe_ratio": float(min_var_sharpe)
            }
            
            # 最大夏普比率组合
            max_sharpe_return = np.sum(sharpe_weights * mean_returns)
            max_sharpe_risk = np.sqrt(sharpe_weights.T @ cov_matrix.values @ sharpe_weights)
            max_sharpe_sharpe = (max_sharpe_return - risk_free_rate) / max_sharpe_risk if max_sharpe_risk > 0 else 0
            
            optimization_results["portfolios"]["max_sharpe"] = {
                "weights": dict(zip(tickers, sharpe_weights.tolist())),
                "expected_return": float(max_sharpe_return * 100),
                "volatility": float(max_sharpe_risk * 100),
                "sharpe_ratio": float(max_sharpe_sharpe)
            }
            
            # 相关性矩阵
            correlation_matrix = returns.corr()
            optimization_results["correlation_matrix"] = correlation_matrix.round(3).to_dict()
            
            # 缓存结果
            self._cache_data(cache_key, optimization_results)
            
            return optimization_results
            
        except Exception as e:
            logger.error(f"Failed to optimize portfolio: {e}")
            raise
    
    async def _get_portfolio_returns(self, portfolio: Dict[str, Any]) -> np.ndarray:
        """获取组合收益率"""
        try:
            holdings = portfolio.get("holdings", {})
            if not holdings:
                return np.array([])
            
            # 获取所有股票的价格数据
            tickers = list(holdings.keys())
            price_data = await self._get_price_matrix(tickers, period="1y")
            
            if price_data.empty:
                return np.array([])
            
            # 计算收益率
            returns_data = price_data.pct_change().dropna()
            
            # 计算权重
            total_value = sum(holding.get("market_value", 0) for holding in holdings.values())
            if total_value == 0:
                return np.array([])
            
            weights = []
            for ticker in tickers:
                weight = holdings[ticker].get("market_value", 0) / total_value
                weights.append(weight)
            
            weights = np.array(weights)
            
            # 计算组合收益率
            portfolio_returns = (returns_data * weights).sum(axis=1)
            
            return portfolio_returns.values
            
        except Exception as e:
            logger.error(f"Failed to get portfolio returns: {e}")
            return np.array([])
    
    async def _get_price_matrix(self, tickers: List[str], period: str = "1y") -> pd.DataFrame:
        """获取价格矩阵"""
        try:
            price_data = {}
            
            for ticker in tickers:
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period=period)
                    if not hist.empty:
                        price_data[ticker] = hist["Close"]
                except Exception as e:
                    logger.warning(f"Failed to get data for {ticker}: {e}")
                    continue
            
            if not price_data:
                return pd.DataFrame()
            
            return pd.DataFrame(price_data).dropna()
            
        except Exception as e:
            logger.error(f"Failed to get price matrix: {e}")
            return pd.DataFrame()
    
    async def _monte_carlo_var(
        self,
        returns: np.ndarray,
        confidence_level: float,
        time_horizon: int,
        portfolio_value: float,
        num_simulations: int = 1000
    ) -> Dict[str, float]:
        """蒙特卡洛VaR计算"""
        try:
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            
            # 生成随机收益率
            simulated_returns = np.random.normal(
                mean_return, std_return, 
                (num_simulations, time_horizon)
            )
            
            # 计算期末组合价值
            portfolio_values = portfolio_value * np.prod(1 + simulated_returns, axis=1)
            
            # 计算收益率
            portfolio_returns = (portfolio_values / portfolio_value) - 1
            
            # 计算VaR
            var_mc = np.percentile(portfolio_returns, (1 - confidence_level) * 100)
            
            return {
                "daily_var": float(var_mc / time_horizon),
                "dollar_var": float(var_mc * portfolio_value),
                "scaled_var": float(var_mc * portfolio_value),
                "num_simulations": num_simulations
            }
            
        except Exception as e:
            logger.error(f"Monte Carlo VaR calculation failed: {e}")
            return {
                "daily_var": 0.0,
                "dollar_var": 0.0,
                "scaled_var": 0.0,
                "num_simulations": 0
            }
    
    def _get_default_scenarios(self) -> List[Dict[str, Any]]:
        """获取默认压力测试情景"""
        return [
            {
                "name": "market_crash",
                "description": "Market crash scenario (-20% across all assets)",
                "impacts": [
                    {"asset": "all", "price_change": -20}
                ]
            },
            {
                "name": "tech_selloff",
                "description": "Technology sector selloff",
                "impacts": [
                    {"asset": "AAPL", "price_change": -25},
                    {"asset": "GOOGL", "price_change": -25},
                    {"asset": "MSFT", "price_change": -25},
                    {"asset": "NVDA", "price_change": -30},
                    {"asset": "TSLA", "price_change": -35}
                ]
            },
            {
                "name": "interest_rate_shock",
                "description": "Sudden interest rate increase",
                "impacts": [
                    {"asset": "all", "price_change": -15}
                ]
            },
            {
                "name": "recession",
                "description": "Economic recession scenario",
                "impacts": [
                    {"asset": "all", "price_change": -30}
                ]
            },
            {
                "name": "volatility_spike",
                "description": "High volatility environment",
                "impacts": [
                    {"asset": "all", "price_change": -10}
                ]
            }
        ]
    
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