"""
财务数据服务模块
"""

import os
import yfinance as yf
import pandas as pd
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

class FinancialDataService:
    """财务数据服务"""
    
    def __init__(self):
        self.cache = {}
        # 从环境变量读取数据缓存超时，财务数据变化较慢，默认1小时
        self.cache_timeout = int(os.getenv('DATA_CACHE_TTL', '3600'))
        
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 尝试获取财务数据
            stock = yf.Ticker("AAPL")
            financials = stock.financials
            return not financials.empty
        except Exception as e:
            logger.error(f"Financial data health check failed: {e}")
            return False
    
    async def get_income_statement(
        self, 
        ticker: str, 
        period: str = "annual"
    ) -> Dict[str, Any]:
        """获取损益表"""
        try:
            cache_key = f"income_{ticker}_{period}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            stock = yf.Ticker(ticker)
            
            if period == "annual":
                financials = stock.financials
            else:
                financials = stock.quarterly_financials
            
            if financials.empty:
                raise ValueError(f"No financial data found for {ticker}")
            
            # 获取最新年度/季度数据
            latest_data = financials.iloc[:, 0]  # 最新一列
            
            income_statement = {
                "ticker": ticker,
                "period": period,
                "date": latest_data.name.strftime("%Y-%m-%d") if hasattr(latest_data.name, 'strftime') else str(latest_data.name),
                "timestamp": datetime.now().isoformat(),
                
                # 收入项目
                "total_revenue": self._safe_get(latest_data, "Total Revenue"),
                "operating_revenue": self._safe_get(latest_data, "Operating Revenue"),
                "cost_of_revenue": self._safe_get(latest_data, "Cost Of Revenue"),
                "gross_profit": self._safe_get(latest_data, "Gross Profit"),
                
                # 费用项目
                "operating_expense": self._safe_get(latest_data, "Operating Expense"),
                "selling_general_administrative": self._safe_get(latest_data, "Selling General Administrative"),
                "research_development": self._safe_get(latest_data, "Research Development"),
                
                # 利润项目
                "operating_income": self._safe_get(latest_data, "Operating Income"),
                "ebit": self._safe_get(latest_data, "EBIT"),
                "ebitda": self._safe_get(latest_data, "EBITDA"),
                "interest_expense": self._safe_get(latest_data, "Interest Expense"),
                "pretax_income": self._safe_get(latest_data, "Pretax Income"),
                "tax_provision": self._safe_get(latest_data, "Tax Provision"),
                "net_income": self._safe_get(latest_data, "Net Income"),
                
                # 每股数据
                "basic_eps": self._safe_get(latest_data, "Basic EPS"),
                "diluted_eps": self._safe_get(latest_data, "Diluted EPS"),
                "basic_average_shares": self._safe_get(latest_data, "Basic Average Shares"),
                "diluted_average_shares": self._safe_get(latest_data, "Diluted Average Shares"),
            }
            
            # 计算利润率
            total_revenue = income_statement.get("total_revenue", 0)
            if total_revenue and total_revenue > 0:
                income_statement.update({
                    "gross_margin": (income_statement.get("gross_profit", 0) / total_revenue) * 100,
                    "operating_margin": (income_statement.get("operating_income", 0) / total_revenue) * 100,
                    "net_margin": (income_statement.get("net_income", 0) / total_revenue) * 100,
                })
            
            # 缓存结果
            self._cache_data(cache_key, income_statement)
            
            return income_statement
            
        except Exception as e:
            logger.error(f"Failed to get income statement for {ticker}: {e}")
            raise
    
    async def get_balance_sheet(
        self, 
        ticker: str, 
        period: str = "annual"
    ) -> Dict[str, Any]:
        """获取资产负债表"""
        try:
            cache_key = f"balance_{ticker}_{period}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            stock = yf.Ticker(ticker)
            
            if period == "annual":
                balance_sheet = stock.balance_sheet
            else:
                balance_sheet = stock.quarterly_balance_sheet
            
            if balance_sheet.empty:
                raise ValueError(f"No balance sheet data found for {ticker}")
            
            # 获取最新数据
            latest_data = balance_sheet.iloc[:, 0]
            
            balance_data = {
                "ticker": ticker,
                "period": period,
                "date": latest_data.name.strftime("%Y-%m-%d") if hasattr(latest_data.name, 'strftime') else str(latest_data.name),
                "timestamp": datetime.now().isoformat(),
                
                # 资产
                "total_assets": self._safe_get(latest_data, "Total Assets"),
                "current_assets": self._safe_get(latest_data, "Current Assets"),
                "cash_and_equivalents": self._safe_get(latest_data, "Cash And Cash Equivalents"),
                "short_term_investments": self._safe_get(latest_data, "Other Short Term Investments"),
                "accounts_receivable": self._safe_get(latest_data, "Accounts Receivable"),
                "inventory": self._safe_get(latest_data, "Inventory"),
                "ppe_net": self._safe_get(latest_data, "Properties Plants And Equipment Net"),
                "goodwill": self._safe_get(latest_data, "Goodwill"),
                "intangible_assets": self._safe_get(latest_data, "Other Intangible Assets"),
                
                # 负债
                "total_liabilities": self._safe_get(latest_data, "Total Liabilities Net Minority Interest"),
                "current_liabilities": self._safe_get(latest_data, "Current Liabilities"),
                "accounts_payable": self._safe_get(latest_data, "Accounts Payable"),
                "short_term_debt": self._safe_get(latest_data, "Current Debt"),
                "long_term_debt": self._safe_get(latest_data, "Long Term Debt"),
                "total_debt": self._safe_get(latest_data, "Total Debt"),
                
                # 股东权益
                "total_equity": self._safe_get(latest_data, "Total Equity Gross Minority Interest"),
                "retained_earnings": self._safe_get(latest_data, "Retained Earnings"),
                "common_stock": self._safe_get(latest_data, "Common Stock"),
                "treasury_shares": self._safe_get(latest_data, "Treasury Shares Number"),
            }
            
            # 计算流动比率等指标
            current_assets = balance_data.get("current_assets", 0)
            current_liabilities = balance_data.get("current_liabilities", 0)
            total_assets = balance_data.get("total_assets", 0)
            total_equity = balance_data.get("total_equity", 0)
            total_debt = balance_data.get("total_debt", 0)
            
            if current_liabilities and current_liabilities > 0:
                balance_data["current_ratio"] = current_assets / current_liabilities
            
            if total_equity and total_equity > 0:
                balance_data["debt_to_equity"] = total_debt / total_equity if total_debt else 0
            
            if total_assets and total_assets > 0:
                balance_data["asset_turnover"] = total_assets  # 需要收入数据计算
                balance_data["equity_ratio"] = total_equity / total_assets
            
            # 缓存结果
            self._cache_data(cache_key, balance_data)
            
            return balance_data
            
        except Exception as e:
            logger.error(f"Failed to get balance sheet for {ticker}: {e}")
            raise
    
    async def get_cash_flow(
        self, 
        ticker: str, 
        period: str = "annual"
    ) -> Dict[str, Any]:
        """获取现金流量表"""
        try:
            cache_key = f"cashflow_{ticker}_{period}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            stock = yf.Ticker(ticker)
            
            if period == "annual":
                cashflow = stock.cashflow
            else:
                cashflow = stock.quarterly_cashflow
            
            if cashflow.empty:
                raise ValueError(f"No cash flow data found for {ticker}")
            
            # 获取最新数据
            latest_data = cashflow.iloc[:, 0]
            
            cashflow_data = {
                "ticker": ticker,
                "period": period,
                "date": latest_data.name.strftime("%Y-%m-%d") if hasattr(latest_data.name, 'strftime') else str(latest_data.name),
                "timestamp": datetime.now().isoformat(),
                
                # 经营活动现金流
                "operating_cash_flow": self._safe_get(latest_data, "Operating Cash Flow"),
                "net_income": self._safe_get(latest_data, "Net Income"),
                "depreciation": self._safe_get(latest_data, "Depreciation"),
                "change_working_capital": self._safe_get(latest_data, "Change In Working Capital"),
                
                # 投资活动现金流
                "investing_cash_flow": self._safe_get(latest_data, "Investing Cash Flow"),
                "capex": self._safe_get(latest_data, "Capital Expenditure"),
                "acquisitions": self._safe_get(latest_data, "Acquisitions Net"),
                "investments": self._safe_get(latest_data, "Purchase Of Investment"),
                
                # 筹资活动现金流
                "financing_cash_flow": self._safe_get(latest_data, "Financing Cash Flow"),
                "dividend_paid": self._safe_get(latest_data, "Cash Dividends Paid"),
                "stock_repurchase": self._safe_get(latest_data, "Repurchase Of Capital Stock"),
                "debt_issued": self._safe_get(latest_data, "Long Term Debt Issuance"),
                
                # 自由现金流
                "free_cash_flow": self._calculate_free_cash_flow(latest_data),
            }
            
            # 缓存结果
            self._cache_data(cache_key, cashflow_data)
            
            return cashflow_data
            
        except Exception as e:
            logger.error(f"Failed to get cash flow for {ticker}: {e}")
            raise
    
    async def get_financial_ratios(self, ticker: str) -> Dict[str, Any]:
        """计算财务比率"""
        try:
            cache_key = f"ratios_{ticker}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            # 获取各种财务数据
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 获取财务报表数据
            income_data = await self.get_income_statement(ticker)
            balance_data = await self.get_balance_sheet(ticker)
            cashflow_data = await self.get_cash_flow(ticker)
            
            # 计算各种财务比率
            ratios = {
                "ticker": ticker,
                "timestamp": datetime.now().isoformat(),
                
                # 盈利能力比率
                "roe": self._calculate_roe(income_data, balance_data),
                "roa": self._calculate_roa(income_data, balance_data),
                "roic": self._calculate_roic(income_data, balance_data),
                "gross_margin": income_data.get("gross_margin", 0),
                "operating_margin": income_data.get("operating_margin", 0),
                "net_margin": income_data.get("net_margin", 0),
                
                # 流动性比率
                "current_ratio": balance_data.get("current_ratio", 0),
                "quick_ratio": self._calculate_quick_ratio(balance_data),
                "cash_ratio": self._calculate_cash_ratio(balance_data),
                
                # 杠杆比率
                "debt_to_equity": balance_data.get("debt_to_equity", 0),
                "debt_to_assets": self._calculate_debt_to_assets(balance_data),
                "equity_multiplier": self._calculate_equity_multiplier(balance_data),
                "interest_coverage": self._calculate_interest_coverage(income_data),
                
                # 效率比率
                "asset_turnover": self._calculate_asset_turnover(income_data, balance_data),
                "inventory_turnover": self._calculate_inventory_turnover(income_data, balance_data),
                "receivables_turnover": self._calculate_receivables_turnover(income_data, balance_data),
                
                # 市场比率
                "pe_ratio": info.get("trailingPE"),
                "pb_ratio": info.get("priceToBook"),
                "ps_ratio": info.get("priceToSalesTrailing12Months"),
                "peg_ratio": info.get("pegRatio"),
                "dividend_yield": info.get("dividendYield"),
                
                # 现金流比率
                "operating_cash_flow_ratio": self._calculate_ocf_ratio(cashflow_data, balance_data),
                "free_cash_flow_yield": self._calculate_fcf_yield(cashflow_data, info),
                "cash_conversion_cycle": self._calculate_cash_conversion_cycle(income_data, balance_data),
            }
            
            # 缓存结果
            self._cache_data(cache_key, ratios)
            
            return ratios
            
        except Exception as e:
            logger.error(f"Failed to calculate financial ratios for {ticker}: {e}")
            raise
    
    def _safe_get(self, data: pd.Series, key: str, default: Optional[float] = None) -> Optional[float]:
        """安全获取数据，处理缺失值"""
        try:
            value = data.get(key, default)
            if pd.isna(value):
                return default
            return float(value) if value is not None else default
        except (TypeError, ValueError):
            return default
    
    def _calculate_free_cash_flow(self, cashflow_data: pd.Series) -> Optional[float]:
        """计算自由现金流"""
        ocf = self._safe_get(cashflow_data, "Operating Cash Flow", 0)
        capex = self._safe_get(cashflow_data, "Capital Expenditure", 0)
        return ocf - abs(capex) if ocf and capex else None
    
    def _calculate_roe(self, income_data: Dict, balance_data: Dict) -> Optional[float]:
        """计算ROE"""
        net_income = income_data.get("net_income", 0)
        total_equity = balance_data.get("total_equity", 0)
        return (net_income / total_equity) * 100 if net_income and total_equity else None
    
    def _calculate_roa(self, income_data: Dict, balance_data: Dict) -> Optional[float]:
        """计算ROA"""
        net_income = income_data.get("net_income", 0)
        total_assets = balance_data.get("total_assets", 0)
        return (net_income / total_assets) * 100 if net_income and total_assets else None
    
    def _calculate_roic(self, income_data: Dict, balance_data: Dict) -> Optional[float]:
        """计算ROIC"""
        operating_income = income_data.get("operating_income", 0)
        total_assets = balance_data.get("total_assets", 0)
        current_liabilities = balance_data.get("current_liabilities", 0)
        
        if operating_income and total_assets and current_liabilities:
            invested_capital = total_assets - current_liabilities
            return (operating_income / invested_capital) * 100
        return None
    
    def _calculate_quick_ratio(self, balance_data: Dict) -> Optional[float]:
        """计算速动比率"""
        current_assets = balance_data.get("current_assets", 0)
        inventory = balance_data.get("inventory", 0)
        current_liabilities = balance_data.get("current_liabilities", 0)
        
        if current_assets and current_liabilities:
            quick_assets = current_assets - (inventory or 0)
            return quick_assets / current_liabilities
        return None
    
    def _calculate_cash_ratio(self, balance_data: Dict) -> Optional[float]:
        """计算现金比率"""
        cash = balance_data.get("cash_and_equivalents", 0)
        short_term_inv = balance_data.get("short_term_investments", 0)
        current_liabilities = balance_data.get("current_liabilities", 0)
        
        if current_liabilities:
            cash_equivalents = (cash or 0) + (short_term_inv or 0)
            return cash_equivalents / current_liabilities
        return None
    
    def _calculate_debt_to_assets(self, balance_data: Dict) -> Optional[float]:
        """计算资产负债率"""
        total_debt = balance_data.get("total_debt", 0)
        total_assets = balance_data.get("total_assets", 0)
        return (total_debt / total_assets) * 100 if total_debt and total_assets else None
    
    def _calculate_equity_multiplier(self, balance_data: Dict) -> Optional[float]:
        """计算权益乘数"""
        total_assets = balance_data.get("total_assets", 0)
        total_equity = balance_data.get("total_equity", 0)
        return total_assets / total_equity if total_assets and total_equity else None
    
    def _calculate_interest_coverage(self, income_data: Dict) -> Optional[float]:
        """计算利息保障倍数"""
        operating_income = income_data.get("operating_income", 0)
        interest_expense = income_data.get("interest_expense", 0)
        return operating_income / interest_expense if operating_income and interest_expense else None
    
    def _calculate_asset_turnover(self, income_data: Dict, balance_data: Dict) -> Optional[float]:
        """计算资产周转率"""
        total_revenue = income_data.get("total_revenue", 0)
        total_assets = balance_data.get("total_assets", 0)
        return total_revenue / total_assets if total_revenue and total_assets else None
    
    def _calculate_inventory_turnover(self, income_data: Dict, balance_data: Dict) -> Optional[float]:
        """计算存货周转率"""
        cost_of_revenue = income_data.get("cost_of_revenue", 0)
        inventory = balance_data.get("inventory", 0)
        return cost_of_revenue / inventory if cost_of_revenue and inventory else None
    
    def _calculate_receivables_turnover(self, income_data: Dict, balance_data: Dict) -> Optional[float]:
        """计算应收账款周转率"""
        total_revenue = income_data.get("total_revenue", 0)
        accounts_receivable = balance_data.get("accounts_receivable", 0)
        return total_revenue / accounts_receivable if total_revenue and accounts_receivable else None
    
    def _calculate_ocf_ratio(self, cashflow_data: Dict, balance_data: Dict) -> Optional[float]:
        """计算经营现金流比率"""
        operating_cash_flow = cashflow_data.get("operating_cash_flow", 0)
        current_liabilities = balance_data.get("current_liabilities", 0)
        return operating_cash_flow / current_liabilities if operating_cash_flow and current_liabilities else None
    
    def _calculate_fcf_yield(self, cashflow_data: Dict, info: Dict) -> Optional[float]:
        """计算自由现金流收益率"""
        free_cash_flow = cashflow_data.get("free_cash_flow", 0)
        market_cap = info.get("marketCap", 0)
        return (free_cash_flow / market_cap) * 100 if free_cash_flow and market_cap else None
    
    def _calculate_cash_conversion_cycle(self, income_data: Dict, balance_data: Dict) -> Optional[float]:
        """计算现金转换周期"""
        # 简化计算，实际需要更复杂的逻辑
        inventory_turnover = self._calculate_inventory_turnover(income_data, balance_data)
        receivables_turnover = self._calculate_receivables_turnover(income_data, balance_data)
        
        if inventory_turnover and receivables_turnover:
            days_inventory = 365 / inventory_turnover
            days_receivables = 365 / receivables_turnover
            # 简化处理，实际还需要应付账款周转天数
            return days_inventory + days_receivables
        return None
    
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