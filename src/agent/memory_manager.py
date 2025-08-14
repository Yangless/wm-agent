from typing import Dict, List, Optional, Any
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
import json
from datetime import datetime, timedelta

class MemoryManager:
    """智能体记忆管理器
    
    管理与玩家的对话历史和上下文信息
    """
    
    def __init__(self, memory_window_size: int = 10):
        """初始化记忆管理器
        
        Args:
            memory_window_size: 记忆窗口大小，保留最近N轮对话
        """
        self.memory_window_size = memory_window_size
        self.player_memories: Dict[str, ConversationBufferWindowMemory] = {}
        self.player_contexts: Dict[str, Dict[str, Any]] = {}
        self.last_interaction_time: Dict[str, datetime] = {}
    
    def get_player_memory(self, player_id: str) -> ConversationBufferWindowMemory:
        """获取玩家的记忆对象
        
        Args:
            player_id: 玩家ID
            
        Returns:
            ConversationBufferWindowMemory: 玩家的记忆对象
        """
        if player_id not in self.player_memories:
            self.player_memories[player_id] = ConversationBufferWindowMemory(
                k=self.memory_window_size,
                return_messages=True
            )
        
        return self.player_memories[player_id]
    
    def add_interaction(self, 
                       player_id: str, 
                       human_input: str, 
                       ai_response: str,
                       context: Optional[Dict[str, Any]] = None):
        """添加一次交互记录
        
        Args:
            player_id: 玩家ID
            human_input: 人类输入（触发条件描述）
            ai_response: AI响应
            context: 额外的上下文信息
        """
        memory = self.get_player_memory(player_id)
        
        # 添加到记忆中
        memory.chat_memory.add_user_message(human_input)
        memory.chat_memory.add_ai_message(ai_response)
        
        # 更新上下文
        if context:
            if player_id not in self.player_contexts:
                self.player_contexts[player_id] = {}
            self.player_contexts[player_id].update(context)
        
        # 更新最后交互时间
        self.last_interaction_time[player_id] = datetime.now()
    
    def get_conversation_history(self, player_id: str) -> List[BaseMessage]:
        """获取玩家的对话历史
        
        Args:
            player_id: 玩家ID
            
        Returns:
            List[BaseMessage]: 对话历史消息列表
        """
        memory = self.get_player_memory(player_id)
        return memory.chat_memory.messages
    
    def get_player_context(self, player_id: str) -> Dict[str, Any]:
        """获取玩家的上下文信息
        
        Args:
            player_id: 玩家ID
            
        Returns:
            Dict[str, Any]: 玩家上下文信息
        """
        return self.player_contexts.get(player_id, {})
    
    def update_player_context(self, player_id: str, context: Dict[str, Any]):
        """更新玩家上下文信息
        
        Args:
            player_id: 玩家ID
            context: 要更新的上下文信息
        """
        if player_id not in self.player_contexts:
            self.player_contexts[player_id] = {}
        self.player_contexts[player_id].update(context)
    
    def clear_player_memory(self, player_id: str):
        """清除玩家的记忆
        
        Args:
            player_id: 玩家ID
        """
        if player_id in self.player_memories:
            self.player_memories[player_id].clear()
        if player_id in self.player_contexts:
            del self.player_contexts[player_id]
        if player_id in self.last_interaction_time:
            del self.last_interaction_time[player_id]
    
    def cleanup_old_memories(self, max_age_hours: int = 24):
        """清理过期的记忆
        
        Args:
            max_age_hours: 最大保留时间（小时）
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        expired_players = []
        
        for player_id, last_time in self.last_interaction_time.items():
            if last_time < cutoff_time:
                expired_players.append(player_id)
        
        for player_id in expired_players:
            self.clear_player_memory(player_id)
    
    def get_memory_summary(self, player_id: str) -> str:
        """获取记忆摘要
        
        Args:
            player_id: 玩家ID
            
        Returns:
            str: 记忆摘要
        """
        memory = self.get_player_memory(player_id)
        messages = memory.chat_memory.messages
        context = self.get_player_context(player_id)
        
        if not messages:
            return "无历史交互记录"
        
        summary = f"与玩家 {player_id} 的交互历史：\n"
        summary += f"总交互次数: {len(messages) // 2}\n"
        
        if player_id in self.last_interaction_time:
            last_time = self.last_interaction_time[player_id]
            summary += f"最后交互时间: {last_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if context:
            summary += f"上下文信息: {json.dumps(context, ensure_ascii=False, indent=2)}\n"
        
        # 显示最近的几条消息
        recent_messages = messages[-4:] if len(messages) >= 4 else messages
        summary += "\n最近的对话:\n"
        for i, msg in enumerate(recent_messages):
            role = "用户" if isinstance(msg, HumanMessage) else "AI"
            summary += f"{role}: {msg.content[:100]}...\n"
        
        return summary
    
    def has_recent_interaction(self, player_id: str, hours: int = 1) -> bool:
        """检查是否有最近的交互
        
        Args:
            player_id: 玩家ID
            hours: 时间范围（小时）
            
        Returns:
            bool: 是否有最近交互
        """
        if player_id not in self.last_interaction_time:
            return False
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return self.last_interaction_time[player_id] > cutoff_time
    
    def get_interaction_count(self, player_id: str) -> int:
        """获取交互次数
        
        Args:
            player_id: 玩家ID
            
        Returns:
            int: 交互次数
        """
        memory = self.get_player_memory(player_id)
        return len(memory.chat_memory.messages) // 2
    
    def export_memory_data(self, player_id: str) -> Dict[str, Any]:
        """导出记忆数据
        
        Args:
            player_id: 玩家ID
            
        Returns:
            Dict[str, Any]: 记忆数据
        """
        memory = self.get_player_memory(player_id)
        messages = memory.chat_memory.messages
        context = self.get_player_context(player_id)
        
        return {
            "player_id": player_id,
            "messages": [
                {
                    "type": "human" if isinstance(msg, HumanMessage) else "ai",
                    "content": msg.content,
                    "timestamp": getattr(msg, 'timestamp', None)
                }
                for msg in messages
            ],
            "context": context,
            "last_interaction_time": self.last_interaction_time.get(player_id),
            "interaction_count": len(messages) // 2
        }
    
    def import_memory_data(self, data: Dict[str, Any]):
        """导入记忆数据
        
        Args:
            data: 记忆数据
        """
        player_id = data["player_id"]
        memory = self.get_player_memory(player_id)
        
        # 清除现有记忆
        memory.clear()
        
        # 导入消息
        for msg_data in data["messages"]:
            if msg_data["type"] == "human":
                memory.chat_memory.add_user_message(msg_data["content"])
            else:
                memory.chat_memory.add_ai_message(msg_data["content"])
        
        # 导入上下文
        if "context" in data and data["context"]:
            self.player_contexts[player_id] = data["context"]
        
        # 导入最后交互时间
        if "last_interaction_time" in data and data["last_interaction_time"]:
            self.last_interaction_time[player_id] = data["last_interaction_time"]
    
    def get_all_active_players(self, hours: int = 24) -> List[str]:
        """获取所有活跃玩家ID
        
        Args:
            hours: 活跃时间范围（小时）
            
        Returns:
            List[str]: 活跃玩家ID列表
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        active_players = []
        
        for player_id, last_time in self.last_interaction_time.items():
            if last_time > cutoff_time:
                active_players.append(player_id)
        
        return active_players
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_players = len(self.player_memories)
        total_interactions = sum(
            len(memory.chat_memory.messages) // 2 
            for memory in self.player_memories.values()
        )
        
        active_players_1h = len(self.get_all_active_players(1))
        active_players_24h = len(self.get_all_active_players(24))
        
        return {
            "total_players_with_memory": total_players,
            "total_interactions": total_interactions,
            "active_players_last_1h": active_players_1h,
            "active_players_last_24h": active_players_24h,
            "average_interactions_per_player": total_interactions / total_players if total_players > 0 else 0
        }