from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
from .action import PlayerAction, ActionType

class TriggerType(str, Enum):
    """触发器类型"""
    CONSECUTIVE_FAILURES = "consecutive_failures"  # 连续失败
    EMOTIONAL_DECLINE = "emotional_decline"        # 情绪下降
    HELP_SEEKING = "help_seeking"                  # 寻求帮助
    HIGH_VALUE_RISK = "high_value_risk"            # 高价值玩家风险
    SOCIAL_ISOLATION = "social_isolation"          # 社交孤立
    
    # 新增的触发类型
    EMOTION_INTERVENTION = "emotion_intervention"   # 情绪干预（两个负面+一个正面）
    BOT_DETECTION = "bot_detection"                # 机器人检测
    CHURN_RISK = "churn_risk"                      # 流失风险

class TriggerCondition(BaseModel):
    """触发条件配置"""
    
    trigger_type: TriggerType
    name: str
    description: str
    
    # 基础条件
    min_failures: int = 2                    # 最少失败次数
    time_window_minutes: int = 5             # 时间窗口（分钟）
    
    # 高级条件
    required_action_types: List[ActionType] = []  # 必须包含的行为类型
    excluded_action_types: List[ActionType] = []  # 排除的行为类型
    
    # 玩家筛选条件
    min_vip_level: Optional[int] = None      # 最低VIP等级
    min_total_spent: Optional[float] = None  # 最低消费金额
    
    # 情绪阈值
    max_frustration_level: int = 10          # 最大受挫程度
    min_emotional_impact: int = -5           # 最小情绪影响值
    
    # 优先级
    priority: int = 5                        # 1-10，数字越大优先级越高
    
    # 冷却时间
    cooldown_hours: int = 1                  # 同一玩家触发间隔（小时）
    
    def check_time_window(self, actions: List[PlayerAction]) -> bool:
        """检查时间窗口内的行为"""
        if not actions:
            return False
            
        now = datetime.now()
        window_start = now - timedelta(minutes=self.time_window_minutes)
        
        recent_actions = [
            action for action in actions 
            if action.timestamp >= window_start
        ]
        
        return len(recent_actions) >= self.min_failures
    
    def check_failure_pattern(self, actions: List[PlayerAction]) -> bool:
        """检查失败模式"""
        if len(actions) < self.min_failures:
            return False
            
        # 检查连续失败
        failure_count = 0
        for action in reversed(actions[-10:]):  # 检查最近10个行为
            print("action:", action)
            if action.is_failure():
                failure_count += 1
                if failure_count >= self.min_failures:
                    return True
            else:
                failure_count = 0
                
        return False
    
    def check_action_types(self, actions: List[PlayerAction]) -> bool:
        """检查行为类型条件"""
        print("actions:", actions)

        action_types = {action.action_type for action in actions}
        
        # 检查必须包含的行为类型
        if self.required_action_types:
            if not all(req_type in action_types for req_type in self.required_action_types):
                return False
        
        # 检查排除的行为类型
        if self.excluded_action_types:
            if any(exc_type in action_types for exc_type in self.excluded_action_types):
                return False
                
        return True
    
    def calculate_emotional_impact(self, actions: List[PlayerAction]) -> int:
        """计算总体情绪影响"""
        total_impact = sum(action.get_emotional_impact() for action in actions)
        return total_impact

class TriggerEvent(BaseModel):
    """触发事件记录"""
    
    event_id: str
    player_id: str
    trigger_condition: TriggerCondition
    triggered_at: datetime
    
    # 触发上下文
    triggering_actions: List[PlayerAction]
    player_status_snapshot: Dict[str, Any]
    
    # 处理状态
    processed: bool = False
    processed_at: Optional[datetime] = None
    agent_response: Optional[str] = None
    
    # 结果追踪
    intervention_sent: bool = False
    player_response_tracked: bool = False
    effectiveness_score: Optional[int] = None  # 1-10评分
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def mark_processed(self, agent_response: str):
        """标记为已处理"""
        self.processed = True
        self.processed_at = datetime.now()
        self.agent_response = agent_response
    
    def mark_intervention_sent(self):
        """标记干预已发送"""
        self.intervention_sent = True
    
    def evaluate_effectiveness(self, score: int):
        """评估干预效果"""
        self.effectiveness_score = max(1, min(10, score))
        self.player_response_tracked = True

# 预定义的触发条件
DEFAULT_TRIGGERS = [
    TriggerCondition(
        trigger_type=TriggerType.CONSECUTIVE_FAILURES,
        name="连续攻城失败",
        description="玩家在5分钟内连续2次攻城失败",
        min_failures=1,
        time_window_minutes=20,
        required_action_types=[ActionType.ATTACK_CITY],
        priority=8
    ),
    
    TriggerCondition(
        trigger_type=TriggerType.HIGH_VALUE_RISK,
        name="高价值玩家受挫",
        description="VIP3+玩家出现连续失败和抱怨行为",
        min_failures=1,
        time_window_minutes=10,
        min_vip_level=3,
        required_action_types=[ActionType.BATTLE_LOSE, ActionType.COMPLAIN],
        priority=10
    ),
    
    TriggerCondition(
        trigger_type=TriggerType.HELP_SEEKING,
        name="寻求帮助信号",
        description="玩家失败后主动查看攻略或在世界频道发言",
        min_failures=1,
        time_window_minutes=3,
        required_action_types=[ActionType.BATTLE_LOSE, ActionType.OPEN_GUIDE],
        priority=6
    ),
    
    # 新增的触发条件
    TriggerCondition(
        trigger_type=TriggerType.EMOTION_INTERVENTION,
        name="情绪干预触发",
        description="检测到玩家有两个负面情绪和一个正面情绪的组合",
        min_failures=0,  # 不依赖失败次数
        time_window_minutes=60,  # 1小时内的行为
        priority=9,  # 高优先级
        cooldown_hours=2  # 2小时冷却
    ),
    
    TriggerCondition(
        trigger_type=TriggerType.BOT_DETECTION,
        name="机器人检测触发",
        description="检测到疑似机器人行为模式",
        min_failures=0,
        time_window_minutes=120,  # 2小时内的行为
        priority=7,
        cooldown_hours=6  # 6小时冷却
    ),
    
    TriggerCondition(
        trigger_type=TriggerType.CHURN_RISK,
        name="流失风险触发",
        description="检测到玩家有流失风险",
        min_failures=0,
        time_window_minutes=1440,  # 24小时内的行为
        priority=8,
        cooldown_hours=12  # 12小时冷却
    )
]