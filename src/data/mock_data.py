import json
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..models.player import Player, PlayerStatus
from ..models.action import PlayerAction, ActionType
from ..config.settings import settings

class MockDataGenerator:
    """模拟数据生成器"""
    
    def __init__(self):
        self.players: Dict[str, Player] = {}
        self.action_history: List[PlayerAction] = []
        
        # 预定义的玩家名称
        self.player_names = [
            "张三", "李四", "王五", "赵六", "钱七", "孙八", "周九", "吴十",
            "DragonSlayer", "ShadowHunter", "FireMage", "IceQueen", 
            "StormLord", "NightWolf", "GoldenEagle", "SilverFox"
        ]
        
        # 城市名称
        self.city_names = [
            "雷霆要塞", "烈火城", "寒冰堡", "暗影谷", "光明神殿",
            "Dragon Keep", "Storm Castle", "Fire Citadel", "Ice Fortress"
        ]
    
    def generate_player(self, 
                       player_id: Optional[str] = None,
                       username: Optional[str] = None,
                       player_type: str = "normal") -> Player:
        """生成一个模拟玩家
        
        Args:
            player_id: 指定玩家ID，如果为None则自动生成
            username: 指定用户名，如果为None则随机选择
            player_type: 玩家类型 (normal, high_value, frustrated, new)
        """
        if not player_id:
            player_id = f"player_{uuid.uuid4().hex[:8]}"
        
        if not username:
            username = random.choice(self.player_names)
        
        # 根据玩家类型设置不同的属性
        if player_type == "high_value":
            vip_level = random.randint(3, 8)
            total_spent = random.uniform(100, 1000)
            level = random.randint(20, 50)
            equipment_power = random.randint(500, 2000)
        elif player_type == "frustrated":
            vip_level = random.randint(1, 4)
            total_spent = random.uniform(10, 100)
            level = random.randint(10, 25)
            equipment_power = random.randint(200, 800)
        elif player_type == "new":
            vip_level = 0
            total_spent = 0
            level = random.randint(1, 5)
            equipment_power = random.randint(50, 200)
        else:  # normal
            vip_level = random.randint(0, 3)
            total_spent = random.uniform(0, 50)
            level = random.randint(5, 30)
            equipment_power = random.randint(150, 1000)
        
        # 创建玩家对象
        player = Player(
            player_id=player_id,
            username=username,
            vip_level=vip_level,
            level=level,
            total_playtime_hours=random.uniform(10, 500),
            last_login=datetime.now() - timedelta(minutes=random.randint(0, 60)),
            registration_date=datetime.now() - timedelta(days=random.randint(1, 365)),
            total_spent=total_spent,
            last_purchase_date=datetime.now() - timedelta(days=random.randint(1, 30)) if total_spent > 0 else None,
            current_currency=random.randint(100, 10000),
            current_stage=random.randint(1, 20),
            equipment_power=equipment_power,
            current_status=PlayerStatus.ACTIVE if player_type != "frustrated" else PlayerStatus.FRUSTRATED,
            frustration_level=random.randint(0, 3) if player_type != "frustrated" else random.randint(5, 8),
            consecutive_failures=0 if player_type != "frustrated" else random.randint(1, 3),
            guild_id=f"guild_{random.randint(1, 10)}" if random.random() > 0.3 else None,
            friends_count=random.randint(0, 50)
        )
        
        self.players[player_id] = player
        return player
    
    def generate_action_sequence(self, 
                               player_id: str,
                               sequence_type: str = "normal",
                               count: int = 10) -> List[PlayerAction]:
        """生成玩家行为序列
        
        Args:
            player_id: 玩家ID
            sequence_type: 序列类型 (normal, frustration, success, mixed)
            count: 生成的行为数量
        """
        actions = []
        base_time = datetime.now() - timedelta(minutes=30)
        
        for i in range(count):
            action_time = base_time + timedelta(minutes=i * 2 + random.uniform(0, 2))
            
            if sequence_type == "frustration":
                action_type = self._get_frustration_action(i, count)
            elif sequence_type == "satisfaction":
                action_type = self._get_success_action(i, count)
            elif sequence_type == "success":
                action_type = self._get_success_action(i, count)
            elif sequence_type == "mixed":
                action_type = self._get_mixed_action(i, count)
            else:  # normal
                action_type = self._get_normal_action()
            
            action = PlayerAction(
                action_id=f"action_{uuid.uuid4().hex[:8]}",
                player_id=player_id,
                action_type=action_type,
                timestamp=action_time,
                target=self._get_action_target(action_type),
                result=self._get_action_result(action_type, sequence_type),
                value=self._get_action_value(action_type),
                location=f"zone_{random.randint(1, 5)}",
                session_id=f"session_{uuid.uuid4().hex[:8]}",
                metadata=self._get_action_metadata(action_type)
            )
            
            actions.append(action)
            self.action_history.append(action)
        
        return actions
    
    def _get_frustration_action(self, index: int, total: int) -> ActionType:
        """获取受挫序列的行为类型"""
        # 受挫序列：开始正常 -> 连续失败 -> 抱怨/求助
        if index < total * 0.3:
            return random.choice([ActionType.LOGIN, ActionType.ATTACK_CITY, ActionType.OPEN_INVENTORY])
        elif index < total * 0.7:
            return random.choice([ActionType.ATTACK_CITY, ActionType.BATTLE_LOSE, ActionType.ATTACK_PLAYER])
        else:
            return random.choice([ActionType.COMPLAIN, ActionType.CHAT_WORLD, ActionType.OPEN_GUIDE, ActionType.RAGE_QUIT])
    
    def _get_success_action(self, index: int, total: int) -> ActionType:
        """获取成功序列的行为类型"""
        success_actions = [
            ActionType.LOGIN, ActionType.BATTLE_WIN, ActionType.LEVEL_UP,
            ActionType.COMPLETE_QUEST, ActionType.PURCHASE, ActionType.UPGRADE_EQUIPMENT
        ]
        return random.choice(success_actions)
    
    def _get_satisfaction_action(self, index: int, total: int) -> ActionType:
        """获取满意序列的行为类型"""
        # 满意序列：开始正常 -> 连续成功 -> 分享/反馈
        if index < total * 0.3:
            return random.choice([ActionType.LOGIN, ActionType.BATTLE_WIN, ActionType.LEVEL_UP])
        elif index < total * 0.7:
            return random.choice([ActionType.BATTLE_WIN, ActionType.COMPLETE_QUEST, ActionType.PURCHASE])
        else:
            return random.choice([ActionType.SHARE, ActionType.FEEDBACK, ActionType.CHAT_WORLD])
    
    def _get_mixed_action(self, index: int, total: int) -> ActionType:
        """获取混合序列的行为类型"""
        all_actions = list(ActionType)
        return random.choice(all_actions)
    
    def _get_normal_action(self) -> ActionType:
        """获取正常的行为类型"""
        normal_actions = [
            ActionType.LOGIN, ActionType.ATTACK_CITY, ActionType.CHAT_GUILD,
            ActionType.OPEN_SHOP, ActionType.COMPLETE_QUEST, ActionType.LOGOUT
        ]
        return random.choice(normal_actions)
    
    def _get_action_target(self, action_type: ActionType) -> Optional[str]:
        """获取行为目标"""
        if action_type in [ActionType.ATTACK_CITY, ActionType.DEFEND]:
            return random.choice(self.city_names)
        elif action_type == ActionType.ATTACK_PLAYER:
            return f"player_{random.randint(1000, 9999)}"
        elif action_type in [ActionType.CHAT_PRIVATE]:
            return f"friend_{random.randint(1, 100)}"
        return None
    
    def _get_action_result(self, action_type: ActionType, sequence_type: str) -> Optional[str]:
        """获取行为结果"""
        if action_type in [ActionType.ATTACK_CITY, ActionType.ATTACK_PLAYER, ActionType.DEFEND]:
            if sequence_type == "frustration":
                return "failure" if random.random() > 0.3 else "success"
            elif sequence_type == "success":
                return "success" if random.random() > 0.2 else "failure"
            else:
                return "success" if random.random() > 0.5 else "failure"
        return None
    
    def _get_action_value(self, action_type: ActionType) -> Optional[float]:
        """获取行为数值"""
        if action_type == ActionType.PURCHASE:
            return random.uniform(1, 100)
        elif action_type in [ActionType.BATTLE_WIN, ActionType.COMPLETE_QUEST]:
            return random.uniform(100, 1000)  # 经验值或金币
        return None
    
    def _get_action_metadata(self, action_type: ActionType) -> Dict[str, Any]:
        """获取行为元数据"""
        metadata = {}
        
        if action_type == ActionType.CHAT_WORLD:
            messages = [
                "这游戏太难了", "有人能帮帮我吗", "怎么老是失败", 
                "攻略在哪里", "装备不够强", "需要更多资源"
            ]
            metadata["message"] = random.choice(messages)
        elif action_type == ActionType.COMPLAIN:
            complaints = [
                "游戏平衡性有问题", "敌人太强了", "资源获取太慢",
                "充值才能玩", "新手不友好", "难度曲线太陡"
            ]
            metadata["complaint"] = random.choice(complaints)
        
        return metadata
    
    def create_frustration_scenario(self, player_id: str = "zhang_san") -> Dict[str, Any]:
        """创建标准的受挫场景
        
        这是核心演示场景：玩家连续攻城失败后表现出受挫情绪
        """
        # 创建受挫类型的玩家
        player = self.generate_player(
            player_id=player_id,
            username="张三",
            player_type="high_value"  # 高价值玩家更需要关注
        )
        
        # 生成特定的受挫行为序列
        scenario_actions = []
        base_time = datetime.now() - timedelta(minutes=10)
        
        # 第一次攻城失败
        scenario_actions.append(PlayerAction(
            action_id=f"action_{uuid.uuid4().hex[:8]}",
            player_id=player_id,
            action_type=ActionType.ATTACK_CITY,
            timestamp=base_time,
            target="雷霆要塞",
            result="failure",
            value=0,
            metadata={"damage_dealt": 1200, "enemy_remaining_hp": 300}
        ))
        
        # 第二次攻城失败（2分钟后）
        scenario_actions.append(PlayerAction(
            action_id=f"action_{uuid.uuid4().hex[:8]}",
            player_id=player_id,
            action_type=ActionType.ATTACK_CITY,
            timestamp=base_time + timedelta(minutes=2),
            target="雷霆要塞",
            result="failure",
            value=0,
            metadata={"damage_dealt": 1150, "enemy_remaining_hp": 450}
        ))
        
        # 在世界频道抱怨（30秒后）
        scenario_actions.append(PlayerAction(
            action_id=f"action_{uuid.uuid4().hex[:8]}",
            player_id=player_id,
            action_type=ActionType.CHAT_WORLD,
            timestamp=base_time + timedelta(minutes=2, seconds=30),
            target="world_channel",
            result="sent",
            metadata={"message": "这游戏太难了，连续两次都打不过这个城"}
        ))
        
        # 查看攻略（1分钟后）
        scenario_actions.append(PlayerAction(
            action_id=f"action_{uuid.uuid4().hex[:8]}",
            player_id=player_id,
            action_type=ActionType.OPEN_GUIDE,
            timestamp=base_time + timedelta(minutes=3, seconds=30),
            target="strategy_guide",
            result="opened",
            metadata={"guide_section": "城市攻略", "time_spent_seconds": 45}
        ))
        
        # 更新玩家状态
        player.increment_failures()
        player.increment_failures()
        
        # 保存数据
        self.action_history.extend(scenario_actions)
        
        return {
            "player": player,
            "actions": scenario_actions,
            "scenario_type": "frustration",
            "trigger_conditions_met": True,
            "description": "高价值玩家张三在5分钟内连续两次攻城失败，随后在世界频道抱怨并查看攻略"
        }
    
    def save_to_files(self):
        """保存数据到文件"""
        # 确保数据目录存在
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # 保存玩家数据
        players_data = {
            player_id: player.dict() 
            for player_id, player in self.players.items()
        }
        
        with open(settings.player_data_file, 'w', encoding='utf-8') as f:
            json.dump(players_data, f, ensure_ascii=False, indent=2, default=str)
        
        # 保存行为历史
        actions_data = [action.dict() for action in self.action_history]
        
        with open(settings.action_history_file, 'w', encoding='utf-8') as f:
            json.dump(actions_data, f, ensure_ascii=False, indent=2, default=str)
    
    def load_from_files(self):
        """从文件加载数据"""
        try:
            # 加载玩家数据
            if Path(settings.player_data_file).exists():
                with open(settings.player_data_file, 'r', encoding='utf-8') as f:
                    players_data = json.load(f)
                    self.players = {
                        player_id: Player(**player_data)
                        for player_id, player_data in players_data.items()
                    }
            
            # 加载行为历史
            if Path(settings.action_history_file).exists():
                with open(settings.action_history_file, 'r', encoding='utf-8') as f:
                    actions_data = json.load(f)
                    self.action_history = [
                        PlayerAction(**action_data)
                        for action_data in actions_data
                    ]
        except Exception as e:
            print(f"加载数据文件时出错: {e}")
    
    def get_player_actions(self, player_id: str, limit: int = 50) -> List[PlayerAction]:
        """获取指定玩家的行为历史"""
        player_actions = [
            action for action in self.action_history
            if action.player_id == player_id
        ]
        # 按时间倒序排列，返回最近的行为
        player_actions.sort(key=lambda x: x.timestamp, reverse=True)
        return player_actions[:limit]
    
    def get_recent_actions(self, minutes: int = 30) -> List[PlayerAction]:
        """获取最近N分钟的所有行为"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [
            action for action in self.action_history
            if action.timestamp >= cutoff_time
        ]