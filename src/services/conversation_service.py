from sqlmodel import Session, select
from typing import List, Optional
from uuid import UUID
from ..models.conversation import Conversation, Message
from ..models.task import Task


class ConversationService:
    @staticmethod
    def get_or_create_conversation(session: Session, user_id: str, conversation_id: Optional[UUID] = None) -> Conversation:
        """Get existing conversation or create new one"""
        if conversation_id:
            conversation = session.exec(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id
                )
            ).first()
            if conversation:
                return conversation
        
        # Create new conversation
        conversation = Conversation(user_id=user_id)
        session.add(conversation)
        session.flush()  # Flush to get ID without committing
        return conversation
    
    @staticmethod
    def get_conversation_history(session: Session, conversation_id: UUID) -> List[Message]:
        """Get all messages in a conversation"""
        messages = session.exec(
            select(Message).where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        ).all()
        return messages
    
    @staticmethod
    def add_message(session: Session, conversation_id: UUID, user_id: str, role: str, content: str) -> Message:
        """Add a message to conversation"""
        message = Message(
            conversation_id=conversation_id,
            user_id=user_id,
            role=role,
            content=content
        )
        session.add(message)
        
        # Update conversation timestamp
        conversation = session.get(Conversation, conversation_id)
        if conversation:
            conversation.updated_at = message.created_at
        
        session.flush()
        return message
