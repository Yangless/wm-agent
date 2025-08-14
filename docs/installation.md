# 安装和配置指南

本指南将帮助您完成智能游戏助手的安装、配置和初始设置。

## 📋 系统要求

### 基础要求
- **操作系统**: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)
- **Python**: 3.8 或更高版本
- **内存**: 最少 4GB RAM (推荐 8GB+)
- **存储**: 至少 1GB 可用空间

### 可选要求
- **OpenAI API Key**: 用于完整的LLM功能
- **Git**: 用于版本控制和代码管理

## 🚀 安装步骤

### 方法一：使用 uv (推荐)

[uv](https://github.com/astral-sh/uv) 是一个快速的Python包管理器，推荐使用。

1. **安装 uv**:
   ```bash
   # Windows (PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **克隆项目**:
   ```bash
   git clone <repository-url>
   cd Agent-demo
   ```

3. **安装依赖**:
   ```bash
   uv sync
   ```

### 方法二：使用传统 pip

1. **克隆项目**:
   ```bash
   git clone <repository-url>
   cd Agent-demo
   ```

2. **创建虚拟环境** (推荐):
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   ```

## ⚙️ 配置设置

### 1. 环境变量配置

复制环境变量模板并进行配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# OpenAI API 配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TEMPERATURE=0.7

# 系统配置
LOG_LEVEL=INFO
DATA_DIR=data
REPORTS_DIR=data/reports

# 数据库配置 (如果使用)
DATABASE_URL=sqlite:///data/game_agent.db

# 缓存配置
CACHE_TTL=3600
CACHE_SIZE=1000
```

### 2. OpenAI API Key 获取

如果您需要完整的LLM功能，请按以下步骤获取API Key：

1. 访问 [OpenAI Platform](https://platform.openai.com/)
2. 注册或登录账户
3. 导航到 "API Keys" 页面
4. 点击 "Create new secret key"
5. 复制生成的API Key到 `.env` 文件中

**注意**: 请妥善保管您的API Key，不要将其提交到版本控制系统中。

### 3. 目录结构初始化

系统会自动创建必要的目录，但您也可以手动创建：

```bash
mkdir -p data/reports
mkdir -p data/cache
mkdir -p logs
```

## 🔧 高级配置

### 自定义设置文件

您可以通过修改 `src/config/settings.py` 来自定义系统行为：

```python
# 智能体配置
AGENT_CONFIG = {
    "max_iterations": 10,        # 最大推理迭代次数
    "memory_window": 100,        # 记忆窗口大小
    "temperature": 0.7,          # LLM温度参数
    "model_name": "gpt-3.5-turbo",  # 使用的模型
    "timeout": 30                # 请求超时时间(秒)
}

# 触发条件配置
DEFAULT_TRIGGERS = [
    {
        "name": "连续失败触发",
        "type": "consecutive_failures",
        "threshold": 3,           # 连续失败次数阈值
        "time_window": 300,       # 时间窗口(秒)
        "cooldown_hours": 1,      # 冷却时间(小时)
        "enabled": True
    },
    {
        "name": "长时间无活动",
        "type": "inactivity",
        "threshold": 1800,        # 无活动时间阈值(秒)
        "cooldown_hours": 2,
        "enabled": True
    },
    {
        "name": "高频失败",
        "type": "high_failure_rate",
        "threshold": 0.8,         # 失败率阈值
        "min_actions": 10,        # 最少行为数量
        "time_window": 600,       # 时间窗口(秒)
        "cooldown_hours": 0.5,
        "enabled": True
    }
]

# 数据管理配置
DATA_CONFIG = {
    "max_players": 10000,        # 最大玩家数量
    "max_actions_per_player": 1000,  # 每个玩家最大行为数量
    "cleanup_interval": 3600,    # 数据清理间隔(秒)
    "backup_interval": 86400     # 数据备份间隔(秒)
}
```

### 日志配置

修改日志级别和输出格式：

```python
# 在 settings.py 中
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "simple": {
            "format": "%(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": "logs/agent.log",
            "formatter": "detailed",
            "level": "INFO"
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": "INFO"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["file", "console"]
    }
}
```

## ✅ 验证安装

### 1. 运行基础测试

```bash
# 使用 uv
uv run python -c "from src.config.settings import Settings; print('配置加载成功')"

# 使用 pip
python -c "from src.config.settings import Settings; print('配置加载成功')"
```

### 2. 运行演示程序

```bash
# 运行完整演示
uv run demo.py

# 或者
python demo.py
```

成功运行后，您应该看到类似以下的输出：

```
=== 智能游戏助手演示 ===
初始化系统...
配置加载完成
数据管理器初始化完成
智能体初始化完成

=== 系统统计 ===
总玩家数: 4
活跃玩家: 2
受挫玩家: 1
高价值玩家: 1
总行为数: 57
总触发数: 0
总邮件数: 0

演示完成！
```

### 3. 检查生成的文件

验证以下文件和目录是否正确创建：

```
Agent-demo/
├── data/
│   ├── players.json
│   ├── actions.json
│   └── reports/
├── logs/
│   └── agent.log
└── demo.log
```

## 🐛 常见问题

### 问题1: ModuleNotFoundError

**错误**: `ModuleNotFoundError: No module named 'src'`

**解决方案**:
```bash
# 确保在项目根目录下运行
cd Agent-demo

# 使用 uv run 或设置 PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

### 问题2: OpenAI API 错误

**错误**: `openai.error.AuthenticationError`

**解决方案**:
1. 检查 `.env` 文件中的 `OPENAI_API_KEY` 是否正确
2. 确认API Key有效且有足够的配额
3. 检查网络连接

### 问题3: 权限错误

**错误**: `PermissionError: [Errno 13] Permission denied`

**解决方案**:
```bash
# 确保有写入权限
chmod -R 755 data/
chmod -R 755 logs/
```

### 问题4: 依赖版本冲突

**解决方案**:
```bash
# 清理并重新安装
uv clean
uv sync

# 或使用 pip
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

## 🔄 更新和维护

### 更新依赖

```bash
# 使用 uv
uv sync --upgrade

# 使用 pip
pip install -r requirements.txt --upgrade
```

### 数据备份

定期备份重要数据：

```bash
# 创建备份
cp -r data/ backup/data_$(date +%Y%m%d)/
cp -r logs/ backup/logs_$(date +%Y%m%d)/
```

### 性能优化

1. **调整缓存大小**: 根据内存情况调整 `CACHE_SIZE`
2. **优化日志级别**: 生产环境建议使用 `WARNING` 或 `ERROR`
3. **定期清理**: 设置自动清理旧数据和日志

## 📞 获取帮助

如果您在安装过程中遇到问题：

1. 查看 [常见问题](#-常见问题) 部分
2. 检查 `logs/agent.log` 中的错误信息
3. 提交 Issue 并包含详细的错误信息
4. 参考项目文档和示例代码

---

安装完成后，您可以继续阅读 [API使用文档](api_usage.md) 了解如何使用系统的各项功能。