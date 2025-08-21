from typing import Dict, List, Optional, Any ,Type, Union
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import json
from datetime import datetime
import traceback

# 假设这些类从您的项目中导入
from ..models.player import Player, BotRiskLevel
from ..llm.llm_client import LLMClient
from ..data.data_manager import DataManager # 显式导入DataManager

class BotDetectionInput(BaseModel):
    """机器人检测工具输入参数"""
    player_id: str = Field(description="玩家ID")
    behavior_data: Dict[str, Any] = Field(description="玩家行为数据")
    time_window_hours: int = Field(default=24, description="分析时间窗口（小时）")
    analysis_depth: str = Field(default="standard", description="分析深度: basic, standard, detailed")


class BotDetectionTool(BaseTool):
    """机器人检测工具
    
    使用LLM分析玩家行为模式，识别潜在的机器人用户。
    分析包括行为规律性、操作模式、时间分布等多个维度。
    """
    
    name: str = "bot_detection"
    description: str = "分析玩家行为模式，识别潜在的机器人用户"
    args_schema: Type[BotDetectionInput] = BotDetectionInput

    # ========================== 修改点 1：依赖项名称变更 ==========================
    llm_client: LLMClient
    
    data_manager: Optional[DataManager] = None # 将 player_manager 修改为 data_manager
    # =======================================================================
    
    def _parse_input(
        self, tool_input: Union[str, dict], tool_call_id: Optional[str] = None
    ) -> Union[str, dict]:
        """
        重写 LangChain 的 _parse_input 方法来处理LLM可能输出的字符串格式
        """
        # 此方法逻辑保持不变
        if isinstance(tool_input, dict):
            return tool_input
        if isinstance(tool_input, str):
            try:
                cleaned_input = tool_input.strip().lstrip('```json').lstrip('```').rstrip('```')
                return json.loads(cleaned_input)
            except json.JSONDecodeError:
                return tool_input
        return tool_input
    
    def _run(self, player_id: str, behavior_data: Dict[str, Any], 
             time_window_hours: int = 24, analysis_depth: str = "standard") -> str:
        """执行机器人检测"""
        try:
            player = self._get_player_info(player_id)
            print(player_id)
            print(player)
            if not player:
                raise ValueError(f"玩家ID {player_id} 不存在")
            
            detection_prompt = self._build_detection_prompt(
                player, behavior_data, time_window_hours, analysis_depth
            )
            
            response = self.llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": detection_prompt}
                ],
                temperature=0.1
            )
            
            detection_result = self._parse_llm_response(response)
            
            # ========================== 修改点 2：使用 data_manager ==========================
            if self.data_manager and detection_result.get("success"):
                self._update_player_bot_risk(player_id, detection_result)
            # =========================================================================
            
            return json.dumps(detection_result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            traceback.print_exc()
            error_result = {
                "success": False,
                "error": str(e),
                "player_id": player_id,
                "timestamp": datetime.now().isoformat()
            }
            return json.dumps(error_result, ensure_ascii=False, indent=2)
    
    def _get_system_prompt(self) -> str:
        """获取系统提示"""
        # 此方法逻辑保持不变
        return """
你是一个专业的游戏机器人检测专家。你的任务是分析玩家的行为数据，识别潜在的机器人用户...
"""
    
    def _build_detection_prompt(self, player: Player, behavior_data: Dict[str, Any], 
                               time_window_hours: int, analysis_depth: str) -> str:
        """构建检测提示"""
        # 此方法逻辑保持不变
        prompt_parts = []
        prompt_parts.append(f"""
玩家基本信息：
- 玩家ID: {player.player_id}
- 用户名: {player.username}
- 账户创建时间: {getattr(player, 'created_at', '未知')}
- VIP等级: {player.vip_level}
...
""")
        # ... (后续 prompt 构建逻辑保持不变)
        return "\n".join(prompt_parts)
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        # 此方法逻辑保持不变
        try:
            response = response.strip().lstrip('```json').lstrip('```').rstrip('```')
            if response.strip().startswith('{'):
                return json.loads(response)
            
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            raise json.JSONDecodeError("在响应中未找到有效的JSON对象", response, 0)
        except json.JSONDecodeError as e:
            return {
                "success": False, "error": f"JSON解析错误: {str(e)}",
                "raw_response": response, "timestamp": datetime.now().isoformat()
            }
    
    def _update_player_bot_risk(self, player_id: str, detection_result: Dict[str, Any]):
        """更新玩家机器人风险状态"""
        try:
            # ========================== 修改点 3：使用 data_manager ==========================
            if not self.data_manager: return
            player = self.data_manager.get_player(player_id)
            if not player: return
            # =========================================================================
            
            risk_level_str = detection_result.get("bot_risk_level", "LOW")
            detection_score = detection_result.get("detection_score", 0.0)
            risk_indicators = []
            
            for indicator in detection_result.get("risk_indicators", []):
                risk_indicators.append(f"{indicator.get('category', '')}: {indicator.get('description', '')}")
            
            try:
                risk_level = BotRiskLevel(risk_level_str.upper())
            except ValueError:
                risk_level = BotRiskLevel.LOW
            
            # 调用Player对象自身的方法来更新状态
            player.update_bot_risk(risk_level, detection_score, risk_indicators)
            
            # ========================== 修改点 4：持久化更新 ==========================
            # 通过data_manager将更新后的player对象保存
            self.data_manager.update_player(player)
            # =======================================================================
                
        except Exception as e:
            print(f"更新玩家机器人风险状态时出错: {str(e)}")
    
    def _get_player_info(self, player_id: str) -> Optional[Player]:
        """获取玩家信息"""
        # ========================== 修改点 5：使用 data_manager ==========================
        if self.data_manager:
            return self.data_manager.get_player(player_id)
        # =========================================================================
        return None
    
    async def _arun(self, *args, **kwargs):
        """异步运行（暂不实现）"""
        raise NotImplementedError("BotDetectionTool不支持异步运行")