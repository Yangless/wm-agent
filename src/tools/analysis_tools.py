from typing import List, Dict, Any, Optional,Union
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import json
from datetime import datetime, timedelta

from ..data.data_manager import DataManager
from ..models.action import ActionType
from ..models.trigger import TriggerCondition, DEFAULT_TRIGGERS
import traceback
class AnalyzePlayerBehaviorInput(BaseModel):
    """分析玩家行为工具的输入参数"""
    player_id: str = Field(description="玩家ID")
    analysis_depth: str = Field(default="standard", description="分析深度：basic(基础), standard(标准), detailed(详细)")
    time_window_hours: int = Field(default=24, description="分析时间窗口（小时）")

class AnalyzePlayerBehaviorTool(BaseTool):
    """分析玩家行为模式工具
    
    深度分析玩家的行为模式，识别风险信号和干预时机
    """
    
    name: str = "analyze_player_behavior"
    description: str = """深度分析玩家的行为模式，识别情绪状态、风险等级和干预需求。
    输入参数是一个JSON对象，格式为：{"player_id": "玩家ID", "analysis_depth": "basic", "time_window_hours": 24}
    - player_id: 玩家ID (必填)
    - analysis_depth: 分析深度 (可选, basic/standard/detailed, 默认 standard)
    - time_window_hours: 分析时间窗口（小时）(可选, 默认 24)
    返回：JSON格式的详细行为分析报告"""
    args_schema: type = AnalyzePlayerBehaviorInput
    data_manager: DataManager = Field(default_factory=DataManager)

    def _parse_and_validate_input(self, tool_input: Any) -> AnalyzePlayerBehaviorInput:
        """
        解析并验证输入参数，使其能够健壮地处理各种输入格式。
        """
        try:
            if isinstance(tool_input, AnalyzePlayerBehaviorInput):
                return tool_input
            
            elif isinstance(tool_input, str):
                try:
                    data = json.loads(tool_input)
                except json.JSONDecodeError as e:
                    raise ValueError(f"输入不是有效的JSON格式: {str(e)}")
                
                if not isinstance(data, dict):
                    raise ValueError(f"JSON输入必须是一个对象，但收到的是: {type(data).__name__}")
                
                return AnalyzePlayerBehaviorInput(**data)
            
            elif isinstance(tool_input, dict):
                return AnalyzePlayerBehaviorInput(**tool_input)
            
            else:
                raise ValueError(f"不支持的输入类型: {type(tool_input).__name__}")
                
        except ValidationError as e:
            error_details = [f"字段 '{err['loc'][0]}': {err['msg']}" for err in e.errors()]
            raise ValueError(f"输入参数验证失败: {'; '.join(error_details)}")
        
        except Exception as e:
            raise ValueError(f"解析输入时发生未知错误: {str(e)}")

    def _run(self, tool_input: Any) -> str:
        """
        以健壮的方式执行工具的核心逻辑。
        """
        validated_input = None
        try:
            # 步骤1: 解析和验证输入
            validated_input = self._parse_and_validate_input(tool_input)
            player_id = validated_input.player_id
            analysis_depth = validated_input.analysis_depth
            time_window_hours = validated_input.time_window_hours

            # 步骤2: 业务逻辑验证
            if not player_id or not player_id.strip():
                return self._create_error_response("player_id 不能为空")

            # 步骤3: 获取玩家数据
            player = self.data_manager.get_player(player_id)
            if not player:
                return self._create_error_response("玩家不存在", player_id)
            
            # 步骤4: 获取行为数据
            time_window_minutes = time_window_hours * 60
            actions = self.data_manager.get_player_actions(
                player_id=player_id,
                limit=100,
                time_window_minutes=time_window_minutes
            )
            
            # 步骤5: 执行分析
            if analysis_depth == "basic":
                analysis_result = self._basic_analysis(player, actions)
            elif analysis_depth == "detailed":
                analysis_result = self._detailed_analysis(player, actions)
            else:
                analysis_result = self._standard_analysis(player, actions)
            
            # 步骤6: 组合最终结果
            analysis_result.update({
                "player_id": player_id,
                "analysis_timestamp": datetime.now().isoformat(),
                "analysis_depth": analysis_depth,
                "time_window_hours": time_window_hours,
                "total_actions_analyzed": len(actions)
            })
            
            return self._create_success_response(analysis_result)
            
        except ValueError as e:
            # 输入验证/解析错误
            player_id_for_error = validated_input.player_id if validated_input else None
            return self._create_error_response(f"输入错误: {str(e)}", player_id_for_error)
            
        except Exception as e:
            # 其他系统级错误
            traceback.print_exc()
            player_id_for_error = validated_input.player_id if validated_input else None
            return self._create_error_response(f"分析玩家行为时出错: {str(e)}", player_id_for_error)

    def _create_success_response(self, analysis_data: dict) -> str:
        """创建成功的JSON响应"""
        response = {
            "success": True,
            "analysis_report": analysis_data,
            "message": "分析成功"
        }
        return json.dumps(response, ensure_ascii=False, indent=2, default=str)

    def _create_error_response(self, error_msg: str, player_id: str = None) -> str:
        """创建失败的JSON响应"""
        response = {
            "success": False,
            "error": error_msg,
            "analysis_report": None
        }
        if player_id:
            response["player_id"] = player_id
        return json.dumps(response, ensure_ascii=False, indent=2)

    async def _arun(self, tool_input: Any) -> str:
        """
        异步执行 - 保持与 _run 相同的输入处理逻辑。
        """
        return self._run(tool_input)

    # _basic_analysis, _standard_analysis, _detailed_analysis 等分析方法的实现保持不变...
    def _basic_analysis(self, player, actions: List) -> Dict[str, Any]:
        """基础分析"""
        if not actions:
            return {
                "risk_level": 1,
                "emotional_state": "unknown",
                "intervention_needed": False,
                "summary": "无足够数据进行分析"
            }
        
        failure_count = sum(1 for action in actions if action.is_failure())
        success_count = sum(1 for action in actions if action.is_success())
        
        risk_level = 1
        if player.consecutive_failures >= 3:
            risk_level = 8
        elif player.consecutive_failures >= 2:
            risk_level = 5
        elif failure_count > success_count:
            risk_level = 3
        
        emotional_state = "neutral"
        if player.frustration_level >= 7:
            emotional_state = "frustrated"
        elif player.frustration_level >= 4:
            emotional_state = "concerned"
        elif success_count > failure_count * 2:
            emotional_state = "positive"
        
        return {
            "risk_level": risk_level,
            "emotional_state": emotional_state,
            "intervention_needed": risk_level >= 6,
            "failure_count": failure_count,
            "success_count": success_count,
            "consecutive_failures": player.consecutive_failures,
            "summary": f"玩家当前风险等级为{risk_level}，情绪状态：{emotional_state}"
        }
    
    def _standard_analysis(self, player, actions: List) -> Dict[str, Any]:
        """标准分析"""
        basic_result = self._basic_analysis(player, actions)
        
        if not actions:
            return basic_result
        
        behavior_pattern = self.data_manager.analyze_player_behavior_pattern(player.player_id)
        time_analysis = self._analyze_time_patterns(actions)
        social_analysis = self._analyze_social_behavior(actions)
        trigger_analysis = self._check_trigger_conditions(player, actions)
        intervention_suggestions = self._generate_intervention_suggestions(
            player, behavior_pattern, trigger_analysis
        )
        
        result = basic_result.copy()
        result.update({
            "behavior_pattern": behavior_pattern,
            "time_analysis": time_analysis,
            "social_analysis": social_analysis,
            "trigger_analysis": trigger_analysis,
            "intervention_suggestions": intervention_suggestions
        })
        
        return result
    
    def _detailed_analysis(self, player, actions: List) -> Dict[str, Any]:
        """详细分析"""
        standard_result = self._standard_analysis(player, actions)
        
        if not actions:
            return standard_result
        
        emotional_trajectory = self._analyze_emotional_trajectory(actions)
        sequence_analysis = self._analyze_action_sequences(actions)
        value_assessment = self._assess_player_value(player, actions)
        prediction = self._predict_future_behavior(player, actions)
        personalized_recommendations = self._generate_personalized_recommendations(
            player, actions, emotional_trajectory
        )
        
        result = standard_result.copy()
        result.update({
            "emotional_trajectory": emotional_trajectory,
            "sequence_analysis": sequence_analysis,
            "value_assessment": value_assessment,
            "prediction": prediction,
            "personalized_recommendations": personalized_recommendations
        })
        
        return result

    # 保持所有其他辅助分析方法 (_analyze_time_patterns, _analyze_social_behavior, etc.) 不变
    def _analyze_time_patterns(self, actions: List) -> Dict[str, Any]:
        """分析时间模式"""
        if not actions:
            return {"pattern": "no_data"}
        
        hour_distribution = {}
        for action in actions:
            hour = action.timestamp.hour
            hour_distribution[hour] = hour_distribution.get(hour, 0) + 1
        
        peak_hour = max(hour_distribution.items(), key=lambda x: x[1])[0] if hour_distribution else 0
        
        if len(actions) > 1:
            intervals = []
            for i in range(1, len(actions)):
                interval = (actions[i-1].timestamp - actions[i].timestamp).total_seconds() / 60
                intervals.append(interval)
            avg_interval = sum(intervals) / len(intervals)
        else:
            avg_interval = 0
        
        return {
            "peak_activity_hour": peak_hour,
            "average_interval_minutes": avg_interval,
            "total_active_hours": len(hour_distribution),
            "activity_distribution": hour_distribution
        }
    
    def _analyze_social_behavior(self, actions: List) -> Dict[str, Any]:
        """分析社交行为"""
        social_actions = [action for action in actions if action.is_social_activity()]
        help_seeking_actions = [action for action in actions if action.is_help_seeking()]
        
        return {
            "social_activity_count": len(social_actions),
            "help_seeking_count": len(help_seeking_actions),
            "social_ratio": len(social_actions) / len(actions) if actions else 0,
            "is_socially_active": len(social_actions) >= 3,
            "is_seeking_help": len(help_seeking_actions) > 0
        }
    
    def _check_trigger_conditions(self, player, actions: List) -> Dict[str, Any]:
        """检查触发条件"""
        triggered_conditions = []
        
        for condition in DEFAULT_TRIGGERS:
            if condition.check_time_window(actions):
                if condition.check_failure_pattern(actions):
                    if condition.check_action_types(actions):
                        player_matches = True
                        if condition.min_vip_level and player.vip_level < condition.min_vip_level:
                            player_matches = False
                        if condition.min_total_spent and player.total_spent < condition.min_total_spent:
                            player_matches = False
                        
                        if player_matches:
                            triggered_conditions.append({
                                "condition_name": condition.name,
                                "trigger_type": condition.trigger_type.value,
                                "priority": condition.priority,
                                "description": condition.description
                            })
        
        return {
            "triggered_conditions": triggered_conditions,
            "highest_priority": max([c["priority"] for c in triggered_conditions]) if triggered_conditions else 0,
            "should_trigger_intervention": len(triggered_conditions) > 0
        }
    
    def _analyze_emotional_trajectory(self, actions: List) -> Dict[str, Any]:
        """分析情绪轨迹"""
        if not actions:
            return {"trajectory": "no_data"}
        
        emotional_points = []
        cumulative_impact = 0
        
        for action in reversed(actions):
            impact = action.get_emotional_impact()
            cumulative_impact += impact
            emotional_points.append({
                "timestamp": action.timestamp.isoformat(),
                "impact": impact,
                "cumulative": cumulative_impact,
                "action_type": action.action_type.value
            })
        
        if len(emotional_points) >= 3:
            recent_trend = emotional_points[-3:]
            trend_direction = "stable"
            if all(p["cumulative"] < recent_trend[0]["cumulative"] for p in recent_trend[1:]):
                trend_direction = "declining"
            elif all(p["cumulative"] > recent_trend[0]["cumulative"] for p in recent_trend[1:]):
                trend_direction = "improving"
        else:
            trend_direction = "insufficient_data"
        
        return {
            "trajectory": emotional_points,
            "current_emotional_score": cumulative_impact,
            "trend_direction": trend_direction,
            "lowest_point": min(emotional_points, key=lambda x: x["cumulative"])["cumulative"] if emotional_points else 0,
            "highest_point": max(emotional_points, key=lambda x: x["cumulative"])["cumulative"] if emotional_points else 0
        }
    
    def _analyze_action_sequences(self, actions: List) -> Dict[str, Any]:
        """分析行为序列"""
        if len(actions) < 3:
            return {"pattern": "insufficient_data"}
        
        sequences = []
        for i in range(len(actions) - 2):
            sequence = [
                actions[i].action_type.value,
                actions[i+1].action_type.value,
                actions[i+2].action_type.value
            ]
            sequences.append(sequence)
        
        problem_sequences = []
        for seq in sequences:
            if "battle_lose" in seq and "complain" in seq:
                problem_sequences.append("failure_frustration")
            elif seq.count("battle_lose") >= 2:
                problem_sequences.append("repeated_failure")
            elif "rage_quit" in seq:
                problem_sequences.append("rage_quit_pattern")
        
        return {
            "total_sequences": len(sequences),
            "problem_sequences": problem_sequences,
            "risk_patterns_detected": len(problem_sequences),
            "most_common_sequence": max(set(map(tuple, sequences)), key=sequences.count) if sequences else None
        }
    
    def _assess_player_value(self, player, actions: List) -> Dict[str, Any]:
        """评估玩家价值"""
        value_score = 0
        value_score += player.vip_level * 10
        
        if player.total_spent >= 1000:
            value_score += 50
        elif player.total_spent >= 100:
            value_score += 30
        elif player.total_spent >= 10:
            value_score += 10
        
        value_score += min(player.total_playtime_hours / 10, 20)
        
        if player.guild_id:
            value_score += 5
        value_score += min(player.friends_count / 5, 10)
        
        if player.current_status.value == "churning":
            risk_multiplier = 1.5
        elif player.current_status.value == "frustrated":
            risk_multiplier = 1.3
        else:
            risk_multiplier = 1.0
        
        final_value = value_score * risk_multiplier
        
        return {
            "base_value_score": value_score,
            "risk_multiplier": risk_multiplier,
            "final_value_score": final_value,
            "value_tier": "high" if final_value >= 80 else "medium" if final_value >= 40 else "low",
            "retention_priority": "critical" if final_value >= 100 else "high" if final_value >= 60 else "normal"
        }
    
    def _predict_future_behavior(self, player, actions: List) -> Dict[str, Any]:
        """预测未来行为"""
        if not actions:
            return {"prediction": "insufficient_data"}
        
        churn_risk = 0
        
        if player.consecutive_failures >= 3:
            churn_risk += 40
        elif player.consecutive_failures >= 2:
            churn_risk += 20
        
        churn_risk += player.frustration_level * 5
        
        recent_actions_count = len([a for a in actions if a.timestamp >= datetime.now() - timedelta(hours=6)])
        if recent_actions_count == 0:
            churn_risk += 30
        elif recent_actions_count < 3:
            churn_risk += 15
        
        social_actions = [a for a in actions if a.is_social_activity()]
        if len(social_actions) == 0:
            churn_risk += 10
        
        churn_risk = min(100, churn_risk)
        
        return {
            "churn_risk_percentage": churn_risk,
            "risk_level": "high" if churn_risk >= 70 else "medium" if churn_risk >= 40 else "low",
            "recommended_action": self._get_recommended_action(churn_risk),
            "intervention_urgency": "immediate" if churn_risk >= 80 else "soon" if churn_risk >= 60 else "monitor"
        }
    
    def _get_recommended_action(self, churn_risk: int) -> str:
        """获取推荐行动"""
        if churn_risk >= 80:
            return "立即进行高优先级干预，提供丰厚奖励和个人化支持"
        elif churn_risk >= 60:
            return "发送安抚消息和适当奖励，密切监控后续行为"
        elif churn_risk >= 40:
            return "提供游戏建议和小额奖励，鼓励继续游戏"
        else:
            return "继续监控，保持正常的游戏体验"
    
    def _generate_intervention_suggestions(self, player, behavior_pattern: Dict, trigger_analysis: Dict) -> List[str]:
        """生成干预建议"""
        suggestions = []
        
        if trigger_analysis["should_trigger_intervention"]:
            suggestions.append("立即触发智能体干预流程")
        
        if behavior_pattern.get("pattern") == "high_frustration":
            suggestions.append("发送高优先级安抚消息")
            suggestions.append("提供装备强化材料或金币奖励")
        
        if behavior_pattern.get("pattern") == "seeking_help":
            suggestions.append("提供详细的游戏攻略和建议")
            suggestions.append("推荐加入活跃公会")
        
        if player.is_high_value():
            suggestions.append("提供VIP专属客服支持")
            suggestions.append("发送个性化的高价值奖励")
        
        return suggestions
    
    def _generate_personalized_recommendations(self, player, actions: List, emotional_trajectory: Dict) -> List[str]:
        """生成个性化建议"""
        recommendations = []
        
        if emotional_trajectory["trend_direction"] == "declining":
            recommendations.append("情绪呈下降趋势，建议立即干预")
        
        if player.level < 10:
            recommendations.append("新手玩家，提供新手指导和保护机制")
        elif player.level > 30:
            recommendations.append("高级玩家，提供挑战性内容和高级奖励")
        
        if player.equipment_power < 500:
            recommendations.append("装备较弱，建议提供装备强化资源")
        
        return recommendations