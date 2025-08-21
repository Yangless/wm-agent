from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """项目配置设置"""
    
    # 模型配置
    model_provider: str = "volces"  # 模型提供商类型
    model_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    model_name: str = "ep-20250721140404-4bf2t"
    model_api_key: str = "8d8f08ce-ee01-4bcc-9142-ce10e05cf0c5"
    model_retry_count: int = 3
    model_retry_delay: int = 1
    model_timeout: int = 30
    
    # 兼容性配置（保持向后兼容）
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"
    
    # 智能体配置
    agent_max_iterations: int = 10
    agent_memory_window: int = 20
    
    # 游戏数据配置
    data_dir: str = "data"
    player_data_file: str = "data/players.json"
    action_history_file: str = "data/action_history.json"
    
    # 触发条件配置
    failure_threshold: int = 2  # 连续失败次数阈值
    time_window_minutes: int = 5  # 时间窗口（分钟）
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "logs/agent.log"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# 全局配置实例
settings = Settings()