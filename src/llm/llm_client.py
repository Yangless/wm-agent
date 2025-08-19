from typing import Dict, List, Optional, Any
import json
import logging
from datetime import datetime

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

try:
    from volcenginesdkarkruntime import Ark
except ImportError:
    Ark = None


class LLMClient:
    """统一的LLM客户端，支持多种模型提供商"""
    
    def __init__(self, 
                 model_name: str,
                 api_key: str,
                 base_url: Optional[str] = None,
                 timeout: int = 30,
                 max_retries: int = 3,
                 provider: str = "openai"):
        """
        初始化LLM客户端
        
        Args:
            model_name: 模型名称
            api_key: API密钥
            base_url: API基础URL（可选）
            timeout: 超时时间
            max_retries: 最大重试次数
            provider: 提供商类型 (openai, volces)
        """
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.provider = provider
        self.logger = logging.getLogger(__name__)
        
        # 初始化客户端
        self._client = self._initialize_client()
    
    def _initialize_client(self):
        """初始化具体的客户端"""
        try:
            if self.provider.lower() == "openai":
                if ChatOpenAI is None:
                    raise ImportError("langchain_openai not installed")
                
                client_kwargs = {
                    "model": self.model_name,
                    "api_key": self.api_key,
                    "timeout": self.timeout,
                    "max_retries": self.max_retries
                }
                
                if self.base_url:
                    client_kwargs["base_url"] = self.base_url
                
                return ChatOpenAI(**client_kwargs)
            
            elif self.provider.lower() == "volces":
                if Ark is None:
                    raise ImportError("volcenginesdkarkruntime not installed")
                
                return Ark(
                    api_key=self.api_key,
                    base_url=self.base_url or "https://ark.cn-beijing.volces.com/api/v3"
                )
            
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.provider} client: {e}")
            return None
    
    def chat_completion(self, 
                       messages: List[Dict[str, str]], 
                       temperature: float = 0.7,
                       max_tokens: Optional[int] = None) -> str:
        """
        执行聊天完成
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            str: 模型响应
        """
        if not self._client:
            raise RuntimeError("LLM client not initialized")
        
        try:
            if self.provider.lower() == "openai":
                # 转换消息格式为langchain格式
                from langchain.schema import HumanMessage, SystemMessage, AIMessage
                
                langchain_messages = []
                for msg in messages:
                    if msg["role"] == "system":
                        langchain_messages.append(SystemMessage(content=msg["content"]))
                    elif msg["role"] == "user":
                        langchain_messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        langchain_messages.append(AIMessage(content=msg["content"]))
                
                # 设置参数
                kwargs = {"temperature": temperature}
                if max_tokens:
                    kwargs["max_tokens"] = max_tokens
                
                # 临时设置参数
                original_temp = getattr(self._client, 'temperature', None)
                original_max_tokens = getattr(self._client, 'max_tokens', None)
                
                self._client.temperature = temperature
                if max_tokens:
                    self._client.max_tokens = max_tokens
                
                try:
                    response = self._client.invoke(langchain_messages)
                    return response.content
                finally:
                    # 恢复原始参数
                    if original_temp is not None:
                        self._client.temperature = original_temp
                    if original_max_tokens is not None:
                        self._client.max_tokens = original_max_tokens
            
            elif self.provider.lower() == "volces":
                # Volces API调用
                response = self._client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens or 1000
                )
                return response.choices[0].message.content
            
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            self.logger.error(f"Chat completion failed: {e}")
            raise
    
    def is_available(self) -> bool:
        """检查客户端是否可用"""
        return self._client is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": self.provider,
            "model_name": self.model_name,
            "available": self.is_available(),
            "base_url": self.base_url
        }