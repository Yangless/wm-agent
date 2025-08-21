from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from collections import defaultdict, deque

from ..models.player import Player
from ..models.action import PlayerAction, ActionType
from ..models.trigger import TriggerCondition, TriggerEvent, TriggerType
from ..data.data_manager import DataManager

class BehaviorAnalyzer:
    """玩家行为分析器
    
    实时分析玩家行为模式，识别情绪状态和风险信号
    """
    
    def __init__(self, data_manager: DataManager):
        """初始化行为分析器
        
        Args:
            data_manager: 数据管理器
        """
        self.data_manager = data_manager
        self.logger = logging.getLogger(__name__)
        
        # 行为模式缓存
        self.behavior_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl_minutes = 10
        
        # 实时行为队列（用于快速检测）
        self.recent_actions: Dict[str, deque] = defaultdict(lambda: deque(maxlen=20))
        
        # 情绪状态跟踪
        self.emotional_states: Dict[str, Dict[str, Any]] = {}
        
        # 风险评分缓存
        self.risk_scores: Dict[str, Tuple[float, datetime]] = {}
    
    def analyze_player_behavior(self, 
                              player_id: str, 
                              time_window_minutes: int = 60,
                              force_refresh: bool = False) -> Dict[str, Any]:
        """分析玩家行为模式
        
        Args:
            player_id: 玩家ID
            time_window_minutes: 分析时间窗口（分钟）
            force_refresh: 是否强制刷新缓存
            
        Returns:
            Dict[str, Any]: 行为分析结果
        """
        # 检查缓存
        cache_key = f"{player_id}_{time_window_minutes}"
        if not force_refresh and self._is_cache_valid(cache_key):
            return self.behavior_cache[cache_key]["data"]
        
        try:
            # 获取玩家信息
            print("player_id:", player_id)
            #type
            print("type(player_id):", type(player_id))
            player = self.data_manager.get_player(player_id)
            if not player:
                return {"error": "玩家不存在"}
            
            # 获取行为数据
            actions = self.data_manager.get_player_actions(
                player_id=player_id,
                limit=100,
                time_window_minutes=time_window_minutes
            )
            
            # 执行分析
            analysis_result = self._perform_comprehensive_analysis(player, actions)
            
            # 更新缓存
            self.behavior_cache[cache_key] = {
                "data": analysis_result,
                "timestamp": datetime.now()
            }
            
            # 更新实时行为队列
            self._update_recent_actions(player_id, actions)
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"分析玩家 {player_id} 行为时出错: {e}")
            return {"error": str(e)}
    
    def _perform_comprehensive_analysis(self, player: Player, actions: List[PlayerAction]) -> Dict[str, Any]:
        """执行综合行为分析
        
        Args:
            player: 玩家对象
            actions: 行为列表
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        if not actions:
            return {
                "pattern": "no_activity",
                "risk_level": 1,
                "emotional_state": "unknown",
                "intervention_needed": False,
                "confidence": 0.0
            }
        
        # 基础统计分析
        basic_stats = self._analyze_basic_statistics(actions)
        
        # 行为序列分析
        sequence_analysis = self._analyze_action_sequences(actions)
        
        # 情绪轨迹分析
        emotional_analysis = self._analyze_emotional_trajectory(actions)
        
        # 时间模式分析
        temporal_analysis = self._analyze_temporal_patterns(actions)
        
        # 社交行为分析
        social_analysis = self._analyze_social_behavior(actions)
        
        # 风险评估
        risk_assessment = self._assess_risk_level(player, actions, emotional_analysis)
        
        # 行为模式识别
        behavior_pattern = self._identify_behavior_pattern(
            basic_stats, sequence_analysis, emotional_analysis, social_analysis
        )
        
        # 干预建议
        intervention_suggestion = self._generate_intervention_suggestion(
            player, behavior_pattern, risk_assessment
        )
        
        return {
            "player_id": player.player_id,
            "analysis_timestamp": datetime.now().isoformat(),
            "pattern": behavior_pattern["primary_pattern"],
            "pattern_confidence": behavior_pattern["confidence"],
            "risk_level": risk_assessment["risk_score"],
            "emotional_state": emotional_analysis["current_state"],
            "intervention_needed": intervention_suggestion["needed"],
            "intervention_urgency": intervention_suggestion["urgency"],
            "basic_stats": basic_stats,
            "sequence_analysis": sequence_analysis,
            "emotional_analysis": emotional_analysis,
            "temporal_analysis": temporal_analysis,
            "social_analysis": social_analysis,
            "risk_assessment": risk_assessment,
            "behavior_patterns": behavior_pattern,
            "intervention_suggestion": intervention_suggestion
        }
    
    def _analyze_basic_statistics(self, actions: List[PlayerAction]) -> Dict[str, Any]:
        """分析基础统计信息
        
        Args:
            actions: 行为列表
            
        Returns:
            Dict[str, Any]: 基础统计结果
        """
        total_actions = len(actions)
        failure_count = sum(1 for action in actions if action.is_failure())
        success_count = sum(1 for action in actions if action.is_success())
        social_count = sum(1 for action in actions if action.is_social_activity())
        help_seeking_count = sum(1 for action in actions if action.is_help_seeking())
        
        # 按行为类型统计
        action_type_counts = defaultdict(int)
        for action in actions:
            action_type_counts[action.action_type.value] += 1
        
        # 计算比率
        failure_rate = failure_count / total_actions if total_actions > 0 else 0
        success_rate = success_count / total_actions if total_actions > 0 else 0
        social_rate = social_count / total_actions if total_actions > 0 else 0
        
        return {
            "total_actions": total_actions,
            "failure_count": failure_count,
            "success_count": success_count,
            "social_count": social_count,
            "help_seeking_count": help_seeking_count,
            "failure_rate": failure_rate,
            "success_rate": success_rate,
            "social_rate": social_rate,
            "action_type_distribution": dict(action_type_counts),
            "most_common_action": max(action_type_counts.items(), key=lambda x: x[1])[0] if action_type_counts else None
        }
    
    def _analyze_action_sequences(self, actions: List[PlayerAction]) -> Dict[str, Any]:
        """分析行为序列模式
        
        Args:
            actions: 行为列表
            
        Returns:
            Dict[str, Any]: 序列分析结果
        """
        if len(actions) < 3:
            return {"pattern": "insufficient_data"}
        
        # 按时间排序（最新的在前）
        sorted_actions = sorted(actions, key=lambda x: x.timestamp, reverse=True)
        
        # 分析连续失败模式
        consecutive_failures = self._find_consecutive_failures(sorted_actions)
        
        # 分析失败-抱怨模式
        failure_complaint_patterns = self._find_failure_complaint_patterns(sorted_actions)
        
        # 分析求助模式
        help_seeking_patterns = self._find_help_seeking_patterns(sorted_actions)
        
        # 分析退出风险模式
        quit_risk_patterns = self._find_quit_risk_patterns(sorted_actions)
        
        # 分析恢复模式
        recovery_patterns = self._find_recovery_patterns(sorted_actions)
        
        return {
            "consecutive_failures": consecutive_failures,
            "failure_complaint_patterns": failure_complaint_patterns,
            "help_seeking_patterns": help_seeking_patterns,
            "quit_risk_patterns": quit_risk_patterns,
            "recovery_patterns": recovery_patterns,
            "dominant_pattern": self._identify_dominant_sequence_pattern({
                "consecutive_failures": consecutive_failures,
                "failure_complaint": failure_complaint_patterns,
                "help_seeking": help_seeking_patterns,
                "quit_risk": quit_risk_patterns,
                "recovery": recovery_patterns
            })
        }
    
    def _analyze_emotional_trajectory(self, actions: List[PlayerAction]) -> Dict[str, Any]:
        """分析情绪轨迹
        
        Args:
            actions: 行为列表
            
        Returns:
            Dict[str, Any]: 情绪分析结果
        """
        if not actions:
            return {"current_state": "unknown", "trajectory": "stable"}
        
        # 按时间排序
        sorted_actions = sorted(actions, key=lambda x: x.timestamp)
        
        # 计算情绪轨迹点
        emotional_points = []
        cumulative_score = 0
        
        for action in sorted_actions:
            impact = action.get_emotional_impact()
            cumulative_score += impact
            emotional_points.append({
                "timestamp": action.timestamp,
                "impact": impact,
                "cumulative_score": cumulative_score,
                "action_type": action.action_type.value
            })
        
        # 分析趋势
        trajectory = self._analyze_emotional_trend(emotional_points)
        
        # 确定当前情绪状态
        current_state = self._determine_emotional_state(cumulative_score, trajectory)
        
        # 计算情绪波动性
        volatility = self._calculate_emotional_volatility(emotional_points)
        
        return {
            "current_state": current_state,
            "trajectory": trajectory,
            "current_score": cumulative_score,
            "volatility": volatility,
            "emotional_points": emotional_points[-10:],  # 只保留最近10个点
            "lowest_point": min(emotional_points, key=lambda x: x["cumulative_score"])["cumulative_score"] if emotional_points else 0,
            "highest_point": max(emotional_points, key=lambda x: x["cumulative_score"])["cumulative_score"] if emotional_points else 0
        }
    
    def _analyze_temporal_patterns(self, actions: List[PlayerAction]) -> Dict[str, Any]:
        """分析时间模式
        
        Args:
            actions: 行为列表
            
        Returns:
            Dict[str, Any]: 时间模式分析结果
        """
        if not actions:
            return {"pattern": "no_data"}
        
        # 按小时分布
        hour_distribution = defaultdict(int)
        for action in actions:
            hour_distribution[action.timestamp.hour] += 1
        
        # 计算活动间隔
        intervals = []
        sorted_actions = sorted(actions, key=lambda x: x.timestamp)
        for i in range(1, len(sorted_actions)):
            interval = (sorted_actions[i].timestamp - sorted_actions[i-1].timestamp).total_seconds() / 60
            intervals.append(interval)
        
        avg_interval = sum(intervals) / len(intervals) if intervals else 0
        
        # 识别活跃时段
        peak_hours = sorted(hour_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # 分析活动密度
        if avg_interval < 5:  # 5分钟内
            activity_density = "very_high"
        elif avg_interval < 15:  # 15分钟内
            activity_density = "high"
        elif avg_interval < 60:  # 1小时内
            activity_density = "medium"
        else:
            activity_density = "low"
        
        return {
            "hour_distribution": dict(hour_distribution),
            "peak_hours": peak_hours,
            "average_interval_minutes": avg_interval,
            "activity_density": activity_density,
            "total_active_hours": len(hour_distribution),
            "session_pattern": self._identify_session_pattern(intervals)
        }
    
    def _analyze_social_behavior(self, actions: List[PlayerAction]) -> Dict[str, Any]:
        """分析社交行为
        
        Args:
            actions: 行为列表
            
        Returns:
            Dict[str, Any]: 社交行为分析结果
        """
        social_actions = [action for action in actions if action.is_social_activity()]
        help_seeking_actions = [action for action in actions if action.is_help_seeking()]
        
        # 分析社交活跃度
        social_ratio = len(social_actions) / len(actions) if actions else 0
        
        if social_ratio >= 0.3:
            social_level = "very_active"
        elif social_ratio >= 0.15:
            social_level = "active"
        elif social_ratio >= 0.05:
            social_level = "moderate"
        else:
            social_level = "isolated"
        
        # 分析求助行为
        help_seeking_ratio = len(help_seeking_actions) / len(actions) if actions else 0
        
        return {
            "social_actions_count": len(social_actions),
            "help_seeking_count": len(help_seeking_actions),
            "social_ratio": social_ratio,
            "help_seeking_ratio": help_seeking_ratio,
            "social_level": social_level,
            "is_seeking_help": len(help_seeking_actions) > 0,
            "social_isolation_risk": social_ratio < 0.05 and len(actions) > 10
        }
    
    def _assess_risk_level(self, 
                          player: Player, 
                          actions: List[PlayerAction], 
                          emotional_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """评估风险等级
        
        Args:
            player: 玩家对象
            actions: 行为列表
            emotional_analysis: 情绪分析结果
            
        Returns:
            Dict[str, Any]: 风险评估结果
        """
        risk_score = 0
        risk_factors = []
        
        # 连续失败风险
        if player.consecutive_failures >= 3:
            risk_score += 30
            risk_factors.append("consecutive_failures_high")
        elif player.consecutive_failures >= 2:
            risk_score += 15
            risk_factors.append("consecutive_failures_medium")
        
        # 受挫程度风险
        frustration_risk = player.frustration_level * 5
        risk_score += frustration_risk
        if frustration_risk >= 25:
            risk_factors.append("high_frustration")
        
        # 情绪状态风险
        emotional_state = emotional_analysis["current_state"]
        if emotional_state == "frustrated":
            risk_score += 20
            risk_factors.append("emotional_frustrated")
        elif emotional_state == "declining":
            risk_score += 15
            risk_factors.append("emotional_declining")
        
        # 情绪轨迹风险
        if emotional_analysis["trajectory"] == "declining":
            risk_score += 15
            risk_factors.append("emotional_trajectory_declining")
        
        # 活动减少风险
        recent_actions = [a for a in actions if a.timestamp >= datetime.now() - timedelta(hours=2)]
        if len(recent_actions) == 0 and len(actions) > 5:
            risk_score += 25
            risk_factors.append("activity_stopped")
        elif len(recent_actions) < 3 and len(actions) > 10:
            risk_score += 10
            risk_factors.append("activity_decreased")
        
        # 社交孤立风险
        social_actions = [a for a in actions if a.is_social_activity()]
        if len(social_actions) == 0 and len(actions) > 10:
            risk_score += 10
            risk_factors.append("social_isolation")
        
        # 玩家价值调整
        if player.is_high_value():
            risk_score *= 1.2  # 高价值玩家风险权重更高
            risk_factors.append("high_value_player")
        
        # 限制风险分数范围
        risk_score = min(100, max(0, risk_score))
        
        # 确定风险等级
        if risk_score >= 70:
            risk_level = "critical"
        elif risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 30:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "churn_probability": risk_score / 100,
            "intervention_priority": self._calculate_intervention_priority(risk_score, player)
        }
    
    def _identify_behavior_pattern(self, 
                                 basic_stats: Dict[str, Any],
                                 sequence_analysis: Dict[str, Any],
                                 emotional_analysis: Dict[str, Any],
                                 social_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """识别行为模式
        
        Args:
            basic_stats: 基础统计
            sequence_analysis: 序列分析
            emotional_analysis: 情绪分析
            social_analysis: 社交分析
            
        Returns:
            Dict[str, Any]: 行为模式识别结果
        """
        patterns = []
        confidence_scores = {}
        
        # 高受挫模式
        if (basic_stats["failure_rate"] > 0.6 and 
            emotional_analysis["current_state"] in ["frustrated", "declining"]):
            patterns.append("high_frustration")
            confidence_scores["high_frustration"] = 0.8
        
        # 求助模式
        if (social_analysis["is_seeking_help"] and 
            basic_stats["failure_rate"] > 0.4):
            patterns.append("seeking_help")
            confidence_scores["seeking_help"] = 0.7
        
        # 社交孤立模式
        if social_analysis["social_isolation_risk"]:
            patterns.append("social_isolation")
            confidence_scores["social_isolation"] = 0.6
        
        # 恢复模式
        if (emotional_analysis["trajectory"] == "improving" and 
            basic_stats["success_rate"] > 0.5):
            patterns.append("recovery")
            confidence_scores["recovery"] = 0.7
        
        # 稳定模式
        if (basic_stats["failure_rate"] < 0.3 and 
            emotional_analysis["current_state"] == "stable"):
            patterns.append("stable")
            confidence_scores["stable"] = 0.6
        
        # 退出风险模式
        if (sequence_analysis["quit_risk_patterns"]["detected"] and
            emotional_analysis["trajectory"] == "declining"):
            patterns.append("quit_risk")
            confidence_scores["quit_risk"] = 0.9
        
        # 确定主要模式
        if patterns:
            primary_pattern = max(patterns, key=lambda p: confidence_scores.get(p, 0))
            primary_confidence = confidence_scores[primary_pattern]
        else:
            primary_pattern = "unknown"
            primary_confidence = 0.0
        
        return {
            "detected_patterns": patterns,
            "primary_pattern": primary_pattern,
            "confidence": primary_confidence,
            "confidence_scores": confidence_scores
        }
    
    def _generate_intervention_suggestion(self, 
                                        player: Player,
                                        behavior_pattern: Dict[str, Any],
                                        risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """生成干预建议
        
        Args:
            player: 玩家对象
            behavior_pattern: 行为模式
            risk_assessment: 风险评估
            
        Returns:
            Dict[str, Any]: 干预建议
        """
        primary_pattern = behavior_pattern["primary_pattern"]
        risk_level = risk_assessment["risk_level"]
        
        # 确定是否需要干预
        needs_intervention = (
            risk_level in ["high", "critical"] or
            primary_pattern in ["high_frustration", "quit_risk", "seeking_help"]
        )
        
        # 确定干预紧急程度
        if risk_level == "critical" or primary_pattern == "quit_risk":
            urgency = "immediate"
        elif risk_level == "high" or primary_pattern == "high_frustration":
            urgency = "high"
        elif primary_pattern == "seeking_help":
            urgency = "medium"
        else:
            urgency = "low"
        
        # 生成具体建议
        suggestions = self._generate_specific_suggestions(primary_pattern, player, risk_assessment)
        
        return {
            "needed": needs_intervention,
            "urgency": urgency,
            "primary_reason": primary_pattern,
            "risk_level": risk_level,
            "suggestions": suggestions,
            "estimated_impact": self._estimate_intervention_impact(player, primary_pattern)
        }
    
    # 辅助方法实现
    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self.behavior_cache:
            return False
        
        cache_time = self.behavior_cache[cache_key]["timestamp"]
        return (datetime.now() - cache_time).total_seconds() < self.cache_ttl_minutes * 60
    
    def _update_recent_actions(self, player_id: str, actions: List[PlayerAction]):
        """更新最近行为队列"""
        # 按时间排序，最新的在前
        sorted_actions = sorted(actions, key=lambda x: x.timestamp, reverse=True)
        
        # 更新队列
        self.recent_actions[player_id].clear()
        for action in sorted_actions[:20]:  # 只保留最近20个
            self.recent_actions[player_id].append(action)
    
    def _find_consecutive_failures(self, actions: List[PlayerAction]) -> Dict[str, Any]:
        """查找连续失败模式"""
        max_consecutive = 0
        current_consecutive = 0
        
        for action in actions:
            if action.is_failure():
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return {
            "max_consecutive_failures": max_consecutive,
            "current_consecutive": current_consecutive,
            "detected": max_consecutive >= 2
        }
    
    def _find_failure_complaint_patterns(self, actions: List[PlayerAction]) -> Dict[str, Any]:
        """查找失败-抱怨模式"""
        patterns_found = 0
        
        for i in range(len(actions) - 1):
            if (actions[i].is_failure() and 
                actions[i+1].action_type in [ActionType.COMPLAIN]):
                patterns_found += 1
        
        return {
            "patterns_count": patterns_found,
            "detected": patterns_found > 0
        }
    
    def _find_help_seeking_patterns(self, actions: List[PlayerAction]) -> Dict[str, Any]:
        """查找求助模式"""
        help_actions = [action for action in actions if action.is_help_seeking()]
        
        return {
            "help_seeking_count": len(help_actions),
            "detected": len(help_actions) > 0,
            "recent_help_seeking": any(
                action.timestamp >= datetime.now() - timedelta(minutes=30)
                for action in help_actions
            )
        }
    
    def _find_quit_risk_patterns(self, actions: List[PlayerAction]) -> Dict[str, Any]:
        """查找退出风险模式"""
        quit_indicators = 0
        
        # 检查是否有愤怒退出
        for action in actions:
            if action.action_type == ActionType.RAGE_QUIT:
                quit_indicators += 2
            elif action.action_type in [ActionType.COMPLAIN]:
                quit_indicators += 1
        
        return {
            "quit_indicators": quit_indicators,
            "detected": quit_indicators >= 3
        }
    
    def _find_recovery_patterns(self, actions: List[PlayerAction]) -> Dict[str, Any]:
        """查找恢复模式"""
        recent_successes = sum(
            1 for action in actions[:5]  # 最近5个行为
            if action.is_success()
        )
        
        return {
            "recent_successes": recent_successes,
            "detected": recent_successes >= 3
        }
    
    def _identify_dominant_sequence_pattern(self, patterns: Dict[str, Dict]) -> str:
        """识别主导序列模式"""
        if patterns["quit_risk"]["detected"]:
            return "quit_risk"
        elif patterns["consecutive_failures"]["detected"]:
            return "consecutive_failures"
        elif patterns["failure_complaint"]["detected"]:
            return "failure_complaint"
        elif patterns["help_seeking"]["detected"]:
            return "help_seeking"
        elif patterns["recovery"]["detected"]:
            return "recovery"
        else:
            return "normal"
    
    def _analyze_emotional_trend(self, emotional_points: List[Dict]) -> str:
        """分析情绪趋势"""
        if len(emotional_points) < 3:
            return "insufficient_data"
        
        recent_points = emotional_points[-5:]  # 最近5个点
        
        # 计算趋势
        trend_sum = 0
        for i in range(1, len(recent_points)):
            if recent_points[i]["cumulative_score"] > recent_points[i-1]["cumulative_score"]:
                trend_sum += 1
            elif recent_points[i]["cumulative_score"] < recent_points[i-1]["cumulative_score"]:
                trend_sum -= 1
        
        if trend_sum >= 2:
            return "improving"
        elif trend_sum <= -2:
            return "declining"
        else:
            return "stable"
    
    def _determine_emotional_state(self, cumulative_score: float, trajectory: str) -> str:
        """确定情绪状态"""
        if cumulative_score <= -10:
            return "frustrated"
        elif cumulative_score <= -5:
            return "concerned"
        elif cumulative_score >= 10:
            return "positive"
        elif cumulative_score >= 5:
            return "satisfied"
        else:
            if trajectory == "declining":
                return "declining"
            elif trajectory == "improving":
                return "improving"
            else:
                return "stable"
    
    def _calculate_emotional_volatility(self, emotional_points: List[Dict]) -> float:
        """计算情绪波动性"""
        if len(emotional_points) < 2:
            return 0.0
        
        changes = []
        for i in range(1, len(emotional_points)):
            change = abs(emotional_points[i]["cumulative_score"] - emotional_points[i-1]["cumulative_score"])
            changes.append(change)
        
        return sum(changes) / len(changes) if changes else 0.0
    
    def _identify_session_pattern(self, intervals: List[float]) -> str:
        """识别会话模式"""
        if not intervals:
            return "single_session"
        
        avg_interval = sum(intervals) / len(intervals)
        
        if avg_interval < 5:  # 5分钟内
            return "intensive_session"
        elif avg_interval < 30:  # 30分钟内
            return "active_session"
        elif avg_interval < 120:  # 2小时内
            return "casual_session"
        else:
            return "sporadic_session"
    
    def _calculate_intervention_priority(self, risk_score: float, player: Player) -> int:
        """计算干预优先级"""
        base_priority = int(risk_score / 10)  # 0-10
        
        # 高价值玩家优先级提升
        if player.is_high_value():
            base_priority += 2
        elif player.vip_level >= 3:
            base_priority += 1
        
        return min(10, max(1, base_priority))
    
    def _generate_specific_suggestions(self, 
                                     pattern: str, 
                                     player: Player, 
                                     risk_assessment: Dict[str, Any]) -> List[str]:
        """生成具体建议"""
        suggestions = []
        
        if pattern == "high_frustration":
            suggestions.extend([
                "发送高优先级安抚消息",
                "提供装备强化资源",
                "推荐适合的游戏内容"
            ])
        
        elif pattern == "seeking_help":
            suggestions.extend([
                "提供详细游戏攻略",
                "推荐加入活跃公会",
                "安排新手指导"
            ])
        
        elif pattern == "quit_risk":
            suggestions.extend([
                "立即发送挽留消息",
                "提供丰厚补偿奖励",
                "安排客服主动联系"
            ])
        
        elif pattern == "social_isolation":
            suggestions.extend([
                "推荐社交活动",
                "介绍合适的游戏伙伴",
                "提供团队活动奖励"
            ])
        
        # 根据玩家价值调整建议
        if player.is_high_value():
            suggestions.append("提供VIP专属服务")
        
        return suggestions
    
    def _estimate_intervention_impact(self, player: Player, pattern: str) -> str:
        """估计干预影响"""
        if pattern in ["quit_risk", "high_frustration"]:
            return "high" if player.is_high_value() else "medium"
        elif pattern == "seeking_help":
            return "medium"
        else:
            return "low"
    
    def get_real_time_risk_score(self, player_id: str) -> float:
        """获取实时风险评分
        
        Args:
            player_id: 玩家ID
            
        Returns:
            float: 风险评分 (0-100)
        """
        # 检查缓存
        if player_id in self.risk_scores:
            score, timestamp = self.risk_scores[player_id]
            if (datetime.now() - timestamp).total_seconds() < 300:  # 5分钟缓存
                return score
        
        # 快速分析最近行为
        recent_actions = list(self.recent_actions[player_id])
        if not recent_actions:
            return 0.0
        
        player = self.data_manager.get_player(player_id)
        if not player:
            return 0.0
        
        # 简化的风险计算
        risk_score = 0
        
        # 连续失败
        risk_score += player.consecutive_failures * 10
        
        # 受挫程度
        risk_score += player.frustration_level * 3
        
        # 最近失败率
        recent_failures = sum(1 for action in recent_actions[:5] if action.is_failure())
        risk_score += recent_failures * 5
        
        risk_score = min(100, max(0, risk_score))
        
        # 更新缓存
        self.risk_scores[player_id] = (risk_score, datetime.now())
        
        return risk_score
    
    def clear_cache(self, player_id: Optional[str] = None):
        """清理缓存
        
        Args:
            player_id: 玩家ID，如果为None则清理所有缓存
        """
        if player_id:
            # 清理特定玩家的缓存
            keys_to_remove = [key for key in self.behavior_cache.keys() if key.startswith(player_id)]
            for key in keys_to_remove:
                del self.behavior_cache[key]
            
            if player_id in self.recent_actions:
                del self.recent_actions[player_id]
            
            if player_id in self.risk_scores:
                del self.risk_scores[player_id]
        else:
            # 清理所有缓存
            self.behavior_cache.clear()
            self.recent_actions.clear()
            self.risk_scores.clear()
    
    def get_analyzer_stats(self) -> Dict[str, Any]:
        """获取分析器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "cached_analyses": len(self.behavior_cache),
            "tracked_players": len(self.recent_actions),
            "risk_score_cache_size": len(self.risk_scores),
            "cache_ttl_minutes": self.cache_ttl_minutes
        }