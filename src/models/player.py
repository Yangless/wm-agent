from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class PlayerStatus(str, Enum):
    """玩家状态枚举"""
    ACTIVE = "active"          # 活跃
    FRUSTRATED = "frustrated"  # 受挫
    SATISFIED = "satisfied"    # 满意
    CHURNING = "churning"      # 流失风险
    INACTIVE = "inactive"      # 不活跃

class EmotionType(str, Enum):
    """情绪类型枚举"""
    # 负面情绪
    FRUSTRATION = "frustration"    # 挫败感
    ANGER = "anger"              # 愤怒
    BOREDOM = "boredom"          # 无聊
    ANXIETY = "anxiety"          # 焦虑
    DISAPPOINTMENT = "disappointment"  # 失望
    
    # 正面情绪
    JOY = "joy"                  # 快乐
    EXCITEMENT = "excitement"    # 兴奋
    SATISFACTION = "satisfaction"  # 满足
    PRIDE = "pride"              # 自豪
    CURIOSITY = "curiosity"      # 好奇

class BotRiskLevel(str, Enum):
    """机器人风险等级"""
    LOW = "low"        # 低风险
    MEDIUM = "medium"  # 中等风险
    HIGH = "high"      # 高风险
    CONFIRMED = "confirmed"  # 确认为机器人

class ChurnRiskLevel(str, Enum):
    """流失风险等级"""
    LOW = "low"        # 低风险
    MEDIUM = "medium"  # 中等风险
    HIGH = "high"      # 高风险
    CRITICAL = "critical"  # 极高风险

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
    consecutive_satisfions: int = 0
    
    # 情绪状态 (新增)
    current_emotions: List[EmotionType] = []  # 当前情绪列表
    emotion_history: List[Dict[str, Any]] = []  # 情绪历史记录
    dominant_negative_emotions: List[EmotionType] = []  # 主要负面情绪（最多2个）
    dominant_positive_emotion: Optional[EmotionType] = None  # 主要正面情绪（1个）
    emotion_intensity: Dict[str, float] = {}  # 情绪强度 (0.0-1.0)
    last_emotion_analysis: Optional[datetime] = None  # 最后一次情绪分析时间
    
    # 机器人识别 (新增)
    bot_risk_level: BotRiskLevel = BotRiskLevel.LOW
    bot_detection_score: float = 0.0  # 0.0-1.0 机器人检测分数
    bot_indicators: List[str] = []  # 机器人行为指标
    last_bot_analysis: Optional[datetime] = None  # 最后一次机器人分析时间
    manual_bot_flag: Optional[bool] = None  # 人工标记的机器人标志
    
    # 流失风险识别 (新增)
    churn_risk_level: ChurnRiskLevel = ChurnRiskLevel.LOW
    churn_prediction_score: float = 0.0  # 0.0-1.0 流失预测分数
    churn_risk_factors: List[str] = []  # 流失风险因子
    last_churn_analysis: Optional[datetime] = None  # 最后一次流失分析时间
    predicted_churn_date: Optional[datetime] = None  # 预测流失日期
    
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
        
        # 基于情绪状态 (新增)
        if len(self.dominant_negative_emotions) >= 2:
            priority += 2
        
        # 基于流失风险 (新增)
        if self.churn_risk_level == ChurnRiskLevel.CRITICAL:
            priority += 3
        elif self.churn_risk_level == ChurnRiskLevel.HIGH:
            priority += 2
        
        return min(10, priority)
    
    def update_emotions(self, emotions: List[EmotionType], intensities: Dict[str, float] = None):
        """更新玩家情绪状态
        
        Args:
            emotions: 检测到的情绪列表
            intensities: 情绪强度字典
        """
        self.current_emotions = emotions
        if intensities:
            self.emotion_intensity.update(intensities)
        
        # 分离负面和正面情绪
        negative_emotions = [e for e in emotions if e in [
            EmotionType.FRUSTRATION, EmotionType.ANGER, EmotionType.BOREDOM,
            EmotionType.ANXIETY, EmotionType.DISAPPOINTMENT
        ]]
        positive_emotions = [e for e in emotions if e in [
            EmotionType.JOY, EmotionType.EXCITEMENT, EmotionType.SATISFACTION,
            EmotionType.PRIDE, EmotionType.CURIOSITY
        ]]
        
        # 更新主要负面情绪（最多2个）
        if negative_emotions:
            # 按强度排序，取前2个
            sorted_negative = sorted(negative_emotions, 
                                   key=lambda e: intensities.get(e.value, 0.5) if intensities else 0.5, 
                                   reverse=True)
            self.dominant_negative_emotions = sorted_negative[:2]
        
        # 更新主要正面情绪（1个）
        if positive_emotions:
            # 取强度最高的正面情绪
            self.dominant_positive_emotion = max(positive_emotions,
                                               key=lambda e: intensities.get(e.value, 0.5) if intensities else 0.5)
        
        # 记录情绪历史
        emotion_record = {
            "timestamp": datetime.now().isoformat(),
            "emotions": [e.value for e in emotions],
            "intensities": intensities or {},
            "dominant_negative": [e.value for e in self.dominant_negative_emotions],
            "dominant_positive": self.dominant_positive_emotion.value if self.dominant_positive_emotion else None
        }
        self.emotion_history.append(emotion_record)
        
        # 保持历史记录不超过100条
        if len(self.emotion_history) > 100:
            self.emotion_history = self.emotion_history[-100:]
        
        self.last_emotion_analysis = datetime.now()
    
    def update_bot_risk(self, risk_level: BotRiskLevel, detection_score: float, indicators: List[str] = None):
        """更新机器人风险评估
        
        Args:
            risk_level: 风险等级
            detection_score: 检测分数 (0.0-1.0)
            indicators: 风险指标列表
        """
        self.bot_risk_level = risk_level
        self.bot_detection_score = max(0.0, min(1.0, detection_score))
        if indicators:
            self.bot_indicators = indicators
        self.last_bot_analysis = datetime.now()
    
    def update_churn_risk(self, risk_level: ChurnRiskLevel, prediction_score: float, 
                         risk_factors: List[str] = None, predicted_date: datetime = None):
        """更新流失风险评估
        
        Args:
            risk_level: 风险等级
            prediction_score: 预测分数 (0.0-1.0)
            risk_factors: 风险因子列表
            predicted_date: 预测流失日期
        """
        self.churn_risk_level = risk_level
        self.churn_prediction_score = max(0.0, min(1.0, prediction_score))
        if risk_factors:
            self.churn_risk_factors = risk_factors
        if predicted_date:
            self.predicted_churn_date = predicted_date
        self.last_churn_analysis = datetime.now()
    
    def needs_emotion_intervention(self) -> bool:
        """判断是否需要基于情绪的干预
        
        Returns:
            bool: 是否需要干预
        """
        # 如果有2个负面情绪（安慰干预）或2个正面情绪（奖励干预），需要干预
        negative_intervention = len(self.dominant_negative_emotions) >= 2
        positive_intervention = len(self.dominant_positive_emotions) >= 2
        return negative_intervention or positive_intervention
    
    def is_likely_bot(self) -> bool:
        """判断是否可能是机器人用户
        
        Returns:
            bool: 是否可能是机器人
        """
        if self.manual_bot_flag is not None:
            return self.manual_bot_flag
        return self.bot_risk_level in [BotRiskLevel.HIGH, BotRiskLevel.CONFIRMED]
    
    def is_at_churn_risk(self) -> bool:
        """判断是否有流失风险
        
        Returns:
            bool: 是否有流失风险
        """
        return self.churn_risk_level in [ChurnRiskLevel.HIGH, ChurnRiskLevel.CRITICAL]