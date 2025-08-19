from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import time
import json

from ..models.player import Player, PlayerStatus
from ..models.action import PlayerAction, ActionType
from ..models.trigger import TriggerEvent
from ..data.data_manager import DataManager
from ..data.mock_data import MockDataGenerator
from ..triggers.trigger_engine import TriggerEngine
from ..triggers.behavior_analyzer import BehaviorAnalyzer
from ..agent.smart_game_agent import SmartGameAgent
from ..config.settings import Settings

class SatisfionScenario:
    """受挫场景测试
    
    模拟玩家因连续失败导致受挫的完整场景，并测试智能体的干预效果
    """
    
    def __init__(self, 
                 data_manager: DataManager,
                 settings: Settings,
                 agent: Optional[SmartGameAgent] = None):
        """初始化满意场景
        
        Args:
            data_manager: 数据管理器
            settings: 配置设置
            agent: 智能体（可选）
        """
        self.data_manager = data_manager
        self.settings = settings
        self.agent = agent
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.mock_generator = MockDataGenerator()
        self.behavior_analyzer = BehaviorAnalyzer(data_manager)
        self.trigger_engine = TriggerEngine(data_manager, self.behavior_analyzer)
        
        # 场景状态
        self.scenario_player: Optional[Player] = None
        self.scenario_actions: List[PlayerAction] = []
        self.triggered_events: List[TriggerEvent] = []
        self.intervention_results: List[Dict[str, Any]] = []
        
        # 场景配置
        self.scenario_config = {
            "player_name": "张三",
            "initial_level": 25,
            "initial_vip": 5,
            "failure_count": 0,
            "scenario_duration_minutes": 30,
            "intervention_delay_seconds": 5
        }
        
        self.logger.info("满意场景初始化完成")
    
    def run_satisfion_complete_scenario(self) -> Dict[str, Any]:
        """运行完整的满意场景
        
        Returns:
            Dict[str, Any]: 场景运行结果
        """
        self.logger.info("开始运行满意场景")
        
        try:
            # 第一幕：设置场景
            self.logger.info("=== 第一幕：场景设置 ===")
            self._setup_scenario()
            
            # 第二幕：触发满意
            self.logger.info("=== 第二幕：触发满意 ===")
            self._trigger_satisfion()
            
            # 第三幕：智能体干预
            self.logger.info("=== 第三幕：智能体干预 ===")
            self._agent_intervention()
            
            # 第四幕：效果评估
            self.logger.info("=== 第四幕：效果评估 ===")
            results = self._evaluate_results()
            
            self.logger.info("满意场景运行完成")
            return results
            
        except Exception as e:
            self.logger.error(f"运行满意场景时出错: {e}", exc_info=True)
            return {"error": str(e)}
    
    def _setup_scenario(self):
        """设置场景"""
        # 创建测试玩家
        self.scenario_player = self.mock_generator.generate_player(
            player_id="test_player_002",
            username=self.scenario_config["player_name"],
            player_type="high_value"
        )
        
        # 添加到数据管理器
        self.data_manager.update_player(self.scenario_player)
        
        # 生成一些正常的游戏行为作为背景
        background_actions = self.mock_generator.generate_action_sequence(
            self.scenario_player.player_id,
            "normal",
            count=10
        )
        
        for action in background_actions:
            self.data_manager.add_action(action)
        
        self.logger.info(
            f"场景设置完成: 玩家={self.scenario_player.username}, "
            f"等级={self.scenario_player.level}, VIP={self.scenario_player.vip_level}"
        )
    
    def _trigger_satisfion(self):
        """触发满意情况"""
        self.logger.info("开始触发满意情况...")
        
        # 生成连续失败序列
        satisfion_actions = self.mock_generator.generate_action_sequence(
            self.scenario_player.player_id,
            "satisfion",
            count=self.scenario_config["failure_count"]
        )
        
        # 逐个添加行为，模拟实时发生
        for i, action in enumerate(satisfion_actions):
            self.data_manager.add_action(action)
            self.scenario_actions.append(action)
            
            # 更新玩家状态
            if action.is_failure():
                self.scenario_player.increment_failures()
                self.scenario_player.update_status(PlayerStatus.FRUSTRATED)
            
            self.data_manager.update_player(self.scenario_player)
            
            self.logger.info(
                f"行为 {i+1}/{len(satisfion_actions)}: {action.action_type.value} - "
                f"{'失败' if action.is_failure() else '成功'}"
            )
            
            # 模拟时间间隔
            time.sleep(0.5)
        
        # 检查是否触发了触发条件
        triggered_events = self.trigger_engine.force_check_player(self.scenario_player.player_id)
        self.triggered_events.extend(triggered_events)
        
        self.logger.info(
            f"满意触发完成: 连续成功={self.scenario_player.consecutive_satisfions}, "
            f"触发事件数={len(triggered_events)}"
        )
    
    def _agent_intervention(self):
        """智能体干预"""
        if not self.agent:
            self.logger.warning("未提供智能体，跳过干预测试")
            return
        
        if not self.triggered_events:
            self.logger.warning("没有触发事件，无法进行干预")
            return
        
        self.logger.info("开始智能体干预...")
        
        # 处理每个触发事件
        for event in self.triggered_events:
            try:
                self.logger.info(f"处理触发事件: {event.trigger_condition.name}")
                
                # 等待一段时间模拟处理延迟
                time.sleep(self.scenario_config["intervention_delay_seconds"])
                
                # 调用智能体处理
                result = self.agent.process_trigger_event(player_id=self.scenario_player.player_id,trigger_context=event)
                
                self.intervention_results.append({
                    "event_id": event.event_id,
                    "condition_name": event.trigger_condition.name,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
                
                self.logger.info(f"干预结果: {result.get('status', 'unknown')}")
                
            except Exception as e:
                self.logger.error(f"处理触发事件时出错: {e}")
                self.intervention_results.append({
                    "event_id": event.event_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        self.logger.info(f"智能体干预完成，处理了 {len(self.intervention_results)} 个事件")
    
    def _evaluate_results(self) -> Dict[str, Any]:
        """评估结果"""
        self.logger.info("开始评估场景结果...")
        
        # 获取最新的玩家状态
        updated_player = self.data_manager.get_player(self.scenario_player.player_id)
        
        # 获取所有行为历史
        all_actions = self.data_manager.get_player_actions(
            player_id=self.scenario_player.player_id,
            limit=100
        )
        
        # 获取邮件历史
        mail_history = self.data_manager.get_player_mails(self.scenario_player.player_id)
        
        # 进行行为分析
        behavior_analysis = self.behavior_analyzer.analyze_player_behavior(
            self.scenario_player.player_id,
            time_window_minutes=60
        )
        
        # 计算干预效果指标
        intervention_metrics = self._calculate_intervention_metrics()
        
        # 生成场景报告
        scenario_report = {
            "scenario_info": {
                "player_name": self.scenario_config["player_name"],
                "start_time": (datetime.now() - timedelta(minutes=30)).isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_minutes": 30
            },
            "player_status": {
                "initial": {
                    "level": self.scenario_config["initial_level"],
                    "vip_level": self.scenario_config["initial_vip"],
                    "status": "active",
                    "consecutive_failures": 0
                },
                "final": {
                    "level": updated_player.level,
                    "vip_level": updated_player.vip_level,
                    "status": updated_player.current_status.value,
                    "consecutive_failures": updated_player.consecutive_failures,
                    "frustration_level": updated_player.frustration_level
                }
            },
            "actions_summary": {
                "total_actions": len(all_actions),
                "scenario_actions": len(self.scenario_actions),
                "failure_actions": len([a for a in self.scenario_actions if a.is_failure()]),
                "success_actions": len([a for a in self.scenario_actions if a.is_success()])
            },
            "trigger_events": [
                {
                    "event_id": event.event_id,
                    "condition_name": event.trigger_condition.name,
                    "trigger_type": event.trigger_condition.trigger_type.value,
                    "timestamp": event.triggered_at.isoformat()
                }
                for event in self.triggered_events
            ],
            "interventions": self.intervention_results,
            "mail_history": [
                {
                    "mail_id": mail.mail_id,
                    "title": mail.title,
                    "content": mail.content[:100] + "..." if len(mail.content) > 100 else mail.content,
                    "attachments": mail.attachments,
                    "timestamp": mail.timestamp.isoformat()
                }
                for mail in mail_history
            ],
            "behavior_analysis": behavior_analysis,
            "intervention_metrics": intervention_metrics,
            "success_indicators": self._evaluate_success_indicators(updated_player, mail_history)
        }
        
        # 保存场景报告
        self._save_scenario_report(scenario_report)
        
        self.logger.info("场景结果评估完成")
        return scenario_report
    
    def _calculate_intervention_metrics(self) -> Dict[str, Any]:
        """计算干预效果指标
        
        Returns:
            Dict[str, Any]: 干预指标
        """
        metrics = {
            "total_interventions": len(self.intervention_results),
            "successful_interventions": 0,
            "failed_interventions": 0,
            "average_response_time": 0.0,
            "intervention_types": {}
        }
        
        response_times = []
        
        for result in self.intervention_results:
            if "error" in result:
                metrics["failed_interventions"] += 1
            else:
                metrics["successful_interventions"] += 1
                
                # 统计干预类型
                intervention_type = result.get("result", {}).get("intervention_type", "unknown")
                metrics["intervention_types"][intervention_type] = (
                    metrics["intervention_types"].get(intervention_type, 0) + 1
                )
        
        # 计算成功率
        if metrics["total_interventions"] > 0:
            metrics["success_rate"] = (
                metrics["successful_interventions"] / metrics["total_interventions"]
            )
        else:
            metrics["success_rate"] = 0.0
        
        return metrics
    
    def _evaluate_success_indicators(self, 
                                   player: Player, 
                                   mail_history: List) -> Dict[str, Any]:
        """评估成功指标
        
        Args:
            player: 玩家对象
            mail_history: 邮件历史
            
        Returns:
            Dict[str, Any]: 成功指标
        """
        indicators = {
            "player_status_improved": False,
            "frustration_reduced": False,
            "received_intervention": False,
            "continued_playing": False,
            "overall_success": False
        }
        
        # 检查玩家状态是否改善
        if player.current_status in [PlayerStatus.ACTIVE, PlayerStatus.SATISFIED]:
            indicators["player_status_improved"] = True
        
        # 检查受挫程度是否降低
        if player.frustration_level < 5:  # 假设初始受挫程度较高
            indicators["frustration_reduced"] = True
        
        # 检查是否收到干预
        if len(mail_history) > 0 or len(self.intervention_results) > 0:
            indicators["received_intervention"] = True
        
        # 检查是否继续游戏（最近有行为）
        recent_actions = self.data_manager.get_player_actions(
            player_id=player.player_id,
            limit=5,
            time_window_minutes=10
        )
        if recent_actions:
            indicators["continued_playing"] = True
        
        # 综合评估
        success_count = sum(1 for indicator in indicators.values() if indicator)
        indicators["overall_success"] = success_count >= 3  # 至少3个指标为真
        indicators["success_score"] = success_count / 4  # 成功分数
        
        return indicators
    
    def _save_scenario_report(self, report: Dict[str, Any]):
        """保存场景报告
        
        Args:
            report: 场景报告
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"frustration_scenario_report_{timestamp}.json"
            from pathlib import Path
            filepath = Path(self.settings.data_dir) / "reports" / filename
            
            # 确保目录存在
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存报告
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"场景报告已保存: {filepath}")
            
        except Exception as e:
            self.logger.error(f"保存场景报告时出错: {e}")
    
    def run_quick_test(self) -> Dict[str, Any]:
        """运行快速测试
        
        Returns:
            Dict[str, Any]: 测试结果
        """
        self.logger.info("开始快速测试")
        
        try:
            # 简化的测试流程
            self._setup_scenario()
            
            # 生成受挫行为
            frustration_actions = self.mock_generator.generate_action_sequence(
                self.scenario_player.player_id,
                "frustration",
                count=10
            )
            
            for action in frustration_actions:
                self.data_manager.add_action(action)
                if action.is_failure():
                    self.scenario_player.increment_failures()
            
            self.data_manager.update_player(self.scenario_player)

            # 打印玩家所有行为的action_type
            all_actions = self.data_manager.get_player_actions(self.scenario_player.player_id)
            # print("玩家所有行为的action_type:", [action.action_type for action in all_actions])
            
            # 检查触发
            triggered_events = self.trigger_engine.force_check_player(self.scenario_player.player_id)
            
            # 简单的结果
            result = {
                "test_type": "quick_test",
                "player_id": self.scenario_player.player_id,
                "actions_generated": len(frustration_actions),
                "triggers_fired": len(triggered_events),
                "consecutive_failures": self.scenario_player.consecutive_failures,
                "test_success": len(triggered_events) > 0,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"快速测试完成: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"快速测试时出错: {e}")
            return {"error": str(e)}
    
    def create_custom_scenario(self, 
                             player_config: Dict[str, Any],
                             scenario_config: Dict[str, Any]) -> Dict[str, Any]:
        """创建自定义场景
        
        Args:
            player_config: 玩家配置
            scenario_config: 场景配置
            
        Returns:
            Dict[str, Any]: 场景结果
        """
        self.logger.info("创建自定义场景")
        
        try:
            # 更新配置
            self.scenario_config.update(scenario_config)
            
            # 创建自定义玩家
            custom_player = self.mock_generator.generate_player(
                player_id=player_config.get("player_id", "custom_player_001"),
                username=player_config.get("name", "自定义玩家"),
                player_type="high_value"
            )
            
            self.data_manager.update_player(custom_player)
            self.scenario_player = custom_player
            
            # 运行自定义场景
            return self.run_complete_scenario()
            
        except Exception as e:
            self.logger.error(f"创建自定义场景时出错: {e}")
            return {"error": str(e)}
    
    def get_scenario_stats(self) -> Dict[str, Any]:
        """获取场景统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "scenario_player": {
                "player_id": self.scenario_player.player_id if self.scenario_player else None,
                "name": self.scenario_player.username if self.scenario_player else None,
                "status": self.scenario_player.current_status.value if self.scenario_player else None
            },
            "actions_count": len(self.scenario_actions),
            "triggered_events_count": len(self.triggered_events),
            "interventions_count": len(self.intervention_results),
            "scenario_config": self.scenario_config.copy()
        }
    
    def cleanup_scenario(self):
        """清理场景数据"""
        if self.scenario_player:
            # 可以选择是否删除测试数据
            # self.data_manager.remove_player(self.scenario_player.player_id)
            pass
        
        self.scenario_actions.clear()
        self.triggered_events.clear()
        self.intervention_results.clear()
        
        self.logger.info("场景数据清理完成")