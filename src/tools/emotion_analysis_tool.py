from typing import Dict, List, Optional, Any , Type, Union
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import json
from datetime import datetime
import traceback

# 假设这些类从您的项目中导入
from src.models.player import Player, EmotionType
from src.llm.llm_client import LLMClient
from src.data.data_manager import DataManager # 显式导入DataManager以获得更好的类型提示

class EmotionAnalysisInput(BaseModel):
    """情绪分析工具输入参数"""
    player_id: str = Field(description="玩家ID")
    behavior_data: Dict[str, Any] = Field(description="玩家行为数据")
    context: Optional[str] = Field(default=None, description="分析上下文")
    analysis_depth: str = Field(default="standard", description="分析深度: basic, standard, detailed")


class EmotionAnalysisTool(BaseTool):
    """情绪分析工具
    
    使用LLM分析玩家的情绪状态，识别负面和正面情绪，
    支持基于正面情绪的奖励干预和基于负面情绪的安慰干预。
    """
    
    name: str = "emotion_analysis"
    description: str = "分析玩家情绪状态，识别负面和正面情绪，支持奖励和安慰两种干预类型"
    args_schema: Type[EmotionAnalysisInput] = EmotionAnalysisInput
    
    # ========================== 修改点 1：依赖项名称变更 ==========================
    llm_client: LLMClient
    data_manager: Optional[DataManager] = None  # 将 player_manager 修改为 data_manager
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
             context: Optional[str] = None, analysis_depth: str = "standard") -> str:
        """执行情绪分析"""
        try:
            print("_get_player_info:",player_id)
            print("self.data_manager:",self.data_manager)
            player = self._get_player_info(player_id)
            if not player:
                raise ValueError(f"玩家ID {player_id} 不存在")
            
            print("收到的行为数据:", behavior_data)
            print("分析上下文:", context)
            
            analysis_prompt = self._build_analysis_prompt(
                player, behavior_data, context, analysis_depth
            )
            
            response = self.llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3
            )
            
            analysis_result = self._parse_llm_response(response)
            
            # ========================== 修改点 2：使用 data_manager ==========================
            if self.data_manager and analysis_result.get("emotions"):
                self._update_player_emotions(player_id, analysis_result)
            # =========================================================================
            
            return json.dumps(analysis_result, ensure_ascii=False, indent=2)
            
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
你是一个专业的游戏玩家情绪分析师。你的任务是分析玩家的行为数据，识别其情绪状态...
"""
    
    def _build_analysis_prompt(self, player: Player, behavior_data: Dict[str, Any], 
                              context: Optional[str], analysis_depth: str) -> str:
        """构建分析提示"""
        # 此方法逻辑保持不变
        prompt_parts = []
        prompt_parts.append(f"""
玩家基本信息：
- 玩家ID: {player.player_id}
- 用户名: {player.username}
- VIP等级: {player.vip_level}
- 总游戏时长: {player.total_playtime_hours}小时
- 最后登录: {player.last_login}
- 当前状态: {player.current_status}
- 挫败等级: {player.frustration_level}
- 连续失败次数: {player.consecutive_failures}
""")
        # ... (后续 prompt 构建逻辑保持不变)
        if hasattr(player, 'emotion_history') and player.emotion_history:
             prompt_parts.append(f"""
最近情绪历史：
{json.dumps(player.emotion_history[-3:], ensure_ascii=False, indent=2)}
""")
        prompt_parts.append(f"""
当前行为数据：
{json.dumps(behavior_data, ensure_ascii=False, indent=2)}
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
    
    def _update_player_emotions(self, player_id: str, analysis_result: Dict[str, Any]):
        """更新玩家情绪状态"""
        try:
            # ========================== 修改点 3：使用 data_manager ==========================
            if not self.data_manager: return
            player = self.data_manager.get_player(player_id)
            if not player: return
            # =========================================================================
            
            emotions_data = analysis_result.get("emotions", [])
            emotions = []
            intensities = {}
            
            for emotion_data in emotions_data:
                emotion_type_str = emotion_data.get("type", "")
                try:
                    emotion_type = EmotionType(emotion_type_str.upper())
                    emotions.append(emotion_type)
                    intensities[emotion_type.value] = emotion_data.get("intensity", 0.5)
                except ValueError:
                    continue
            
            if emotions:
                # 调用Player对象自身的方法来更新状态
                player.update_emotions(emotions, intensities)
                # 通过data_manager将更新后的player对象持久化（如果需要）
                self.data_manager.update_player(player)
                
        except Exception as e:
            print(f"更新玩家情绪状态时出错: {str(e)}")
    
    def _get_player_info(self, player_id: str) -> Optional[Player]:
        """获取玩家信息"""
        # ========================== 修改点 4：使用 data_manager ==========================
        
        if self.data_manager:
            print("self.data_manager_player_id:",player_id)
            return self.data_manager.get_player(player_id)
        # =========================================================================
        return None
    
    async def _arun(self, *args, **kwargs):
        """异步运行（暂不实现）"""
        raise NotImplementedError("EmotionAnalysisTool不支持异步运行")