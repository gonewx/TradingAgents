"""
TradingAgents for Claude Code - 量化交易分析系统
灵感来源于原 TradingAgents 项目，感谢原团队的创新理念
"""

import os
from pathlib import Path

# 加载.env文件
try:
    from dotenv import load_dotenv
    
    # 查找.env文件路径
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    env_file = project_root / '.env'
    
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ 已加载环境变量文件: {env_file}")
    else:
        print(f"⚠️ 未找到.env文件: {env_file}")
        
except ImportError:
    print("⚠️ python-dotenv 未安装，无法加载.env文件")
except Exception as e:
    print(f"⚠️ 加载.env文件时出错: {e}")

__version__ = "0.1.0"
__author__ = "TradingAgents for Claude Code Team"