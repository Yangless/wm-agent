import streamlit as st
import sys
import os
from datetime import datetime, timedelta
import json
from typing import Dict, Any, List
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots



project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from models.player import Player
from models.action import PlayerAction, ActionType
from agent.smart_game_agent import SmartGameAgent
from config.settings import Settings

# 页面配置
st.set_page_config(
    page_title="智能游戏Agent可视化界面",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}
.action-button {
    width: 100%;
    margin: 0.2rem 0;
}
.intervention-alert {
    background-color: #e8f4fd;
    border-left: 4px solid #1f77b4;
    padding: 1rem;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# 初始化session state
if 'player' not in st.session_state:
    st.session_state.player = Player(
        player_id="demo_player_001",
        username="玩家1",
        registration_date=datetime.now(),
        level=15,
        experience=2500,
        coins=1000,
        gems=50
    )

if 'agent' not in st.session_state:
    settings = Settings()
    st.session_state.agent = SmartGameAgent(settings)

if 'action_history' not in st.session_state:
    st.session_state.action_history = []

if 'intervention_history' not in st.session_state:
    st.session_state.intervention_history = []

if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = {
        'emotions': [],
        'bot_scores': [],
        'churn_scores': [],
        'timestamps': []
    }

def main():
    st.title("🎮 智能游戏Agent可视化界面")
    st.markdown("实时监控玩家行为，智能分析情绪状态，预测风险并提供个性化干预")
    st.markdown("---")
    
    # 侧边栏 - 玩家信息和控制面板
    with st.sidebar:
        st.header("👤 玩家信息")
        player = st.session_state.player
        
        # 玩家基础信息
        col1, col2 = st.columns(2)
        with col1:
            st.metric("等级", player.level)
            st.metric("金币", player.coins)
        with col2:
            st.metric("经验值", player.experience)
            st.metric("宝石", player.gems)
        
        st.markdown("---")
        
        # 当前状态指标
        st.header("📊 实时状态")
        
        # 情绪状态
        if hasattr(player, 'current_emotions') and player.current_emotions:
            st.subheader("😊 当前情绪")
            emotion_text = ", ".join(player.current_emotions)
            st.info(emotion_text)
        else:
            st.info("暂无情绪数据")
        
        # 风险指标
        if hasattr(player, 'bot_risk_level'):
            risk_color = "🟢" if player.bot_risk_level == "low" else "🟡" if player.bot_risk_level == "medium" else "🔴"
            st.metric("🤖 机器人风险", f"{risk_color} {player.bot_risk_level}")
        
        if hasattr(player, 'churn_risk_level'):
            churn_color = "🟢" if player.churn_risk_level == "low" else "🟡" if player.churn_risk_level == "medium" else "🔴"
            st.metric("📉 流失风险", f"{churn_color} {player.churn_risk_level}")
        
        st.markdown("---")
        
        # 控制面板
        st.header("⚙️ 控制面板")
        if st.button("🔄 重置玩家数据", use_container_width=True):
            reset_player_data()
        
        if st.button("📊 导出分析报告", use_container_width=True):
            export_analysis_report()
    
    # 主界面布局
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 动作生成", "🤖 Agent分析", "📈 数据可视化", "📜 历史记录"])
    
    with tab1:
        render_action_generator()
    
    with tab2:
        render_agent_analysis()
    
    with tab3:
        render_data_visualization()
    
    with tab4:
        render_history_records()

def render_action_generator():
    """渲染动作生成器界面"""
    st.header("🎯 动作生成器")
    st.markdown("点击下方按钮生成不同类型的玩家动作，Agent将实时分析并提供干预建议")
    
    # 战斗相关动作
    st.subheader("⚔️ 战斗动作")
    battle_col1, battle_col2, battle_col3, battle_col4 = st.columns(4)
    
    with battle_col1:
        if st.button("🏆 战斗胜利", use_container_width=True, type="primary"):
            generate_action(ActionType.BATTLE_WIN, {"enemy_type": "boss", "reward": "legendary_item"})
    
    with battle_col2:
        if st.button("💀 战斗失败", use_container_width=True):
            generate_action(ActionType.BATTLE_LOSE, {"enemy_type": "elite", "attempts": 3})
    
    with battle_col3:
        if st.button("⚡ 技能使用", use_container_width=True):
            generate_action(ActionType.SKILL_USE, {"skill_name": "ultimate_attack", "mana_cost": 50})
    
    with battle_col4:
        if st.button("🛡️ 防御动作", use_container_width=True):
            generate_action(ActionType.SKILL_USE, {"skill_name": "shield_block", "damage_reduced": 80})
    
    # 抽卡相关动作
    st.subheader("🎴 抽卡动作")
    card_col1, card_col2, card_col3, card_col4 = st.columns(4)
    
    with card_col1:
        if st.button("✨ 抽到传说卡", use_container_width=True, type="primary"):
            generate_action(ActionType.CARD_DRAW, {"rarity": "legendary", "card_name": "Dragon Lord"})
    
    with card_col2:
        if st.button("🎭 抽到史诗卡", use_container_width=True):
            generate_action(ActionType.CARD_DRAW, {"rarity": "epic", "card_name": "Fire Mage"})
    
    with card_col3:
        if st.button("📦 普通抽卡", use_container_width=True):
            generate_action(ActionType.CARD_DRAW, {"rarity": "common", "card_name": "Goblin Warrior"})
    
    with card_col4:
        if st.button("💸 抽卡失败", use_container_width=True):
            generate_action(ActionType.CARD_DRAW, {"rarity": "common", "duplicate": True})
    
    # 经济相关动作
    st.subheader("💰 经济动作")
    econ_col1, econ_col2, econ_col3, econ_col4 = st.columns(4)
    
    with econ_col1:
        if st.button("💎 购买道具", use_container_width=True):
            generate_action(ActionType.ITEM_PURCHASE, {"item": "health_potion", "cost": 100})
    
    with econ_col2:
        if st.button("🏪 商店浏览", use_container_width=True):
            generate_action(ActionType.ITEM_PURCHASE, {"action": "browse", "time_spent": 120})
    
    with econ_col3:
        if st.button("💰 获得奖励", use_container_width=True):
            generate_action(ActionType.ITEM_PURCHASE, {"reward_type": "daily_bonus", "amount": 500})
    
    with econ_col4:
        if st.button("📈 升级装备", use_container_width=True):
            generate_action(ActionType.ITEM_PURCHASE, {"upgrade": "weapon", "level": "+1"})
    
    # 社交相关动作
    st.subheader("👥 社交动作")
    social_col1, social_col2, social_col3, social_col4 = st.columns(4)
    
    with social_col1:
        if st.button("💬 发送消息", use_container_width=True):
            generate_action(ActionType.CHAT_MESSAGE, {"message_type": "friendly", "recipient": "guild_member"})
    
    with social_col2:
        if st.button("🎁 赠送礼物", use_container_width=True):
            generate_action(ActionType.GIFT_SEND, {"gift_type": "rare_item", "recipient": "friend"})
    
    with social_col3:
        if st.button("🤝 加入公会", use_container_width=True):
            generate_action(ActionType.CHAT_MESSAGE, {"action": "join_guild", "guild_name": "Dragon Slayers"})
    
    with social_col4:
        if st.button("🏃 退出游戏", use_container_width=True):
            generate_action(ActionType.GAME_EXIT, {"session_duration": 45, "reason": "normal"})

def render_agent_analysis():
    """渲染Agent分析结果界面"""
    st.header("🤖 Agent分析结果")
    
    if st.session_state.intervention_history:
        latest_intervention = st.session_state.intervention_history[-1]
        
        # 最新分析结果概览
        st.subheader("📊 最新分析概览")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'emotion_analysis' in latest_intervention:
                emotion_data = latest_intervention['emotion_analysis']
                intervention_type = emotion_data.get('intervention_type', 'none')
                
                if intervention_type == 'reward':
                    st.success("🎉 积极情绪 - 奖励干预")
                elif intervention_type == 'comfort':
                    st.warning("😔 消极情绪 - 安慰干预")
                else:
                    st.info("😐 情绪稳定")
        
        with col2:
            if 'bot_detection' in latest_intervention:
                bot_data = latest_intervention['bot_detection']
                risk_level = bot_data.get('risk_level', 'unknown')
                
                if risk_level == 'high':
                    st.error("🚨 高机器人风险")
                elif risk_level == 'medium':
                    st.warning("⚠️ 中等机器人风险")
                else:
                    st.success("✅ 低机器人风险")
        
        with col3:
            if 'churn_analysis' in latest_intervention:
                churn_data = latest_intervention['churn_analysis']
                risk_level = churn_data.get('risk_level', 'unknown')
                
                if risk_level == 'high':
                    st.error("📉 高流失风险")
                elif risk_level == 'medium':
                    st.warning("⚠️ 中等流失风险")
                else:
                    st.success("📈 低流失风险")
        
        # 详细分析结果
        st.subheader("🔍 详细分析结果")
        
        # 情绪分析详情
        if 'emotion_analysis' in latest_intervention:
            with st.expander("😊 情绪分析详情", expanded=True):
                emotion_data = latest_intervention['emotion_analysis']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**积极情绪:**")
                    positive_emotions = emotion_data.get('dominant_positive_emotions', [])
                    if positive_emotions:
                        for emotion in positive_emotions:
                            st.write(f"• {emotion}")
                    else:
                        st.write("无")
                
                with col2:
                    st.write("**消极情绪:**")
                    negative_emotions = emotion_data.get('dominant_negative_emotions', [])
                    if negative_emotions:
                        for emotion in negative_emotions:
                            st.write(f"• {emotion}")
                    else:
                        st.write("无")
                
                if 'intervention_suggestions' in emotion_data:
                    st.write("**干预建议:**")
                    for suggestion in emotion_data['intervention_suggestions']:
                        st.write(f"• {suggestion}")
        
        # 机器人检测详情
        if 'bot_detection' in latest_intervention:
            with st.expander("🤖 机器人检测详情"):
                bot_data = latest_intervention['bot_detection']
                st.json(bot_data)
        
        # 流失风险分析详情
        if 'churn_analysis' in latest_intervention:
            with st.expander("📉 流失风险分析详情"):
                churn_data = latest_intervention['churn_analysis']
                st.json(churn_data)
        
        # 干预策略
        if latest_intervention.get('intervention_applied'):
            st.subheader("🎯 应用的干预策略")
            
            intervention_plan = latest_intervention.get('intervention_plan', {})
            if intervention_plan:
                st.markdown(f"**消息内容:** {intervention_plan.get('message_content', '无')}")
                
                rewards = intervention_plan.get('rewards', [])
                if rewards:
                    st.write("**奖励内容:**")
                    for reward in rewards:
                        st.write(f"• {reward}")
    else:
        st.info("🔄 暂无分析结果，请在动作生成器中生成一些动作来触发Agent分析")
        
        # 显示示例分析流程
        st.subheader("📋 分析流程说明")
        st.markdown("""
        1. **动作捕获**: 监控玩家的游戏行为和动作
        2. **情绪分析**: 基于行为模式分析玩家情绪状态
        3. **风险评估**: 检测机器人行为和流失风险
        4. **智能干预**: 根据分析结果提供个性化干预策略
        5. **效果跟踪**: 持续监控干预效果并优化策略
        """)

def render_data_visualization():
    """渲染数据可视化界面"""
    st.header("📈 数据可视化")
    
    if not st.session_state.analysis_data['timestamps']:
        st.info("📊 暂无数据可视化，请先生成一些动作来收集分析数据")
        return
    
    # 创建数据框
    df = pd.DataFrame(st.session_state.analysis_data)
    
    # 情绪趋势图
    st.subheader("😊 情绪变化趋势")
    if df['emotions'].notna().any():
        emotion_fig = px.line(df, x='timestamps', y='emotions', 
                             title='玩家情绪变化趋势',
                             labels={'emotions': '情绪评分', 'timestamps': '时间'})
        emotion_fig.update_layout(height=400)
        st.plotly_chart(emotion_fig, use_container_width=True)
    
    # 风险评分图表
    st.subheader("⚠️ 风险评分监控")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if df['bot_scores'].notna().any():
            bot_fig = px.line(df, x='timestamps', y='bot_scores',
                             title='机器人风险评分',
                             labels={'bot_scores': '风险评分', 'timestamps': '时间'})
            bot_fig.add_hline(y=0.7, line_dash="dash", line_color="red", 
                             annotation_text="高风险阈值")
            bot_fig.update_layout(height=300)
            st.plotly_chart(bot_fig, use_container_width=True)
    
    with col2:
        if df['churn_scores'].notna().any():
            churn_fig = px.line(df, x='timestamps', y='churn_scores',
                               title='流失风险评分',
                               labels={'churn_scores': '风险评分', 'timestamps': '时间'})
            churn_fig.add_hline(y=0.6, line_dash="dash", line_color="orange",
                               annotation_text="中风险阈值")
            churn_fig.update_layout(height=300)
            st.plotly_chart(churn_fig, use_container_width=True)
    
    # 综合仪表板
    st.subheader("📊 综合监控仪表板")
    
    # 创建子图
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('动作频率', '干预次数', '风险分布', '情绪分布'),
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "pie"}, {"type": "pie"}]]
    )
    
    # 动作频率统计
    if st.session_state.action_history:
        action_types = [action['action_type'] for action in st.session_state.action_history]
        action_counts = pd.Series(action_types).value_counts()
        
        fig.add_trace(
            go.Bar(x=action_counts.index, y=action_counts.values, name="动作频率"),
            row=1, col=1
        )
    
    # 干预次数统计
    if st.session_state.intervention_history:
        intervention_types = []
        for intervention in st.session_state.intervention_history:
            if intervention.get('intervention_applied'):
                emotion_data = intervention.get('emotion_analysis', {})
                intervention_type = emotion_data.get('intervention_type', 'none')
                intervention_types.append(intervention_type)
        
        if intervention_types:
            intervention_counts = pd.Series(intervention_types).value_counts()
            fig.add_trace(
                go.Bar(x=intervention_counts.index, y=intervention_counts.values, name="干预次数"),
                row=1, col=2
            )
    
    fig.update_layout(height=600, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

def render_history_records():
    """渲染历史记录界面"""
    st.header("📜 历史记录")
    
    # 统计信息
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总动作数", len(st.session_state.action_history))
    
    with col2:
        st.metric("总干预次数", len(st.session_state.intervention_history))
    
    with col3:
        intervention_count = sum(1 for i in st.session_state.intervention_history if i.get('intervention_applied'))
        st.metric("有效干预次数", intervention_count)
    
    with col4:
        if st.session_state.action_history:
            last_action_time = st.session_state.action_history[-1]['timestamp']
            st.metric("最后动作时间", last_action_time.split(' ')[1] if ' ' in last_action_time else last_action_time)
    
    # 动作历史
    st.subheader("🎯 动作历史")
    
    if st.session_state.action_history:
        # 创建动作历史表格
        action_df = pd.DataFrame(st.session_state.action_history)
        action_df = action_df.sort_values('timestamp', ascending=False)
        
        # 显示最近20条记录
        st.dataframe(
            action_df.head(20),
            use_container_width=True,
            hide_index=True
        )
        
        # 下载按钮
        csv = action_df.to_csv(index=False)
        st.download_button(
            label="📥 下载动作历史CSV",
            data=csv,
            file_name=f"action_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("暂无动作历史记录")
    
    # 干预历史
    st.subheader("🤖 干预历史")
    
    if st.session_state.intervention_history:
        for i, intervention in enumerate(reversed(st.session_state.intervention_history[-10:])):
            with st.expander(f"干预记录 {len(st.session_state.intervention_history) - i}", expanded=False):
                
                # 基本信息
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**时间:** {intervention.get('timestamp', '未知')}")
                    st.write(f"**是否应用干预:** {'是' if intervention.get('intervention_applied') else '否'}")
                
                with col2:
                    if 'emotion_analysis' in intervention:
                        emotion_data = intervention['emotion_analysis']
                        intervention_type = emotion_data.get('intervention_type', 'none')
                        st.write(f"**干预类型:** {intervention_type}")
                
                # 详细数据
                st.json(intervention)
    else:
        st.info("暂无干预历史记录")

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
        with st.spinner("🤖 Agent正在分析中..."):
            result = st.session_state.agent.process_player_action(
                st.session_state.player,
                action
            )
        
        # 记录干预结果
        if result:
            # 添加时间戳
            result['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.intervention_history.append(result)
            
            # 更新分析数据用于可视化
            update_analysis_data(result)
            
            # 显示成功消息
            st.success(f"✅ 成功生成{action_type.value}动作并完成Agent分析！")
            
            # 如果有干预建议，显示通知
            if result.get('intervention_applied'):
                st.balloons()  # 添加庆祝动画
                st.info("🎯 Agent已应用智能干预策略！")
        
        # 刷新页面以显示最新结果
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ 生成动作时出错: {str(e)}")
        st.exception(e)

def update_analysis_data(result: Dict[str, Any]):
    """更新分析数据用于可视化"""
    timestamp = datetime.now()
    
    # 添加时间戳
    st.session_state.analysis_data['timestamps'].append(timestamp)
    
    # 添加情绪数据
    emotion_score = 0
    if 'emotion_analysis' in result:
        emotion_data = result['emotion_analysis']
        intervention_type = emotion_data.get('intervention_type', 'none')
        
        if intervention_type == 'reward':
            emotion_score = 1
        elif intervention_type == 'comfort':
            emotion_score = -1
    
    st.session_state.analysis_data['emotions'].append(emotion_score)
    
    # 添加机器人风险评分
    bot_score = 0
    if 'bot_detection' in result:
        bot_data = result['bot_detection']
        risk_level = bot_data.get('risk_level', 'low')
        
        if risk_level == 'high':
            bot_score = 0.8
        elif risk_level == 'medium':
            bot_score = 0.5
        else:
            bot_score = 0.2
    
    st.session_state.analysis_data['bot_scores'].append(bot_score)
    
    # 添加流失风险评分
    churn_score = 0
    if 'churn_analysis' in result:
        churn_data = result['churn_analysis']
        risk_level = churn_data.get('risk_level', 'low')
        
        if risk_level == 'high':
            churn_score = 0.8
        elif risk_level == 'medium':
            churn_score = 0.5
        else:
            churn_score = 0.2
    
    st.session_state.analysis_data['churn_scores'].append(churn_score)
    
    # 保持数据长度在合理范围内
    max_data_points = 50
    for key in st.session_state.analysis_data:
        if len(st.session_state.analysis_data[key]) > max_data_points:
            st.session_state.analysis_data[key] = st.session_state.analysis_data[key][-max_data_points:]

def reset_player_data():
    """重置玩家数据"""
    st.session_state.action_history = []
    st.session_state.intervention_history = []
    st.session_state.analysis_data = {
        'emotions': [],
        'bot_scores': [],
        'churn_scores': [],
        'timestamps': []
    }
    st.success("✅ 玩家数据已重置")
    st.rerun()

def export_analysis_report():
    """导出分析报告"""
    report_data = {
        'player_info': {
            'player_id': st.session_state.player.player_id,
            'level': st.session_state.player.level,
            'experience': st.session_state.player.experience,
            'coins': st.session_state.player.coins,
            'gems': st.session_state.player.gems
        },
        'action_history': st.session_state.action_history,
        'intervention_history': st.session_state.intervention_history,
        'analysis_data': st.session_state.analysis_data,
        'export_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    report_json = json.dumps(report_data, ensure_ascii=False, indent=2)
    
    st.download_button(
        label="📥 下载分析报告JSON",
        data=report_json,
        file_name=f"agent_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

if __name__ == "__main__":
    main()