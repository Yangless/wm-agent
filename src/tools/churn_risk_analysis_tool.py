from typing import Dict, List, Optional, Any , Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import json
from datetime import datetime, timedelta

from ..models.player import Player, ChurnRiskLevel
from ..llm.llm_client import LLMClient


class ChurnRiskAnalysisInput(BaseModel):
    """流失风险分析工具输入参数"""
    player_id: str = Field(description="玩家ID")
    behavior_data: Dict[str, Any] = Field(description="玩家行为数据")
    time_window_days: int = Field(default=30, description="分析时间窗口（天）")
    analysis_depth: str = Field(default="standard", description="分析深度: basic, standard, detailed")


class ChurnRiskAnalysisTool(BaseTool):
    """流失风险分析工具
    
    使用LLM分析玩家行为模式，预测玩家的流失风险。
    分析包括活跃度变化、参与度下降、消费行为变化等多个维度。
    """
    
    # name = "churn_risk_analysis"
    # description = "分析玩家行为模式，预测玩家的流失风险"
    # args_schema = ChurnRiskAnalysisInput
    name: str = "churn_risk_analysis"
    description: str = "分析玩家行为模式，预测玩家的流失风险"
    args_schema: Type[ChurnRiskAnalysisInput] = ChurnRiskAnalysisInput
    
    # def __init__(self, llm_client: LLMClient, player_manager=None):
    #     super().__init__()
    #     self.llm_client = llm_client
    #     self.player_manager = player_manager
    llm_client: LLMClient
    player_manager: Optional[Any] = None
    
    def _run(self, player_id: str, behavior_data: Dict[str, Any], 
             time_window_days: int = 30, analysis_depth: str = "standard") -> str:
        """执行流失风险分析
        
        Args:
            player_id: 玩家ID
            behavior_data: 玩家行为数据
            time_window_days: 分析时间窗口
            analysis_depth: 分析深度
            
        Returns:
            str: 分析结果的JSON字符串
        """
        try:
            # 获取玩家信息
            player = self._get_player_info(player_id)
            
            # 构建分析提示
            analysis_prompt = self._build_analysis_prompt(
                player, behavior_data, time_window_days, analysis_depth
            )
            
            # 调用LLM进行分析
            response = self.llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.2  # 较低的温度以获得更稳定的预测
            )
            
            # 解析LLM响应
            analysis_result = self._parse_llm_response(response)
            
            # 更新玩家流失风险状态
            if self.player_manager and analysis_result.get("success"):
                self._update_player_churn_risk(player_id, analysis_result)
            
            return json.dumps(analysis_result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "player_id": player_id,
                "timestamp": datetime.now().isoformat()
            }
            return json.dumps(error_result, ensure_ascii=False, indent=2)
    
    def _get_system_prompt(self) -> str:
        """获取系统提示"""
        return """
你是一个专业的游戏用户流失预测专家。你的任务是分析玩家的行为数据，预测玩家的流失风险。

流失风险的关键指标包括：

1. **活跃度变化**：
   - 登录频率下降（如从每日登录变为每周登录）
   - 游戏时长减少（如从每日2小时变为30分钟）
   - 连续未登录天数增加
   - 活跃时段变化（如从黄金时段转为非黄金时段）

2. **参与度下降**：
   - 完成任务数量减少
   - 参与活动频率降低
   - 社交互动减少（如聊天、组队频率下降）
   - 探索新内容的意愿降低

3. **消费行为变化**：
   - 付费频率下降或停止付费
   - 购买物品类型变化（如从成长型道具转为消耗型道具）
   - 对促销活动的响应度降低
   - 游戏内货币使用减少

4. **游戏进度停滞**：
   - 等级提升速度放缓
   - 长时间停留在同一关卡或区域
   - 技能或装备升级频率降低
   - 成就解锁速度下降

5. **负面体验累积**：
   - 连续失败次数增加
   - 挫败感指标上升
   - 客服投诉或负面反馈
   - 对游戏更新的负面反应

6. **生命周期阶段**：
   - 新手期：前7天的留存关键期
   - 成长期：1-3个月的习惯养成期
   - 成熟期：长期玩家的疲劳期
   - 衰退期：活跃度明显下降期

风险等级定义：
- LOW: 行为正常，流失风险较低
- MEDIUM: 存在一些风险信号，需要关注
- HIGH: 多项指标异常，流失风险较高
- CRITICAL: 极高流失风险，需要立即干预

请基于提供的数据进行综合分析，预测流失概率和时间窗口。
"""
    
    def _build_analysis_prompt(self, player: Optional[Player], behavior_data: Dict[str, Any], 
                              time_window_days: int, analysis_depth: str) -> str:
        """构建分析提示"""
        prompt_parts = []
        
        # 玩家基本信息
        if player:
            # 计算玩家生命周期
            account_age_days = 0
            if hasattr(player, 'created_at') and player.created_at:
                account_age_days = (datetime.now() - player.created_at).days
            
            prompt_parts.append(f"""
玩家基本信息：
- 玩家ID: {player.player_id}
- 用户名: {player.username}
- 账户年龄: {account_age_days}天
- VIP等级: {player.vip_level}
- 总游戏时长: {player.total_playtime_hours}小时
- 最后登录: {player.last_login}
- 总消费: ${player.total_spent}
- 当前状态: {player.current_status.value}
- 挫败等级: {player.frustration_level}
- 连续失败次数: {player.consecutive_failures}
""")
            
            # 历史流失风险记录
            if hasattr(player, 'churn_risk_level') and player.churn_risk_level:
                prompt_parts.append(f"""
历史风险评估：
- 当前风险等级: {player.churn_risk_level.value}
- 预测分数: {getattr(player, 'churn_prediction_score', 0.0)}
- 上次分析时间: {getattr(player, 'last_churn_analysis', '未知')}
- 风险因子: {getattr(player, 'churn_risk_factors', [])}
- 预测流失日期: {getattr(player, 'predicted_churn_date', '未知')}
""")
            
            # 情绪状态（如果有）
            if hasattr(player, 'current_emotions') and player.current_emotions:
                prompt_parts.append(f"""
当前情绪状态：
- 当前情绪: {[e.value for e in player.current_emotions]}
- 主要负面情绪: {[e.value for e in getattr(player, 'dominant_negative_emotions', [])]}
- 主要正面情绪: {getattr(player, 'dominant_positive_emotion', {}).value if getattr(player, 'dominant_positive_emotion') else '无'}
""")
        
        # 行为数据分析
        prompt_parts.append(f"""
行为数据分析（最近{time_window_days}天）：
{json.dumps(behavior_data, ensure_ascii=False, indent=2)}
""")
        
        # 分析要求
        if analysis_depth == "basic":
            analysis_requirement = "请进行基础流失风险评估，重点关注明显的风险信号。"
        elif analysis_depth == "detailed":
            analysis_requirement = "请进行详细流失风险分析，包括深度行为分析、趋势预测和干预建议。"
        else:  # standard
            analysis_requirement = "请进行标准流失风险分析，综合评估各项风险指标。"
        
        prompt_parts.append(f"""
分析要求：
{analysis_requirement}

请重点分析以下维度：
1. 活跃度趋势（登录频率、游戏时长）
2. 参与度变化（任务完成、活动参与）
3. 消费行为模式
4. 游戏进度情况
5. 社交互动水平
6. 负面体验累积
7. 生命周期阶段

请以以下JSON格式返回结果：
{{
    "success": true,
    "player_id": "玩家ID",
    "timestamp": "分析时间",
    "churn_risk_level": "LOW/MEDIUM/HIGH/CRITICAL",
    "churn_probability": 0.65,
    "confidence_score": 0.80,
    "predicted_churn_days": 14,
    "risk_factors": [
        {{
            "category": "活跃度下降",
            "description": "登录频率从每日降至每周",
            "severity": "high",
            "trend": "worsening",
            "evidence": ["具体数据1", "具体数据2"]
        }}
    ],
    "behavioral_analysis": {{
        "activity_trend": -0.4,
        "engagement_change": -0.3,
        "spending_pattern": -0.2,
        "progression_rate": -0.1,
        "social_interaction": -0.5,
        "negative_experience": 0.6,
        "lifecycle_stage": "mature"
    }},
    "intervention_recommendations": [
        {{
            "priority": "high",
            "action": "个性化奖励推送",
            "description": "基于玩家偏好推送定制化奖励",
            "expected_impact": 0.3
        }}
    ],
    "monitoring_suggestions": [
        "每日监控登录状态",
        "关注消费行为变化"
    ],
    "next_analysis_days": 7
}}
""")
        
        return "\n".join(prompt_parts)
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            # 尝试直接解析JSON
            if response.strip().startswith('{'):
                return json.loads(response)
            
            # 如果响应包含其他内容，尝试提取JSON部分
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # 如果无法解析，返回错误结果
            return {
                "success": False,
                "error": "无法解析LLM响应",
                "raw_response": response,
                "timestamp": datetime.now().isoformat()
            }
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"JSON解析错误: {str(e)}",
                "raw_response": response,
                "timestamp": datetime.now().isoformat()
            }
    
    def _update_player_churn_risk(self, player_id: str, analysis_result: Dict[str, Any]):
        """更新玩家流失风险状态"""
        try:
            if not self.player_manager:
                return
            
            player = self.player_manager.get_player(player_id)
            if not player:
                return
            
            # 提取风险信息
            risk_level_str = analysis_result.get("churn_risk_level", "LOW")
            prediction_score = analysis_result.get("churn_probability", 0.0)
            predicted_days = analysis_result.get("predicted_churn_days", 30)
            
            # 提取风险因子
            risk_factors = []
            for factor in analysis_result.get("risk_factors", []):
                risk_factors.append(f"{factor.get('category', '')}: {factor.get('description', '')}")
            
            try:
                risk_level = ChurnRiskLevel(risk_level_str)
            except ValueError:
                risk_level = ChurnRiskLevel.LOW
            
            # 计算预测流失日期
            predicted_date = None
            if predicted_days > 0:
                predicted_date = datetime.now() + timedelta(days=predicted_days)
            
            # 更新玩家流失风险
            player.update_churn_risk(risk_level, prediction_score, risk_factors, predicted_date)
                
        except Exception as e:
            print(f"更新玩家流失风险状态时出错: {str(e)}")
    
    def _get_player_info(self, player_id: str) -> Optional[Player]:
        """获取玩家信息"""
        if self.player_manager:
            return self.player_manager.get_player(player_id)
        return None
    
    async def _arun(self, *args, **kwargs):
        """异步运行（暂不实现）"""
        raise NotImplementedError("ChurnRiskAnalysisTool不支持异步运行")