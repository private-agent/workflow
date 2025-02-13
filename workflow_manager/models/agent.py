from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class Agent:
    name: str                   # 智能体名称
    type: str                   # 智能体类型
    endpoints: Dict[str, str]   # 智能体接口地址
    properties: Dict[str, Any]  # 智能体属性

    def __post_init__(self):
        # 验证必需的endpoints
        required_endpoints = {'health', 'service'}
        if not all(ep in self.endpoints for ep in required_endpoints):
            raise ValueError(f"Agent must have {required_endpoints} endpoints")

    @property
    def health_endpoint(self) -> str:
        """健康检查接口"""
        return self.endpoints['health']

    @property
    def service_endpoint(self) -> str:
        """服务接口"""
        return self.endpoints['service']

    def is_function_agent(self) -> bool:
        """判断是否为功能智能体"""
        return self.type == 'function'