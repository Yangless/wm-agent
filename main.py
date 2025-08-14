#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能体游戏场景实现 - 主程序入口

这个程序实现了一个基于LangChain的ReAct智能体，
用于检测和干预游戏中玩家的受挫情况。

主要功能：
1. 监控玩家行为数据
2. 智能识别受挫场景
3. 自动生成个性化干预方案
4. 发送安抚消息和奖励
"""

import asyncio
import sys
from pathlib import Path
from loguru import logger

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config.settings import settings
from src.agent.smart_agent import SmartGameAgent
from src.data.mock_data import MockDataGenerator
from src.scenarios.frustration_scenario import FrustrationScenario

def setup_logging():
    """配置日志系统"""
    logger.remove()  # 移除默认处理器
    
    # 控制台输出
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # 文件输出
    log_file = Path(settings.log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        log_file,
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="1 day",
        retention="7 days"
    )

def create_directories():
    """创建必要的目录结构"""
    directories = [
        "data",
        "logs", 
        "output",
        "tests/data"
    ]
    
    for dir_name in directories:
        Path(dir_name).mkdir(parents=True, exist_ok=True)
        logger.debug(f"确保目录存在: {dir_name}")

async def run_demo_scenario():
    """运行演示场景"""
    logger.info("🚀 启动AI智能体演示场景")
    
    try:
        # 1. 初始化数据生成器
        logger.info("📊 初始化模拟数据...")
        data_generator = MockDataGenerator()
        
        # 2. 创建智能体
        logger.info("🤖 初始化智能体...")
        agent = SmartGameAgent()
        
        # 3. 创建受挫场景
        logger.info("🎭 设置受挫场景...")
        scenario = FrustrationScenario(agent, data_generator)
        
        # 4. 运行场景
        logger.info("▶️  开始执行场景...")
        result = await scenario.run_scenario()
        
        # 5. 输出结果
        logger.success("✅ 场景执行完成")
        logger.info(f"📋 场景结果: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ 场景执行失败: {str(e)}")
        raise

def main():
    """主函数"""
    print("="*60)
    print("🎮 AI智能体游戏场景实现系统")
    print("📝 基于LangChain ReAct架构")
    print("🎯 专注解决玩家受挫干预场景")
    print("="*60)
    
    # 设置日志
    setup_logging()
    logger.info("系统启动中...")
    
    # 创建目录
    create_directories()
    
    # 检查配置
    if not settings.openai_api_key:
        logger.warning("⚠️  未设置OpenAI API Key，将使用模拟模式")
    
    try:
        # 运行异步主逻辑
        result = asyncio.run(run_demo_scenario())
        
        print("\n" + "="*60)
        print("🎉 演示完成！")
        print(f"📊 执行结果: {result.get('status', 'unknown')}")
        if 'message' in result:
            print(f"💬 智能体响应: {result['message']}")
        print("="*60)
        
    except KeyboardInterrupt:
        logger.info("👋 用户中断，程序退出")
    except Exception as e:
        logger.error(f"💥 程序执行出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()