# API 使用文档

本文档详细介绍智能游戏助手的核心API和组件使用方法。

## 📚 目录

- [核心组件](#核心组件)
- [数据管理](#数据管理)
- [智能体使用](#智能体使用)
- [工具集成](#工具集成)
- [触发系统](#触发系统)
- [场景测试](#场景测试)
- [扩展开发](#扩展开发)

## 🏗️ 核心组件

### Settings 配置管理

```python
from src.config.settings import Settings

# 初始化配置
settings = Settings()

# 访问配置项
print(f"数据目录: {settings.data_dir}")
print(f"日志级别: {settings.log_level}")
print(f"OpenAI模型: {settings.openai_model}")

# 获取智能体配置
agent_config = settings.get_agent_config()
print(f"最大迭代次数: {agent_config['max_iterations']}")

# 获取触发条件
triggers = settings.get_default_triggers()
for trigger in triggers:
    print(f"触发器: {trigger['name']}, 启用: {trigger['enabled']}")
```

### DataManager 数据管理

```python
from src.data.data_manager import DataManager
from src.config.settings import Settings

# 初始化数据管理器
settings = Settings()
data_manager = DataManager(settings)

# 玩家管理
player_data = {
    "player_id": "player_123",
    "username": "TestPlayer",
    "level": 10,
    "vip_level": 2,
    "last_login": "2024-01-15T10:30:00",
    "total_playtime": 3600,
    "is_active": True
}

# 添加/更新玩家
data_manager.update_player(player_data)

# 获取玩家信息
player = data_manager.get_player("player_123")
print(f"玩家: {player.username}, 等级: {player.level}")

# 获取所有玩家
all_players = data_manager.get_all_players()
print(f"总玩家数: {len(all_players)}")

# 行为管理
action_data = {
    "action_id": "action_001",
    "player_id": "player_123",
    "action_type": "battle",
    "result": "failure",
    "timestamp": "2024-01-15T10:35:00",
    "details": {"enemy_level": 15, "damage_dealt": 100}
}

# 添加行为记录
data_manager.add_action(action_data)

# 获取玩家行为历史
actions = data_manager.get_player_actions("player_123")
print(f"玩家行为数: {len(actions)}")

# 获取最近行为
recent_actions = data_manager.get_recent_actions("player_123", hours=1)
print(f"最近1小时行为数: {len(recent_actions)}")

# 系统统计
stats = data_manager.get_statistics()
print(f"系统统计: {stats}")
```

## 🤖 智能体使用

### SmartGameAgent 基础使用

```python
from src.agent.smart_game_agent import SmartGameAgent
from src.data.data_manager import DataManager
from src.config.settings import Settings

# 初始化
settings = Settings()
data_manager = DataManager(settings)
agent = SmartGameAgent(data_manager, settings)

# 分析玩家行为
player_id = "player_123"
analysis_result = agent.analyze_player_behavior(player_id)

print(f"分析结果:")
print(f"  需要干预: {analysis_result.needs_intervention}")
print(f"  风险等级: {analysis_result.risk_level}")
print(f"  建议行动: {analysis_result.recommended_actions}")

# 执行干预
if analysis_result.needs_intervention:
    intervention_result = agent.execute_intervention(player_id, analysis_result)
    print(f"干预结果: {intervention_result}")

# 生成安慰消息
context = {
    "player_name": "TestPlayer",
    "recent_failures": 3,
    "player_level": 10
}

message = agent.generate_soothing_message(context)
print(f"生成的消息: {message}")
```

### 高级智能体功能

```python
# 批量分析多个玩家
player_ids = ["player_123", "player_456", "player_789"]
results = agent.batch_analyze_players(player_ids)

for player_id, result in results.items():
    print(f"玩家 {player_id}: 风险等级 {result.risk_level}")

# 设置自定义分析参数
custom_params = {
    "failure_threshold": 5,
    "time_window": 600,  # 10分钟
    "risk_factors": ["consecutive_failures", "inactivity", "negative_feedback"]
}

result = agent.analyze_player_behavior(player_id, custom_params)

# 获取智能体状态
status = agent.get_status()
print(f"智能体状态: {status}")
```

## 🛠️ 工具集成

### 玩家工具 (Player Tools)

```python
from src.tools.player_tools import get_player_status, get_player_action_history

# 获取玩家状态
status_result = get_player_status.run({
    "player_id": "player_123",
    "include_recent_actions": True,
    "time_window_hours": 24
})

print(f"玩家状态: {status_result}")

# 获取行为历史
history_result = get_player_action_history.run({
    "player_id": "player_123",
    "limit": 50,
    "action_types": ["battle", "purchase", "social"]
})

print(f"行为历史: {history_result}")
```

### 消息工具 (Message Tools)

```python
from src.tools.message_tools import generate_soothing_message, send_in_game_mail

# 生成安慰消息
message_result = generate_soothing_message.run({
    "player_context": {
        "name": "TestPlayer",
        "level": 10,
        "recent_failures": 3,
        "preferred_language": "zh-CN"
    },
    "message_type": "encouragement",
    "tone": "friendly"
})

print(f"生成的消息: {message_result}")

# 发送游戏内邮件
mail_result = send_in_game_mail.run({
    "player_id": "player_123",
    "subject": "特别关怀",
    "content": "亲爱的玩家，我们注意到您最近遇到了一些挑战...",
    "attachments": [
        {"type": "item", "id": "health_potion", "quantity": 5},
        {"type": "currency", "id": "gold", "quantity": 1000}
    ]
})

print(f"邮件发送结果: {mail_result}")
```

### 分析工具 (Analysis Tools)

```python
from src.tools.analysis_tools import analyze_player_behavior, calculate_risk_score

# 分析玩家行为
analysis_result = analyze_player_behavior.run({
    "player_id": "player_123",
    "analysis_type": "comprehensive",
    "time_range": {
        "start": "2024-01-15T00:00:00",
        "end": "2024-01-15T23:59:59"
    }
})

print(f"行为分析: {analysis_result}")

# 计算风险评分
risk_result = calculate_risk_score.run({
    "player_id": "player_123",
    "factors": ["failure_rate", "session_length", "spending_pattern"],
    "weights": {"failure_rate": 0.4, "session_length": 0.3, "spending_pattern": 0.3}
})

print(f"风险评分: {risk_result}")
```

## ⚡ 触发系统

### TriggerEngine 使用

```python
from src.triggers.trigger_engine import TriggerEngine
from src.triggers.behavior_analyzer import BehaviorAnalyzer

# 初始化触发引擎
trigger_engine = TriggerEngine(data_manager, settings)
behavior_analyzer = BehaviorAnalyzer(data_manager)

# 启动引擎
trigger_engine.start()

# 注册自定义处理器
def custom_intervention_handler(player_id, trigger_type, context):
    print(f"自定义干预: 玩家 {player_id}, 触发类型 {trigger_type}")
    # 实现自定义干预逻辑
    return {"status": "handled", "action": "custom_intervention"}

trigger_engine.register_handler("consecutive_failures", custom_intervention_handler)

# 手动检查触发条件
player_id = "player_123"
trigger_result = trigger_engine.check_triggers(player_id)

if trigger_result:
    print(f"触发结果: {trigger_result}")

# 获取引擎状态
engine_status = trigger_engine.get_status()
print(f"引擎状态: {engine_status}")

# 停止引擎
trigger_engine.stop()
```

### BehaviorAnalyzer 使用

```python
# 分析玩家行为模式
patterns = behavior_analyzer.analyze_patterns("player_123")
print(f"行为模式: {patterns}")

# 检测异常行为
anomalies = behavior_analyzer.detect_anomalies("player_123")
print(f"异常行为: {anomalies}")

# 计算受挫指标
frustration_score = behavior_analyzer.calculate_frustration_score("player_123")
print(f"受挫评分: {frustration_score}")

# 预测玩家流失风险
churn_risk = behavior_analyzer.predict_churn_risk("player_123")
print(f"流失风险: {churn_risk}")
```

## 🎭 场景测试

### FrustrationScenario 使用

```python
from src.scenarios.frustration_scenario import FrustrationScenario

# 创建场景实例
scenario = FrustrationScenario(data_manager, agent)

# 运行完整场景
result = scenario.run_scenario()
print(f"场景测试结果: {result}")

# 运行快速测试
quick_result = scenario.run_quick_test()
print(f"快速测试结果: {quick_result}")

# 生成场景报告
report = scenario.generate_report()
print(f"场景报告: {report}")

# 自定义场景参数
custom_params = {
    "player_count": 5,
    "failure_count": 4,
    "time_span": 300,  # 5分钟
    "intervention_enabled": True
}

custom_result = scenario.run_scenario(custom_params)
print(f"自定义场景结果: {custom_result}")
```

### 创建自定义场景

```python
from src.scenarios.base_scenario import BaseScenario

class CustomScenario(BaseScenario):
    def __init__(self, data_manager, agent):
        super().__init__(data_manager, agent)
        self.scenario_name = "自定义场景"
    
    def setup_scenario(self):
        """设置场景初始状态"""
        # 创建测试玩家
        self.test_player = self.data_generator.generate_player(
            player_id="custom_test_player",
            username="CustomTestPlayer",
            player_type="normal"
        )
        
        # 添加到数据管理器
        self.data_manager.update_player(self.test_player)
        
        return True
    
    def execute_scenario(self):
        """执行场景逻辑"""
        player_id = self.test_player["player_id"]
        
        # 生成特定行为序列
        actions = self.data_generator.generate_action_sequence(
            player_id=player_id,
            sequence_type="custom",
            count=10
        )
        
        # 添加行为到数据管理器
        for action in actions:
            self.data_manager.add_action(action)
        
        # 触发分析
        analysis_result = self.agent.analyze_player_behavior(player_id)
        
        return {
            "player_id": player_id,
            "actions_generated": len(actions),
            "analysis_result": analysis_result,
            "success": True
        }
    
    def cleanup_scenario(self):
        """清理场景数据"""
        # 清理测试数据
        pass

# 使用自定义场景
custom_scenario = CustomScenario(data_manager, agent)
result = custom_scenario.run_scenario()
print(f"自定义场景结果: {result}")
```

## 🔧 扩展开发

### 创建自定义工具

```python
from langchain.tools import BaseTool
from typing import Optional, Type
from pydantic import BaseModel, Field

class CustomToolInput(BaseModel):
    player_id: str = Field(description="玩家ID")
    custom_param: str = Field(description="自定义参数")

class CustomTool(BaseTool):
    name = "custom_tool"
    description = "自定义工具的描述"
    args_schema: Type[BaseModel] = CustomToolInput
    
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
    
    def _run(self, player_id: str, custom_param: str) -> str:
        """执行工具逻辑"""
        # 实现自定义逻辑
        player = self.data_manager.get_player(player_id)
        if not player:
            return f"玩家 {player_id} 不存在"
        
        # 自定义处理逻辑
        result = f"处理玩家 {player.username} 的自定义参数 {custom_param}"
        return result
    
    async def _arun(self, player_id: str, custom_param: str) -> str:
        """异步执行"""
        return self._run(player_id, custom_param)

# 使用自定义工具
custom_tool = CustomTool(data_manager)
result = custom_tool.run({"player_id": "player_123", "custom_param": "test"})
print(f"自定义工具结果: {result}")
```

### 扩展触发条件

```python
from src.triggers.base_trigger import BaseTrigger

class CustomTrigger(BaseTrigger):
    def __init__(self, config):
        super().__init__(config)
        self.trigger_type = "custom_trigger"
    
    def should_trigger(self, player_data, context):
        """判断是否应该触发"""
        # 实现自定义触发逻辑
        player_id = player_data.get("player_id")
        
        # 获取玩家最近行为
        recent_actions = context.get("recent_actions", [])
        
        # 自定义判断条件
        if len(recent_actions) > 10:
            failure_count = sum(1 for action in recent_actions 
                              if action.get("result") == "failure")
            
            if failure_count >= self.config.get("threshold", 5):
                return True
        
        return False
    
    def get_intervention_context(self, player_data, context):
        """获取干预上下文"""
        return {
            "trigger_type": self.trigger_type,
            "player_id": player_data.get("player_id"),
            "custom_data": "自定义干预数据"
        }

# 注册自定义触发器
custom_trigger_config = {
    "name": "自定义触发器",
    "threshold": 5,
    "enabled": True
}

custom_trigger = CustomTrigger(custom_trigger_config)
trigger_engine.register_trigger(custom_trigger)
```

## 📊 监控和调试

### 性能监控

```python
import time
from functools import wraps

def monitor_performance(func):
    """性能监控装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        print(f"{func.__name__} 执行时间: {end_time - start_time:.2f}秒")
        return result
    return wrapper

# 使用监控装饰器
@monitor_performance
def analyze_large_dataset():
    # 分析大量数据
    pass
```

### 调试工具

```python
# 启用详细日志
import logging
logging.getLogger().setLevel(logging.DEBUG)

# 获取系统状态
def get_system_status():
    return {
        "data_manager": data_manager.get_statistics(),
        "trigger_engine": trigger_engine.get_status(),
        "agent": agent.get_status()
    }

status = get_system_status()
print(f"系统状态: {status}")

# 导出调试数据
def export_debug_data(player_id):
    debug_data = {
        "player": data_manager.get_player(player_id),
        "actions": data_manager.get_player_actions(player_id),
        "analysis": agent.analyze_player_behavior(player_id)
    }
    
    import json
    with open(f"debug_{player_id}.json", "w", encoding="utf-8") as f:
        json.dump(debug_data, f, ensure_ascii=False, indent=2)

export_debug_data("player_123")
```

## 🚀 最佳实践

### 1. 错误处理

```python
try:
    result = agent.analyze_player_behavior(player_id)
except Exception as e:
    logger.error(f"分析玩家行为失败: {e}")
    # 实现降级策略
    result = default_analysis_result
```

### 2. 资源管理

```python
# 使用上下文管理器
with data_manager.transaction():
    # 批量操作
    for player_data in batch_data:
        data_manager.update_player(player_data)
```

### 3. 配置管理

```python
# 使用环境特定配置
if settings.environment == "production":
    # 生产环境配置
    agent_config["temperature"] = 0.3
else:
    # 开发环境配置
    agent_config["temperature"] = 0.7
```

---

更多详细信息请参考源代码注释和示例。如有问题，请查看 [故障排除指南](troubleshooting.md) 或提交Issue。