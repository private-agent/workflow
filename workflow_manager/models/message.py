from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class Message:
    user_id: str                    # 用户ID
    content: str                    # 消息内容
    session_id: Optional[str]       # 会话ID
    timestamp: datetime = None      # 消息时间戳
    metadata: Dict[str, Any] = None # 元数据

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'user_id': self.user_id,
            'content': self.content,
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }