# 工作流管理系统

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

智能体协同工作流管理系统，支持多类型智能体的动态注册、服务调用和质量检查。

## 功能特性

- 🚀 多类型智能体支持（SESSION/MISSION/FUNCTION/CHECKER）
- ⚡ 异步工作流引擎（基于asyncio）
- 🔧 动态服务路由与负载均衡
- 📊 OpenAI兼容的接口规范
- 🛡️ 智能体健康检查与自动重试机制
- 📝 详尽的日志记录与轮转策略

## 核心模块

```bash
.
├── workflow_manager/
│   ├── services/
│   │   ├── workflow.py    # 工作流引擎
│   │   └── agent_client.py # 智能体调用客户端
│   ├── models/
│   │   ├── message.py     # 消息模型
│   │   └── agent.py       # 智能体模型
│   ├── agent_registry.py  # 智能体注册中心
│   └── utils/
│       ├── logger.py      # 日志系统
│       └── exceptions.py  # 异常处理
├── tests/
│   └── mock_agents/       # 模拟智能体实现
└── requirements-test.txt  # 测试依赖
```

## 快速开始

### 容器化部署

```bash
# 1. 克隆仓库
git clone https://github.com/your-org/workflow-system.git
cd workflow-system

# 2. 创建环境文件
cp .env.example .env  # 按需修改配置

# 3. 构建并启动服务
docker-compose up -d --build

# 4. 查看运行状态
docker-compose ps

# 5. 跟踪日志
docker-compose logs -f workflow
```

### API调用示例

```bash
# 发送处理请求
curl -X POST http://localhost:5000/message \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "api_user_001",
    "content": "请将'你好世界'翻译成英文",
    "session_id": "session_123"
  }'
```

预期响应格式

```json
{
  "status": "success",
  "data": {
    "id": "chatcmpl-9a7b3c2d1e",
    "choices": [...],
    "system": {
      "SESSION": {...},
      "MISSION": {...},
      "FUNCTION": {
        "translator": {
          "translation": "Hello World"
        }
      }
    },
    "CHECKER": {
      "quality_score": 0.95
    }
  }
}
```

## API接口规范

### 1. 消息处理接口

```http
POST /message
Content-Type: application/json
{
    "user_id": "string",
    "content": "string",
    "session_id": "string | null"
}
```

**功能**：处理用户消息并返回工作流执行结果
**请求字段**：
- `user_id`：用户唯一标识（必填）
- `content`：消息内容（必填）
- `session_id`：会话ID（可选）

**成功响应**：

```json
{
  "status": "success",
  "data": {
    "id": "请求ID",
    "choices": [{
      "role": "assistant",
      "content": "响应内容"
    }],
  },
  "system": {
    "SESSION": "会话管理结果",
    "MISSION": "任务分发结果",
    "FUNCTION": {
      "智能体名称": "功能处理结果"
    },
    "CHECKER": "质量检查结果"
  }
}

```

### 2. 智能体注册接口

```http
POST /agent/register
Content-Type: application/json
{
    "name": "string",
    "type": "SESSION|MISSION|FUNCTION|CHECKER",
    "endpoints": {
        "health": "http://...",
        "service": "http://..."
    },
    "properties": {}
}
```

**功能**：注册新的智能体服务
**请求字段**：
- `name`：智能体唯一名称（必填）
- `type`：智能体类型（必填）
- `endpoints`：服务端点（必填）
- `properties`：扩展属性（可选）

**成功响应**：

```json
{
    "status": "success",
    "message": "Agent registered successfully"
}
```

### 3. 智能体注销接口

```http
POST /agent/unregister
Content-Type: application/json
{
    "name": "string"
}
```

**功能**：注销已注册的智能体
**请求字段**：
- `name`：要注销的智能体名称（必填）

**成功响应**：

```json
{
    "status": "success",
    "message": "Agent unregistered successfully"
}
```

### 错误响应格式

```json
{
    "status": "error",
    "message": "错误描述信息",
    "error_type": "AgentCallError|ValidationError|..."
}
```

## 开发测试

```bash
# 运行完整测试套件
pytest tests/ -v --log-cli-level=DEBUG

# 运行单个测试用例
pytest tests/test_workflow.py::test_workflow_basic -v
```

## 配置说明

通过环境变量定制系统行为：

```ini
LOG_LEVEL=DEBUG          # 日志级别
LOG_FILE_SIZE=100M      # 单个日志文件大小
LOG_BACKUP_COUNT=10     # 最大备份文件数
API_TIMEOUT=5           # 默认接口超时
```

## 文档资源

- [github/private-agent/docs](https://github.com/private-agent/docs)

## 贡献指南

欢迎通过Issue和PR参与贡献，请遵循以下规范：
1. 新功能开发请创建特性分支
2. 提交前运行完整测试套件
3. 更新相关文档
4. 保持代码风格统一

## 许可协议

本项目采用 [MIT License](LICENSE)