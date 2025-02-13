# 智能体类型定义
AGENT_TYPES = {
    'FUNCTION': 'function',    # 功能智能体
    'SESSION': 'session',      # 会话管理智能体
    'MISSION': 'mission',      # 任务分发智能体
    'CHECKER': 'checker'       # 会话检查智能体
}

# 工作流配置
WORKFLOW_CONFIG = {
    'default_workflow': [
        {
            'agent_type': 'SESSION',
            'required': True,
            'timeout': 5
        },
        {
            'agent_type': 'MISSION',
            'required': True,
            'timeout': 10
        },
        {
            'agent_type': 'FUNCTION',  # 动态路由的实际执行步骤
            'required': True,
            'timeout': 15,
            'dynamic_routing': True
        },
        {
            'agent_type': 'CHECKER',
            'required': False,
            'timeout': 5,
            'is_final': True  # 新增标记表示最终输出
        }
    ]
}

# API配置
API_CONFIG = {
    'default_timeout': 5,
    'max_retries': 3,
    'retry_delay': 1
}