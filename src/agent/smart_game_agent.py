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

from src.tools import (
    GetPlayerStatusTool,
    GetPlayerActionHistoryTool,
    SendInGameMailTool,
    GenerateSoothingMessageTool,
    AnalyzePlayerBehaviorTool
)
from src.tools.emotion_analysis_tool import EmotionAnalysisTool
from src.tools.bot_detection_tool import BotDetectionTool
from src.tools.churn_risk_analysis_tool import ChurnRiskAnalysisTool
from src.llm.llm_client import LLMClient
from src.data.data_manager import DataManager
from .memory_manager import MemoryManager
from src.config.settings import Settings
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
        
        # 初始化LLM客户端
        self.llm_client = None
        if self.llm:
            try:
                self.llm_client = LLMClient(
                    model_name=self.settings.model_name if self.settings.model_provider == "volces" else self.settings.openai_model,
                    api_key=self.settings.model_api_key if self.settings.model_provider == "volces" else self.settings.openai_api_key,
                    base_url=self.settings.model_base_url if self.settings.model_provider == "volces" else None,
                    timeout=self.settings.model_timeout,
                    max_retries=self.settings.model_retry_count,
                    provider=self.settings.model_provider
                )
                self.logger.info("LLM客户端初始化完成")
            except Exception as e:
                self.logger.warning(f"LLM客户端初始化失败: {e}")
                self.llm_client = None
        
        # 初始化记忆管理器
        self.memory_manager = MemoryManager(
            memory_window_size=self.settings.agent_memory_window
        )
        
        # 初始化工具
        print("初始化工具")
        self.tools = self._initialize_tools()
        
        # 初始化Agent
        print("初始化Agent")
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
        
        # 添加新的分析工具（如果LLM客户端可用）
        if self.llm_client:
            try:
                # 情绪分析工具
                emotion_tool = EmotionAnalysisTool(
                    llm_client=self.llm_client,
                    player_manager=getattr(self.data_manager, 'player_manager', None)
                )
                tools.append(emotion_tool)
                
                # 机器人检测工具
                bot_detection_tool = BotDetectionTool(
                    llm_client=self.llm_client,
                    player_manager=getattr(self.data_manager, 'player_manager', None)
                )
                tools.append(bot_detection_tool)
                
                # 流失风险分析工具
                churn_analysis_tool = ChurnRiskAnalysisTool(
                    llm_client=self.llm_client,
                    player_manager=getattr(self.data_manager, 'player_manager', None)
                )
                tools.append(churn_analysis_tool)
                
                self.logger.info("成功添加新的分析工具")
            except Exception as e:
                self.logger.warning(f"添加新分析工具失败: {e}")
        else:
            self.logger.warning("LLM客户端不可用，跳过新分析工具的初始化")
        
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
            # 框架会自动将 "generate_soothing_message, send_reward_tool" 这个字符串填充到提示词中 {tool_names} 的位置。
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
            # 执行新的分析流程
            analysis_results = self._perform_comprehensive_analysis(player_id, trigger_context)
            print("analysis_results:", analysis_results)
            # 检查是否需要基于情绪的干预
            emotion_intervention_needed = self._check_emotion_intervention_needed(player_id, analysis_results)
            print("emotion_intervention_needed:", emotion_intervention_needed)
            # 构建输入问题（包含分析结果）
            input_question = self._build_input_question(player_id, trigger_context, analysis_results)
            print("input_question:", input_question)
            # 获取玩家记忆
            memory = self.memory_manager.get_player_memory(player_id)
            print("memory:", memory)
  
            if self.agent_executor:
                # 使用LLM Agent处理
                print("input_question:", input_question)
                result = self._process_with_llm_agent(player_id, input_question, memory)
                
                # 如果需要情绪干预，添加特殊处理
                if emotion_intervention_needed:
                    result = self._enhance_result_with_emotion_intervention(result, analysis_results)
            else:
                # 使用规则引擎处理
                result = self._process_with_rule_engine(player_id, trigger_context)
                
                # 规则引擎也支持情绪干预
                if emotion_intervention_needed:
                    result = self._add_emotion_intervention_to_rule_result(result, analysis_results)
            
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
    
    def _build_input_question(self, player_id: str, trigger_context: Dict[str, Any], analysis_results: Dict[str, Any] = None) -> str:
        """构建输入问题
        
        Args:
            player_id: 玩家ID
            trigger_context: 触发上下文
            
        Returns:
            str: 格式化的输入问题
        """
        question = f"玩家 {player_id} 触发了干预条件。\n\n"
        question += "触发信息：\n"

        if analysis_results:
            question += "\n预分析结果：\n"
            # 将 analysis_results 格式化为 JSON 字符串，喂给 LLM
            question += json.dumps(analysis_results, ensure_ascii=False, indent=2)
        # 打印trigger_context    打印trigger_context的类型
        

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
        # for key, value in vars(trigger_context).items():
        for key, value in trigger_context.items():
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

    def _process_with_llm_agent(self,player_id,input_question: str, memory) -> Dict[str, Any]:
        """使用LLM Agent处理
        
        Args:
            input_question: 输入问题
            memory: 记忆对象
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            # 获取玩家状态
            player = self.data_manager.get_player(player_id)

            print("player_process_with_llm_agent:", player)
            if not player:
                return {
                    "success": False,
                    "error": "玩家不存在",
                    "method": "rule_engine"
                }
       
            response = self.agent_executor.invoke({
                "input": input_question
                
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
    
    def process_player_action(self, player, action) -> Dict[str, Any]:
        """处理玩家动作并触发分析
        
        Args:
            player: 玩家对象
            action: PlayerAction对象
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            self.data_manager.add_action(action)

            # 构建触发上下文
            trigger_context = {
                "event_id": f"action_{action.action_id}",
                "triggered_at": action.timestamp.isoformat(),
                "triggering_actions": [action],
                "action_type": action.action_type.value,
                "player_action": action
            }
            
            # 调用现有的触发事件处理逻辑
            result = self.process_trigger_event(player.player_id, trigger_context)
            
            # 添加动作相关信息到结果中
            result["action_processed"] = {
                "action_id": action.action_id,
                "action_type": action.action_type.value,
                "timestamp": action.timestamp.isoformat()
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"处理玩家动作时出错: {e}")
            return {
                "success": False,
                "error": str(e),
                "action_id": action.action_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def _perform_comprehensive_analysis(self, player_id: str, trigger_context: Dict[str, Any]) -> Dict[str, Any]:
        """执行综合分析
        
        Args:
            player_id: 玩家ID
            trigger_context: 触发上下文
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        analysis_results = {
            "emotion_analysis": None,
            "bot_detection": None,
            "churn_risk_analysis": None,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        if not self.llm_client:
            self.logger.warning("LLM客户端不可用，跳过综合分析")
            return analysis_results
        
        try:
            # 获取玩家信息
            player = self.data_manager.get_player(player_id)
            if not player:
                self.logger.warning(f"未找到玩家 {player_id}")
                return analysis_results
            
            # 构建行为数据
            print("构建行为数据")
            behavior_data = self._extract_behavior_data(player, trigger_context)
            print("行为数据:", behavior_data)
            # 1. 情绪分析（优先级最高）
            try:
                emotion_tool = EmotionAnalysisTool(
                    llm_client=self.llm_client,
                    player_manager=getattr(self.data_manager, 'player_manager', None)
                )
                emotion_result = emotion_tool._run(
                    player_id=player_id,
                    behavior_data=behavior_data,
                    analysis_depth="standard"
                )
                analysis_results["emotion_analysis"] = json.loads(emotion_result)
                self.logger.info(f"完成玩家 {player_id} 的情绪分析")
            except Exception as e:
                traceback.print_exc()
                self.logger.error(f"情绪分析失败: {e}")
            
            # 2. 机器人检测（如果不是明显的人类玩家）
            try:
                bot_tool = BotDetectionTool(
                    llm_client=self.llm_client,
                    player_manager=getattr(self.data_manager, 'player_manager', None)
                )
                bot_result = bot_tool._run(
                    player_id=player_id,
                    behavior_data=behavior_data,
                    time_window_hours=24
                )
                analysis_results["bot_detection"] = json.loads(bot_result)
                self.logger.info(f"完成玩家 {player_id} 的机器人检测")
            except Exception as e:
                traceback.print_exc()
                self.logger.error(f"机器人检测失败: {e}")
            
            # 3. 流失风险分析
            try:
                churn_tool = ChurnRiskAnalysisTool(
                    llm_client=self.llm_client,
                    player_manager=getattr(self.data_manager, 'player_manager', None)
                )
                churn_result = churn_tool._run(
                    player_id=player_id,
                    behavior_data=behavior_data,
                    time_window_days=30
                )
                analysis_results["churn_risk_analysis"] = json.loads(churn_result)
                self.logger.info(f"完成玩家 {player_id} 的流失风险分析")
            except Exception as e:
                traceback.print_exc()
                self.logger.error(f"流失风险分析失败: {e}")
            
        except Exception as e:
            traceback.print_exc()
            self.logger.error(f"综合分析过程中出错: {e}")
        
        return analysis_results
    
    def _extract_behavior_data(self, player, trigger_context: Dict[str, Any]) -> Dict[str, Any]:
        """提取行为数据
        
        Args:
            player: 玩家对象
            trigger_context: 触发上下文
            
        Returns:
            Dict[str, Any]: 行为数据
        """
        behavior_data = {
            "player_basic_info": {
                "player_id": player.player_id,
                "username": player.username,
                "vip_level": player.vip_level,
                "total_playtime_hours": player.total_playtime_hours,
                "last_login": player.last_login.isoformat() if player.last_login else None,
                "total_spent": player.total_spent,
                "current_status": player.current_status.value,
                "frustration_level": player.frustration_level,
                "consecutive_failures": player.consecutive_failures
            },
            "trigger_info": {
                "event_id": getattr(trigger_context, 'event_id', None),
                "trigger_condition": getattr(trigger_context, 'trigger_condition', {}).name if hasattr(getattr(trigger_context, 'trigger_condition', {}), 'name') else None,
                "triggered_at": getattr(trigger_context, 'triggered_at', None),
                "triggering_actions": getattr(trigger_context, 'triggering_actions', [])
            },
            "recent_activity": {
                "login_frequency": "daily",  # 这里可以从实际数据中获取
                "session_duration": "2-3 hours",
                "task_completion_rate": 0.75,
                "social_interactions": 5,
                "purchase_behavior": "occasional"
            }
        }
        
        return behavior_data
    
    def _check_emotion_intervention_needed(self, player_id: str, analysis_results: Dict[str, Any]) -> bool:
        """检查是否需要基于情绪的干预
        
        Args:
            player_id: 玩家ID
            analysis_results: 分析结果
            
        Returns:
            bool: 是否需要干预
        """
        try:
            emotion_analysis = analysis_results.get("emotion_analysis")
            if not emotion_analysis or not emotion_analysis.get("success"):
                return False
            
            # 检查是否有显著的正面情绪（奖励干预）
            dominant_positive = emotion_analysis.get("dominant_positive_emotions", [])
            positive_intervention = len(dominant_positive) >= 2  # 两个正面情绪触发奖励
            
            # 检查是否有显著的负面情绪（安慰干预）
            dominant_negative = emotion_analysis.get("dominant_negative_emotions", [])
            negative_intervention = len(dominant_negative) >= 2  # 两个负面情绪触发安慰
            
            intervention_needed = positive_intervention or negative_intervention
            
            if intervention_needed:
                intervention_type = "奖励" if positive_intervention else "安慰"
                emotions = dominant_positive if positive_intervention else dominant_negative
                self.logger.info(f"玩家 {player_id} 需要{intervention_type}干预: 情绪{emotions}")
            
            return intervention_needed
            
        except Exception as e:
            self.logger.error(f"检查情绪干预需求时出错: {e}")
            return False
    
    def _enhance_result_with_emotion_intervention(self, result: Dict[str, Any], analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """增强结果，添加情绪干预
        
        Args:
            result: 原始结果
            analysis_results: 分析结果
            
        Returns:
            Dict[str, Any]: 增强后的结果
        """
        try:
            emotion_analysis = analysis_results.get("emotion_analysis", {})
            intervention_type = emotion_analysis.get("intervention_type", "none")
            
            # 添加情绪干预标记
            result["emotion_intervention_applied"] = True
            result["emotion_analysis_summary"] = {
                "dominant_negative_emotions": emotion_analysis.get("dominant_negative_emotions", []),
                "dominant_positive_emotions": emotion_analysis.get("dominant_positive_emotions", []),
                "intervention_type": intervention_type,
                "intervention_suggestions": emotion_analysis.get("intervention_suggestions", [])
            }
            
            # 根据干预类型增强最终答案
            original_answer = result.get("final_answer", "")
            if intervention_type == "reward":
                emotion_enhancement = "\n\n【奖励干预】恭喜您！我们检测到您当前的积极情绪状态，特别为您准备了额外的奖励和惊喜！"
            elif intervention_type == "comfort":
                emotion_enhancement = "\n\n【安慰干预】我们理解您当前可能遇到的困难，已经为您准备了特别的支持和帮助。请不要气馁！"
            else:
                emotion_enhancement = "\n\n【情绪干预】基于情绪分析，我们为您准备了个性化的支持。"
            
            result["final_answer"] = original_answer + emotion_enhancement
            
            return result
            
        except Exception as e:
            self.logger.error(f"增强情绪干预结果时出错: {e}")
            return result
    
    def _add_emotion_intervention_to_rule_result(self, result: Dict[str, Any], analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """为规则引擎结果添加情绪干预
        
        Args:
            result: 规则引擎结果
            analysis_results: 分析结果
            
        Returns:
            Dict[str, Any]: 增强后的结果
        """
        try:
            emotion_analysis = analysis_results.get("emotion_analysis", {})
            intervention_type = emotion_analysis.get("intervention_type", "none")
            
            # 添加情绪干预信息
            result["emotion_intervention_applied"] = True
            result["emotion_context"] = {
                "negative_emotions": emotion_analysis.get("dominant_negative_emotions", []),
                "positive_emotions": emotion_analysis.get("dominant_positive_emotions", []),
                "intervention_type": intervention_type,
                "intervention_reason": f"检测到{intervention_type}干预需求"
            }
            
            # 增强干预计划
            if "intervention_plan" in result:
                plan = result["intervention_plan"]
                if intervention_type == "reward":
                    plan["message_content"] += "\n\n恭喜您的出色表现！我们为您准备了特别的奖励。"
                    plan["rewards"].append("celebration_reward_package:1")
                elif intervention_type == "comfort":
                    plan["message_content"] += "\n\n我们理解您的困难，特别为您准备了额外的关怀和支持。"
                    plan["rewards"].append("comfort_support_package:1")
                else:
                    plan["message_content"] += "\n\n我们注意到您当前的情绪状态，特别为您准备了个性化支持。"
                    plan["rewards"].append("emotion_support_package:1")
            
            return result
            
        except Exception as e:
            self.logger.error(f"为规则引擎结果添加情绪干预时出错: {e}")
            return result
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