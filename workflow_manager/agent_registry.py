from typing import Dict, List
from .models.agent import Agent
from .utils.exceptions import AgentNotFoundError, AgentAlreadyExistsError

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, Agent] = {}

    def register(self, agent: Agent) -> None:
        """注册新的智能体"""
        if agent.name in self._agents:
            raise AgentAlreadyExistsError(f"Agent {agent.name} already exists")
        self._agents[agent.name] = agent

    def unregister(self, agent_name: str) -> None:
        """注销智能体"""
        if agent_name not in self._agents:
            raise AgentNotFoundError(f"Agent {agent_name} not found")
        del self._agents[agent_name]

    def get_agent(self, agent_name: str) -> Agent:
        """获取指定智能体"""
        if agent_name not in self._agents:
            raise AgentNotFoundError(f"Agent {agent_name} not found")
        return self._agents[agent_name]

    def get_agents_by_type(self, agent_type: str) -> List[Agent]:
        """获取指定类型的所有智能体"""
        return [agent for agent in self._agents.values() if agent.type == agent_type]

    def get_all_agents(self) -> List[Agent]:
        """获取所有注册的智能体"""
        return list(self._agents.values())