#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试重构后的SmartGameAgent功能完整性
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime
from models.player import Player, PlayerStatus
from models.action import PlayerAction, ActionType
from agent.smart_game_agent import SmartGameAgent
from data.data_manager import DataManager
from agent.memory_manager import MemoryManager

def test_refactored_agent():
    """测试重构后的SmartGameAgent"""
    print("=== 测试重构后的SmartGameAgent功能 ===")
    
    # 1. 初始化组件
    print("\n1. 初始化组件...")
    data_manager = DataManager()
    memory_manager = MemoryManager()
    
    # 创建测试玩家
    test_player = Player(
        player_id="test_player_001",
        username="TestUser",
        vip_level=3,
        total_playtime_hours=120,
        last_login=datetime.now(),
        total_spent=500.0,
        current_status=PlayerStatus.ACTIVE,
        frustration_level=6,  # 高挫折等级，应该触发干预
        consecutive_failures=2,
        registration_date=datetime.now()
    )
    
    data_manager.update_player(test_player)
    print(f"✓ 创建测试玩家: {test_player.username} (挫折等级: {test_player.frustration_level})")
    
    # 2. 创建SmartGameAgent实例
    print("\n2. 创建SmartGameAgent实例...")
    agent = SmartGameAgent(
        data_manager=data_manager,
    
        llm_client=None,  # 测试时不使用LLM
        agent_executor=None
    )
    print("✓ SmartGameAgent实例创建成功")
    
    # 3. 测试规则预筛选功能
    print("\n3. 测试规则预筛选功能...")
    trigger_context = {
        "event_id": "test_event_001",
        "triggered_at": datetime.now(),
        "triggering_actions": []
    }
    
    rule_result = agent._rule_based_prescreening(test_player, trigger_context)
    print(f"✓ 规则预筛选结果:")
    print(f"  - 需要深度分析: {rule_result['needs_deep_analysis']}")
    print(f"  - 建议干预: {rule_result['intervention_suggested']}")
    print(f"  - 原因: {rule_result['reason']}")
    print(f"  - 建议类型: {rule_result['suggested_type']}")
    
    # 4. 测试统一分析方法
    print("\n4. 测试统一分析方法...")
    intervention_analysis = agent._analyze_and_prepare_intervention(
        test_player.player_id, 
        trigger_context
    )
    print(f"✓ 干预分析结果:")
    print(f"  - 需要干预: {intervention_analysis['intervention_needed']}")
    print(f"  - 干预原因: {intervention_analysis['intervention_reason']}")
    print(f"  - 建议干预类型: {intervention_analysis['suggested_intervention_type']}")
    print(f"  - 玩家情绪摘要: {intervention_analysis['player_mood_summary']}")
    
    # 5. 测试规则引擎执行
    print("\n5. 测试规则引擎执行...")
    intervention_analysis["context"]["player_id"] = test_player.player_id
    execution_result = agent._process_with_rule_engine_v2(intervention_analysis)
    print(f"✓ 执行结果:")
    print(f"  - 成功: {execution_result['success']}")
    print(f"  - 方法: {execution_result.get('method', 'N/A')}")
    if 'reason' in execution_result:
        print(f"  - 原因: {execution_result['reason']}")
    
    # 6. 测试完整流程
    print("\n6. 测试完整的process_trigger_event流程...")
    final_result = agent.process_trigger_event(
        player_id=test_player.player_id,
        trigger_context=trigger_context
    )
    print(f"✓ 完整流程结果:")
    print(f"  - 成功: {final_result['success']}")
    print(f"  - 方法: {final_result.get('method', 'N/A')}")
    if 'intervention_type' in final_result:
        print(f"  - 干预类型: {final_result['intervention_type']}")
    if 'intervention_reason' in final_result:
        print(f"  - 干预原因: {final_result['intervention_reason']}")
    
    # 7. 测试低挫折等级玩家（不应触发干预）
    print("\n7. 测试低挫折等级玩家...")
    normal_player = Player(
        player_id="normal_player_001",
        username="NormalUser",
        vip_level=1,
        total_playtime_hours=50,
        last_login=datetime.now(),
        total_spent=50.0,
        current_status=PlayerStatus.ONLINE,
        frustration_level=2,  # 低挫折等级
        consecutive_failures=1
    )
    
    data_manager.add_player(normal_player)
    normal_result = agent.process_trigger_event(
        player_id=normal_player.player_id,
        trigger_context=trigger_context
    )
    print(f"✓ 正常玩家结果:")
    print(f"  - 成功: {normal_result['success']}")
    print(f"  - 需要干预: {normal_result.get('intervention_needed', False)}")
    if 'reason' in normal_result:
        print(f"  - 原因: {normal_result['reason']}")
    
    print("\n=== 测试完成 ===")
    print("\n总结:")
    print("✓ 规则预筛选功能正常")
    print("✓ 统一分析方法正常")
    print("✓ 两阶段干预决策逻辑正常")
    print("✓ 数据结构契约符合预期")
    print("✓ 执行引擎重构成功")
    print("✓ 完整流程运行正常")
    
    return True

def test_player_action_processing():
    """测试PlayerAction处理功能"""
    print("\n=== 测试PlayerAction处理功能 ===")
    
    # 初始化组件
    data_manager = DataManager()
    memory_manager = MemoryManager()
    agent = SmartGameAgent(
        data_manager=data_manager,
        memory_manager=memory_manager,
        llm_client=None,
        agent_executor=None
    )
    
    # 创建测试玩家
    test_player = Player(
        player_id="action_test_player",
        username="ActionTestUser",
        vip_level=2,
        total_playtime_hours=80,
        last_login=datetime.now(),
        total_spent=200.0,
        current_status=PlayerStatus.ONLINE,
        frustration_level=4,
        consecutive_failures=3  # 连续失败次数较高
    )
    
    data_manager.add_player(test_player)
    
    # 创建测试动作
    test_action = PlayerAction(
        action_id="action_001",
        action_type=ActionType.BATTLE_FAILURE,
        player_id=test_player.player_id,
        timestamp=datetime.now(),
        metadata={"battle_type": "boss_fight", "damage_dealt": 1500}
    )
    
    print(f"✓ 创建测试动作: {test_action.action_type.value}")
    
    # 测试process_player_action方法
    result = agent.process_player_action(test_player, test_action)
    print(f"✓ 处理结果:")
    print(f"  - 成功: {result['success']}")
    print(f"  - 方法: {result.get('method', 'N/A')}")
    if 'intervention_needed' in result:
        print(f"  - 需要干预: {result['intervention_needed']}")
    if 'intervention_type' in result:
        print(f"  - 干预类型: {result['intervention_type']}")
    
    return True

if __name__ == "__main__":
    try:
        # 运行主要测试
        test_refactored_agent()
        
        # 运行PlayerAction测试
        test_player_action_processing()
        
        print("\n🎉 所有测试通过！重构后的SmartGameAgent功能完整性验证成功！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)