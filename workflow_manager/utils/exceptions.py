class WorkflowException(Exception):
    """工作流基础异常类"""
    pass

class AgentNotFoundError(WorkflowException):
    """找不到智能体异常"""
    pass

class AgentAlreadyExistsError(WorkflowException):
    """智能体已存在异常"""
    pass

class AgentCallError(WorkflowException):
    """智能体调用异常"""
    pass

class WorkflowConfigError(WorkflowException):
    """工作流配置错误"""
    pass