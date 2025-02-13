from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from workflow_manager.utils.logger import logger  # 新增导入

class MessageRequest(BaseModel):
    """OpenAI兼容请求格式"""
    model: str = "gpt-3.5-turbo"
    messages: list[dict]  # 标准消息格式
    temperature: float = 0.7
    # SESSION智能体专用扩展字段
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    # 工作流上下文
    workflow_data: Dict[str, Any] = {}
    current_step: int = 0

class OpenAIResponse(BaseModel):
    """OpenAI兼容响应格式"""
    object: str = "chat.completion"
    created: int  # 时间戳
    choices: list[dict]
    usage: dict

class MockAgentBase:
    def __init__(self, name: str, port: int):
        self.app = FastAPI()
        self.name = name
        self.port = port
        self.logger = logger.getChild(f'MockAgent.{name}')  # 新增子logger
        self.logger.debug(f"初始化模拟智能体 | 名称: {name} | 端口: {port}")

        # 注册路由
        self.app.get("/health")(self.health_check)
        self.app.post("/service")(self.process)

    async def health_check(self):
        """健康检查接口"""
        return {"status": "healthy"}

    async def process(self, request: MessageRequest):
        """需要子类实现的处理逻辑"""
        self.logger.debug(
            f"请求详情 | 用户: {request.user_id} "
            f"| 会话ID: {request.session_id} "
            f"| 消息数: {len(request.messages)}"
        )
        self.logger.debug(f"工作流数据: {request.workflow_data}")
        raise NotImplementedError()

    def get_app(self):
        """获取FastAPI应用实例"""
        from fastapi import Request

        app = FastAPI()

        @app.get("/health")
        async def health():
            return await self.health_check()

        @app.post("/service")
        async def service(request: Request):
            # 解析请求体
            body = await request.json()
            # 转换为MessageRequest对象
            msg_request = MessageRequest(**body)
            return await self.process(msg_request)

        return app