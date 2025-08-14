# 智能游戏助手 (Smart Game Agent)

基于 LangChain 和 ReAct 框架的智能游戏玩家行为分析与干预系统。

## 🎯 项目简介

智能游戏助手是一个先进的AI系统，专门设计用于分析游戏玩家的行为模式，识别潜在的负面情绪（如受挫、愤怒等），并通过智能化的干预措施来改善玩家体验。系统采用ReAct（Reasoning and Acting）智能体架构，能够自主分析、推理并采取相应的行动。

## ✨ 核心功能

### 🔍 智能行为分析
- **实时行为监控**：持续跟踪玩家的游戏行为和操作模式
- **情绪状态识别**：基于行为数据识别玩家的情绪状态
- **风险评估**：评估玩家流失或负面体验的风险等级
- **模式识别**：识别异常行为模式和潜在问题

### 🤖 智能干预系统
- **自动触发机制**：基于预设条件自动触发干预流程
- **个性化消息生成**：使用LLM生成个性化的安慰和鼓励消息
- **游戏内邮件系统**：通过游戏内邮件发送关怀信息
- **多层次干预策略**：从轻度提醒到深度关怀的多级干预

### 📊 数据管理与分析
- **玩家数据管理**：完整的玩家信息和行为历史管理
- **统计分析**：系统运行状态和效果统计
- **报告生成**：详细的分析报告和干预效果评估

## 🏗️ 系统架构

```
智能游戏助手
├── 数据层 (Data Layer)
│   ├── 玩家数据管理 (Player Data Management)
│   ├── 行为历史记录 (Action History)
│   └── 模拟数据生成 (Mock Data Generation)
├── 分析层 (Analysis Layer)
│   ├── 行为分析器 (Behavior Analyzer)
│   ├── 触发引擎 (Trigger Engine)
│   └── 风险评估 (Risk Assessment)
├── 智能体层 (Agent Layer)
│   ├── ReAct智能体 (ReAct Agent)
│   ├── 记忆管理 (Memory Management)
│   └── 工具集成 (Tool Integration)
└── 工具层 (Tools Layer)
    ├── 玩家状态查询 (Player Status Query)
    ├── 行为历史分析 (Action History Analysis)
    ├── 消息生成 (Message Generation)
    └── 邮件发送 (Mail Sending)
```

## 🚀 快速开始

### 环境要求
- Python 3.8+
- OpenAI API Key (可选，用于完整LLM功能)

### 安装依赖

```bash
# 使用 uv (推荐)
uv sync

# 或使用 pip
pip install -r requirements.txt
```

### 配置设置

1. 复制环境变量模板：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，配置必要的参数：
```env
OPENAI_API_KEY=your_openai_api_key_here
LOG_LEVEL=INFO
DATA_DIR=data
```

### 运行演示

```bash
# 运行完整演示
uv run demo.py

# 或运行主程序
uv run main.py
```

## 📖 使用指南

### 基础使用

```python
from src.agent.smart_game_agent import SmartGameAgent
from src.data.data_manager import DataManager
from src.config.settings import Settings

# 初始化系统
settings = Settings()
data_manager = DataManager(settings)
agent = SmartGameAgent(data_manager, settings)

# 分析玩家行为
player_id = "player_123"
analysis_result = agent.analyze_player_behavior(player_id)

# 执行干预
if analysis_result.needs_intervention:
    intervention_result = agent.execute_intervention(player_id, analysis_result)
```

### 自定义场景

```python
from src.scenarios.frustration_scenario import FrustrationScenario

# 创建自定义场景
scenario = FrustrationScenario(data_manager, agent)

# 运行场景测试
result = scenario.run_scenario()
print(f"场景测试结果: {result}")
```

## 🔧 配置说明

### 触发条件配置

系统支持多种触发条件的配置：

```python
# 在 src/config/settings.py 中配置
DEFAULT_TRIGGERS = [
    {
        "name": "连续失败触发",
        "type": "consecutive_failures",
        "threshold": 3,
        "time_window": 300,  # 5分钟
        "enabled": True
    },
    {
        "name": "长时间无活动",
        "type": "inactivity",
        "threshold": 1800,  # 30分钟
        "enabled": True
    }
]
```

### 智能体配置

```python
# 配置智能体参数
AGENT_CONFIG = {
    "max_iterations": 10,
    "memory_window": 100,
    "temperature": 0.7,
    "model_name": "gpt-3.5-turbo"
}
```

## 📊 监控与分析

### 系统统计

```python
# 获取系统统计信息
stats = data_manager.get_statistics()
print(f"总玩家数: {stats['total_players']}")
print(f"活跃玩家: {stats['active_players']}")
print(f"受挫玩家: {stats['frustrated_players']}")
```

### 日志分析

系统会生成详细的日志文件：
- `demo.log` - 主要运行日志
- `data/reports/` - 场景分析报告

## 🛠️ 扩展开发

### 添加新的分析工具

```python
from src.tools.analysis_tools import BaseAnalysisTool

class CustomAnalysisTool(BaseAnalysisTool):
    def analyze(self, player_data):
        # 实现自定义分析逻辑
        return analysis_result
```

### 创建新的触发条件

```python
from src.triggers.trigger_engine import BaseTrigger

class CustomTrigger(BaseTrigger):
    def should_trigger(self, player_data, context):
        # 实现自定义触发逻辑
        return True/False
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [LangChain](https://github.com/langchain-ai/langchain) - 强大的LLM应用开发框架
- [OpenAI](https://openai.com/) - 提供优秀的语言模型API
- [ReAct](https://arxiv.org/abs/2210.03629) - 推理与行动结合的智能体架构

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 发送邮件
- 参与讨论

---

**智能游戏助手** - 让AI为游戏体验保驾护航 🎮✨