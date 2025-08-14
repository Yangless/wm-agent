from typing import List, Dict, Any, Optional
from langchain.tools import BaseTool
from langchain.llms.base import LLM
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from pydantic import BaseModel, Field
import json
import random

class GenerateSoothingMessageInput(BaseModel):
    
    """生成安抚消息工具的输入参数"""
    failure_context: str = Field(description="失败场景的上下文描述")
    player_info: Optional[Dict[str, Any]] = Field(default=None, description="玩家信息（可选）")
    message_tone: str = Field(default="encouraging", description="消息语调：encouraging(鼓励), empathetic(同理心), helpful(帮助性)")


class GenerateSoothingMessageTool(BaseTool):

    
    """生成安抚消息工具
    
    调用LLM生成个性化、有同理心的安抚文案
    """
    
    name: str = "generate_soothing_message"
    description: str = """根据玩家的失败场景和角色信息，生成一段个性化、有同理心的安抚文案。
    输入参数：
    - failure_context: 失败场景的描述
    - player_info: 玩家信息（可选）
    - message_tone: 消息语调（encouraging/empathetic/helpful）
    返回：生成的安抚文本消息"""
    args_schema: type = GenerateSoothingMessageInput
    
    # --- 核心修改点 开始 ---

    # 1. 将 llm 保持为 Pydantic 字段声明。
    #    这样在创建工具实例时，可以通过关键字参数传入，例如：
    #    tool = GenerateSoothingMessageTool(llm=my_llm_instance)
    llm: Optional[LLM] = None   # 设为None，以便在没有LLM时也能工作
    
    # 2. 将 fallback_templates 定义为类属性。
    #    它对于所有实例都是相同的，只在类加载时创建一次，更高效。
    fallback_templates: Dict[str, List[str]] = {
        "encouraging": [
            "不要气馁，{username}！每个强者都经历过挫折，这只是成长路上的一个小插曲。相信你的实力，再试一次吧！",
            "失败是成功之母，{username}！你已经很努力了，稍作调整就能取得胜利。加油！",
            "{username}，真正的勇士不是不会失败，而是能从失败中站起来。你就是这样的勇士！"
        ],
        "empathetic": [
            "我理解你现在的感受，{username}。连续的失败确实让人沮丧，但请记住，你并不孤单。",
            "{username}，我知道这很难受。每个玩家都会遇到这样的时刻，这是游戏的一部分。",
            "感受到你的挫折了，{username}。这种时候确实不好受，但这也说明你很在乎这个游戏。"
        ],
        "helpful": [
            "{username}，让我来帮助你！也许可以尝试调整一下策略，或者先提升一下装备等级？",
            "别担心，{username}！我为你准备了一些资源，希望能帮助你度过这个难关。",
            "{username}，遇到困难时寻求帮助是明智的选择。让我们一起找到解决方案！"
        ]
    }

    # 3. 将 prompt_template 也定义为类属性。
    #    它也是静态的，不需要在每次创建实例时都重新生成。
    prompt_template: PromptTemplate = PromptTemplate(
        input_variables=["failure_context", "player_info", "message_tone"],
        template="""
你是一个游戏中的智能助手，专门帮助遇到困难的玩家。请根据以下信息生成一段温暖、个性化的安抚消息：

失败场景：{failure_context}

玩家信息：{player_info}

消息语调：{message_tone}

要求：
1. 语言要温暖、有同理心
2. 根据玩家的VIP等级和消费情况调整语调
3. 提供具体的建议或鼓励
4. 长度控制在50-100字
5. 使用中文
6. 避免过于正式的语言，要亲切自然

生成的安抚消息：
"""
    )

    
    def _run(self, 
             failure_context: str, 
             player_info: Optional[Dict[str, Any]] = None,
             message_tone: str = "encouraging") -> str:
        """执行工具逻辑"""
        try:
            # 现在 self.llm 是通过Pydantic初始化的可选字段
            if self.llm:
                return self._generate_with_llm(failure_context, player_info, message_tone)
            else:
                return self._generate_fallback_message(failure_context, player_info, message_tone)
                
        except Exception as e:
            return json.dumps({
                "error": f"生成安抚消息时出错: {str(e)}",
                "fallback_message": "亲爱的玩家，遇到困难不要气馁，我们相信你能克服挑战！"
            }, ensure_ascii=False)
    
    def _generate_with_llm(self, 
                          failure_context: str, 
                          player_info: Optional[Dict[str, Any]],
                          message_tone: str) -> str:
        """使用LLM生成消息"""
        try:
            # self.prompt_template 现在是类属性，可以直接访问
            print("self.llm:", self.llm)
            chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
            
            player_info_str = "未提供玩家信息"
            print("player_info:", player_info)
            if  player_info:
                

                player_info_str = f"""玩家ID: {player_info.get('player_id', '未知')}
用户名: {player_info.get('username', '未知')}
VIP等级: {player_info.get('vip_level', 0)}
游戏等级: {player_info.get('level', 1)}
消费金额: {player_info.get('total_spent', 0)}元
当前状态: {player_info.get('current_status', '未知')}
受挫程度: {player_info.get('frustration_level', 0)}/10
连续失败次数: {player_info.get('consecutive_failures', 0)}"""
            
            result = chain.run(
                failure_context=failure_context,
                player_info=player_info_str,
                message_tone=message_tone
            )
            
            return json.dumps({
                "success": True,
                "message": result.strip(),
                "generation_method": "llm",
                "tone": message_tone
            }, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return self._generate_fallback_message(failure_context, player_info, message_tone)
    
    def _generate_fallback_message(self, 
                                  failure_context: str, 
                                  player_info: Optional[Dict[str, Any]],
                                  message_tone: str) -> str:
        """使用预定义模板生成消息"""
        try:
            username = "勇敢的冒险者"
            if player_info and "username" in player_info:
                username = player_info["username"]
            
            # self.fallback_templates 现在是类属性，可以直接访问
            if message_tone not in self.fallback_templates:
                message_tone = "encouraging"
            
            templates = self.fallback_templates[message_tone]
            base_message = random.choice(templates).format(username=username)
            
            personalized_message = self._personalize_message(base_message, player_info, failure_context)
            
            return json.dumps({
                "success": True,
                "message": personalized_message,
                "generation_method": "template",
                "tone": message_tone
            }, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"生成模板消息时出错: {str(e)}",
                "message": "亲爱的玩家，遇到困难不要气馁，我们相信你能克服挑战！"
            }, ensure_ascii=False)
    
    def _personalize_message(self, 
                           base_message: str, 
                           player_info: Optional[Dict[str, Any]],
                           failure_context: str) -> str:
        """个性化消息内容"""
        # (此方法无需改动)
        if not player_info:
            return base_message
        
        vip_level = player_info.get("vip_level", 0)
        if vip_level >= 5:
            base_message += " 作为我们尊贵的VIP会员，我特别为你准备了一些额外的帮助。"
        elif vip_level >= 3:
            base_message += " 感谢你对游戏的支持，让我来为你提供一些帮助。"
        
        consecutive_failures = player_info.get("consecutive_failures", 0)
        if consecutive_failures >= 3:
            base_message += " 我注意到你最近遇到了一些挑战，这里有一些资源可能对你有帮助。"
        
        if "攻城" in failure_context or "attack_city" in failure_context:
            base_message += " 建议先检查一下装备和兵力配置，或者尝试攻打等级稍低的城市来积累经验。"
        elif "PVP" in failure_context or "attack_player" in failure_context:
            base_message += " PVP战斗需要策略，可以先观察对手的阵容，调整自己的战术。"
        
        return base_message
    
    async def _arun(self, 
                    failure_context: str, 
                    player_info: Optional[Dict[str, Any]] = None,
                    message_tone: str = "encouraging") -> str:
        """异步执行"""
        # (此方法无需改动)
        return self._run(failure_context, player_info, message_tone)

# class GenerateSoothingMessageTool(BaseTool):
#     """生成安抚消息工具
    
#     调用LLM生成个性化、有同理心的安抚文案
#     """
    
#     name: str = "generate_soothing_message"
#     description: str = """根据玩家的失败场景和角色信息，生成一段个性化、有同理心的安抚文案。
#     输入参数：
#     - failure_context: 失败场景的描述
#     - player_info: 玩家信息（可选）
#     - message_tone: 消息语调（encouraging/empathetic/helpful）
#     返回：生成的安抚文本消息"""
#     args_schema: type = GenerateSoothingMessageInput
#     llm: Optional[LLM]
#     def __init__(self):
#         super().__init__()
#         self.llm = llm
        
#         # 预定义的安抚消息模板（当没有LLM时使用）
#         self.fallback_templates = {
#             "encouraging": [
#                 "不要气馁，{username}！每个强者都经历过挫折，这只是成长路上的一个小插曲。相信你的实力，再试一次吧！",
#                 "失败是成功之母，{username}！你已经很努力了，稍作调整就能取得胜利。加油！",
#                 "{username}，真正的勇士不是不会失败，而是能从失败中站起来。你就是这样的勇士！"
#             ],
#             "empathetic": [
#                 "我理解你现在的感受，{username}。连续的失败确实让人沮丧，但请记住，你并不孤单。",
#                 "{username}，我知道这很难受。每个玩家都会遇到这样的时刻，这是游戏的一部分。",
#                 "感受到你的挫折了，{username}。这种时候确实不好受，但这也说明你很在乎这个游戏。"
#             ],
#             "helpful": [
#                 "{username}，让我来帮助你！也许可以尝试调整一下策略，或者先提升一下装备等级？",
#                 "别担心，{username}！我为你准备了一些资源，希望能帮助你度过这个难关。",
#                 "{username}，遇到困难时寻求帮助是明智的选择。让我们一起找到解决方案！"
#             ]
#         }
        
#         # LLM提示模板
#         self.prompt_template = PromptTemplate(
#             input_variables=["failure_context", "player_info", "message_tone"],
#             template="""
# 你是一个游戏中的智能助手，专门帮助遇到困难的玩家。请根据以下信息生成一段温暖、个性化的安抚消息：

# 失败场景：{failure_context}

# 玩家信息：{player_info}

# 消息语调：{message_tone}

# 要求：
# 1. 语言要温暖、有同理心
# 2. 根据玩家的VIP等级和消费情况调整语调
# 3. 提供具体的建议或鼓励
# 4. 长度控制在50-100字
# 5. 使用中文
# 6. 避免过于正式的语言，要亲切自然

# 生成的安抚消息：
# """
#         )
    
#     def _run(self, 
#              failure_context: str, 
#              player_info: Optional[Dict[str, Any]] = None,
#              message_tone: str = "encouraging") -> str:
#         """执行工具逻辑"""
#         try:
#             # 如果有LLM，使用LLM生成
#             if self.llm:
#                 return self._generate_with_llm(failure_context, player_info, message_tone)
#             else:
#                 return self._generate_fallback_message(failure_context, player_info, message_tone)
                
#         except Exception as e:
#             return json.dumps({
#                 "error": f"生成安抚消息时出错: {str(e)}",
#                 "fallback_message": "亲爱的玩家，遇到困难不要气馁，我们相信你能克服挑战！"
#             }, ensure_ascii=False)
    
#     def _generate_with_llm(self, 
#                           failure_context: str, 
#                           player_info: Optional[Dict[str, Any]],
#                           message_tone: str) -> str:
#         """使用LLM生成消息"""
#         try:
#             # 创建LLM链
#             chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
            
#             # 准备输入
#             player_info_str = "未提供玩家信息"
#             if player_info:
#                 player_info_str = f"""玩家ID: {player_info.get('player_id', '未知')}
# 用户名: {player_info.get('username', '未知')}
# VIP等级: {player_info.get('vip_level', 0)}
# 游戏等级: {player_info.get('level', 1)}
# 消费金额: {player_info.get('total_spent', 0)}元
# 当前状态: {player_info.get('current_status', '未知')}
# 受挫程度: {player_info.get('frustration_level', 0)}/10
# 连续失败次数: {player_info.get('consecutive_failures', 0)}"""
            
#             # 生成消息
#             result = chain.run(
#                 failure_context=failure_context,
#                 player_info=player_info_str,
#                 message_tone=message_tone
#             )
            
#             return json.dumps({
#                 "success": True,
#                 "message": result.strip(),
#                 "generation_method": "llm",
#                 "tone": message_tone
#             }, ensure_ascii=False, indent=2)
            
#         except Exception as e:
#             # LLM失败时回退到模板
#             return self._generate_fallback_message(failure_context, player_info, message_tone)
    
#     def _generate_fallback_message(self, 
#                                   failure_context: str, 
#                                   player_info: Optional[Dict[str, Any]],
#                                   message_tone: str) -> str:
#         """使用预定义模板生成消息"""
#         try:
#             # 获取玩家用户名
#             username = "勇敢的冒险者"
#             if player_info and "username" in player_info:
#                 username = player_info["username"]
            
#             # 选择合适的语调模板
#             if message_tone not in self.fallback_templates:
#                 message_tone = "encouraging"
            
#             templates = self.fallback_templates[message_tone]
#             base_message = random.choice(templates).format(username=username)
            
#             # 根据玩家信息个性化消息
#             personalized_message = self._personalize_message(base_message, player_info, failure_context)
            
#             return json.dumps({
#                 "success": True,
#                 "message": personalized_message,
#                 "generation_method": "template",
#                 "tone": message_tone
#             }, ensure_ascii=False, indent=2)
            
#         except Exception as e:
#             return json.dumps({
#                 "success": False,
#                 "error": f"生成模板消息时出错: {str(e)}",
#                 "message": "亲爱的玩家，遇到困难不要气馁，我们相信你能克服挑战！"
#             }, ensure_ascii=False)
    
#     def _personalize_message(self, 
#                            base_message: str, 
#                            player_info: Optional[Dict[str, Any]],
#                            failure_context: str) -> str:
#         """个性化消息内容"""
#         if not player_info:
#             return base_message
        
#         # 根据VIP等级调整
#         vip_level = player_info.get("vip_level", 0)
#         if vip_level >= 5:
#             base_message += " 作为我们尊贵的VIP会员，我特别为你准备了一些额外的帮助。"
#         elif vip_level >= 3:
#             base_message += " 感谢你对游戏的支持，让我来为你提供一些帮助。"
        
#         # 根据连续失败次数调整
#         consecutive_failures = player_info.get("consecutive_failures", 0)
#         if consecutive_failures >= 3:
#             base_message += " 我注意到你最近遇到了一些挑战，这里有一些资源可能对你有帮助。"
        
#         # 根据失败场景添加具体建议
#         if "攻城" in failure_context or "attack_city" in failure_context:
#             base_message += " 建议先检查一下装备和兵力配置，或者尝试攻打等级稍低的城市来积累经验。"
#         elif "PVP" in failure_context or "attack_player" in failure_context:
#             base_message += " PVP战斗需要策略，可以先观察对手的阵容，调整自己的战术。"
        
#         return base_message
    
#     async def _arun(self, 
#                     failure_context: str, 
#                     player_info: Optional[Dict[str, Any]] = None,
#                     message_tone: str = "encouraging") -> str:
#         """异步执行"""
#         return self._run(failure_context, player_info, message_tone)




class MockLLM(LLM):
    """模拟LLM，用于测试"""
    
    @property
    def _llm_type(self) -> str:
        return "mock"
    
    def _call(self, prompt: str, stop: Optional[list] = None) -> str:
        """模拟LLM调用"""
        # 简单的基于关键词的响应生成
        if "VIP" in prompt and "高" in prompt:
            return "尊敬的VIP玩家，我理解您现在的困扰。作为我们的重要用户，我特别为您准备了一些珍贵的资源来帮助您度过这个难关。请不要气馁，您的实力我们都看在眼里！"
        elif "连续失败" in prompt:
            return "我知道连续的失败让人沮丧，但这正是成长的机会。每个顶级玩家都经历过这样的时刻。让我为您提供一些实用的建议和资源支持！"
        elif "攻城" in prompt:
            return "攻城确实是游戏中的一大挑战！建议您先提升装备等级，或者调整兵种搭配。我为您准备了一些强化材料，希望能助您一臂之力！"
        else:
            return "亲爱的玩家，遇到困难是成长的必经之路。相信自己，调整策略，胜利就在前方！我已经为您准备了一些帮助，请查收！"