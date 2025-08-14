from typing import Optional, List, Dict, Any
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import json

from ..data.data_manager import DataManager
from ..models.action import ActionType

class GetPlayerStatusInput(BaseModel):
    """获取玩家状态工具的输入参数"""
    player_id: str = Field(description="玩家ID")

class GetPlayerStatusTool(BaseTool):
    """
    获取玩家状态工具
    
    查询玩家当前的核心数据，如VIP等级、最近充值时间、装备水平等
    """
    
    name: str = "get_player_status"
    description: str = """查询玩家当前的核心数据，包括VIP等级、消费情况、装备水平、当前状态等信息。
    输入参数：player_id (玩家ID)
    返回：JSON格式的玩家状态信息"""
    args_schema: type = GetPlayerStatusInput
    data_manager: DataManager
    # def __init__(self, data_manager: DataManager):
    #     super().__init__()
    #     self.data_manager = data_manager
    
    def _run(self, player_id: str) -> str:
        """执行工具逻辑"""
        try:
            player = self.data_manager.get_player(player_id)
            
            if not player:
                return json.dumps({
                    "error": "玩家不存在",
                    "player_id": player_id
                }, ensure_ascii=False)
            
            # 构建返回的玩家状态信息
            status_info = {
                "player_id": player.player_id,
                "username": player.username,
                "vip_level": player.vip_level,
                "level": player.level,
                "total_spent": player.total_spent,
                "current_currency": player.current_currency,
                "equipment_power": player.equipment_power,
                "current_status": player.current_status.value,
                "frustration_level": player.frustration_level,
                "consecutive_failures": player.consecutive_failures,
                "is_high_value": player.is_high_value(),
                "intervention_priority": player.get_intervention_priority(),
                "last_login": player.last_login.isoformat() if player.last_login else None,
                "total_playtime_hours": player.total_playtime_hours,
                "guild_id": player.guild_id,
                "friends_count": player.friends_count
            }
            
            return json.dumps(status_info, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return json.dumps({
                "error": f"查询玩家状态时出错: {str(e)}",
                "player_id": player_id
            }, ensure_ascii=False)
    
    async def _arun(self, player_id: str) -> str:
        """异步执行"""
        return self._run(player_id)

class GetPlayerActionHistoryInput(BaseModel):
    """获取玩家行为历史工具的输入参数"""
    player_id: str = Field(description="玩家ID")
    last_n_events: int = Field(default=10, description="获取最近N条行为记录")
    time_window_minutes: Optional[int] = Field(default=None, description="时间窗口（分钟），如果指定则只返回该时间内的行为")
    action_types: Optional[List[str]] = Field(default=None, description="筛选的行为类型列表")

class GetPlayerActionHistoryTool(BaseTool):
    """
    获取玩家行为历史工具
    
    查询玩家的行为历史记录，支持多种筛选条件
    """
    name: str = "get_player_action_history"
    description: str = """查询玩家的行为历史记录，支持多种筛选条件。
    输入参数：
    - player_id: 玩家ID
    - last_n_events: 获取最近N条记录（默认10条）
    - time_window_minutes: 时间窗口（分钟），可选
    - action_types: 行为类型筛选列表，可选
    返回：行为事件列表的JSON格式"""
    args_schema: type = GetPlayerActionHistoryInput
    data_manager: DataManager

    # def __init__(self, data_manager: DataManager):
    #     super().__init__()
    #     self.data_manager = data_manager
    
    def _run(self, 
             player_id: str, 
             last_n_events: int = 10,
             time_window_minutes: Optional[int] = None,
             action_types: Optional[List[str]] = None) -> str:
        """执行工具逻辑"""
        try:
            # 转换行为类型
            filter_action_types = None
            if action_types:
                try:
                    filter_action_types = [ActionType(action_type) for action_type in action_types]
                except ValueError as e:
                    return json.dumps({
                        "error": f"无效的行为类型: {str(e)}",
                        "valid_types": [action_type.value for action_type in ActionType]
                    }, ensure_ascii=False)
            
            # 获取行为历史
            actions = self.data_manager.get_player_actions(
                player_id=player_id,
                limit=last_n_events,
                action_types=filter_action_types,
                time_window_minutes=time_window_minutes
            )
            
            if not actions:
                return json.dumps({
                    "message": "未找到符合条件的行为记录",
                    "player_id": player_id,
                    "actions": []
                }, ensure_ascii=False)
            
            # 构建返回数据
            actions_data = []
            for action in actions:
                action_info = {
                    "action_id": action.action_id,
                    "action_type": action.action_type.value,
                    "timestamp": action.timestamp.isoformat(),
                    "target": action.target,
                    "result": action.result,
                    "value": action.value,
                    "location": action.location,
                    "is_failure": action.is_failure(),
                    "is_success": action.is_success(),
                    "emotional_impact": action.get_emotional_impact(),
                    "metadata": action.metadata
                }
                actions_data.append(action_info)
            
            # 分析行为模式
            behavior_analysis = self.data_manager.analyze_player_behavior_pattern(player_id)
            
            result = {
                "player_id": player_id,
                "total_actions": len(actions_data),
                "time_range": {
                    "from": actions[-1].timestamp.isoformat() if actions else None,
                    "to": actions[0].timestamp.isoformat() if actions else None
                },
                "behavior_analysis": behavior_analysis,
                "actions": actions_data
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return json.dumps({
                "error": f"查询行为历史时出错: {str(e)}",
                "player_id": player_id
            }, ensure_ascii=False)
    
    async def _arun(self, 
                    player_id: str, 
                    last_n_events: int = 10,
                    time_window_minutes: Optional[int] = None,
                    action_types: Optional[List[str]] = None) -> str:
        """异步执行"""
        return self._run(player_id, last_n_events, time_window_minutes, action_types)

class SendInGameMailInput(BaseModel):
    """发送游戏内邮件工具的输入参数"""
    player_id: str = Field(description="玩家ID")
    title: str = Field(description="邮件标题")
    content: str = Field(description="邮件内容")
    attachment_list: Optional[List[Dict[str, Any]]] = Field(default=None, description="附件列表")
    
class SendInGameMailTool(BaseTool):
    """
    发送游戏内邮件工具
    
    向玩家发送游戏内邮件，可以包含安慰、奖励或指导内容
    """
    name: str = "send_in_game_mail"
    description: str = """向玩家发送游戏内邮件，可以包含安慰、奖励或指导内容。
    输入参数：
    - player_id: 玩家ID
    - title: 邮件标题
    - content: 邮件内容
    - attachment_list: 附件列表，可选，格式为[{"item_type": "gold", "amount": 1000}, ...]
    返回：发送成功/失败状态"""
    args_schema: type = SendInGameMailInput
    data_manager: DataManager
    
    # def __init__(self, data_manager: DataManager):
    #     super().__init__()
    #     self.data_manager = data_manager
    
    def _run(self, 
             player_id: str, 
             title: str, 
             content: str,
             attachment_list: Optional[List[Dict[str, Any]]] = None) -> str:
        """执行工具逻辑"""
        try:
            # 检查玩家是否存在
            player = self.data_manager.get_player(player_id)
            if not player:
                return json.dumps({
                    "success": False,
                    "error": "玩家不存在",
                    "player_id": player_id
                }, ensure_ascii=False)
            
            # 处理附件
            processed_attachments = []
            if attachment_list:
                for attachment in attachment_list:
                    if isinstance(attachment, dict):
                        # 验证附件格式
                        if "item_type" in attachment and "amount" in attachment:
                            processed_attachments.append({
                                "item_type": attachment["item_type"],
                                "amount": attachment["amount"],
                                "description": attachment.get("description", "")
                            })
                        else:
                            return json.dumps({
                                "success": False,
                                "error": "附件格式错误，需要包含item_type和amount字段"
                            }, ensure_ascii=False)
            
            # 发送邮件
            mail = self.data_manager.send_mail(
                player_id=player_id,
                title=title,
                content=content,
                attachments=processed_attachments
            )
            
            return json.dumps({
                "success": True,
                "mail_id": mail["mail_id"],
                "player_id": player_id,
                "title": title,
                "sent_at": mail["sent_at"],
                "attachments_count": len(processed_attachments),
                "message": "邮件发送成功"
            }, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"发送邮件时出错: {str(e)}",
                "player_id": player_id
            }, ensure_ascii=False)
    
    async def _arun(self, 
                    player_id: str, 
                    title: str, 
                    content: str,
                    attachment_list: Optional[List[Dict[str, Any]]] = None) -> str:
        """异步执行"""
        return self._run(player_id, title, content, attachment_list)