#!/bin/bash

# TradingAgents for Claude Code MCP 服务器启动脚本
# 灵感来源于原 TradingAgents 项目，感谢原团队的设计
# ✅ 已修复：使用标准 FastMCP SSE 服务器实现

echo "🚀 启动 TradingAgents for Claude Code MCP 服务器"
echo "⚠️  重要提醒：本项目仅用于 Claude Code 技术研究，严禁用于实际投资！"
echo "🔬 技术学习用途：探索 MCP、subagents、slash commands 等功能"
echo "🚫 投资风险提醒：任何投资损失与项目开发者无关"
echo "✅ 状态：MCP 服务器已修复，使用 SSE 协议，与 Claude Code 完全兼容"
echo "================================"

# 检查虚拟环境和 Python
if [ -d ".venv" ]; then
    echo "📦 检测到 uv 虚拟环境，激活中..."
    source .venv/bin/activate
elif ! command -v python &> /dev/null; then
    echo "❌ Python 未安装或未在 PATH 中"
    echo "💡 建议使用 uv 创建虚拟环境: uv venv && source .venv/bin/activate"
    exit 1
fi

# 检查项目目录
if [ ! -f "tradingagents/mcp/trading_server.py" ]; then
    echo "❌ 未找到服务器文件，请确保在项目根目录运行"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
python -c "
import sys
required = ['pandas', 'numpy', 'yfinance', 'requests', 'feedparser', 'stockstats', 'textblob', 'finnhub', 'praw']
missing = []
for module in required:
    try:
        __import__(module)
    except ImportError:
        missing.append(module)
        
if missing:
    print('❌ 缺少依赖:', ', '.join(missing))
    print('请运行: uv pip install -r requirements.txt')
    print('或传统方式: pip install -r requirements.txt')
    sys.exit(1)
else:
    print('✅ 依赖检查通过')
"

if [ $? -ne 0 ]; then
    exit 1
fi

# 检查环境变量
echo "🔧 检查环境配置..."
python -c "
import os
apis = ['FINNHUB_API_KEY', 'REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET']
configured = sum(1 for api in apis if os.getenv(api))
print(f'📊 已配置 API 密钥: {configured}/{len(apis)}')
if configured == 0:
    print('⚠️ 警告: 未配置 API 密钥，某些功能将受限')
"

# 加载环境变量
if [ -f ".env" ]; then
    echo "📄 加载 .env 文件..."
    set -a  # 自动导出变量
    source .env
    set +a  # 关闭自动导出
fi

# 启动选项
echo ""
echo "启动选项:"
echo "  1. 启动 MCP 服务器 (用于 Claude Code)"
echo "  2. 运行快速演示"
echo "  3. 运行健康检查"
echo "  4. 退出"
echo ""

read -p "请选择 (1-4): " choice

case $choice in
    1)
        echo "🚀 启动 MCP 服务器..."
        
        # 从环境变量读取配置
        MCP_HOST=${MCP_SERVER_HOST:-"localhost"}
        MCP_PORT=${MCP_SERVER_PORT:-"6550"}
        
        echo "服务器将在 ${MCP_HOST}:${MCP_PORT} 运行 (SSE 端点: /sse)"
        echo "按 Ctrl+C 停止服务器"
        echo ""
        python -m tradingagents.mcp.trading_server
        ;;
    2)
        echo "🎮 运行快速演示..."
        python quick_start.py
        ;;
    3)
        echo "🔍 运行健康检查..."
        python -c "
import asyncio
import sys
sys.path.insert(0, '.')

async def health_check():
    server = None
    try:
        from tradingagents.mcp.trading_server import TradingAgentsServer
        server = TradingAgentsServer()
        health = await server.health_check()
        
        print(f'系统状态: {health[\"status\"]}')
        print('服务状态:')
        for service, status in health['services'].items():
            icon = '✅' if status == 'healthy' else '❌'
            print(f'  {icon} {service}: {status}')
            
        proxy_config = await server.proxy_get_config()
        proxy_status = '已配置' if proxy_config['proxy_configured'] else '未配置'
        print(f'代理配置: {proxy_status}')
        
    except Exception as e:
        print(f'❌ 健康检查失败: {e}')
    finally:
        # 确保关闭所有资源
        if server:
            try:
                await server.close()
            except Exception as e:
                pass  # 忽略关闭时的错误

asyncio.run(health_check())
"
        ;;
    4)
        echo "👋 退出"
        exit 0
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac