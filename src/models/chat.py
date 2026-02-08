from sqlmodel import SQLModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID


class ChatRequest(SQLModel):
    conversation_id: Optional[UUID] = None
    message: str


class ChatResponse(SQLModel):
    conversation_id: Optional[UUID] = None
    response: str
    tool_calls: List[Dict[str, Any]] = []


class MCPToolCall(SQLModel):
    tool_name: str
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None


class MCPToolResponse(SQLModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
