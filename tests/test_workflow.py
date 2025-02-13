import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import asyncio
from workflow_manager.models.message import Message
from workflow_manager.models.agent import Agent
from workflow_manager.agent_registry import AgentRegistry
from workflow_manager.services.workflow import WorkflowService
from .mock_agents.agents import start_mock_agents, stop_mock_agents
import pytest_asyncio
from workflow_manager.utils.exceptions import AgentCallError
from workflow_manager.utils.logger import logger  # 新增导入
import json

@pytest.fixture
async def mock_environment():
    """设置测试环境"""
    logger.info("初始化测试环境...")
    servers = []
    workflow = None
    try:
        logger.debug("启动模拟智能体服务...")
        servers = await start_mock_agents()

        # 创建注册表
        registry = AgentRegistry()

        # 注册智能体
        registry.register(Agent(
            name="session",
            type="SESSION",
            endpoints={
                "health": "http://127.0.0.1:8001/health",
                "service": "http://127.0.0.1:8001/service"
            },
            properties={}
        ))

        registry.register(Agent(
            name="mission",
            type="MISSION",
            endpoints={
                "health": "http://127.0.0.1:8002/health",
                "service": "http://127.0.0.1:8002/service"
            },
            properties={}
        ))

        registry.register(Agent(
            name="calculator",
            type="FUNCTION",
            endpoints={
                "health": "http://127.0.0.1:8003/health",
                "service": "http://127.0.0.1:8003/service"
            },
            properties={"capability": "math"}
        ))

        registry.register(Agent(
            name="translator",
            type="FUNCTION",
            endpoints={
                "health": "http://127.0.0.1:8004/health",
                "service": "http://127.0.0.1:8004/service"
            },
            properties={"capability": "translation"}
        ))

        registry.register(Agent(
            name="checker",
            type="CHECKER",
            endpoints={
                "health": "http://127.0.0.1:8005/health",
                "service": "http://127.0.0.1:8005/service"
            },
            properties={}
        ))

        yield registry
    finally:
        logger.info("开始清理测试环境...")
        # 添加关闭顺序
        if workflow:
            await workflow.agent_client.close()
            await workflow.close()

        # 关闭所有模拟服务器
        if servers:
            await stop_mock_agents(servers)

        # 强制清理aiohttp连接
        await asyncio.sleep(0.5)
        if workflow and workflow.agent_client.session:
            await workflow.agent_client.session.close()

@pytest.mark.asyncio
async def test_workflow_basic(mock_environment):
    """测试基本工作流程"""
    registry = mock_environment
    workflow = WorkflowService(registry)
    try:
        message = Message(
            user_id="test_user",
            content="我今天买了3个苹果，帮我记录一下",
            session_id=None
        )

        result = await workflow.process_message(message)

        # 验证结果
        assert "id" in result
        assert "system" in result
        assert "SESSION" in result["system"]
        assert "MISSION" in result["system"]
        assert "CHECKER" in result["system"]
        assert result["system"]["CHECKER"].get('choices') is not None
        assert len(result["system"]["CHECKER"]["choices"]) > 0

    finally:
        await workflow.close()

@pytest.mark.asyncio
async def test_workflow_error_handling(mock_environment):
    """测试错误处理"""
    registry = mock_environment
    workflow = WorkflowService(registry)
    try:
        # 注销一个必需的智能体
        registry.unregister("session")

        message = Message(
            user_id="test_user",
            content="测试消息",
            session_id=None
        )

        with pytest.raises(AgentCallError):
            await workflow.process_message(message)

    finally:
        await workflow.close()

@pytest.mark.asyncio
async def test_dynamic_routing(mock_environment):
    """测试动态路由"""
    registry = mock_environment
    workflow = WorkflowService(registry)
    try:
        message = Message(
            user_id="test_user",
            content="请将'你好'翻译成英语",
            session_id=None
        )

        result = await workflow.process_message(message)

        # 验证检查智能体的输出
        assert "system" in result
        assert "CHECKER" in result["system"]

        # 解析CHECKER的响应内容
        checker_data = result["system"]["CHECKER"]
        assert "choices" in checker_data
        assert len(checker_data["choices"]) > 0

        checker_content = json.loads(checker_data["choices"][0]["message"]["content"])
        assert "quality_score" in checker_content
        assert checker_content["quality_score"] > 0.9
        assert any("翻译结果准确" in suggestion for suggestion in checker_content.get("suggestions", []))

    finally:
        await workflow.close()