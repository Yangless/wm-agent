from typing import Dict, List, Optional, Any ,Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import json
from datetime import datetime

from src.models.player import Player, EmotionType
from src.llm.llm_client import LLMClient
import traceback

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
    # name = "emotion_analysis"
    # description = "分析玩家情绪状态，识别负面和正面情绪，支持奖励和安慰两种干预类型"
    # args_schema = EmotionAnalysisInput
    args_schema: Type[EmotionAnalysisInput] = EmotionAnalysisInput
    
    # def __init__(self, llm_client: LLMClient, player_manager=None):
    #     super().__init__()
    #     self.llm_client = llm_client
    #     self.player_manager = player_manager
    
    llm_client: LLMClient
    player_manager: Optional[Any] = None

    def _run(self, player_id: str, behavior_data: Dict[str, Any], 
             context: Optional[str] = None, analysis_depth: str = "standard") -> str:
        """执行情绪分析
        
        Args:
            player_id: 玩家ID
            behavior_data: 玩家行为数据
            context: 分析上下文
            analysis_depth: 分析深度
            
        Returns:
            str: 分析结果的JSON字符串
        """
        try:
            # 获取玩家信息
            player = self._get_player_info(player_id)
            
            # 打印行为数据
            print("behavior_data:", behavior_data)
            print("context:", context)
            # 构建分析提示
            analysis_prompt = self._build_analysis_prompt(
                player, behavior_data, context, analysis_depth
            )
            # 打印分析提示
            print("analysis_prompt:", analysis_prompt)
            
            # 调用LLM进行分析
            response = self.llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3
            )

            print("response:", response)
            
            # 解析LLM响应
            analysis_result = self._parse_llm_response(response)
            print("analysis_result:", analysis_result)
            
            # 更新玩家情绪状态
            if self.player_manager and analysis_result.get("emotions"):
                self._update_player_emotions(player_id, analysis_result)
            
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
        return """
你是一个专业的游戏玩家情绪分析师。你的任务是分析玩家的行为数据，识别其情绪状态。

请特别关注以下情绪类型：

负面情绪：
- FRUSTRATION（挫败感）：连续失败、卡关、技能不足
- ANGER（愤怒）：不公平对待、系统问题、其他玩家行为
- BOREDOM（无聊）：重复性任务、缺乏挑战、内容单调
- ANXIETY（焦虑）：竞争压力、时间限制、不确定性
- DISAPPOINTMENT（失望）：期望落空、奖励不足、进度缓慢

正面情绪：
- JOY（快乐）：成功完成任务、获得奖励、社交互动
- EXCITEMENT（兴奋）：新内容、挑战、期待
- SATISFACTION（满足）：目标达成、技能提升、认可
- PRIDE（自豪）：成就解锁、排名提升、技能展示
- CURIOSITY（好奇）：探索新区域、学习新机制、发现秘密

分析要求：
1. 识别当前主要的情绪状态（可以有多个）
2. 评估每种情绪的强度（0.0-1.0）
3. 特别关注是否存在"两个负面情绪"
4. 特别关注是否存在"两个正面情绪"
4. 提供干预建议
5. 评估情绪变化趋势

请以JSON格式返回分析结果。
"""
    
    def _build_analysis_prompt(self, player: Optional[Player], behavior_data: Dict[str, Any], 
                              context: Optional[str], analysis_depth: str) -> str:
        """构建分析提示"""
        prompt_parts = []
        
        # 玩家基本信息
        if player:
            prompt_parts.append(f"""
玩家基本信息：
- 玩家ID: {player.player_id}
- 用户名: {player.username}
- VIP等级: {player.vip_level}
- 总游戏时长: {player.total_playtime_hours}小时
- 最后登录: {player.last_login}
- 当前状态: {player.current_status.value}
- 挫败等级: {player.frustration_level}
- 连续失败次数: {player.consecutive_failures}
""")
            
            # 历史情绪信息
            if hasattr(player, 'emotion_history') and player.emotion_history:
                recent_emotions = player.emotion_history[-3:]  # 最近3次情绪记录
                prompt_parts.append(f"""
最近情绪历史：
{json.dumps(recent_emotions, ensure_ascii=False, indent=2)}
""")
        
        # 行为数据
        prompt_parts.append(f"""
当前行为数据：
{json.dumps(behavior_data, ensure_ascii=False, indent=2)}
""")
        
        # 上下文信息
        if context:
            prompt_parts.append(f"""
分析上下文：
{context}
""")
        
        # 分析要求
        if analysis_depth == "basic":
            analysis_requirement = "请进行基础情绪识别，重点关注主要情绪状态。"
        elif analysis_depth == "detailed":
            analysis_requirement = "请进行详细情绪分析，包括情绪成因、发展趋势和具体干预建议。"
        else:  # standard
            analysis_requirement = "请进行标准情绪分析，识别主要情绪并提供干预建议。"
        
        prompt_parts.append(f"""
分析要求：
{analysis_requirement}

请特别关注以下两种干预场景：
1. 正面情绪场景：连续胜利、连续抽到金卡等，如果检测到2个或以上正面情绪，需要奖励干预
2. 负面情绪场景：连续被攻击、连续失败等，如果检测到2个或以上负面情绪，需要安慰干预

请以以下JSON格式返回结果：
{{
    "success": true,
    "player_id": "玩家ID",
    "timestamp": "分析时间",
    "emotions": [
        {{
            "type": "情绪类型",
            "intensity": 0.8,
            "category": "negative/positive",
            "indicators": ["指标1", "指标2"]
        }}
    ],
    "dominant_negative_emotions": ["负面情绪1", "负面情绪2"],
    "dominant_positive_emotions": ["正面情绪1", "正面情绪2"],
    "intervention_needed": true/false,
    "intervention_type": "reward/comfort/none",
    "intervention_reason": "干预原因",
    "intervention_suggestions": ["建议1", "建议2"],
    "emotion_trend": "improving/declining/stable",
    "confidence_score": 0.85
}}
""")
        
        return "\n".join(prompt_parts)
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            # 尝试直接解析JSON
            if response.strip().startswith('{'):
                return json.loads(response)
            
            # 如果响应包含其他内容，尝试提取JSON部分
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # 如果无法解析，返回错误结果
            return {
                "success": False,
                "error": "无法解析LLM响应",
                "raw_response": response,
                "timestamp": datetime.now().isoformat()
            }
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"JSON解析错误: {str(e)}",
                "raw_response": response,
                "timestamp": datetime.now().isoformat()
            }
    
    def _update_player_emotions(self, player_id: str, analysis_result: Dict[str, Any]):
        """更新玩家情绪状态"""
        try:
            if not self.player_manager:
                return
            
            player = self.player_manager.get_player(player_id)
            if not player:
                return
            
            # 提取情绪信息
            emotions_data = analysis_result.get("emotions", [])
            emotions = []
            intensities = {}
            
            for emotion_data in emotions_data:
                emotion_type_str = emotion_data.get("type", "")
                try:
                    emotion_type = EmotionType(emotion_type_str)
                    emotions.append(emotion_type)
                    intensities[emotion_type.value] = emotion_data.get("intensity", 0.5)
                except ValueError:
                    # 忽略无法识别的情绪类型
                    continue
            
            # 更新玩家情绪
            if emotions:
                player.update_emotions(emotions, intensities)
                
        except Exception as e:
            print(f"更新玩家情绪状态时出错: {str(e)}")
    
    def _get_player_info(self, player_id: str) -> Optional[Player]:
        """获取玩家信息"""
        if self.player_manager:
            return self.player_manager.get_player(player_id)
        return None
    
    async def _arun(self, *args, **kwargs):
        """异步运行（暂不实现）"""
        raise NotImplementedError("EmotionAnalysisTool不支持异步运行")