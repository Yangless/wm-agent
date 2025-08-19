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
    initial_sidebar_state="expanded"
)

# 初始化session state
if 'player' not in st.session_state:
    st.session_state.player = Player(
        player_id="player_001",
        username="起个名字真难",
        registration_date=datetime.now(),


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
    
    # 侧边栏 - 玩家信息
    with st.sidebar:
        st.header("👤 玩家信息")
        player = st.session_state.player

        # 使用 st.write 和 Markdown 语法
        st.write(f"**玩家ID:** {player.player_id}")
        st.write(f"**用户名:** {player.username}")
        st.write(f"**等级:** {player.level}")
        st.write(f"**VIP等级:** {player.vip_level}")
        
        formatted_date = player.registration_date.strftime("%Y-%m-%d")
        st.write(f"**注册时间:** {formatted_date}")



        
        st.markdown("---")
        st.header("📊 当前状态")

        # --- 显示当前情绪状态 (已优化) ---
        st.subheader("😊 当前情绪")

        # 检查属性是否存在且列表不为空
        if hasattr(player, 'current_emotions') and player.current_emotions:
            # 遍历并显示每个情绪的 .value
            for emotion in player.current_emotions:
                st.write(f"• {emotion.value.capitalize()}") # 使用 .capitalize() 让首字母大写，更美观
        else:
            # 如果列表为空，显示提示信息
            st.info("未知 (暂无情绪分析数据)")

        # --- 显示风险等级 (关键修改) ---
        st.subheader("⚠️ 风险评估")

        # --- 机器人风险等级 (使用 Markdown) ---
        if hasattr(player, 'bot_risk_level') and player.bot_risk_level:
            risk_level_value = player.bot_risk_level.value.upper() # 获取值并转为大写
            
            # 根据风险等级设置颜色
            if risk_level_value == "HIGH":
                color = "red"
            elif risk_level_value == "MEDIUM":
                color = "orange"
            else:
                color = "green"
                
            # 使用 Markdown 和 HTML/CSS 来显示带颜色的文本
            st.markdown(f'🤖 **机器人风险等级:** <span style="color:{color}; font-weight:bold;">{risk_level_value}</span>', unsafe_allow_html=True)
        else:
            st.markdown('🤖 **机器人风险等级:** 未知')

        # --- 流失风险等级 (使用 Markdown) ---
        if hasattr(player, 'churn_risk_level') and player.churn_risk_level:
            churn_level_value = player.churn_risk_level.value.upper()
            
            if churn_level_value in ["HIGH", "CRITICAL"]:
                color = "red"
            elif churn_level_value == "MEDIUM":
                color = "orange"
            else:
                color = "green"
                
            st.markdown(f'📉 **流失风险等级:** <span style="color:{color}; font-weight:bold;">{churn_level_value}</span>', unsafe_allow_html=True)
        else:
            st.markdown('📉 **流失风险等级:** 未知')
    
    # 主界面布局
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🎯 动作生成器")
        
        # 动作生成按钮区域
        st.subheader("选择要生成的动作类型：")
        
        # 战斗相关动作
        st.markdown("**⚔️ 战斗动作**")
        battle_col1, battle_col2, battle_col3 = st.columns(3)
        
        with battle_col1:
            if st.button("🏆 战斗胜利", use_container_width=True):
                generate_action(ActionType.BATTLE_WIN)
        
        with battle_col2:
            if st.button("💀 战斗失败", use_container_width=True):
                generate_action(ActionType.BATTLE_LOSE)
        
        with battle_col3:
            if st.button("⚡ 技能使用", use_container_width=True):
                generate_action(ActionType.SKILL_USE)
        
        # 抽卡相关动作
        st.markdown("**🎴 抽卡动作**")
        card_col1, card_col2, card_col3 = st.columns(3)
        
        with card_col1:
            if st.button("✨ 抽到稀有卡", use_container_width=True):
                generate_action(ActionType.CARD_DRAW, {"rarity": "legendary"})
        
        with card_col2:
            if st.button("📦 普通抽卡", use_container_width=True):
                generate_action(ActionType.CARD_DRAW, {"rarity": "common"})
        
        with card_col3:
            if st.button("💎 购买道具", use_container_width=True):
                generate_action(ActionType.ITEM_PURCHASE)
        
        # 社交相关动作
        st.markdown("**👥 社交动作**")
        social_col1, social_col2, social_col3 = st.columns(3)
        
        with social_col1:
            if st.button("💬 发送消息", use_container_width=True):
                generate_action(ActionType.CHAT_MESSAGE)
        
        with social_col2:
            if st.button("🎁 赠送礼物", use_container_width=True):
                generate_action(ActionType.GIFT_SEND)
        
        with social_col3:
            if st.button("🏃 退出游戏", use_container_width=True):
                generate_action(ActionType.GAME_EXIT)
    
    with col2:
        st.header("🤖 Agent分析结果")
        
        # 显示最新的分析结果
        if st.session_state.intervention_history:
            latest_intervention = st.session_state.intervention_history[-1]
            
            st.subheader("最新干预结果")
            st.json(latest_intervention)
        else:
            st.info("暂无分析结果，请生成一些动作来触发Agent分析")
    
    # 历史记录区域
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