from typing import Dict, Any
import aiohttp
import asyncio
from ..models.agent import Agent
from ..config import API_CONFIG
from ..utils.logger import logger

class AgentClient:
    def __init__(self):
        self.session = None
        self.config = {
            'default_timeout': 30,
            'max_retries': 3,
            'retry_delay': 1,
            'api_key': 'test-key'  # 添加默认测试key
        }
        self.logger = logger.getChild('AgentClient')

    async def ensure_session(self):
        """确保aiohttp session已创建"""
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def close(self):
        """关闭客户端session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.logger.debug("AgentClient session已关闭")

    async def check_health(self, agent: Agent) -> bool:
        """检查智能体健康状态"""
        await self.ensure_session()
        try:
            async with self.session.get(
                agent.health_endpoint,
                timeout=self.config['default_timeout']
            ) as response:
                return response.status == 200
        except:
            return False

    async def call_service(
        self,
        agent: Agent,
        data: Dict[str, Any],
        timeout: int = None
    ) -> Dict[str, Any]:
        """调用智能体服务"""
        await self.ensure_session()

        self.logger.debug(
            f"请求内容 | 用户: {data.get('message', {}).get('user_id', 'unknown')} "
            f"| 内容摘要: {str(data.get('message', {}).get('content', ''))[:200]}..."
        )
        self.logger.debug(f"完整请求元数据: { {k: v for k, v in data.items() if k != 'message'} }")

        self.logger.debug(
            f"准备调用服务 | 智能体: {agent.name} "
            f"| 端点: {agent.service_endpoint} "
            f"| 超时: {timeout}s"
        )

        if timeout is None:
            timeout = self.config['default_timeout']

        retries = self.config['max_retries']
        while retries > 0:
            try:
                self.logger.debug(f"尝试调用 | 剩余重试次数: {retries}")
                # 添加OpenAI格式头信息
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.config['api_key']}",
                    "OpenAI-Beta": "workflow-v1"
                }

                async with self.session.post(
                    agent.service_endpoint,
                    json=data,
                    headers=headers,
                    timeout=timeout
                ) as response:
                    self.logger.debug(f"收到响应 | 状态码: {response.status}")
                    if response.status == 200:
                        json_response = await response.json()
                        # 验证响应格式
                        if not all(k in json_response for k in ('object', 'choices')):
                            raise ValueError("Invalid OpenAI format response")
                        self.logger.debug(f"成功响应内容: {json_response}")
                        return json_response
                    error_msg = f"服务调用失败，状态码: {response.status}"
                    self.logger.warning(error_msg)
                    raise Exception(error_msg)
            except Exception as e:
                self.logger.debug(f"调用异常: {str(e)}")
                retries -= 1
                if retries == 0:
                    self.logger.error("所有重试次数已用尽")
                    raise
                await asyncio.sleep(self.config['retry_delay'])