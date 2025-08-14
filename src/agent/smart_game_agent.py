from typing import List, Dict, Any, Optional, Union
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool
from langchain.schema import AgentAction, AgentFinish
from langchain_openai import ChatOpenAI
import json
import logging
from datetime import datetime
import traceback

from ..tools import (
    GetPlayerStatusTool,
    GetPlayerActionHistoryTool,
    SendInGameMailTool,
    GenerateSoothingMessageTool,
    AnalyzePlayerBehaviorTool
)
from ..data.data_manager import DataManager
from .memory_manager import MemoryManager
from ..config.settings import Settings
import traceback


class SmartGameAgent:
    """智能游戏AI助手
    
    基于ReAct架构的智能体，能够分析玩家行为并提供个性化干预
    """
    
    def __init__(self, 
                 data_manager: DataManager,
                 settings: Optional[Settings] = None,
                 llm: Optional[ChatOpenAI] = None):
        """初始化智能体
        
        Args:
            data_manager: 数据管理器
            settings: 配置设置
            llm: 语言模型实例
        """
        self.data_manager = data_manager
        self.settings = settings or Settings()
        self.logger = logging.getLogger(__name__)
        
        # 初始化LLM
        if llm:
            self.llm = llm
        else:
            try:
                if self.settings.model_provider == "volces":
                    print("model_provider:",self.settings.model_provider)
                    self.llm = ChatOpenAI(
                        model=self.settings.model_name,
                        base_url=self.settings.model_base_url,
                        api_key=self.settings.model_api_key,
                        temperature=0.7,
                        max_tokens=1000,
                        timeout=self.settings.model_timeout,
                        max_retries=self.settings.model_retry_count
                    )
                    print("LLM 初始化完成")
                else:
                    # 默认使用OpenAI配置
                    self.llm = ChatOpenAI(
                        model=self.settings.openai_model,
                        api_key=self.settings.openai_api_key,
                        temperature=0.7,
                        max_tokens=1000
                    )
                
            except Exception as e:
                self.logger.warning(f"无法初始化LLM ({self.settings.model_provider}): {e}，将使用模拟模式")
                self.llm = None
        
        # 初始化记忆管理器
        self.memory_manager = MemoryManager(
            memory_window_size=self.settings.agent_memory_window
        )
        
        # 初始化工具
        # print("初始化工具")
        self.tools = self._initialize_tools()
        
        # 初始化Agent
        # print("初始化Agent")
        self.agent_executor = self._create_agent_executor()
        
        # 统计信息
        self.intervention_count = 0
        self.success_count = 0
        self.mails_sent = 0
        self.total_response_time = 0.0
        self.start_time = datetime.now()
    
    def _initialize_tools(self) -> List[BaseTool]:
        """初始化工具集
        
        Returns:
            List[BaseTool]: 工具列表
        """
        # print("self.data_manager",self.data_manager)
        soothing_tool = GenerateSoothingMessageTool()
        
        # 2. 将 llm 实例作为属性手动赋值给它
        soothing_tool.llm = self.llm

        tools = [
            GetPlayerStatusTool(data_manager=self.data_manager),
            GetPlayerActionHistoryTool(data_manager=self.data_manager),
            SendInGameMailTool(data_manager=self.data_manager),
            soothing_tool,
            AnalyzePlayerBehaviorTool(data_manager=self.data_manager)
        ]
        
        self.logger.info(f"初始化了 {len(tools)} 个工具")
        return tools
    
    def _create_agent_executor(self) -> Optional[AgentExecutor]:
        """创建Agent执行器
        
        Returns:
            Optional[AgentExecutor]: Agent执行器
        """
        if not self.llm:
            self.logger.warning("没有可用的LLM，Agent将在模拟模式下运行")
            return None
        
        # 定义ReAct提示模板
        from langchain.prompts import PromptTemplate
        react_prompt = PromptTemplate.from_template(
    """
你是一个智能的游戏AI助手，专门负责识别和帮助遇到困难的玩家。

你的核心任务是：
1. 分析玩家的行为模式和情绪状态
2. 识别需要干预的关键时刻
3. 提供个性化的安抚和帮助
4. 发送合适的奖励和建议

你有以下工具可以使用：
{tools}

使用以下格式进行思考和行动：

Question: 需要处理的问题或情况
Thought: 我需要思考如何处理这个情况
Action: 要使用的工具名称，必须是以下工具之一 [{tool_names}]
Action Input: 工具的输入参数（JSON格式）
Observation: 工具执行的结果
... (这个思考/行动/观察的过程可以重复多次)
Thought: 我现在知道最终答案了
Final Answer: 最终的处理结果和建议

重要原则：
- 始终以玩家体验为中心
- 提供有同理心和个性化的帮助
- 根据玩家价值和情况调整干预强度
- 避免过度干预，保持游戏的自然流畅性
- 记录所有重要的交互和决策

开始！

Question: {input}
Thought: {agent_scratchpad}

    """
)
        
        try:
            # 创建ReAct Agent
            tool_names = [tool.__class__.__name__ for tool in self.tools]
            print("tool_names:", tool_names)
            agent = create_react_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=react_prompt
            )
            
            # 创建Agent执行器
            agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                max_iterations=self.settings.agent_max_iterations,
                handle_parsing_errors="Check your output and make sure it conforms to the expected format. Use the exact format: Thought: [your thought]\nAction: [tool name]\nAction Input: [input]\nObservation: [observation]\nThought: [final thought]\nFinal Answer: [answer]",
                return_intermediate_steps=True
            )
            
            self.logger.info("成功创建ReAct Agent执行器")
            return agent_executor
            
        except Exception as e:
            self.logger.error(f"创建Agent执行器失败: {e}")
            error_details = traceback.format_exc()
            print(error_details)
            return None
    
    def process_trigger_event(self, 
                             player_id: str, 
                             trigger_context: Dict[str, Any]) -> Dict[str, Any]:
        """处理触发事件
        
        Args:
            player_id: 玩家ID
            trigger_context: 触发上下文信息
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        self.intervention_count += 1
        start_time = datetime.now()
        
        self.logger.info(f"开始处理玩家 {player_id} 的触发事件")
        import traceback
        try:
            # 构建输入问题
            input_question = self._build_input_question(player_id, trigger_context)
            
            # 获取玩家记忆
            memory = self.memory_manager.get_player_memory(player_id)
            print("memory:", memory)
  
            if self.agent_executor:
                # 使用LLM Agent处理
                print("input_question:", input_question)
                result = self._process_with_llm_agent(input_question, memory)
            else:
                # 使用规则引擎处理
                result = self._process_with_rule_engine(player_id, trigger_context)
            
            # 记录交互
            self.memory_manager.add_interaction(
                player_id=player_id,
                human_input=input_question,
                ai_response=result.get("final_answer", "处理完成"),
                context=trigger_context
            )
            
            # 更新统计
            if result.get("success", False):
                self.success_count += 1
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self.total_response_time += processing_time  # 累加响应时间
            result["processing_time_seconds"] = processing_time
            result["timestamp"] = datetime.now().isoformat()
            
            self.logger.info(f"完成处理玩家 {player_id} 的事件，耗时 {processing_time:.2f} 秒")
            
            return result
            
        except Exception as e:
            self.logger.error(f"处理触发事件时出错: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "player_id": player_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def _build_input_question(self, player_id: str, trigger_context: Dict[str, Any]) -> str:
        """构建输入问题
        
        Args:
            player_id: 玩家ID
            trigger_context: 触发上下文
            
        Returns:
            str: 格式化的输入问题
        """
        question = f"玩家 {player_id} 触发了干预条件。\n\n"
        question += "触发信息：\n"
        # 打印trigger_context    打印trigger_context的类型
        import json

        # 只迭代所需的字段
        required_keys = [
        "player_id",
        "player_status_snapshot",
        "event_id",
        "trigger_condition",
        "triggered_at",
        "triggering_actions"
        ]

        # 遍历 trigger_context 的属性
        for key, value in vars(trigger_context).items():
        # 如果是我们需要的字段
            if key == "player_id":
                question += f"- 玩家ID: {value}\n"
            elif key == "player_status_snapshot":
                question += f"- 玩家等级: {value['level']}\n"
                question += f"- VIP等级: {value['vip_level']}\n"
            elif key == "event_id":
                question += f"- 事件ID: {value}\n"
            elif key == "trigger_condition":
                question += f"- 触发条件: {value.name}\n"
                question += f"- 描述: {value.description}\n"
                question += f"- 最小失败次数: {value.min_failures}\n"
                question += f"- 时间窗口: {value.time_window_minutes}分钟\n"
            elif key == "triggered_at":
                question += f"- 触发时间: {value}\n"
            elif key == "triggering_actions":
                question += "- 行为记录:\n"
                for action in value:
                    question += f"  - 行为ID: {action.action_id}\n"
                    question += f"    行为类型: {action.action_type.value}\n"
                    question += f"    时间: {action.timestamp}\n"
                    question += f"    地点: {action.location}\n"
            else:
                continue  # 忽略其他不需要的数据

        question += "\n请分析这个玩家的情况并提供合适的干预措施。"
        
        return question

    def _process_with_llm_agent(self, input_question: str, memory) -> Dict[str, Any]:
        """使用LLM Agent处理
        
        Args:
            input_question: 输入问题
            memory: 记忆对象
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            # 执行Agent
            response = self.agent_executor.invoke({
                "input": input_question,
                "chat_history": memory.chat_memory.messages
            })
            
            return {
                "success": True,
                "final_answer": response.get("output", ""),
                "intermediate_steps": response.get("intermediate_steps", []),
                "method": "llm_agent"
            }
            
        except Exception as e:
            self.logger.error(f"LLM Agent处理失败: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "method": "llm_agent"
            }
    
    def _process_with_rule_engine(self, player_id: str, trigger_context: Dict[str, Any]) -> Dict[str, Any]:
        """使用规则引擎处理（备用方案）
        
        Args:
            player_id: 玩家ID
            trigger_context: 触发上下文
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        self.logger.info("使用规则引擎处理（LLM不可用）")
        
        try:
            # 获取玩家状态
            player = self.data_manager.get_player(player_id)
            if not player:
                return {
                    "success": False,
                    "error": "玩家不存在",
                    "method": "rule_engine"
                }
            
            # 分析玩家行为
            behavior_analysis = self.data_manager.analyze_player_behavior_pattern(player_id)
            
            # 生成干预措施
            intervention_plan = self._generate_rule_based_intervention(
                player, behavior_analysis, trigger_context
            )
            
            # 执行干预
            execution_result = self._execute_intervention_plan(player_id, intervention_plan)
            
            return {
                "success": True,
                "final_answer": f"基于规则引擎为玩家 {player_id} 执行了干预措施",
                "intervention_plan": intervention_plan,
                "execution_result": execution_result,
                "method": "rule_engine"
            }
            
        except Exception as e:
            self.logger.error(f"规则引擎处理失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "rule_engine"
            }
    
    def _generate_rule_based_intervention(self, 
                                        player, 
                                        behavior_analysis: Dict[str, Any],
                                        trigger_context: Dict[str, Any]) -> Dict[str, Any]:
        """生成基于规则的干预计划
        
        Args:
            player: 玩家对象
            behavior_analysis: 行为分析结果
            trigger_context: 触发上下文
            
        Returns:
            Dict[str, Any]: 干预计划
        """
        plan = {
            "message_type": "soothing",
            "message_content": "",
            "rewards": [],
            "priority": "normal"
        }
        
        # 根据玩家价值调整干预强度
        if player.is_high_value():
            plan["priority"] = "high"
            plan["rewards"].extend(["gold:1000", "gem:50"])
        elif player.vip_level >= 3:
            plan["priority"] = "medium"
            plan["rewards"].extend(["gold:500", "gem:20"])
        else:
            plan["rewards"].extend(["gold:200", "gem:5"])
        
        # 根据行为模式调整消息
        if behavior_analysis["pattern"] == "high_frustration":
            plan["message_content"] = f"亲爱的玩家，我们注意到您最近遇到了一些挑战。请不要气馁，每个强者都会经历挫折。我们为您准备了一些资源来帮助您重新出发！"
        elif behavior_analysis["pattern"] == "seeking_help":
            plan["message_content"] = f"我们看到您在寻求帮助，这很棒！我们为您准备了一些实用的建议和资源。记住，团队合作是成功的关键！"
        else:
            plan["message_content"] = f"感谢您对游戏的热情！我们为您准备了一些小礼物，希望能让您的游戏体验更加愉快。"
        
        # 根据连续失败次数调整
        if player.consecutive_failures >= 3:
            plan["rewards"].append("equipment_enhance_stone:3")
            plan["message_content"] += "\n\n另外，我们为您提供了装备强化石，帮助您提升实力！"
        
        return plan
    
    def _execute_intervention_plan(self, player_id: str, plan: Dict[str, Any]) -> Dict[str, Any]:
        """执行干预计划
        
        Args:
            player_id: 玩家ID
            plan: 干预计划
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            # 发送邮件
            mail_result = self.data_manager.send_mail(
                player_id=player_id,
                title="来自游戏团队的关怀",
                content=plan["message_content"],
                attachments=plan["rewards"]
            )
            
            # 更新邮件发送统计
            self.mails_sent += 1
            
            # 更新玩家状态
            player = self.data_manager.get_player(player_id)
            if player:
                # 重置连续失败计数
                player.reset_failure_count()
                # 降低受挫程度
                player.frustration_level = max(0, player.frustration_level - 2)
                self.data_manager.update_player(player)
            
            return {
                "mail_sent": mail_result,
                "player_status_updated": True,
                "rewards_given": plan["rewards"]
            }
            
        except Exception as e:
            self.logger.error(f"执行干预计划失败: {e}")
            return {
                "mail_sent": False,
                "error": str(e)
            }
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """获取智能体统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        uptime = (datetime.now() - self.start_time).total_seconds()
        memory_stats = self.memory_manager.get_memory_stats()
        average_response_time = self.total_response_time / self.intervention_count if self.intervention_count > 0 else 0.0
        
        return {
            "uptime_seconds": uptime,
            "total_interventions": self.intervention_count,
            "total_events_processed": self.intervention_count,  # 添加demo.py期望的键名
            "successful_interventions": self.success_count,
            "mails_sent": self.mails_sent,  # 添加邮件发送统计
            "average_response_time": average_response_time,  # 添加平均响应时间
            "success_rate": self.success_count / self.intervention_count if self.intervention_count > 0 else 0,
            "llm_available": self.llm is not None,
            "agent_executor_available": self.agent_executor is not None,
            "tools_count": len(self.tools),
            "memory_stats": memory_stats
        }
    
    def cleanup_old_data(self, max_age_hours: int = 24):
        """清理过期数据
        
        Args:
            max_age_hours: 最大保留时间（小时）
        """
        self.memory_manager.cleanup_old_memories(max_age_hours)
        self.logger.info(f"清理了超过 {max_age_hours} 小时的旧数据")
    
    def export_session_data(self) -> Dict[str, Any]:
        """导出会话数据
        
        Returns:
            Dict[str, Any]: 会话数据
        """
        return {
            "agent_stats": self.get_agent_stats(),
            "memory_stats": self.memory_manager.get_memory_stats(),
            "active_players": self.memory_manager.get_all_active_players(),
            "export_timestamp": datetime.now().isoformat()
        }