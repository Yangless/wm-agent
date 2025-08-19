#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能游戏助手演示脚本

这个脚本演示了完整的智能体工作流程：
1. 初始化系统组件
2. 创建测试场景
3. 触发智能体干预
4. 展示结果分析
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
import json

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config.settings import Settings
from src.data.data_manager import DataManager
from src.data.mock_data import MockDataGenerator
from src.agent.smart_game_agent import SmartGameAgent
from src.triggers.trigger_engine import TriggerEngine
from src.triggers.behavior_analyzer import BehaviorAnalyzer
from src.scenarios.frustration_scenario import FrustrationScenario
from src.scenarios.satisfion_scenario import SatisfionScenario
def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('demo.log', encoding='utf-8')
        ]
    )
    
    # 设置第三方库的日志级别
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)

def print_banner():
    """打印横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    智能游戏助手演示系统                        ║
║                                                              ║
║  这个演示展示了AI智能体如何识别玩家满意情况并提供个性化干预    ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_section(title: str):
    """打印章节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_step(step: str):
    """打印步骤"""
    print(f"\n🔸 {step}")

def print_result(result: dict, title: str = "结果"):
    """打印结果"""
    print(f"\n📊 {title}:")
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))

def demo_basic_functionality():
    """演示基础功能"""
    print_section("第一部分：基础功能演示")
    
    # 初始化设置
    print_step("初始化系统设置")
    settings = Settings()
    print(f"✅ 配置加载完成")
    print(f"   - 玩家数据文件: {settings.player_data_file}")
    print(f"   - 最大迭代次数: {settings.agent_max_iterations}")
    print(f"   - 记忆窗口: {settings.agent_memory_window}")
    
    # 初始化数据管理器
    print_step("初始化数据管理器")
    data_manager = DataManager()
    print(f"✅ 数据管理器初始化完成")
    
    # 创建模拟数据
    print_step("生成模拟玩家数据")
    mock_generator = MockDataGenerator()
    
    # 创建几个测试玩家
    players = [
        mock_generator.generate_player("player_001", "张三", "high_value"),
        mock_generator.generate_player("player_002", "李四", "normal"),
        mock_generator.generate_player("player_003", "王五", "high_value")
    ]
    
    for player in players:
        data_manager.update_player(player)
        print(f"   ✅ 创建玩家: {player.username} (等级{player.level}, VIP{player.vip_level})")
    
    # 生成行为数据
    print_step("生成玩家行为数据")
    for i, player in enumerate(players):
        # 生成正常行为
        normal_actions = mock_generator.generate_action_sequence(
            player.player_id, "normal", count=10
        )
        for action in normal_actions:
            data_manager.add_action(action)
        
        # # 为部分玩家生成异常行为（受挫、失败等）
        # if i < 2:  # 前两个玩家生成异常行为
        #     frustration_actions = mock_generator.generate_action_sequence(
        #         player.player_id, "frustration", count=5
        #     )
        #     for action in frustration_actions:
        #         data_manager.add_action(action)
        #     print(f"   ✅ 为 {player.username} 生成了 {len(normal_actions)} 个正常行为 + {len(frustration_actions)} 个异常行为")
        # else:
        #     print(f"   ✅ 为 {player.username} 生成了 {len(normal_actions)} 个正常行为")

        
               # 为部分玩家生成异常行为（受挫、失败等）
        if i < 2:  # 前两个玩家生成满意行为
            satisfaction_actions = mock_generator.generate_action_sequence(
                player.player_id, "satisfaction", count=5
            )
            for action in satisfaction_actions:
                data_manager.add_action(action)
            print(f"   ✅ 为 {player.username} 生成了 {len(normal_actions)} 个正常行为 + {len(satisfaction_actions)} 个满意行为")
        else:
            print(f"   ✅ 为 {player.username} 生成了 {len(normal_actions)} 个正常行为")
    
    # 展示数据统计
    print_step("数据统计概览")
    stats = data_manager.get_statistics()
    print_result(stats, "数据统计")
    
    return data_manager, settings

def demo_behavior_analysis(data_manager: DataManager):
    """演示行为分析功能"""
    print_section("第二部分：行为分析演示")
    
    # 初始化行为分析器
    print_step("初始化行为分析器")
    analyzer = BehaviorAnalyzer(data_manager)
    print(f"✅ 行为分析器初始化完成")
    
    # 分析第一个玩家
    print_step("分析玩家行为模式")
    player_id = "player_001"
    analysis = analyzer.analyze_player_behavior(player_id, time_window_minutes=120)
    
    if "error" not in analysis:
        print(f"✅ 玩家 {player_id} 行为分析完成")
        print(f"   - 行为模式: {analysis['pattern']}")
        print(f"   - 风险等级: {analysis['risk_level']}")
        print(f"   - 情绪状态: {analysis['emotional_state']}")
        print(f"   - 需要干预: {analysis['intervention_needed']}")
    else:
        print(f"❌ 分析失败: {analysis['error']}")
    
    return analyzer

def demo_trigger_system(data_manager: DataManager, analyzer: BehaviorAnalyzer):
    """演示触发系统"""
    print_section("第三部分：触发系统演示")
    
    # 初始化触发引擎
    print_step("初始化触发引擎")
    trigger_engine = TriggerEngine(data_manager, analyzer)
    print(f"✅ 触发引擎初始化完成")
    
    # 显示触发条件
    print_step("查看触发条件")
    conditions = trigger_engine.get_condition_list()
    print(f"✅ 加载了 {len(conditions)} 个触发条件:")
    for condition in conditions[:3]:  # 只显示前3个
        print(f"   - {condition['name']}: {condition['description']}")
    
    # 强制检查玩家
    print_step("检查玩家触发条件")
    player_id = "player_001"
    triggered_events = trigger_engine.force_check_player(player_id)
    
    if triggered_events:
        print(f"✅ 检测到 {len(triggered_events)} 个触发事件:")
        for event in triggered_events:
            print(f"   - {event.trigger_condition.name}: {event.trigger_condition.trigger_type.value}")
    else:
        print(f"ℹ️  玩家 {player_id} 当前没有触发任何条件")
    
    return trigger_engine
import traceback
def demo_agent_system(data_manager: DataManager, settings: Settings):
    """演示智能体系统"""
    print_section("第四部分：智能体系统演示")
    
    # 初始化智能体
    print_step("初始化智能体")
    try:
        agent = SmartGameAgent(data_manager, settings)
        print(f"✅ 智能体初始化完成")
        print(f"   - LLM状态: {'已连接' if agent.llm else '未连接（使用规则引擎）'}")
        print(f"   - 工具数量: {len(agent.tools)}")
    except Exception as e:
        print(f"❌ 智能体初始化失败: {e}")
        print(f"ℹ️  将使用模拟智能体进行演示")
        error_details = traceback.format_exc()
        print(error_details)
        agent = None
    
    # 展示工具列表
    if agent:
        print_step("智能体工具列表")
        for tool in agent.tools:
            print(f"   - {tool.name}: {tool.description[:50]}...")
    
    return agent

def demo_satisfion_scenario(data_manager: DataManager, settings: Settings, agent):
    """演示受挫场景"""
    print_section("第五部分：满意场景完整演示")
    
    # 创建满意场景
    print_step("创建满意场景测试")
    scenario = SatisfionScenario(data_manager, settings, agent)
    
    print(f"✅ 满意场景初始化完成")
    

    
    # 如果有智能体，运行完整场景
    if agent :
        print_step("运行完整满意场景")
        print("⏳ 这可能需要几分钟时间...")
        
        try:
            

            full_result = scenario.run_satisfion_complete_scenario()
            
            if "error" not in full_result:
                print(f"✅ 完整场景测试完成")
                
                # 显示关键结果
                success_indicators = full_result.get('success_indicators', {})
                print(f"\n📈 成功指标:")
                print(f"   - 玩家状态改善: {'是' if success_indicators.get('player_status_improved') else '否'}")
                print(f"   - 满意程度提高: {'是' if success_indicators.get('satisfaction_increased') else '否'}")
                print(f"   - 收到干预措施: {'是' if success_indicators.get('received_intervention') else '否'}")
                print(f"   - 继续游戏: {'是' if success_indicators.get('continued_playing') else '否'}")
                print(f"   - 整体成功: {'是' if success_indicators.get('overall_success') else '否'}")
                print(f"   - 成功分数: {success_indicators.get('success_score', 0):.2f}")
                
                # 显示干预结果
                interventions = full_result.get('interventions', [])
                if interventions:
                    print(f"\n🎯 干预措施 ({len(interventions)} 个):")
                    for intervention in interventions:
                        if 'error' not in intervention:
                            result = intervention.get('result', {})
                            print(f"   - 条件: {intervention['condition_name']}")
                            print(f"     状态: {result.get('status', 'unknown')}")
                            if 'actions_taken' in result:
                                print(f"     措施: {', '.join(result['actions_taken'])}")
                
                # 显示邮件历史
                mail_history = full_result.get('mail_history', [])
                if mail_history:
                    print(f"\n📧 发送邮件 ({len(mail_history)} 封):")
                    for mail in mail_history:
                        print(f"   - {mail['title']}: {mail['content']}")
                        if mail['attachments']:
                            print(f"     附件: {mail['attachments']}")
            else:
                print(f"❌ 完整场景测试失败: {full_result['error']}")
                
        except Exception as e:
            print(f"❌ 运行完整场景时出错: {e}")
    
    return scenario

def demo_system_stats(data_manager: DataManager, analyzer: BehaviorAnalyzer, 
                     trigger_engine: TriggerEngine, agent):
    """演示系统统计"""
    print_section("第六部分：系统统计信息")
    
    # 数据管理器统计
    print_step("数据管理器统计")
    data_stats = data_manager.get_statistics()
    print(f"✅ 数据统计:")
    print(f"   - 玩家总数: {data_stats['total_players']}")
    print(f"   - 行为总数: {data_stats['total_actions']}")
    print(f"   - 触发事件: {data_stats['total_triggers']}")
    print(f"   - 邮件总数: {data_stats['total_mails']}")
    
    # 行为分析器统计
    print_step("行为分析器统计")
    analyzer_stats = analyzer.get_analyzer_stats()
    print(f"✅ 分析器统计:")
    print(f"   - 缓存分析: {analyzer_stats['cached_analyses']}")
    print(f"   - 跟踪玩家: {analyzer_stats['tracked_players']}")
    print(f"   - 风险评分缓存: {analyzer_stats['risk_score_cache_size']}")
    
    # 触发引擎统计
    print_step("触发引擎统计")
    trigger_stats = trigger_engine.get_trigger_stats()
    print(f"✅ 触发引擎统计:")
    print(f"   - 引擎状态: {trigger_stats['engine_status']}")
    print(f"   - 触发条件: {trigger_stats['total_conditions']}")
    print(f"   - 注册处理器: {trigger_stats['registered_handlers']}")
    
    # 智能体统计
    if agent:
        print_step("智能体统计")
        agent_stats = agent.get_agent_stats()
        print(f"✅ 智能体统计:")
        print(f"   - 处理事件: {agent_stats['total_events_processed']}")
        print(f"   - 成功干预: {agent_stats['successful_interventions']}")
        print(f"   - 发送邮件: {agent_stats['mails_sent']}")
        print(f"   - 平均响应时间: {agent_stats['average_response_time']:.2f}秒")

def main():
    """主函数"""
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # 打印横幅
        print_banner()
        
        # 演示基础功能
        data_manager, settings = demo_basic_functionality()
        
        # 演示行为分析
        analyzer = demo_behavior_analysis(data_manager)
        
        # 演示触发系统
        trigger_engine = demo_trigger_system(data_manager, analyzer)
        
        # 演示智能体系统
        agent = demo_agent_system(data_manager, settings)
        
        # 演示满意场景
        scenario = demo_satisfion_scenario(data_manager, settings, agent)
        
        # 演示系统统计
        demo_system_stats(data_manager, analyzer, trigger_engine, agent)
        
        # 结束
        print_section("演示完成")
        print("🎉 智能游戏助手演示已完成！")
        print("\n📝 演示总结:")
        print("   1. ✅ 系统初始化和配置")
        print("   2. ✅ 玩家数据模拟和管理")
        print("   3. ✅ 行为分析和模式识别")
        print("   4. ✅ 触发条件检测")
        print("   5. ✅ 智能体干预决策")
        print("   6. ✅ 满意场景完整流程")
        print("   7. ✅ 系统性能统计")
        
        print("\n💡 提示:")
        print("   - 查看 demo.log 获取详细日志")
        print("   - 查看 data/ 目录下的生成数据")
        print("   - 查看 data/reports/ 目录下的场景报告")
        
        if not agent or not agent.llm:
            print("\n⚠️  注意:")
            print("   - 未配置OpenAI API，使用了规则引擎模拟")
            print("   - 配置 .env 文件中的 OPENAI_API_KEY 以启用完整功能")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  演示被用户中断")
        logger.info("演示被用户中断")
    except Exception as e:
        print(f"\n\n❌ 演示过程中发生错误: {e}")
        logger.error(f"演示过程中发生错误: {e}", exc_info=True)
    finally:
        print("\n👋 感谢使用智能游戏助手演示系统！")

if __name__ == "__main__":
    main()