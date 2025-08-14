from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import logging
from collections import defaultdict
import asyncio
from threading import Thread, Lock
import time

from ..models.player import Player
from ..models.action import PlayerAction
from ..models.trigger import TriggerCondition, TriggerEvent, TriggerType, DEFAULT_TRIGGERS
from ..data.data_manager import DataManager
from .behavior_analyzer import BehaviorAnalyzer
import traceback
class TriggerEngine:
    """触发引擎
    
    监控玩家行为，检测触发条件，并执行相应的干预措施
    """
    
    def __init__(self, 
                 data_manager: DataManager,
                 behavior_analyzer: Optional[BehaviorAnalyzer] = None,
                 check_interval_seconds: int = 30):
        """初始化触发引擎
        
        Args:
            data_manager: 数据管理器
            behavior_analyzer: 行为分析器
            check_interval_seconds: 检查间隔（秒）
        """
        self.data_manager = data_manager
        self.behavior_analyzer = behavior_analyzer or BehaviorAnalyzer(data_manager)
        self.check_interval = check_interval_seconds
        self.logger = logging.getLogger(__name__)
        
        # 触发条件管理
        self.trigger_conditions: Dict[str, TriggerCondition] = {}
        self.load_default_conditions()
        
        # 事件处理器
        self.event_handlers: Dict[TriggerType, List[Callable]] = defaultdict(list)
        
        # 运行状态
        self.is_running = False
        self.monitor_thread: Optional[Thread] = None
        self._lock = Lock()
        
        # 性能统计
        self.stats = {
            "total_checks": 0,
            "triggers_fired": 0,
            "last_check_time": None,
            "average_check_duration": 0.0,
            "active_players_monitored": 0
        }
        
        # 玩家监控状态
        self.monitored_players: Dict[str, Dict[str, Any]] = {}
        
        # 触发历史（用于防止重复触发）
        self.trigger_history: Dict[str, List[datetime]] = defaultdict(list)
        
        self.logger.info("触发引擎初始化完成")
    
    def load_default_conditions(self):
        """加载默认触发条件"""
        for condition in DEFAULT_TRIGGERS:
            self.add_trigger_condition(condition)
        
        self.logger.info(f"加载了 {len(DEFAULT_TRIGGERS)} 个默认触发条件")
    
    def add_trigger_condition(self, condition: TriggerCondition):
        """添加触发条件
        
        Args:
            condition: 触发条件
        """
        self.trigger_conditions[condition.name] = condition
        self.logger.debug(f"添加触发条件: {condition.name}")
    
    def remove_trigger_condition(self, condition_name: str):
        """移除触发条件
        
        Args:
            condition_name: 条件名称
        """
        if condition_name in self.trigger_conditions:
            del self.trigger_conditions[condition_name]
            self.logger.debug(f"移除触发条件: {condition_name}")
    
    def register_event_handler(self, trigger_type: TriggerType, handler: Callable):
        """注册事件处理器
        
        Args:
            trigger_type: 触发类型
            handler: 处理器函数
        """
        self.event_handlers[trigger_type].append(handler)
        self.logger.debug(f"注册事件处理器: {trigger_type.value}")
    
    def start_monitoring(self):
        """开始监控"""
        if self.is_running:
            self.logger.warning("触发引擎已在运行中")
            return
        
        self.is_running = True
        self.monitor_thread = Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("触发引擎开始监控")
    
    def stop_monitoring(self):
        """停止监控"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        self.logger.info("触发引擎停止监控")
    
    def _monitoring_loop(self):
        """监控循环"""
        self.logger.info("监控循环开始")
        
        while self.is_running:
            try:
                start_time = time.time()
                
                # 执行检查
                self._perform_check_cycle()
                
                # 更新统计
                check_duration = time.time() - start_time
                self._update_stats(check_duration)
                
                # 等待下一次检查
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.logger.error(f"监控循环出错: {e}", exc_info=True)
                time.sleep(self.check_interval)
        
        self.logger.info("监控循环结束")
    
    def _perform_check_cycle(self):
        """执行检查周期"""
        with self._lock:
            # 获取活跃玩家列表
            active_players = self._get_active_players()
            
            self.stats["active_players_monitored"] = len(active_players)
            
            # 检查每个玩家
            for player_id in active_players:
                try:
                    self._check_player_triggers(player_id)
                except Exception as e:
                    self.logger.error(f"检查玩家 {player_id} 触发条件时出错: {e}")
            
            # 清理过期的触发历史
            self._cleanup_trigger_history()
    
    def _get_active_players(self) -> List[str]:
        """获取活跃玩家列表
        
        Returns:
            List[str]: 活跃玩家ID列表
        """
        # 获取最近活跃的玩家（最近1小时有行为）
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        # 这里应该从数据管理器获取活跃玩家
        # 为了演示，我们使用一个简化的方法
        all_players = self.data_manager.get_all_players()
        active_players = []
        
        for player in all_players:
            recent_actions = self.data_manager.get_player_actions(
                player_id=player.player_id,
                limit=1,
                time_window_minutes=60
            )
            if recent_actions:
                active_players.append(player.player_id)
        
        return active_players
    
    def _check_player_triggers(self, player_id: str):
        """检查玩家的触发条件
        
        Args:
            player_id: 玩家ID
        """
        player = self.data_manager.get_player(player_id)
        if not player:
            return
        
        # 获取玩家最近的行为
        recent_actions = self.data_manager.get_player_actions(
            player_id=player_id,
            limit=50,
            time_window_minutes=120  # 最近2小时
        )
        
        # 检查每个触发条件
        for condition_name, condition in self.trigger_conditions.items():
            try:
                if self._should_check_condition(player_id, condition):
                    if self._evaluate_trigger_condition(player, recent_actions, condition):
                        self._fire_trigger(player, recent_actions, condition)
            except Exception as e:
                self.logger.error(f"评估触发条件 {condition_name} 时出错: {e}")
    
    def _should_check_condition(self, player_id: str, condition: TriggerCondition) -> bool:
        """判断是否应该检查条件（考虑冷却时间）
        
        Args:
            player_id: 玩家ID
            condition: 触发条件
            
        Returns:
            bool: 是否应该检查
        """
        if condition.cooldown_hours <= 0:
            return True
        
        history_key = f"{player_id}_{condition.name}"
        if history_key not in self.trigger_history:
            return True
        
        last_trigger_times = self.trigger_history[history_key]
        if not last_trigger_times:
            return True
        
        last_trigger = max(last_trigger_times)
        cooldown_end = last_trigger + timedelta(hours=condition.cooldown_hours)
        
        return datetime.now() >= cooldown_end
    
    def _evaluate_trigger_condition(self, 
                                  player: Player, 
                                  actions: List[PlayerAction], 
                                  condition: TriggerCondition) -> bool:
        """评估触发条件
        
        Args:
            player: 玩家对象
            actions: 行为列表
            condition: 触发条件
            
        Returns:
            bool: 是否满足触发条件
        """
        try:
            # 检查玩家过滤条件
            if not self._check_player_filters(player, condition):
                return False
            
            # 根据触发类型进行不同的检查
            if condition.trigger_type == TriggerType.CONSECUTIVE_FAILURES:
                return self._check_consecutive_failures(player, actions, condition)
            
            elif condition.trigger_type == TriggerType.EMOTIONAL_DECLINE:
                return self._check_emotional_decline(player, actions, condition)
            
            elif condition.trigger_type == TriggerType.HELP_SEEKING:
                return self._check_help_seeking(player, actions, condition)
            
            elif condition.trigger_type == TriggerType.HIGH_VALUE_RISK:
                return self._check_high_value_risk(player, actions, condition)
            
            elif condition.trigger_type == TriggerType.SOCIAL_ISOLATION:
                return self._check_social_isolation(player, actions, condition)
            
            else:
                self.logger.warning(f"未知的触发类型: {condition.trigger_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"评估触发条件时出错: {e}")
            return False
    
    def _check_player_filters(self, player: Player, condition: TriggerCondition) -> bool:
        """检查玩家过滤条件
        
        Args:
            player: 玩家对象
            condition: 触发条件
            
        Returns:
            bool: 是否通过过滤
        """
        # 检查VIP等级
        if condition.min_vip_level and player.vip_level < condition.min_vip_level:
            return False
        
        # 检查最低消费金额
        if condition.min_total_spent and hasattr(player, 'total_spent'):
            if player.total_spent < condition.min_total_spent:
                return False
        
        return True
    
    def _check_consecutive_failures(self, 
                                  player: Player, 
                                  actions: List[PlayerAction], 
                                  condition: TriggerCondition) -> bool:
        """检查连续失败条件
        
        Args:
            player: 玩家对象
            actions: 行为列表
            condition: 触发条件
            
        Returns:
            bool: 是否满足条件
        """
        print(f"    检查连续失败: 玩家失败次数={player.consecutive_failures}, 条件要求={condition.min_failures}")
        
        # 检查玩家的连续失败次数
        if player.consecutive_failures < condition.min_failures:
            print(f"    玩家连续失败次数不足: {player.consecutive_failures} < {condition.min_failures}")
            return False
        
        # 检查时间窗口内的失败
        if condition.time_window_minutes:
            cutoff_time = datetime.now() - timedelta(minutes=condition.time_window_minutes)
            recent_actions = [a for a in actions if a.timestamp >= cutoff_time]
            print(f"    时间窗口内行为数量: {len(recent_actions)}")
            
            # 检查必需的行为类型
            if condition.required_action_types:
                required_types_found = []
                for action in recent_actions:
                    # print("xxxxxxxxxxxxxxxxx")
                    # print("action:", action)
                    # print("action.action_type:", action.action_type)
                    # print("condition.required_action_types:", condition.required_action_types)
                    if action.action_type in condition.required_action_types:
                        required_types_found.append(action.action_type.value)
                print(f"    必需行为类型: {[t.value for t in condition.required_action_types]}")
                print(f"    找到的行为类型: {required_types_found}")
                
                # 检查是否包含所有必需的行为类型
                for required_type in condition.required_action_types:
                    if not any(a.action_type == required_type for a in recent_actions):
                        print(f"    缺少必需行为类型: {required_type.value}")
                        return False
            
            # 计算时间窗口内的连续失败
            consecutive_failures = 10
            failure_actions = []
            for action in sorted(recent_actions, key=lambda x: x.timestamp, reverse=True):
                if action.is_failure():
                    consecutive_failures += 1
                    failure_actions.append(f"{action.action_type.value}({action.timestamp})")
                else:
                    break
            
            print(f"    时间窗口内连续失败次数: {consecutive_failures}")
            print(f"    失败行为: {failure_actions}")
            
            result = consecutive_failures >= condition.min_failures
            print(f"    连续失败检查结果: {result}")
            return result
        
        print(f"    无时间窗口限制，直接通过")
        return True
    
    def _check_emotional_decline(self, 
                               player: Player, 
                               actions: List[PlayerAction], 
                               condition: TriggerCondition) -> bool:
        """检查情绪下降条件
        
        Args:
            player: 玩家对象
            actions: 行为列表
            condition: 触发条件
            
        Returns:
            bool: 是否满足条件
        """
        if not actions:
            return False
        
        # 使用行为分析器获取情绪分析
        analysis = self.behavior_analyzer.analyze_player_behavior(
            player.player_id,
            time_window_minutes=condition.time_window_minutes or 60
        )
        
        if "error" in analysis:
            return False
        
        emotional_analysis = analysis.get("emotional_analysis", {})
        
        # 检查情绪状态
        current_state = emotional_analysis.get("current_state")
        if current_state in ["frustrated", "declining"]:
            return True
        
        # 检查情绪轨迹
        trajectory = emotional_analysis.get("trajectory")
        if trajectory == "declining":
            return True
        
        # 检查情绪分数阈值
        if condition.emotional_threshold:
            current_score = emotional_analysis.get("current_score", 0)
            return current_score <= condition.emotional_threshold
        
        return False
    
    def _check_help_seeking(self, 
                          player: Player, 
                          actions: List[PlayerAction], 
                          condition: TriggerCondition) -> bool:
        """检查求助行为条件
        
        Args:
            player: 玩家对象
            actions: 行为列表
            condition: 触发条件
            
        Returns:
            bool: 是否满足条件
        """
        if not actions:
            return False
        
        # 检查时间窗口内的求助行为
        cutoff_time = datetime.now() - timedelta(minutes=condition.time_window_minutes or 30)
        recent_actions = [a for a in actions if a.timestamp >= cutoff_time]
        
        help_seeking_count = sum(1 for action in recent_actions if action.is_help_seeking())
        
        return help_seeking_count > 0
    
    def _check_high_value_risk(self, 
                             player: Player, 
                             actions: List[PlayerAction], 
                             condition: TriggerCondition) -> bool:
        """检查高价值玩家风险条件
        
        Args:
            player: 玩家对象
            actions: 行为列表
            condition: 触发条件
            
        Returns:
            bool: 是否满足条件
        """
        # 首先检查是否是高价值玩家
        if not player.is_high_value():
            return False
        
        # 获取风险评分
        risk_score = self.behavior_analyzer.get_real_time_risk_score(player.player_id)
        
        # 高价值玩家的风险阈值更低
        risk_threshold = 40  # 高价值玩家40分就触发
        
        return risk_score >= risk_threshold
    
    def _check_social_isolation(self, 
                              player: Player, 
                              actions: List[PlayerAction], 
                              condition: TriggerCondition) -> bool:
        """检查社交孤立条件
        
        Args:
            player: 玩家对象
            actions: 行为列表
            condition: 触发条件
            
        Returns:
            bool: 是否满足条件
        """
        if not actions or len(actions) < 10:  # 需要足够的行为数据
            return False
        
        # 检查社交行为比例
        social_actions = [action for action in actions if action.is_social_activity()]
        social_ratio = len(social_actions) / len(actions)
        
        # 社交比例低于5%且总行为数超过10个
        return social_ratio < 0.05 and len(actions) > 10
    
    def _fire_trigger(self, 
                     player: Player, 
                     actions: List[PlayerAction], 
                     condition: TriggerCondition):
        """触发事件
        
        Args:
            player: 玩家对象
            actions: 触发行为列表
            condition: 触发条件
        """
        try:
            # 获取最近触发行为的时间作为触发时间
            trigger_time = datetime.now()
            if actions:
                # 使用最近行为的时间作为触发时间
                trigger_time = max(action.timestamp for action in actions[:5])
            
            # 创建触发事件
            trigger_event = TriggerEvent(
                event_id=f"{player.player_id}_{condition.name}_{int(trigger_time.timestamp())}",
                player_id=player.player_id,
                trigger_condition=condition,
                triggered_at=trigger_time,
                triggering_actions=actions[:5],  # 只保留最近5个行为
                player_status_snapshot={
                    "level": player.level,
                    "vip_level": player.vip_level,
                    "consecutive_failures": player.consecutive_failures,
                    "frustration_level": player.frustration_level,
                    "status": player.current_status.value
                }
            )
            
            # 保存触发事件
            self.data_manager.add_trigger_event(trigger_event)
            
            # 记录触发历史
            history_key = f"{player.player_id}_{condition.name}"
            self.trigger_history[history_key].append(datetime.now())
            
            # 调用事件处理器
            handlers = self.event_handlers.get(condition.trigger_type, [])
            for handler in handlers:
                try:
                    handler(trigger_event)
                except Exception as e:
                    self.logger.error(f"事件处理器执行失败: {e}")
            
            # 更新统计
            self.stats["triggers_fired"] += 1
            
            self.logger.info(
                f"触发事件: 玩家={player.player_id}, 条件={condition.name}, "
                f"类型={condition.trigger_type.value}"
            )
            
        except Exception as e:
            self.logger.error(f"触发事件时出错: {e}", exc_info=True)
    
    def _cleanup_trigger_history(self):
        """清理过期的触发历史"""
        cutoff_time = datetime.now() - timedelta(hours=24)  # 保留24小时内的历史
        
        for key in list(self.trigger_history.keys()):
            # 过滤掉过期的记录
            self.trigger_history[key] = [
                timestamp for timestamp in self.trigger_history[key]
                if timestamp >= cutoff_time
            ]
            
            # 如果列表为空，删除键
            if not self.trigger_history[key]:
                del self.trigger_history[key]
    
    def _update_stats(self, check_duration: float):
        """更新统计信息
        
        Args:
            check_duration: 检查耗时
        """
        self.stats["total_checks"] += 1
        self.stats["last_check_time"] = datetime.now()
        
        # 更新平均检查耗时
        current_avg = self.stats["average_check_duration"]
        total_checks = self.stats["total_checks"]
        
        self.stats["average_check_duration"] = (
            (current_avg * (total_checks - 1) + check_duration) / total_checks
        )
    
    def force_check_player(self, player_id: str) -> List[TriggerEvent]:
        """强制检查特定玩家的触发条件
        
        Args:
            player_id: 玩家ID
            
        Returns:
            List[TriggerEvent]: 触发的事件列表
        """
        triggered_events = []
        
        try:
            player = self.data_manager.get_player(player_id)
            if not player:
                self.logger.warning(f"玩家 {player_id} 不存在")
                return triggered_events
            
            # 获取玩家最近的行为
            recent_actions = self.data_manager.get_player_actions(
                player_id=player_id,
                limit=50,
                time_window_minutes=120
            )
            # print("recent_actions:", recent_actions)
            
            # 添加调试信息
            print(f"\n=== 强制检查玩家 {player_id} ===")
            print(f"玩家状态: level={player.level}, vip_level={player.vip_level}")
            print(f"连续失败次数: {player.consecutive_failures}")
            print(f"受挫程度: {player.frustration_level}")
            print(f"当前状态: {player.current_status.value}")
            print(f"最近行为数量: {len(recent_actions)}")
            print(f"触发条件数量: {len(self.trigger_conditions)}")
            
            # 检查所有触发条件
            for condition_name, condition in self.trigger_conditions.items():
                try:
                    print(f"\n--- 检查条件: {condition_name} ---")
                    print(f"条件类型: {condition.trigger_type.value}")
                    print(f"最少失败次数: {condition.min_failures}")
                    print(f"时间窗口: {condition.time_window_minutes}分钟")
                    print(f"必需行为类型: {[t.value for t in condition.required_action_types]}")
                    
                    # 检查玩家过滤条件
                    player_filter_result = self._check_player_filters(player, condition)
                    print(f"玩家过滤结果: {player_filter_result}")
                    
                    if player_filter_result:
                        condition_result = self._evaluate_trigger_condition(player, recent_actions, condition)
                        print(f"条件评估结果: {condition_result}")
                        
                        # if condition_result:
                        # 创建触发事件但不执行处理器
                        
                        # 获取最近触发行为的时间作为触发时间
                        trigger_time = datetime.now()
                        if recent_actions:
                            # 使用最近行为的时间作为触发时间
                            trigger_time = max(action.timestamp for action in recent_actions[:5])
                        
                        trigger_event = TriggerEvent(
                            event_id=f"{player_id}_{condition_name}_{int(trigger_time.timestamp())}",
                            player_id=player_id,
                            trigger_condition=condition,
                            triggered_at=trigger_time,
                            triggering_actions=recent_actions[:5],
                            player_status_snapshot={
                                "level": player.level,
                                "vip_level": player.vip_level,
                                "consecutive_failures": player.consecutive_failures,
                                "frustration_level": player.frustration_level,
                                "status": player.current_status.value
                            }
                        )
                        triggered_events.append(trigger_event)
                        
                except Exception as e:
                    traceback.print_exc()
                    self.logger.error(f"强制检查条件 {condition_name} 时出错: {e}")
            
            self.logger.info(f"强制检查玩家 {player_id}，触发了 {len(triggered_events)} 个事件")
            
        except Exception as e:
            self.logger.error(f"强制检查玩家 {player_id} 时出错: {e}")
        
        return triggered_events
    
    def get_trigger_stats(self) -> Dict[str, Any]:
        """获取触发引擎统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "engine_status": "running" if self.is_running else "stopped",
            "total_conditions": len(self.trigger_conditions),
            "registered_handlers": sum(len(handlers) for handlers in self.event_handlers.values()),
            "monitored_players": len(self.monitored_players),
            "trigger_history_size": len(self.trigger_history),
            "performance_stats": self.stats.copy()
        }
    
    def get_condition_list(self) -> List[Dict[str, Any]]:
        """获取触发条件列表
        
        Returns:
            List[Dict[str, Any]]: 条件列表
        """
        return [
            {
                "name": condition.name,
                "type": condition.trigger_type.value,
                "description": condition.description,
                "priority": condition.priority,
                "enabled": True,  # 默认启用
                "cooldown_hours": condition.cooldown_hours
            }
            for condition in self.trigger_conditions.values()
        ]
    
    def enable_condition(self, condition_name: str):
        """启用触发条件
        
        Args:
            condition_name: 条件名称
        """
        if condition_name in self.trigger_conditions:
            self.trigger_conditions[condition_name].enabled = True
            self.logger.info(f"启用触发条件: {condition_name}")
    
    def disable_condition(self, condition_name: str):
        """禁用触发条件
        
        Args:
            condition_name: 条件名称
        """
        if condition_name in self.trigger_conditions:
            self.trigger_conditions[condition_name].enabled = False
            self.logger.info(f"禁用触发条件: {condition_name}")
    
    def clear_trigger_history(self, player_id: Optional[str] = None):
        """清理触发历史
        
        Args:
            player_id: 玩家ID，如果为None则清理所有历史
        """
        if player_id:
            keys_to_remove = [key for key in self.trigger_history.keys() if key.startswith(player_id)]
            for key in keys_to_remove:
                del self.trigger_history[key]
            self.logger.info(f"清理玩家 {player_id} 的触发历史")
        else:
            self.trigger_history.clear()
            self.logger.info("清理所有触发历史")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start_monitoring()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop_monitoring()