import json
import traceback
from typing import Union, Any, Optional, List, Dict
from pydantic import BaseModel, Field, ValidationError
from langchain.tools import BaseTool
from ..data.data_manager import DataManager
from ..models.action import ActionType

from pydantic import BaseModel

# 保持原有的 Input 定义不变
class GetPlayerStatusInput(BaseModel):
    """为 GetPlayerStatusTool 定义输入格式."""
    
    player_id: str = Field(description="玩家ID")

class GetPlayerStatusTool(BaseTool):
    """
    获取玩家状态工具
    
    查询玩家当前的核心数据，如VIP等级、最近充值时间、装备水平等
    """
    
    name: str = "get_player_status"
    description: str = """查询玩家当前的核心数据，包括VIP等级、消费情况、装备水平、当前状态等信息。
    输入参数是一个JSON对象，格式为：{"player_id": "玩家ID"},没有其他信息，只有{"player_id": "玩家ID"}
    返回：JSON格式的玩家状态信息"""
    args_schema: type = GetPlayerStatusInput
    data_manager: DataManager = Field(default_factory=DataManager)

    def _parse_and_validate_input(self, tool_input: Any) -> GetPlayerStatusInput:
        """
        解析并验证输入参数
        
        Args:
            tool_input: 任意类型的输入
            
        Returns:
            GetPlayerStatusInput: 验证后的输入对象
            
        Raises:
            ValueError: 输入格式错误或验证失败
        """
        try:
            # 情况1: 已经是正确的 Pydantic 对象
            if isinstance(tool_input, GetPlayerStatusInput):
                return tool_input
            
            # 情况2: JSON 字符串 (最常见的 Agent 调用方式)
            elif isinstance(tool_input, str):
                try:
                    data = json.loads(tool_input)
                except json.JSONDecodeError as e:
                    raise ValueError(f"JSON 解析失败: {str(e)}")
                
                # 验证解析后的数据是字典
                if not isinstance(data, dict):
                    raise ValueError(f"输入必须是JSON对象，收到: {type(data).__name__}")
                
                # 使用 Pydantic 验证
                return GetPlayerStatusInput(**data)
            
            # 情况3: 字典
            elif isinstance(tool_input, dict):
                return GetPlayerStatusInput(**tool_input)
            
            # 情况4: 不支持的类型
            else:
                raise ValueError(f"不支持的输入类型: {type(tool_input).__name__}")
                
        except ValidationError as e:
            # Pydantic 验证错误，提供更友好的错误信息
            error_details = []
            for error in e.errors():
                field = error['loc'][0] if error['loc'] else 'unknown'
                msg = error['msg']
                error_details.append(f"字段 '{field}': {msg}")
            raise ValueError(f"输入验证失败: {'; '.join(error_details)}")
        
        except Exception as e:
            raise ValueError(f"输入解析失败: {str(e)}")

    def _run(self, tool_input: Any) -> str:
        """
        执行工具逻辑
        
        Args:
            tool_input: 任意格式的输入（Agent会传入各种格式）
            
        Returns:
            str: JSON格式的结果
        """
        player_id = None  # 用于错误处理中的显示
        
        try:
            # 第一步：解析和验证输入
            print(f"原始输入: {tool_input}")
            print(f"输入类型: {type(tool_input)}")
            
            validated_input = self._parse_and_validate_input(tool_input)
            player_id = validated_input.player_id
            
            print(f"验证成功 - player_id: {player_id}, 类型: {type(player_id)}")
            
            # 第二步：业务逻辑验证
            if not player_id or not player_id.strip():
                return self._create_error_response("player_id 不能为空", player_id)
            
            # 第三步：获取玩家数据
            player = self.data_manager.get_player(player_id)
            
            if not player:
                print(f"未找到玩家: {player_id}")
                return self._create_error_response("玩家不存在", player_id)
            
            # 第四步：成功获取数据
            print(f"成功获取玩家状态: {player.dict()}")
            
            return self._create_success_response(player.dict())
            
        except ValueError as e:
            # 输入验证错误
            print(f"输入验证错误: {str(e)}")
            return self._create_error_response(f"输入错误: {str(e)}", player_id)
            
        except Exception as e:
            # 系统错误
            print(f"系统错误: {str(e)}")
            traceback.print_exc()
            return self._create_error_response(f"系统错误: {str(e)}", player_id)

    def _create_success_response(self, player_data: dict) -> str:
        """创建成功响应"""
        return json.dumps({
            "success": True,
            "player_status": player_data,
            "message": "查询成功"
        }, ensure_ascii=False, default=str)

    def _create_error_response(self, error_msg: str, player_id: str = None) -> str:
        """创建错误响应"""
        response = {
            "success": False,
            "error": error_msg,
            "player_status": None
        }
        
        # 只在有效的 player_id 时才包含
        if player_id:
            response["player_id"] = player_id
            
        return json.dumps(response, ensure_ascii=False)

    async def _arun(self, tool_input: Any) -> str:
        """异步执行 - 保持与 _run 相同的输入处理逻辑"""
        return self._run(tool_input)

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
    输入参数JSON格式：
    {
        "player_id": "玩家ID",
        "last_n_events": 10,  // 可选，默认10
        "time_window_minutes": null,  // 可选，时间窗口（分钟）
        "action_types": null  // 可选，行为类型列表
    }
    返回：行为事件列表的JSON格式"""
    args_schema: type = GetPlayerActionHistoryInput
    data_manager: DataManager

    def _parse_and_validate_input(self, tool_input: Any) -> GetPlayerActionHistoryInput:
        """
        解析并验证输入参数
        
        Args:
            tool_input: 任意类型的输入
            
        Returns:
            GetPlayerActionHistoryInput: 验证后的输入对象
            
        Raises:
            ValueError: 输入格式错误或验证失败
        """
        try:
            # 情况1: 已经是正确的 Pydantic 对象
            if isinstance(tool_input, GetPlayerActionHistoryInput):
                return tool_input
            
            # 情况2: JSON 字符串 (最常见的 Agent 调用方式)
            elif isinstance(tool_input, str):
                try:
                    data = json.loads(tool_input)
                except json.JSONDecodeError as e:
                    raise ValueError(f"JSON 解析失败: {str(e)}")
                
                if not isinstance(data, dict):
                    raise ValueError(f"输入必须是JSON对象，收到: {type(data).__name__}")
                
                return GetPlayerActionHistoryInput(**data)
            
            # 情况3: 字典
            elif isinstance(tool_input, dict):
                return GetPlayerActionHistoryInput(**tool_input)
            
            # 情况4: 不支持的类型
            else:
                raise ValueError(f"不支持的输入类型: {type(tool_input).__name__}")
                
        except ValidationError as e:
            # Pydantic 验证错误
            error_details = []
            for error in e.errors():
                field = '.'.join(str(loc) for loc in error['loc']) if error['loc'] else 'unknown'
                msg = error['msg']
                error_details.append(f"字段 '{field}': {msg}")
            raise ValueError(f"输入验证失败: {'; '.join(error_details)}")
        
        except Exception as e:
            raise ValueError(f"输入解析失败: {str(e)}")

    def _run(self, tool_input: Any) -> str:
        """
        执行工具逻辑
        
        Args:
            tool_input: 任意格式的输入（Agent会传入各种格式）
            
        Returns:
            str: JSON格式的结果
        """
        player_id = None  # 用于错误处理
        
        try:
            # 第一步：解析和验证输入
            print(f"原始输入: {tool_input}")
            print(f"输入类型: {type(tool_input)}")
            
            validated_input = self._parse_and_validate_input(tool_input)
            
            # 提取参数
            player_id = validated_input.player_id
            last_n_events = validated_input.last_n_events
            time_window_minutes = validated_input.time_window_minutes
            action_types = validated_input.action_types
            
            print(f"验证成功 - player_id: {player_id}, last_n_events: {last_n_events}")
            
            # 第二步：业务逻辑验证
            if not player_id or not player_id.strip():
                return self._create_error_response("player_id 不能为空", player_id)
            
            if last_n_events <= 0:
                return self._create_error_response("last_n_events 必须大于0", player_id)
            
            # 第三步：转换行为类型
            filter_action_types = None
            if action_types:
                try:
                    filter_action_types = [ActionType(action_type) for action_type in action_types]
                except ValueError as e:
                    return json.dumps({
                        "success": False,
                        "error": f"无效的行为类型: {str(e)}",
                        "valid_types": [action_type.value for action_type in ActionType],
                        "player_id": player_id
                    }, ensure_ascii=False)
            
            # 第四步：获取行为历史
            actions = self.data_manager.get_player_actions(
                player_id=player_id,
                limit=last_n_events,
                action_types=filter_action_types,
                time_window_minutes=time_window_minutes
            )
            
            if not actions:
                return json.dumps({
                    "success": True,
                    "message": "未找到符合条件的行为记录",
                    "player_id": player_id,
                    "total_actions": 0,
                    "actions": []
                }, ensure_ascii=False)
            
            # 第五步：构建返回数据
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
            
            # 第六步：分析行为模式
            behavior_analysis = self.data_manager.analyze_player_behavior_pattern(player_id)
            
            result = {
                "success": True,
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
            
        except ValueError as e:
            # 输入验证错误
            print(f"输入验证错误: {str(e)}")
            return self._create_error_response(f"输入错误: {str(e)}", player_id)
            
        except Exception as e:
            # 系统错误
            print(f"系统错误: {str(e)}")
            traceback.print_exc()
            return self._create_error_response(f"系统错误: {str(e)}", player_id)

    def _create_error_response(self, error_msg: str, player_id: str = None) -> str:
        """创建错误响应"""
        response = {
            "success": False,
            "error": error_msg,
            "actions": []
        }
        
        if player_id:
            response["player_id"] = player_id
            
        return json.dumps(response, ensure_ascii=False)

    async def _arun(self, tool_input: Any) -> str:
        """异步执行 - 保持与 _run 相同的输入处理逻辑"""
        return self._run(tool_input)


class SendInGameMailInput(BaseModel):
    """发送游戏内邮件工具的输入参数"""
    player_id: str = Field(description="玩家ID")
    title: str = Field(description="邮件标题")
    content: str = Field(description="邮件内容")
    attachment_list: Optional[List[Dict[str, Any]]] = Field(default=None, description="附件列表")

class SendInGameMailTool(BaseTool):
    """
    发送游戏内邮件工具 - 完全兼容 LangChain
    
    向玩家发送游戏内邮件，可以包含安慰、奖励或指导内容
    """
    name: str = "send_in_game_mail"
    description: str = """向玩家发送游戏内邮件，可以包含安慰、奖励或指导内容。
    输入参数JSON格式：
    {
        "player_id": "玩家ID",
        "title": "邮件标题", 
        "content": "邮件内容",
        "attachment_list": [  // 可选，附件列表
            {"item_type": "gold", "amount": 1000, "description": "奖励金币"},
            {"item_type": "exp", "amount": 500}
        ]
    }
    返回：发送成功/失败状态的JSON格式"""
    args_schema: type = SendInGameMailInput
    # data_manager: DataManager # 假设这个已经正确初始化
    # ... name, description, args_schema 等属性保持不变 ...

    # ========================== 修改部分开始 ==========================
    # 正确的方法签名，添加 tool_call_id 参数
    def _parse_input(
        self, tool_input: Union[str, dict], tool_call_id: Optional[str] = None
    ) -> Union[str, dict]:
    # ========================== 修改部分结束 ==========================
        """
        重写 LangChain 的 _parse_input 方法来处理LLM可能输出的字符串格式
        
        这个方法会在 LangChain 的验证之前被调用
        """
        print(f"LangChain _parse_input 调用，输入: {tool_input}")
        print(f"输入类型: {type(tool_input)}")
        
        # 如果输入已经是字典，直接返回
        if isinstance(tool_input, dict):
            return tool_input

        # 如果输入是字符串，尝试将其解析为JSON字典
        if isinstance(tool_input, str):
            try:
                parsed_input = json.loads(tool_input)
                print(f"输入是字符串，成功解析为JSON: {parsed_input}")
                return parsed_input
            except json.JSONDecodeError:
                print("字符串输入无法解析为JSON，返回原始输入让Pydantic处理")
                return tool_input

        return tool_input

    def _validate_attachments(self, attachment_list: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """验证附件列表格式"""
        processed_attachments = []
        if not attachment_list: 
            return processed_attachments
        
        if not isinstance(attachment_list, list): 
            raise ValueError(f"附件列表必须是数组格式，收到: {type(attachment_list).__name__}")
        
        for i, attachment in enumerate(attachment_list):
            if not isinstance(attachment, dict): 
                raise ValueError(f"附件[{i}]必须是对象格式，收到: {type(attachment).__name__}")
            
            if "item_type" not in attachment: 
                raise ValueError(f"附件[{i}]缺少必需字段 'item_type'")
            
            if "amount" not in attachment: 
                raise ValueError(f"附件[{i}]缺少必需字段 'amount'")
            
            item_type = attachment["item_type"]
            amount = attachment["amount"]
            
            if not isinstance(item_type, str) or not item_type.strip(): 
                raise ValueError(f"附件[{i}]的 'item_type' 必须是非空字符串")
            
            try:
                amount = int(amount)
                if amount <= 0: 
                    raise ValueError(f"附件[{i}]的 'amount' 必须是正整数")
            except (ValueError, TypeError): 
                raise ValueError(f"附件[{i}]的 'amount' 必须是有效的正整数")
            
            processed_attachment = {
                "item_type": item_type.strip(), 
                "amount": amount, 
                "description": attachment.get("description", "").strip()
            }
            processed_attachments.append(processed_attachment)
        
        return processed_attachments
        
    def _run(self, player_id: str, title: str, content: str, attachment_list: Optional[List[Dict[str, Any]]] = None) -> str:
        """执行发送邮件操作"""
        try:
            print(f"_run 被调用，参数： player_id={player_id}, title={title}, content={content}, attachment_list={attachment_list}")
            
            # 参数验证
            if not player_id or not player_id.strip(): 
                return self._create_error_response("player_id 不能为空", player_id)
            if not title or not title.strip(): 
                return self._create_error_response("邮件标题不能为空", player_id)
            if not content or not content.strip(): 
                return self._create_error_response("邮件内容不能为空", player_id)
            
            # 这里可以添加玩家存在性检查
            # player = self.data_manager.get_player(player_id)
            # if not player: return self._create_error_response("玩家不存在", player_id)
            
            # 验证附件
            try:
                processed_attachments = self._validate_attachments(attachment_list)
                print(f"附件验证成功，共 {len(processed_attachments)} 个附件")
            except ValueError as e: 
                return self._create_error_response(str(e), player_id)
            
            # 发送邮件
            try:
                # 这里是模拟的邮件发送逻辑
                # mail = self.data_manager.send_mail(...)
                mail = {"mail_id": "mail_12345", "sent_at": "2025-08-21T03:30:00Z"}
                
                result = {
                    "success": True, 
                    "mail_id": mail["mail_id"], 
                    "player_id": player_id, 
                    "title": title.strip(), 
                    "sent_at": mail["sent_at"], 
                    "attachments_count": len(processed_attachments), 
                    "message": "邮件发送成功"
                }
                
                if processed_attachments: 
                    result["attachments"] = processed_attachments
                
                print(f"邮件发送成功: mail_id={mail['mail_id']}")
                return json.dumps(result, ensure_ascii=False, indent=2)
                
            except Exception as mail_error:
                print(f"邮件发送失败: {str(mail_error)}")
                return self._create_error_response(f"邮件发送失败: {str(mail_error)}", player_id)
                
        except Exception as e:
            print(f"系统错误: {str(e)}")
            traceback.print_exc()
            return self._create_error_response(f"系统错误: {str(e)}", player_id)

    def _create_error_response(self, error_msg: str, player_id: str = None) -> str:
        """创建错误响应"""
        response = {
            "success": False, 
            "error": error_msg, 
            "mail_id": None, 
            "message": "邮件发送失败"
        }
        if player_id: 
            response["player_id"] = player_id
        return json.dumps(response, ensure_ascii=False)

    async def _arun(self, player_id: str, title: str, content: str, attachment_list: Optional[List[Dict[str, Any]]] = None) -> str:
        """异步执行发送邮件操作"""
        return self._run(player_id, title, content, attachment_list)