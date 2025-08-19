from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ActionType(str, Enum):
    """玩家行为类型枚举"""
    
    # 战斗相关
    ATTACK_CITY = "attack_city"           # 攻城
    ATTACK_PLAYER = "attack_player"       # 攻击玩家
    DEFEND = "defend"                     # 防守
    BATTLE_WIN = "battle_win"             # 战斗胜利
    BATTLE_LOSE = "battle_lose"           # 战斗失败
    SKILL_USE = "skill_use"               # 使用技能
    
    # 社交相关
    CHAT_WORLD = "chat_world"             # 世界聊天
    CHAT_GUILD = "chat_guild"             # 公会聊天
    CHAT_PRIVATE = "chat_private"         # 私聊
    JOIN_GUILD = "join_guild"             # 加入公会
    LEAVE_GUILD = "leave_guild"           # 离开公会
    
    # 系统交互
    LOGIN = "login"                       # 登录
    LOGOUT = "logout"                     # 登出
    OPEN_SHOP = "open_shop"               # 打开商店
    OPEN_INVENTORY = "open_inventory"     # 打开背包
    OPEN_GUIDE = "open_guide"             # 打开攻略
    GAME_EXIT = "game_exit"               # 退出游戏
    
    # 经济行为
    PURCHASE = "purchase"                 # 购买
    SELL = "sell"                         # 出售
    TRADE = "trade"                       # 交易
    CARD_DRAW = "card_draw"               # 抽卡
    
    # 进度相关
    LEVEL_UP = "level_up"                 # 升级
    COMPLETE_QUEST = "complete_quest"     # 完成任务
    UPGRADE_EQUIPMENT = "upgrade_equipment" # 升级装备
    
    # 负面行为
    RAGE_QUIT = "rage_quit"               # 愤怒退出
    COMPLAIN = "complain"                 # 抱怨
    IDLE_TIMEOUT = "idle_timeout"         # 挂机超时

class PlayerAction(BaseModel):
    """玩家行为记录模型"""
    
    action_id: str
    player_id: str
    action_type: ActionType
    timestamp: datetime
    
    # 行为详情
    target: Optional[str] = None          # 行为目标（如攻击的城市ID、聊天对象等）
    result: Optional[str] = None          # 行为结果（成功/失败/其他）
    value: Optional[float] = None         # 数值结果（如伤害、获得金币等）
    
    # 上下文信息
    location: Optional[str] = None        # 发生位置
    session_id: Optional[str] = None      # 会话ID
    
    # 扩展数据
    metadata: Dict[str, Any] = {}
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def is_failure(self) -> bool:
        """判断是否为失败行为"""
        failure_types = {
            ActionType.BATTLE_LOSE,
            ActionType.RAGE_QUIT,
            ActionType.COMPLAIN,
            ActionType.ATTACK_CITY,
            ActionType.IDLE_TIMEOUT
        }
        return self.action_type in failure_types or self.result == "failure"
    
    def is_success(self) -> bool:
        """判断是否为成功行为"""
        success_types = {
            ActionType.BATTLE_WIN,
            ActionType.LEVEL_UP,
            ActionType.COMPLETE_QUEST,
            ActionType.PURCHASE
        }
        return self.action_type in success_types or self.result == "success"
    
    def is_social_activity(self) -> bool:
        """判断是否为社交行为"""
        social_types = {
            ActionType.CHAT_WORLD,
            ActionType.CHAT_GUILD,
            ActionType.CHAT_PRIVATE,
            ActionType.JOIN_GUILD
        }
        return self.action_type in social_types
    
    def is_help_seeking(self) -> bool:
        """判断是否为寻求帮助的行为"""
        help_types = {
            ActionType.OPEN_GUIDE,
            ActionType.CHAT_WORLD,  # 可能在求助
            ActionType.COMPLAIN     # 抱怨也可能是求助的表现
        }
        return self.action_type in help_types
    
    def get_emotional_impact(self) -> int:
        """获取情绪影响值 (-5到+5, 负数表示负面情绪)"""
        impact_map = {
            ActionType.BATTLE_WIN: 3,
            ActionType.LEVEL_UP: 4,
            ActionType.COMPLETE_QUEST: 2,
            ActionType.PURCHASE: 1,
            ActionType.JOIN_GUILD: 2,
            
            ActionType.BATTLE_LOSE: -2,
            ActionType.RAGE_QUIT: -5,
            ActionType.COMPLAIN: -3,
            ActionType.IDLE_TIMEOUT: -1,
            ActionType.LEAVE_GUILD: -2
        }
        return impact_map.get(self.action_type, 0)