import json
from typing import List, Dict, Any
from ..models.message import Message
from ..models.agent import Agent
from ..agent_registry import AgentRegistry
from ..config import WORKFLOW_CONFIG
from .agent_client import AgentClient
from ..utils.exceptions import WorkflowConfigError, AgentCallError
from ..utils.logger import logger  # 新增导入
import asyncio
import uuid

class WorkflowService:
    def __init__(self, agent_registry: AgentRegistry):
        self.agent_registry = agent_registry
        self.agent_client = AgentClient()
        self.workflow_config = WORKFLOW_CONFIG['default_workflow']
        self.logger = logger.getChild('WorkflowService')  # 新增子logger

        # 初始化网络连接
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(self.agent_client.ensure_session())
        else:
            loop.run_until_complete(self.agent_client.ensure_session())

    def _get_response_content(self, response: Dict[str, Any]) -> str:
        """获取响应内容"""
        try:
            return self._get_response_messages(response)['content']
        except Exception as e:
            self.logger.error(f"获取响应内容失败: {response}\n{str(e)}")
            raise e

    def _get_response_messages(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取响应消息"""
        try:
            return response['choices'][0]['message']
        except Exception as e:
            self.logger.error(f"获取响应消息失败: {response}\n{str(e)}")
            raise e

    async def process_message(self, message: Message) -> Dict[str, Any]:
        """处理用户消息"""
        self.logger.debug(f"开始处理消息 | 用户: {message.user_id} | 内容: {message.content}")

        # 构建OpenAI兼容请求格式
        context = {
            'model': "workflow-1.0",
            'messages': [{
                'role': "user",
                'content': message.content
            }],
            'user_id': message.user_id,  # 直接存储用户ID
            'session_id': message.session_id,
            'temperature': 0.7,
            'workflow_data': {},
            'current_step': 0,
        }

        try:
            # 1. 调用会话管理智能体
            self.logger.debug("正在获取SESSION智能体...")
            session_agents = self.agent_registry.get_agents_by_type("SESSION")
            if not session_agents:
                self.logger.error("没有可用的SESSION智能体")
                raise AgentCallError("No available SESSION agent")

            self.logger.debug(f"调用SESSION智能体: {session_agents[0].name}")
            session_result = await self._process_step(session_agents[0], context, timeout=5)
            self.logger.debug(f"SESSION智能体返回结果: {session_result}")
            context['workflow_data']['SESSION'] = session_result
            context['messages'] = session_result.get('choices', []) + context['messages']

            # 2. 获取可用的功能智能体描述
            function_agents = self.agent_registry.get_agents_by_type("FUNCTION")
            agent_descriptions = [
                {
                    'name': agent.name,
                    'type': agent.type,
                    'capabilities': agent.properties.get('capability', '')
                }
                for agent in function_agents
            ]

            # 3. 调用任务分发智能体
            mission_agents = self.agent_registry.get_agents_by_type("MISSION")
            if not mission_agents:
                raise AgentCallError("No available MISSION agent")

            # 准备任务分发上下文
            mission_context = {
                **context,
                "dynamic_prompt": "以下是当前活跃的功能智能体的名称和描述：\n" + "\n".join([f"{agent['name']}: {agent['capabilities']}" for agent in agent_descriptions])
            }
            mission_result = await self._process_step(mission_agents[0], mission_context, timeout=10)
            context['workflow_data']['MISSION'] = mission_result
            try:
                target_agents = json.loads(self._get_response_content(mission_result)).get('target_agents', [])
            except Exception as e:
                self.logger.error(f"任务分发结果解析失败: {mission_result}\n{str(e)}")
                raise e

            # 4. 按顺序调用功能智能体
            function_agents = self.agent_registry.get_agents_by_type("FUNCTION")
            context['workflow_data']['FUNCTION'] = {}  # 改为字典存储结果

            for agent_name in target_agents:
                agent = next((a for a in function_agents if a.name == agent_name), None)
                if not agent:
                    self.logger.error(f"没有找到功能智能体: {agent_name}")
                    continue

                function_result = await self._process_step(agent, context, timeout=15)
                context['workflow_data']['FUNCTION'][agent_name] = function_result  # 按名称存储
                logger.debug("function_result: %s", self._get_response_messages(function_result))
                context['messages'].append(self._get_response_messages(function_result))

            if not target_agents:
                self.logger.error("没有可用的功能智能体")
                context['messages'].append(
                    {
                        "role": "assistant",
                        "content": "没有可用的功能智能体"
                    }
                )

            # 5. 最后调用检查智能体
            checker_agents = self.agent_registry.get_agents_by_type("CHECKER")
            if not checker_agents:
                raise AgentCallError("No available CHECKER agent")

            checker_result = await self._process_step(checker_agents[0], context, timeout=5)

            # 新增CHECKER结果存储
            context['workflow_data']['CHECKER'] = checker_result  # 关键修复点

            # 最终返回结果处理
            final_result = {
                "id": f"chatcmpl-{uuid.uuid4()}",
                **checker_result,  # 包含OpenAI标准字段
                "system": {
                    **context['workflow_data'],
                }
            }
            return final_result

        except Exception as e:
            self.logger.error(f"Workflow error: {str(e)}", exc_info=True)
            raise

    async def _process_step(self, agent: Agent, context: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """处理单个工作流步骤"""
        self.logger.debug(
            f"调用上下文 | 用户: {context.get('user_id', 'unknown')} "
            f"| 当前步骤: {context['current_step']} "
            f"| 工作流数据键: {list(context['workflow_data'].keys())}"
        )
        self.logger.debug(
            f"调用智能体服务 | 名称: {agent.name} "
            f"| 类型: {agent.type} "
            f"| 端点: {agent.service_endpoint}"
        )
        try:
            result = await self.agent_client.call_service(
                agent,
                {
                    "model": context.get('model', 'workflow-1.0'),
                    "dynamic_prompt": context.get('dynamic_prompt', ''),
                    "messages": context['messages'],
                    "user_id": context.get('user_id'),
                    "session_id": context.get('session_id'),
                    "workflow_data": context['workflow_data'],
                    "current_step": context['current_step']
                },
                timeout=timeout
            )
            self.logger.debug(f"智能体调用成功 | 名称: {agent.name} | 响应: {result}")
            return result
        except Exception as e:
            self.logger.error(
                f"智能体调用失败 | 名称: {agent.name} "
                f"| 错误: {str(e)}",
                exc_info=True
            )
            raise

    async def close(self):
        """关闭所有网络资源"""
        await self.agent_client.close()