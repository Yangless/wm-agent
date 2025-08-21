import streamlit as st
import sys
import os
from datetime import datetime
import json
from typing import Dict, Any, List

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from models.player import Player
from models.action import PlayerAction, ActionType
from agent.smart_game_agent import SmartGameAgent
from config.settings import Settings
from src.data.data_manager import DataManager

# 初始化数据管理器
data_manager = DataManager()


# 页面配置
st.set_page_config(
    page_title="智能游戏Agent可视化界面",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="collapsed"  # 折叠侧边栏，因为我们将使用三栏布局
)

# 初始化session state
if 'player' not in st.session_state:
    st.session_state.player = Player(
        player_id="player_001",
        username="起个名字真难",
        registration_date=datetime.now(),
        vip_level=3,
        level=15,
        experience=2500,
        coins=1000,
        gems=50
    )

data_manager.update_player(st.session_state.player)

if 'agent' not in st.session_state:
    settings = Settings()
    st.session_state.agent = SmartGameAgent(data_manager , settings)


if 'action_history' not in st.session_state:
    st.session_state.action_history = []

if 'intervention_history' not in st.session_state:
    st.session_state.intervention_history = []

def main():
    st.title("🎮 智能游戏Agent可视化界面")
    st.markdown("---")
    
    # 创建三栏布局
    col1, col2, col3 = st.columns(3)
    
    # 第一栏：玩家状态与动作日志
    with col1:
        st.header("👤 玩家信息与近期动作")
        
        player = st.session_state.player
        
        # 玩家核心信息
        st.subheader("📋 核心信息")
        st.write(f"**玩家ID:** {player.player_id}")
        st.write(f"**用户名:** {player.username}")
        st.write(f"**等级:** {player.level}")
        st.write(f"**VIP等级:** {player.vip_level}")
        st.write(f"**总游戏时长:** {player.total_playtime_hours:.1f} 小时")
        
        formatted_date = player.registration_date.strftime("%Y-%m-%d")
        st.write(f"**注册日期:** {formatted_date}")
        
        st.markdown("---")
        
        # 玩家情绪状态
        st.subheader("😊 情绪状态")
        
        # 当前情绪
        if hasattr(player, 'current_emotions') and player.current_emotions:
            st.write("**当前情绪:**")
            for emotion in player.current_emotions:
                st.write(f"• {emotion.value.capitalize()}")
        else:
            st.info("暂无情绪分析数据")
        
        # 情绪历史记录（使用expander节约空间）
        with st.expander("📈 情绪历史记录"):
            if hasattr(player, 'emotion_history') and player.emotion_history:
                for i, emotion_record in enumerate(reversed(player.emotion_history[-5:])):
                    st.write(f"**{i+1}.** {emotion_record}")
            else:
                st.info("暂无情绪历史记录")
        
        # 风险评估
        st.subheader("⚠️ 风险评估")
        
        # 机器人风险等级
        if hasattr(player, 'bot_risk_level') and player.bot_risk_level:
            risk_level_value = player.bot_risk_level.value.upper()
            color = "red" if risk_level_value == "HIGH" else "orange" if risk_level_value == "MEDIUM" else "green"
            st.markdown(f'🤖 **机器人风险:** <span style="color:{color}; font-weight:bold;">{risk_level_value}</span>', unsafe_allow_html=True)
        else:
            st.markdown('🤖 **机器人风险:** 未知')
        
        # 流失风险等级
        if hasattr(player, 'churn_risk_level') and player.churn_risk_level:
            churn_level_value = player.churn_risk_level.value.upper()
            color = "red" if churn_level_value in ["HIGH", "CRITICAL"] else "orange" if churn_level_value == "MEDIUM" else "green"
            st.markdown(f'📉 **流失风险:** <span style="color:{color}; font-weight:bold;">{churn_level_value}</span>', unsafe_allow_html=True)
        else:
            st.markdown('📉 **流失风险:** 未知')
        
        st.markdown("---")
        
        # 近期动作日志
        st.subheader("🎯 近期动作日志")
        
        if st.session_state.action_history:
            st.write("**最近5条动作:**")
            for i, action_data in enumerate(reversed(st.session_state.action_history[-5:])):
                timestamp = action_data['timestamp']
                action_type = action_data['action_type']
                details = action_data.get('details', '')
                st.write(f"**{i+1}.** `{timestamp}` - {action_type}")
                if details:
                    st.write(f"   └─ {details}")
        else:
            st.info("暂无动作历史")
    
    # 第二栏：Agent分析过程与结果
    with col2:
        st.header("🤖 Agent 决策过程")
        
        # 显示最新的分析结果
        if st.session_state.intervention_history:
            latest_intervention = st.session_state.intervention_history[-1]
            
            # 核心分析结论
            st.subheader("📊 核心分析结论")
            
            # 从最新干预结果中提取关键信息
            intervention_needed = latest_intervention.get('intervention_applied', False)
            
            # 显示是否干预
            if intervention_needed:
                st.markdown("**🚨 是否干预:** <span style='color:red; font-weight:bold;'>是</span>", unsafe_allow_html=True)
            else:
                st.markdown("**✅ 是否干预:** <span style='color:green; font-weight:bold;'>否</span>", unsafe_allow_html=True)
            
            # 尝试从结果中提取干预原因和背景
            if 'reason' in latest_intervention:
                st.write(f"**干预原因:** {latest_intervention['reason']}")
            
            if 'context' in latest_intervention:
                st.write(f"**干预背景:** {latest_intervention['context']}")
            
            # 显示玩家情绪总结（如果有的话）
            if 'player_mood' in latest_intervention:
                st.write(f"**玩家情绪总结:** {latest_intervention['player_mood']}")
            
            st.markdown("---")
            
            # Agent思考链
            st.subheader("🧠 Agent 思考链")
            
            # 检查是否有intermediate_steps
            if 'intermediate_steps' in latest_intervention and latest_intervention['intermediate_steps']:
                for i, step in enumerate(latest_intervention['intermediate_steps']):
                    st.markdown(f"**步骤 {i+1}:**")
                    
                    # 如果step是元组格式 (action, observation)
                    if isinstance(step, tuple) and len(step) == 2:
                        action, observation = step
                        st.markdown(f"**思考:** {getattr(action, 'log', '正在分析...')}")
                        st.markdown(f"**工具调用:** {getattr(action, 'tool', '未知工具')}")
                        st.markdown(f"**观察:** {observation}")
                    else:
                        # 如果是其他格式，直接显示
                        st.markdown(f"**内容:** {step}")
                    
                    st.markdown("---")
            else:
                st.info("暂无详细的思考过程记录")
            
            st.markdown("---")
            
            # 完整的返回结果
            with st.expander("🔍 查看完整JSON结果"):
                st.json(latest_intervention)
                
        else:
            st.info("暂无分析结果，请在第三栏生成一些动作来触发Agent分析")
    
    # 第三栏：动作生成器
    with col3:
        st.header("🎮 动作生成器")
        
        # 动作生成按钮区域
        st.subheader("选择要生成的动作类型：")
        
        # 战斗相关动作
        st.markdown("**⚔️ 战斗动作**")
        
        if st.button("🏆 战斗胜利", use_container_width=True):
            generate_action(ActionType.BATTLE_WIN)
        
        if st.button("💀 战斗失败", use_container_width=True):
            generate_action(ActionType.BATTLE_LOSE)
        
        if st.button("⚡ 技能使用", use_container_width=True):
            generate_action(ActionType.SKILL_USE)
        
        # 抽卡相关动作
        st.markdown("**🎴 抽卡动作**")
        
        if st.button("✨ 抽到稀有卡", use_container_width=True):
            generate_action(ActionType.CARD_DRAW, {"rarity": "legendary"})
        
        if st.button("📦 普通抽卡", use_container_width=True):
            generate_action(ActionType.CARD_DRAW, {"rarity": "common"})
        
        if st.button("💎 购买道具", use_container_width=True):
            generate_action(ActionType.ITEM_PURCHASE)
        
        # 社交相关动作
        st.markdown("**👥 社交动作**")
        
        if st.button("💬 发送消息", use_container_width=True):
            generate_action(ActionType.CHAT_MESSAGE)
        
        if st.button("🎁 赠送礼物", use_container_width=True):
            generate_action(ActionType.GIFT_SEND)
        
        if st.button("🏃 退出游戏", use_container_width=True):
            generate_action(ActionType.GAME_EXIT)
    
    # 历史记录区域（移到底部）
    st.markdown("---")
    st.header("📜 历史记录")
    
    # 动作历史
    with st.expander("🎯 动作历史", expanded=False):
        if st.session_state.action_history:
            for i, action_data in enumerate(reversed(st.session_state.action_history[-10:])):
                st.write(f"**{i+1}.** {action_data['timestamp']} - {action_data['action_type']} - {action_data.get('details', '')}")
        else:
            st.info("暂无动作历史")
    
    # 干预历史
    with st.expander("🤖 Agent干预历史", expanded=False):
        if st.session_state.intervention_history:
            for i, intervention in enumerate(reversed(st.session_state.intervention_history[-5:])):
                st.write(f"**干预 {i+1}:**")
                st.json(intervention)
                st.markdown("---")
        else:
            st.info("暂无干预历史")

def generate_action(action_type: ActionType, details: Dict[str, Any] = None):
    """生成指定类型的动作并触发Agent分析"""
    try:
        # 创建动作对象
        action = PlayerAction(
            action_id=f"action_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            action_type=action_type,
            player_id=st.session_state.player.player_id,
            timestamp=datetime.now(),
            metadata=details or {}
        )
        
        # 记录动作历史
        action_data = {
            "timestamp": action.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "action_type": action_type.value,
            "details": str(details) if details else ""
        }
        st.session_state.action_history.append(action_data)
        
        # 触发Agent分析
        with st.spinner("Agent正在分析中..."):
            result = st.session_state.agent.process_player_action(
                st.session_state.player,
                action
            )
        
        # 记录干预结果
        if result:
            st.session_state.intervention_history.append(result)
            
            # 显示成功消息
            st.success(f"✅ 成功生成{action_type.value}动作并完成Agent分析！")
            
            # 如果有干预建议，显示通知
            if result.get('intervention_applied'):
                st.info("🤖 Agent已应用干预策略！")
        
        # 刷新页面以显示最新结果
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ 生成动作时出错: {str(e)}")
        st.exception(e)

if __name__ == "__main__":
    main()