from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class PlayerStatus(str, Enum):
    """玩家状态枚举"""
    ACTIVE = "active"          # 活跃
    FRUSTRATED = "frustrated"  # 受挫
    SATISFIED = "satisfied"    # 满意
    CHURNING = "churning"      # 流失风险
    INACTIVE = "inactive"      # 不活跃

class Player(BaseModel):
    """玩家数据模型"""
    
    player_id: str
    username: str
    vip_level: int = 0
    level: int = 1
    
    # 基础属性
    total_playtime_hours: float = 0.0
    last_login: Optional[datetime] = None
    registration_date: datetime
    
    # 经济数据
    total_spent: float = 0.0
    last_purchase_date: Optional[datetime] = None
    current_currency: int = 0
    
    # 游戏进度
    current_stage: int = 1
    equipment_power: int = 100
    
    # 状态信息
    current_status: PlayerStatus = PlayerStatus.ACTIVE
    frustration_level: int = 0  # 0-10的受挫程度
    consecutive_failures: int = 0
    
    # 社交信息
    guild_id: Optional[str] = None
    friends_count: int = 0
    
    # 扩展属性
    custom_attributes: Dict[str, Any] = {}
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        
    def update_status(self, new_status: PlayerStatus, reason: str = ""):
        """更新玩家状态"""
        self.current_status = new_status
        if reason:
            self.custom_attributes["last_status_change_reason"] = reason
            self.custom_attributes["last_status_change_time"] = datetime.now().isoformat()
    
    def increment_failures(self):
        """增加连续失败次数"""
        self.consecutive_failures += 1
        if self.consecutive_failures >= 2:
            self.frustration_level = min(10, self.frustration_level + 2)
            if self.consecutive_failures >= 3:
                self.update_status(PlayerStatus.FRUSTRATED, "连续失败过多")
    
    def reset_failures(self):
        """重置失败计数"""
        self.consecutive_failures = 0
        if self.frustration_level > 0:
            self.frustration_level = max(0, self.frustration_level - 1)
    
    def is_high_value(self) -> bool:
        """判断是否为高价值玩家"""
        return self.vip_level >= 3 or self.total_spent >= 100.0
    
    def get_intervention_priority(self) -> int:
        """获取干预优先级 (1-10, 10最高)"""
        priority = 1
        
        # 基于价值
        if self.is_high_value():
            priority += 3
        
        # 基于受挫程度
        priority += min(4, self.frustration_level // 2)
        
        # 基于连续失败
        priority += min(2, self.consecutive_failures)
        
        return min(10, priority)