from .base import MockAgentBase, MessageRequest
import uvicorn
from typing import Dict, Any
import asyncio
import os
import logging
import time
import json

logger = logging.getLogger(__name__)

class SessionAgent(MockAgentBase):
    async def process(self, request: MessageRequest):
        """会话管理智能体"""
        self.logger.debug(f"收到会话请求: {request}")

        # 生成多条初始消息
        return {
            "object": "chat.completion",
            "created": int(time.time()),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "system",
                        "content": "会话已创建"
                    },
                    "finish_reason": "stop"
                },
                {
                    "index": 1,
                    "message": {
                        "role": "assistant",
                        "content": "我已经准备好为您服务"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }

class MissionAgent(MockAgentBase):
    async def process(self, request: MessageRequest):
        """任务分发智能体"""
        self.logger.debug(
            f"任务分发请求 | 用户输入: {request.messages[-1].get('content')} "
            f"| 历史对话数: {len(request.messages)}"
        )

        return {
            "object": "chat.completion",
            "created": int(time.time()),
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": json.dumps({
                        "target_agents": ["calculator", "translator"],
                        "priority": ["calculator", "translator"]
                    })
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }

class CalculatorAgent(MockAgentBase):
    async def process(self, request: MessageRequest):
        """计算器智能体"""
        return {
            "object": "chat.completion",
            "created": int(time.time()),
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": json.dumps({
                        "result": "1 + 1 = 2",
                        "confidence": 0.9
                    })
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }

class TranslatorAgent(MockAgentBase):
    async def process(self, request: MessageRequest):
        """翻译智能体"""
        content = request.messages[-1]['content']
        source_text = content.split("'")[1] if "'" in content else content

        translation_result = "Hello" if "你好" in source_text else "Unknown"

        return {
            "object": "chat.completion",
            "created": int(time.time()),
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"翻译结果: {translation_result}"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(source_text),
                "completion_tokens": len(translation_result),
                "total_tokens": len(source_text) + len(translation_result)
            }
        }

class CheckerAgent(MockAgentBase):
    async def process(self, request: MessageRequest):
        """检查智能体"""
        self.logger.debug(
            f"质量检查请求 | 对话轮次: {len(request.messages)} "
            f"| 工作流步骤: {request.current_step}"
        )

        # 生成质量评分和建议
        return {
            "object": "chat.completion",
            "created": int(time.time()),
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": json.dumps({
                        "quality_score": 0.95,
                        "suggestions": ["翻译结果准确", "响应时间符合要求"]
                    })
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 20,
                "total_tokens": 70
            }
        }

def run_agent(agent: MockAgentBase):
    """运行单个智能体服务"""
    uvicorn.run(agent.app, host="127.0.0.1", port=agent.port)

async def start_mock_agents():
    """启动所有模拟智能体"""
    agents = [
        SessionAgent("session", 8001),
        MissionAgent("mission", 8002),
        CalculatorAgent("calculator", 8003),
        TranslatorAgent("translator", 8004),
        CheckerAgent("checker", 8005)
    ]

    servers = []
    for agent in agents:
        config = uvicorn.Config(
            agent.app,
            host="127.0.0.1",
            port=agent.port,
            log_level="warning",
            lifespan="on"
        )
        server = uvicorn.Server(config)
        servers.append(server)
        asyncio.create_task(server.serve())

    # 等待服务启动
    await asyncio.sleep(2)
    return servers

async def stop_mock_agents(servers):
    """停止所有模拟智能体"""
    for server in servers:
        try:
            # 先取消所有后台任务
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            for task in tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            # 关闭服务器
            await server.shutdown()

        except Exception as e:
            logger.error(f"停止服务器时出错: {str(e)}")