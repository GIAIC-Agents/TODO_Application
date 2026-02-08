from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session
from typing import List
from uuid import UUID
from ..database import get_session
from ..models.chat import ChatRequest, ChatResponse
from ..services.conversation_service import ConversationService
from ..services.todo_agent import TodoAgent
from ..api.middleware.auth_middleware import JWTBearer
from ..config.settings import settings
import os

router = APIRouter()

# Initialize Todo Agent
todo_agent = TodoAgent()


def get_current_user_id(request: Request) -> str:
    """Get user_id from JWT token stored in request state"""
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    return user_id


@router.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(
    request: Request,
    chat_request: ChatRequest,
    token: str = Depends(JWTBearer()),
    session: Session = Depends(get_session)
):
    """Send message & get AI response"""
    user_id = get_current_user_id(request)
    
    print(f"Chat request from user: {user_id}")
    print(f"Message: {chat_request.message}")
    print(f"Conversation ID: {chat_request.conversation_id}")
    
    try:
        # Get or create conversation
        conversation = ConversationService.get_or_create_conversation(
            session, user_id, chat_request.conversation_id
        )
        
        # Get conversation history
        history = ConversationService.get_conversation_history(session, conversation.id)
        history_dict = [
            {"role": msg.role, "content": msg.content}
            for msg in history
        ]
        
        # Store user message
        ConversationService.add_message(
            session, conversation.id, user_id, "user", chat_request.message
        )
        
        # Process message with agent
        try:
            agent_response = todo_agent.process_message(
                session, user_id, chat_request.message, history_dict
            )
        except Exception as agent_error:
            # If agent processing fails, rollback and create error response
            print(f"Agent processing error: {str(agent_error)}")
            session.rollback()
            
            # Create a fallback response
            from ..models.chat import ChatResponse
            agent_response = ChatResponse(
                conversation_id=conversation.id,
                response=f"Sorry, I encountered an error processing your request. Please try again.",
                tool_calls=[]
            )
        
        # Update conversation_id in response
        agent_response.conversation_id = conversation.id
        
        # Store assistant response
        try:
            ConversationService.add_message(
                session, conversation.id, user_id, "assistant", agent_response.response
            )
            # Commit all changes in one transaction
            session.commit()
        except Exception as msg_error:
            print(f"Error storing assistant message: {str(msg_error)}")
            session.rollback()
            # Still return the response even if we couldn't store it
        
        return agent_response
        
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Rollback any pending transaction
        try:
            session.rollback()
        except:
            pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}"
        )


@router.get("/api/conversations")
def list_conversations(
    request: Request,
    token: str = Depends(JWTBearer()),
    session: Session = Depends(get_session)
):
    """List user's conversations"""
    user_id = get_current_user_id(request)
    
    from sqlmodel import select
    conversations = session.exec(
        select(Conversation).where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
    ).all()
    
    return [
        {
            "id": conv.id,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at
        }
        for conv in conversations
    ]


@router.get("/api/conversations/{conversation_id}/messages")
def get_conversation_messages(
    conversation_id: UUID,
    request: Request,
    token: str = Depends(JWTBearer()),
    session: Session = Depends(get_session)
):
    """Get messages in a conversation"""
    user_id = get_current_user_id(request)
    
    # Verify conversation belongs to user
    from sqlmodel import select
    conversation = session.exec(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        )
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    messages = ConversationService.get_conversation_history(session, conversation_id)
    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at
        }
        for msg in messages
    ]
