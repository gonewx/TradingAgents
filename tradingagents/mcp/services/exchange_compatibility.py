"""
交易所兼容性检查模块
用于验证不同数据源对各交易所股票代码的支持情况
"""

import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

class Exchange(Enum):
    """支持的交易所"""
    NASDAQ = "NASDAQ"
    NYSE = "NYSE" 
    HK = "HK"  # 港交所
    SS = "SS"  # 上海证券交易所
    SZ = "SZ"  # 深圳证券交易所
    TSX = "TSX"  # 多伦多证券交易所

class DataSource(Enum):
    """数据源类型"""
    YFINANCE = "yfinance"
    FINNHUB = "finnhub"
    GOOGLE_NEWS = "google_news"
    REDDIT = "reddit"

class ExchangeCompatibilityChecker:
    """交易所兼容性检查器"""
    
    # 数据源兼容性矩阵
    COMPATIBILITY_MATRIX = {
        DataSource.YFINANCE: {
            Exchange.NASDAQ: True,
            Exchange.NYSE: True,
            Exchange.HK: True,
            Exchange.SS: True,
            Exchange.SZ: True,
            Exchange.TSX: True,
        },
        DataSource.FINNHUB: {
            Exchange.NASDAQ: True,
            Exchange.NYSE: True,
            Exchange.HK: True,  # 支持但需要正确格式
            Exchange.SS: False,  # 不支持A股
            Exchange.SZ: False,  # 不支持A股
            Exchange.TSX: True,
        },
        DataSource.GOOGLE_NEWS: {
            Exchange.NASDAQ: True,
            Exchange.NYSE: True,
            Exchange.HK: True,   # 搜索可能混杂
            Exchange.SS: True,   # 搜索可能混杂
            Exchange.SZ: True,   # 搜索可能混杂
            Exchange.TSX: True,
        },
        DataSource.REDDIT: {
            Exchange.NASDAQ: True,
            Exchange.NYSE: True,
            Exchange.HK: False,  # 主要讨论美股
            Exchange.SS: False,
            Exchange.SZ: False,
            Exchange.TSX: False,
        }
    }
    
    # Finnhub特殊格式要求
    FINNHUB_SYMBOL_FORMATS = {
        Exchange.HK: "{symbol}.HK",     # 港股: 0700.HK
        Exchange.NASDAQ: "{symbol}",    # 美股: AAPL
        Exchange.NYSE: "{symbol}",      # 美股: MSFT
        Exchange.TSX: "{symbol}.TO",    # 加拿大: SHOP.TO
    }
    
    @classmethod
    def parse_symbol(cls, symbol: str) -> Tuple[str, Optional[Exchange]]:
        """
        解析股票代码，返回基础代码和交易所
        
        Args:
            symbol: 股票代码，如 "1952.HK", "AAPL", "000001.SS"
            
        Returns:
            (base_symbol, exchange): 基础代码和交易所枚举
        """
        symbol = symbol.upper().strip()
        
        # 检查是否包含交易所后缀
        if '.' in symbol:
            base, suffix = symbol.rsplit('.', 1)
            try:
                exchange = Exchange(suffix)
                return base, exchange
            except ValueError:
                logger.warning(f"未识别的交易所后缀: {suffix}")
                return symbol, None
        
        # 无后缀，根据格式推断
        if symbol.isdigit():
            if len(symbol) == 4:
                return symbol, Exchange.HK  # 港股4位数字
            elif len(symbol) == 6:
                if symbol.startswith('60'):
                    return symbol, Exchange.SS  # 沪市
                elif symbol.startswith(('00', '30')):
                    return symbol, Exchange.SZ  # 深市
        
        # 默认认为是美股
        return symbol, Exchange.NASDAQ
    
    @classmethod
    def is_supported(cls, symbol: str, data_source: DataSource) -> bool:
        """
        检查数据源是否支持该股票代码
        
        Args:
            symbol: 股票代码
            data_source: 数据源
            
        Returns:
            bool: 是否支持
        """
        _, exchange = cls.parse_symbol(symbol)
        if exchange is None:
            return False
            
        return cls.COMPATIBILITY_MATRIX.get(data_source, {}).get(exchange, False)
    
    @classmethod
    def get_supported_datasources(cls, symbol: str) -> List[DataSource]:
        """
        获取支持该股票代码的所有数据源
        
        Args:
            symbol: 股票代码
            
        Returns:
            List[DataSource]: 支持的数据源列表
        """
        supported = []
        for data_source in DataSource:
            if cls.is_supported(symbol, data_source):
                supported.append(data_source)
        return supported
    
    @classmethod
    def format_for_finnhub(cls, symbol: str) -> Optional[str]:
        """
        将股票代码格式化为Finnhub要求的格式
        
        Args:
            symbol: 原始股票代码
            
        Returns:
            Optional[str]: Finnhub格式的代码，如果不支持则返回None
        """
        base_symbol, exchange = cls.parse_symbol(symbol)
        
        if not cls.is_supported(symbol, DataSource.FINNHUB):
            return None
            
        format_template = cls.FINNHUB_SYMBOL_FORMATS.get(exchange)
        if format_template:
            return format_template.format(symbol=base_symbol)
        
        return base_symbol  # 默认返回基础代码
    
    @classmethod
    def get_compatibility_report(cls, symbol: str) -> Dict:
        """
        生成股票代码的兼容性报告
        
        Args:
            symbol: 股票代码
            
        Returns:
            Dict: 兼容性报告
        """
        base_symbol, exchange = cls.parse_symbol(symbol)
        supported_sources = cls.get_supported_datasources(symbol)
        
        report = {
            "original_symbol": symbol,
            "base_symbol": base_symbol,
            "exchange": exchange.value if exchange else "UNKNOWN",
            "supported_datasources": [ds.value for ds in supported_sources],
            "finnhub_format": cls.format_for_finnhub(symbol),
            "recommendations": []
        }
        
        # 添加建议
        if DataSource.YFINANCE in supported_sources:
            report["recommendations"].append("使用 Yahoo Finance 获取市场数据和技术指标")
        
        if DataSource.FINNHUB in supported_sources:
            report["recommendations"].append(f"使用 Finnhub 格式 '{report['finnhub_format']}' 获取公司资料")
        else:
            report["recommendations"].append("Finnhub 不支持此交易所，建议使用其他数据源")
        
        if DataSource.GOOGLE_NEWS in supported_sources:
            if exchange in [Exchange.HK, Exchange.SS, Exchange.SZ]:
                report["recommendations"].append("新闻搜索可能包含混杂结果，建议结合公司名称过滤")
            else:
                report["recommendations"].append("可使用 Google News 获取相关新闻")
        
        if DataSource.REDDIT not in supported_sources:
            report["recommendations"].append("Reddit 数据主要覆盖美股，此代码相关讨论可能有限")
        
        return report

def validate_symbol_compatibility(symbol: str) -> Dict:
    """
    快速验证股票代码兼容性的便捷函数
    
    Args:
        symbol: 股票代码
        
    Returns:
        Dict: 验证结果
    """
    checker = ExchangeCompatibilityChecker()
    return checker.get_compatibility_report(symbol)

# 测试用例
if __name__ == "__main__":
    # 测试不同类型的股票代码
    test_symbols = ["1952.HK", "AAPL", "000001.SS", "1952", "SHOP.TO"]
    
    for symbol in test_symbols:
        print(f"\n=== {symbol} 兼容性报告 ===")
        report = validate_symbol_compatibility(symbol)
        for key, value in report.items():
            print(f"{key}: {value}")