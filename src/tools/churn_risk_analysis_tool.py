from typing import Dict, List, Optional, Any , Type, Union
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import json
from datetime import datetime, timedelta
import traceback

# 假设这些类从您的项目中导入
from ..models.player import Player, ChurnRiskLevel
from ..llm.llm_client import LLMClient
from ..data.data_manager import DataManager # 显式导入DataManager以获得更好的类型提示

class ChurnRiskAnalysisInput(BaseModel):
    """流失风险分析工具输入参数"""
    player_id: str = Field(description="玩家ID")
    behavior_data: Dict[str, Any] = Field(description="玩家行为数据")
    time_window_days: int = Field(default=30, description="分析时间窗口（天）")
    analysis_depth: str = Field(default="standard", description="分析深度: basic, standard, detailed")


class ChurnRiskAnalysisTool(BaseTool):
    """流失风险分析工具
    
    使用LLM分析玩家行为模式，预测玩家的流失风险。
    分析包括活跃度变化、参与度下降、消费行为变化等多个维度。
    """
    
    name: str = "churn_risk_analysis"
    description: str = "分析玩家行为模式，预测玩家的流失风险"
    args_schema: Type[ChurnRiskAnalysisInput] = ChurnRiskAnalysisInput
    
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
             time_window_days: int = 30, analysis_depth: str = "standard") -> str:
        """执行流失风险分析"""
        try:
            player = self._get_player_info(player_id)
            if not player:
                raise ValueError(f"玩家ID '{player_id}' 不存在")
            
            analysis_prompt = self._build_analysis_prompt(
                player, behavior_data, time_window_days, analysis_depth
            )
            
            response = self.llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.2
            )
            
            analysis_result = self._parse_llm_response(response)
            
            # ========================== 修改点 2：使用 data_manager ==========================
            if self.data_manager and analysis_result.get("success"):
                self._update_player_churn_risk(player_id, analysis_result)
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
你是一个专业的游戏用户流失预测专家。你的任务是分析玩家的行为数据，预测玩家的流失风险...
"""
    
    def _build_analysis_prompt(self, player: Player, behavior_data: Dict[str, Any], 
                              time_window_days: int, analysis_depth: str) -> str:
        """构建分析提示"""
        # 此方法逻辑保持不变
        prompt_parts = []
        account_age_days = 0
        if hasattr(player, 'created_at') and player.created_at:
             account_age_days = (datetime.now().replace(tzinfo=None) - player.created_at.replace(tzinfo=None)).days
        prompt_parts.append(f"""
玩家基本信息：
- 玩家ID: {player.player_id}
- 用户名: {player.username}
- 账户年龄: {account_age_days}天
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
    
    def _update_player_churn_risk(self, player_id: str, analysis_result: Dict[str, Any]):
        """更新玩家流失风险状态"""
        try:
            # ========================== 修改点 3：使用 data_manager ==========================
            if not self.data_manager: return
            player = self.data_manager.get_player(player_id)
            if not player: return
            # =========================================================================
            
            risk_level_str = analysis_result.get("churn_risk_level", "LOW")
            prediction_score = analysis_result.get("churn_probability", 0.0)
            predicted_days = analysis_result.get("predicted_churn_days")
            risk_factors = []

            for factor in analysis_result.get("risk_factors", []):
                risk_factors.append(f"{factor.get('category', '')}: {factor.get('description', '')}")
            
            try:
                risk_level = ChurnRiskLevel(risk_level_str.upper())
            except (ValueError, AttributeError):
                risk_level = ChurnRiskLevel.LOW
            
            predicted_date = None
            if isinstance(predicted_days, (int, float)) and predicted_days > 0:
                predicted_date = datetime.now() + timedelta(days=predicted_days)
            
            # 调用Player对象自身的方法来更新状态
            player.update_churn_risk(risk_level, prediction_score, risk_factors, predicted_date)
            
            # ========================== 修改点 4：持久化更新 ==========================
            # 通过data_manager将更新后的player对象保存
            self.data_manager.update_player(player)
            # =======================================================================
                
        except Exception as e:
            print(f"更新玩家流失风险状态时出错: {str(e)}")
    
    def _get_player_info(self, player_id: str) -> Optional[Player]:
        """获取玩家信息"""
        # ========================== 修改点 5：使用 data_manager ==========================
        if self.data_manager:
            return self.data_manager.get_player(player_id)
        # =========================================================================
        return None
    
    async def _arun(self, *args, **kwargs):
        """异步运行（暂不实现）"""
        raise NotImplementedError("ChurnRiskAnalysisTool不支持异步运行")