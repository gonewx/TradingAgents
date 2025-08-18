"""
交易执行服务模块
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class ExecutionBrokerService:
    """交易执行服务"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 60  # 1分钟缓存
        
        # 模拟交易环境
        self.is_paper_trading = True
        self.paper_account = {
            "cash": 100000.0,
            "buying_power": 100000.0,
            "portfolio_value": 100000.0,
            "positions": {},
            "orders": []
        }
        
        # 券商API配置
        self.alpaca_key_id = os.getenv("ALPACA_KEY_ID")
        self.alpaca_secret_key = os.getenv("ALPACA_SECRET_KEY")
        self.alpaca_base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 在模拟环境下总是健康
            if self.is_paper_trading:
                return True
            
            # 实际环境下检查API连接
            return bool(self.alpaca_key_id and self.alpaca_secret_key)
        except Exception as e:
            logger.error(f"Execution broker health check failed: {e}")
            return False
    
    async def place_order(
        self,
        ticker: str,
        quantity: int,
        side: str,  # 'buy' or 'sell'
        order_type: str = "market",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """下单"""
        try:
            # 验证参数
            if side not in ["buy", "sell"]:
                raise ValueError("Side must be 'buy' or 'sell'")
            
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
            
            if order_type not in ["market", "limit", "stop", "stop_limit"]:
                raise ValueError("Invalid order type")
            
            # 获取当前价格
            current_price = await self._get_current_price(ticker)
            if current_price is None:
                raise ValueError(f"Unable to get current price for {ticker}")
            
            if self.is_paper_trading:
                return await self._place_paper_order(
                    ticker, quantity, side, order_type, 
                    limit_price, stop_price, current_price
                )
            else:
                return await self._place_real_order(
                    ticker, quantity, side, order_type, 
                    limit_price, stop_price
                )
                
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return {
                "error": str(e),
                "ticker": ticker,
                "status": "failed"
            }
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """获取持仓"""
        try:
            if self.is_paper_trading:
                return await self._get_paper_positions()
            else:
                return await self._get_real_positions()
                
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return [{"error": str(e)}]
    
    async def get_account_info(self) -> Dict[str, Any]:
        """获取账户信息"""
        try:
            if self.is_paper_trading:
                return await self._get_paper_account_info()
            else:
                return await self._get_real_account_info()
                
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return {"error": str(e)}
    
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """获取订单状态"""
        try:
            if self.is_paper_trading:
                return await self._get_paper_order_status(order_id)
            else:
                return await self._get_real_order_status(order_id)
                
        except Exception as e:
            logger.error(f"Failed to get order status: {e}")
            return {"error": str(e), "order_id": order_id}
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """取消订单"""
        try:
            if self.is_paper_trading:
                return await self._cancel_paper_order(order_id)
            else:
                return await self._cancel_real_order(order_id)
                
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return {"error": str(e), "order_id": order_id}
    
    async def _place_paper_order(
        self,
        ticker: str,
        quantity: int,
        side: str,
        order_type: str,
        limit_price: Optional[float],
        stop_price: Optional[float],
        current_price: float
    ) -> Dict[str, Any]:
        """模拟下单"""
        
        # 生成订单ID
        order_id = f"paper_{len(self.paper_account['orders'])}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 计算订单价值
        if order_type == "market":
            execution_price = current_price
        elif order_type == "limit":
            execution_price = limit_price or current_price
        else:
            execution_price = current_price
        
        order_value = quantity * execution_price
        
        # 检查资金充足性
        if side == "buy":
            if order_value > self.paper_account["cash"]:
                return {
                    "error": "Insufficient funds",
                    "required": order_value,
                    "available": self.paper_account["cash"],
                    "status": "rejected"
                }
            
            # 扣减现金
            self.paper_account["cash"] -= order_value
            
            # 更新或创建持仓
            if ticker in self.paper_account["positions"]:
                current_pos = self.paper_account["positions"][ticker]
                new_quantity = current_pos["quantity"] + quantity
                new_avg_price = (
                    (current_pos["quantity"] * current_pos["avg_price"] + 
                     quantity * execution_price) / new_quantity
                )
                self.paper_account["positions"][ticker] = {
                    "quantity": new_quantity,
                    "avg_price": new_avg_price,
                    "market_value": new_quantity * current_price,
                    "unrealized_pl": new_quantity * (current_price - new_avg_price)
                }
            else:
                self.paper_account["positions"][ticker] = {
                    "quantity": quantity,
                    "avg_price": execution_price,
                    "market_value": quantity * current_price,
                    "unrealized_pl": quantity * (current_price - execution_price)
                }
        
        else:  # sell
            if ticker not in self.paper_account["positions"]:
                return {
                    "error": f"No position in {ticker} to sell",
                    "status": "rejected"
                }
            
            current_pos = self.paper_account["positions"][ticker]
            if current_pos["quantity"] < quantity:
                return {
                    "error": f"Insufficient shares, have {current_pos['quantity']}, trying to sell {quantity}",
                    "status": "rejected"
                }
            
            # 增加现金
            self.paper_account["cash"] += order_value
            
            # 更新持仓
            remaining_quantity = current_pos["quantity"] - quantity
            if remaining_quantity == 0:
                del self.paper_account["positions"][ticker]
            else:
                self.paper_account["positions"][ticker]["quantity"] = remaining_quantity
                self.paper_account["positions"][ticker]["market_value"] = remaining_quantity * current_price
                self.paper_account["positions"][ticker]["unrealized_pl"] = remaining_quantity * (current_price - current_pos["avg_price"])
        
        # 记录订单
        order_record = {
            "id": order_id,
            "ticker": ticker,
            "quantity": quantity,
            "side": side,
            "order_type": order_type,
            "limit_price": limit_price,
            "stop_price": stop_price,
            "execution_price": execution_price,
            "status": "filled",
            "filled_quantity": quantity,
            "timestamp": datetime.now().isoformat()
        }
        
        self.paper_account["orders"].append(order_record)
        
        # 更新组合价值
        await self._update_portfolio_value()
        
        return {
            "order_id": order_id,
            "status": "filled",
            "filled_quantity": quantity,
            "filled_price": execution_price,
            "ticker": ticker,
            "side": side,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _get_paper_positions(self) -> List[Dict[str, Any]]:
        """获取模拟持仓"""
        positions = []
        
        for ticker, position in self.paper_account["positions"].items():
            # 更新市场价值
            current_price = await self._get_current_price(ticker)
            if current_price:
                market_value = position["quantity"] * current_price
                unrealized_pl = position["quantity"] * (current_price - position["avg_price"])
                unrealized_plpc = (unrealized_pl / (position["quantity"] * position["avg_price"])) * 100
                
                positions.append({
                    "ticker": ticker,
                    "quantity": position["quantity"],
                    "avg_price": position["avg_price"],
                    "current_price": current_price,
                    "market_value": market_value,
                    "unrealized_pl": unrealized_pl,
                    "unrealized_plpc": unrealized_plpc
                })
        
        return positions
    
    async def _get_paper_account_info(self) -> Dict[str, Any]:
        """获取模拟账户信息"""
        await self._update_portfolio_value()
        
        return {
            "cash": self.paper_account["cash"],
            "buying_power": self.paper_account["buying_power"],
            "portfolio_value": self.paper_account["portfolio_value"],
            "equity": self.paper_account["portfolio_value"],
            "day_trade_count": 0,
            "pattern_day_trader": False,
            "trading_blocked": False,
            "account_type": "paper",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _get_paper_order_status(self, order_id: str) -> Dict[str, Any]:
        """获取模拟订单状态"""
        for order in self.paper_account["orders"]:
            if order["id"] == order_id:
                return order
        
        return {"error": f"Order {order_id} not found"}
    
    async def _cancel_paper_order(self, order_id: str) -> Dict[str, Any]:
        """取消模拟订单"""
        for order in self.paper_account["orders"]:
            if order["id"] == order_id:
                if order["status"] == "filled":
                    return {"error": "Cannot cancel filled order", "order_id": order_id}
                
                order["status"] = "cancelled"
                return {"message": "Order cancelled", "order_id": order_id}
        
        return {"error": f"Order {order_id} not found"}
    
    async def _place_real_order(self, *args, **kwargs) -> Dict[str, Any]:
        """真实下单（需要实现Alpaca API）"""
        # 这里应该实现真实的Alpaca API调用
        return {"error": "Real trading not implemented yet"}
    
    async def _get_real_positions(self) -> List[Dict[str, Any]]:
        """获取真实持仓"""
        return [{"error": "Real trading not implemented yet"}]
    
    async def _get_real_account_info(self) -> Dict[str, Any]:
        """获取真实账户信息"""
        return {"error": "Real trading not implemented yet"}
    
    async def _get_real_order_status(self, order_id: str) -> Dict[str, Any]:
        """获取真实订单状态"""
        return {"error": "Real trading not implemented yet"}
    
    async def _cancel_real_order(self, order_id: str) -> Dict[str, Any]:
        """取消真实订单"""
        return {"error": "Real trading not implemented yet"}
    
    async def _get_current_price(self, ticker: str) -> Optional[float]:
        """获取当前价格"""
        try:
            import yfinance as yf
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")
            if not hist.empty:
                return float(hist["Close"].iloc[-1])
            return None
        except Exception as e:
            logger.warning(f"Failed to get current price for {ticker}: {e}")
            return None
    
    async def _update_portfolio_value(self):
        """更新组合价值"""
        try:
            total_market_value = 0
            
            for ticker, position in self.paper_account["positions"].items():
                current_price = await self._get_current_price(ticker)
                if current_price:
                    market_value = position["quantity"] * current_price
                    total_market_value += market_value
                    
                    # 更新持仓的市场价值
                    self.paper_account["positions"][ticker]["market_value"] = market_value
                    self.paper_account["positions"][ticker]["unrealized_pl"] = position["quantity"] * (current_price - position["avg_price"])
            
            self.paper_account["portfolio_value"] = self.paper_account["cash"] + total_market_value
            self.paper_account["buying_power"] = self.paper_account["cash"]  # 简化处理
            
        except Exception as e:
            logger.error(f"Failed to update portfolio value: {e}")
    
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