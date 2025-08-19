from typing import Dict, List, Optional, Any ,Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import json
from datetime import datetime, timedelta

from ..models.player import Player, BotRiskLevel
from ..llm.llm_client import LLMClient


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
    
    # name = "bot_detection"
    # description = "分析玩家行为模式，识别潜在的机器人用户"
    # args_schema = BotDetectionInput
    name: str = "bot_detection"
    description: str = "分析玩家行为模式，识别潜在的机器人用户"
    args_schema: Type[BotDetectionInput] = BotDetectionInput


    # def __init__(self, llm_client: LLMClient, player_manager=None):
    #     super().__init__()
    #     self.llm_client = llm_client
    #     self.player_manager = player_manager
    llm_client: LLMClient
    player_manager: Optional[Any] = None
    
    def _run(self, player_id: str, behavior_data: Dict[str, Any], 
             time_window_hours: int = 24, analysis_depth: str = "standard") -> str:
        """执行机器人检测
        
        Args:
            player_id: 玩家ID
            behavior_data: 玩家行为数据
            time_window_hours: 分析时间窗口
            analysis_depth: 分析深度
            
        Returns:
            str: 检测结果的JSON字符串
        """
        try:
            # 获取玩家信息
            player = self._get_player_info(player_id)
            
            # 构建检测提示
            detection_prompt = self._build_detection_prompt(
                player, behavior_data, time_window_hours, analysis_depth
            )
            
            # 调用LLM进行分析
            response = self.llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": detection_prompt}
                ],
                temperature=0.1  # 较低的温度以获得更一致的分析
            )
            
            # 解析LLM响应
            detection_result = self._parse_llm_response(response)
            
            # 更新玩家机器人风险状态
            if self.player_manager and detection_result.get("success"):
                self._update_player_bot_risk(player_id, detection_result)
            
            return json.dumps(detection_result, ensure_ascii=False, indent=2)
            
        except Exception as e:
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
你是一个专业的游戏机器人检测专家。你的任务是分析玩家的行为数据，识别潜在的机器人用户。

机器人用户的典型特征包括：

1. **行为规律性**：
   - 操作时间间隔过于规律（如每隔固定秒数执行操作）
   - 行为模式高度重复，缺乏人类的随机性
   - 24小时内活动时间分布异常（如连续长时间在线）

2. **操作模式**：
   - 鼠标移动轨迹过于直线或规律
   - 点击位置过于精确，缺乏人类的微小偏差
   - 反应时间过于一致，缺乏人类的变化
   - 从不出现误操作或犹豫

3. **游戏行为**：
   - 执行重复性任务的效率异常高
   - 对游戏环境变化反应迟钝
   - 缺乏探索性行为，只执行特定任务
   - 不参与社交互动或聊天

4. **账户特征**：
   - 账户创建后立即开始高强度游戏
   - 游戏进度异常快速且单一
   - 缺乏正常的学习曲线
   - 设备信息异常或频繁变化

5. **异常指标**：
   - APM（每分钟操作数）异常高且稳定
   - 在线时长异常（如连续20+小时）
   - 经济行为异常（如只进行特定类型的交易）
   - 对游戏更新或变化无适应期

风险等级定义：
- LOW: 行为基本正常，偶有可疑迹象
- MEDIUM: 存在多个可疑指标，需要进一步观察
- HIGH: 高度可疑，多项指标异常
- CONFIRMED: 确认为机器人用户

请基于提供的数据进行综合分析，给出检测结果和置信度。
"""
    
    def _build_detection_prompt(self, player: Optional[Player], behavior_data: Dict[str, Any], 
                               time_window_hours: int, analysis_depth: str) -> str:
        """构建检测提示"""
        prompt_parts = []
        
        # 玩家基本信息
        if player:
            prompt_parts.append(f"""
玩家基本信息：
- 玩家ID: {player.player_id}
- 用户名: {player.username}
- 账户创建时间: {getattr(player, 'created_at', '未知')}
- VIP等级: {player.vip_level}
- 总游戏时长: {player.total_playtime_hours}小时
- 最后登录: {player.last_login}
- 总消费: ${player.total_spent}
""")
            
            # 历史机器人检测记录
            if hasattr(player, 'bot_risk_level') and player.bot_risk_level:
                prompt_parts.append(f"""
历史检测记录：
- 当前风险等级: {player.bot_risk_level.value}
- 检测分数: {getattr(player, 'bot_detection_score', 0.0)}
- 上次分析时间: {getattr(player, 'last_bot_analysis', '未知')}
- 风险指标: {getattr(player, 'bot_indicators', [])}
""")
        
        # 行为数据分析
        prompt_parts.append(f"""
行为数据分析（最近{time_window_hours}小时）：
{json.dumps(behavior_data, ensure_ascii=False, indent=2)}
""")
        
        # 分析要求
        if analysis_depth == "basic":
            analysis_requirement = "请进行基础机器人检测，重点关注明显的异常行为模式。"
        elif analysis_depth == "detailed":
            analysis_requirement = "请进行详细机器人检测，包括深度行为分析、模式识别和风险评估。"
        else:  # standard
            analysis_requirement = "请进行标准机器人检测，综合分析行为模式和风险指标。"
        
        prompt_parts.append(f"""
检测要求：
{analysis_requirement}

请重点分析以下维度：
1. 操作时间规律性
2. 行为模式重复性
3. 反应时间一致性
4. 社交互动频率
5. 游戏进度合理性
6. 在线时长分布
7. 经济行为模式

请以以下JSON格式返回结果：
{{
    "success": true,
    "player_id": "玩家ID",
    "timestamp": "检测时间",
    "bot_risk_level": "LOW/MEDIUM/HIGH/CONFIRMED",
    "detection_score": 0.75,
    "confidence_score": 0.85,
    "risk_indicators": [
        {{
            "category": "操作规律性",
            "description": "操作时间间隔过于规律",
            "severity": "high",
            "evidence": ["具体证据1", "具体证据2"]
        }}
    ],
    "behavioral_analysis": {{
        "operation_regularity": 0.8,
        "pattern_repetition": 0.7,
        "reaction_consistency": 0.9,
        "social_interaction": 0.1,
        "progression_reasonableness": 0.6,
        "online_time_distribution": 0.8,
        "economic_behavior": 0.5
    }},
    "recommendations": [
        "建议进行进一步监控",
        "建议人工审核"
    ],
    "next_check_hours": 24
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
    
    def _update_player_bot_risk(self, player_id: str, detection_result: Dict[str, Any]):
        """更新玩家机器人风险状态"""
        try:
            if not self.player_manager:
                return
            
            player = self.player_manager.get_player(player_id)
            if not player:
                return
            
            # 提取风险信息
            risk_level_str = detection_result.get("bot_risk_level", "LOW")
            detection_score = detection_result.get("detection_score", 0.0)
            risk_indicators = []
            
            # 提取风险指标
            for indicator in detection_result.get("risk_indicators", []):
                risk_indicators.append(f"{indicator.get('category', '')}: {indicator.get('description', '')}")
            
            try:
                risk_level = BotRiskLevel(risk_level_str)
            except ValueError:
                risk_level = BotRiskLevel.LOW
            
            # 更新玩家机器人风险
            player.update_bot_risk(risk_level, detection_score, risk_indicators)
                
        except Exception as e:
            print(f"更新玩家机器人风险状态时出错: {str(e)}")
    
    def _get_player_info(self, player_id: str) -> Optional[Player]:
        """获取玩家信息"""
        if self.player_manager:
            return self.player_manager.get_player(player_id)
        return None
    
    async def _arun(self, *args, **kwargs):
        """异步运行（暂不实现）"""
        raise NotImplementedError("BotDetectionTool不支持异步运行")