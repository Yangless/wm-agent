import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

from src.models.player import Player, PlayerStatus
from src.models.action import PlayerAction, ActionType
from src.models.trigger import TriggerEvent, TriggerCondition
from src.config.settings import settings

class DataManager:
    """数据管理器 - 统一管理所有游戏数据"""
    
    def __init__(self):
        self.players: Dict[str, Player] = {}
        self.action_history: List[PlayerAction] = []
        self.trigger_events: List[TriggerEvent] = []
        self.mail_history: List[Dict[str, Any]] = []
    
    # ==================== 玩家数据管理 ====================
    
    def get_player(self, player_id: str) -> Optional[Player]:
        """获取玩家信息"""
        return self.players.get(player_id)
    
    def update_player(self, player: Player):
        """更新玩家信息"""
        self.players[player.player_id] = player
    
    def get_all_players(self) -> List[Player]:
        """获取所有玩家"""
        return list(self.players.values())
    
    def get_players_by_status(self, status: PlayerStatus) -> List[Player]:
        """根据状态获取玩家列表"""
        return [player for player in self.players.values() if player.current_status == status]
    
    def get_high_value_players(self) -> List[Player]:
        """获取高价值玩家列表"""
        return [player for player in self.players.values() if player.is_high_value()]
    
    # ==================== 行为数据管理 ====================
    
    def add_action(self, action: PlayerAction):
        """添加玩家行为记录"""
        self.action_history.append(action)
        
        # 更新玩家状态
        player = self.get_player(action.player_id)
        if player:
            if action.is_failure():
                player.increment_failures()
            elif action.is_success():
                player.reset_failures()
    
    def get_player_actions(self, 
                          player_id: str, 
                          limit: int = 50,
                          action_types: Optional[List[ActionType]] = None,
                          time_window_minutes: Optional[int] = None) -> List[PlayerAction]:
        """获取玩家行为历史
        
        Args:
            player_id: 玩家ID
            limit: 返回数量限制
            action_types: 筛选的行为类型
            time_window_minutes: 时间窗口（分钟）
        """
        # 筛选玩家行为
        player_actions = [
            action for action in self.action_history
            if action.player_id == player_id
        ]
        
        # 时间窗口筛选
        if time_window_minutes:
            cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
            player_actions = [
                action for action in player_actions
                if action.timestamp >= cutoff_time
            ]
        
        # 行为类型筛选
        if action_types:
            player_actions = [
                action for action in player_actions
                if action.action_type in action_types
            ]
        
        # 按时间倒序排列
        player_actions.sort(key=lambda x: x.timestamp, reverse=True)
        return player_actions[:limit]
    
    def get_recent_failures(self, player_id: str, minutes: int = 10) -> List[PlayerAction]:
        """获取玩家最近的失败行为"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [
            action for action in self.action_history
            if (action.player_id == player_id and 
                action.timestamp >= cutoff_time and 
                action.is_failure())
        ]
    
    def analyze_player_behavior_pattern(self, player_id: str) -> Dict[str, Any]:
        """分析玩家行为模式"""
        recent_actions = self.get_player_actions(player_id, limit=20)
        
        if not recent_actions:
            return {"pattern": "no_data", "risk_level": 0}
        
        # 统计各类行为
        failure_count = sum(1 for action in recent_actions if action.is_failure())
        success_count = sum(1 for action in recent_actions if action.is_success())
        social_count = sum(1 for action in recent_actions if action.is_social_activity())
        help_seeking_count = sum(1 for action in recent_actions if action.is_help_seeking())
        
        # 计算情绪影响
        total_emotional_impact = sum(action.get_emotional_impact() for action in recent_actions)
        
        # 分析连续失败
        consecutive_failures = 0
        for action in recent_actions:
            if action.is_failure():
                consecutive_failures += 1
            else:
                break
        
        # 判断行为模式
        pattern = "normal"
        risk_level = 1
        
        if consecutive_failures >= 3:
            pattern = "high_frustration"
            risk_level = 8
        elif consecutive_failures >= 2 and help_seeking_count > 0:
            pattern = "seeking_help"
            risk_level = 6
        elif failure_count > success_count * 2:
            pattern = "struggling"
            risk_level = 5
        elif total_emotional_impact < -5:
            pattern = "negative_trend"
            risk_level = 4
        
        return {
            "pattern": pattern,
            "risk_level": risk_level,
            "consecutive_failures": consecutive_failures,
            "failure_rate": failure_count / len(recent_actions) if recent_actions else 0,
            "emotional_impact": total_emotional_impact,
            "social_activity": social_count,
            "help_seeking": help_seeking_count,
            "total_actions": len(recent_actions)
        }
    
    # ==================== 触发事件管理 ====================
    
    def add_trigger_event(self, event: TriggerEvent):
        """添加触发事件"""
        self.trigger_events.append(event)
    
    def get_player_trigger_history(self, player_id: str) -> List[TriggerEvent]:
        """获取玩家的触发历史"""
        return [
            event for event in self.trigger_events
            if event.player_id == player_id
        ]
    
    def check_trigger_cooldown(self, player_id: str, trigger_condition: TriggerCondition) -> bool:
        """检查触发冷却时间"""
        recent_triggers = [
            event for event in self.trigger_events
            if (event.player_id == player_id and 
                event.trigger_condition.trigger_type == trigger_condition.trigger_type)
        ]
        
        if not recent_triggers:
            return True  # 没有历史触发，可以触发
        
        # 检查最近的触发时间
        latest_trigger = max(recent_triggers, key=lambda x: x.triggered_at)
        cooldown_end = latest_trigger.triggered_at + timedelta(hours=trigger_condition.cooldown_hours)
        
        return datetime.now() >= cooldown_end
    
    # ==================== 邮件系统管理 ====================
    
    def send_mail(self, 
                  player_id: str, 
                  title: str, 
                  content: str, 
                  attachments: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """发送游戏内邮件"""
        mail = {
            "mail_id": f"mail_{len(self.mail_history) + 1:06d}",
            "player_id": player_id,
            "title": title,
            "content": content,
            "attachments": attachments or [],
            "sent_at": datetime.now().isoformat(),
            "read": False,
            "claimed": False
        }
        
        self.mail_history.append(mail)
        return mail
    
    def get_player_mails(self, player_id: str, unread_only: bool = False) -> List[Dict[str, Any]]:
        """获取玩家邮件"""
        player_mails = [
            mail for mail in self.mail_history
            if mail["player_id"] == player_id
        ]
        
        if unread_only:
            player_mails = [mail for mail in player_mails if not mail["read"]]
        
        return sorted(player_mails, key=lambda x: x["sent_at"], reverse=True)
    
    # ==================== 数据持久化 ====================
    
    def save_to_files(self):
        """保存所有数据到文件"""
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # 保存玩家数据
        players_data = {
            player_id: player.dict() 
            for player_id, player in self.players.items()
        }
        with open(data_dir / "players.json", 'w', encoding='utf-8') as f:
            json.dump(players_data, f, ensure_ascii=False, indent=2, default=str)
        
        # 保存行为历史
        actions_data = [action.dict() for action in self.action_history]
        with open(data_dir / "action_history.json", 'w', encoding='utf-8') as f:
            json.dump(actions_data, f, ensure_ascii=False, indent=2, default=str)
        
        # 保存触发事件
        triggers_data = [event.dict() for event in self.trigger_events]
        with open(data_dir / "trigger_events.json", 'w', encoding='utf-8') as f:
            json.dump(triggers_data, f, ensure_ascii=False, indent=2, default=str)
        
        # 保存邮件历史
        with open(data_dir / "mail_history.json", 'w', encoding='utf-8') as f:
            json.dump(self.mail_history, f, ensure_ascii=False, indent=2, default=str)
    
    def load_from_files(self):
        """从文件加载所有数据"""
        data_dir = Path("data")
        
        try:
            # 加载玩家数据
            players_file = data_dir / "players.json"
            if players_file.exists():
                with open(players_file, 'r', encoding='utf-8') as f:
                    players_data = json.load(f)
                    self.players = {
                        player_id: Player(**player_data)
                        for player_id, player_data in players_data.items()
                    }
            
            # 加载行为历史
            actions_file = data_dir / "action_history.json"
            if actions_file.exists():
                with open(actions_file, 'r', encoding='utf-8') as f:
                    actions_data = json.load(f)
                    self.action_history = [
                        PlayerAction(**action_data)
                        for action_data in actions_data
                    ]
            
            # 加载触发事件
            triggers_file = data_dir / "trigger_events.json"
            if triggers_file.exists():
                with open(triggers_file, 'r', encoding='utf-8') as f:
                    triggers_data = json.load(f)
                    self.trigger_events = [
                        TriggerEvent(**event_data)
                        for event_data in triggers_data
                    ]
            
            # 加载邮件历史
            mail_file = data_dir / "mail_history.json"
            if mail_file.exists():
                with open(mail_file, 'r', encoding='utf-8') as f:
                    self.mail_history = json.load(f)
                    
        except Exception as e:
            print(f"加载数据文件时出错: {e}")
    
    # ==================== 统计分析 ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据统计信息"""
        return {
            "total_players": len(self.players),
            "active_players": len(self.get_players_by_status(PlayerStatus.ACTIVE)),
            "frustrated_players": len(self.get_players_by_status(PlayerStatus.FRUSTRATED)),
            "high_value_players": len(self.get_high_value_players()),
            "total_actions": len(self.action_history),
            "total_triggers": len(self.trigger_events),
            "total_mails": len(self.mail_history),
            "recent_actions_1h": len([
                action for action in self.action_history
                if action.timestamp >= datetime.now() - timedelta(hours=1)
            ])
        }