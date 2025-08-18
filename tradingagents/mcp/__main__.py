"""
TradingAgents MCP服务器主入口
"""

import sys
import os

# 确保项目根目录在Python路径中
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tradingagents.mcp.trading_server import main

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())