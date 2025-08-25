from sqlmodel import Session, select
from app.db.models import Conversation, Message
from typing import List, Optional, Dict, Any
import logging
import datetime
import json
import uuid

logger = logging.getLogger(__name__)


class ConversationService:
    """Service to handle conversations and messages."""

    def __init__(self, session: Session):
        self.session = session

    def create_conversation(self, user_id: str, title: Optional[str] = None) -> Conversation:
        """Create a new conversation for a user."""
        conversation = Conversation(
            user_id=user_id,
            title=title or f"Conversation {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )
        self.session.add(conversation)
        self.session.commit()
        self.session.refresh(conversation)
        logger.info(f"Created conversation {conversation.id} for user {user_id}")
        return conversation

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        query = select(Conversation).where(Conversation.id == conversation_id)
        return self.session.exec(query).first()

    def get_conversation_by_user(self, user_id: str) -> List[Conversation]:
        """Get all conversations for a user."""
        query = select(Conversation).where(Conversation.user_id == user_id)
        return self.session.exec(query).all()

    def add_message(
        self, 
        conversation_id: str, 
        role: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Add a message to a conversation."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            logger.error(f"Conversation {conversation_id} not found")
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Cập nhật thời gian cập nhật của cuộc trò chuyện
        conversation.updated_at = datetime.datetime.now()
        self.session.add(conversation)
        
        # Tạo message mới
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            created_at=datetime.datetime.now(),
            meta_data=json.dumps(metadata) if metadata else "{}"
        )
        self.session.add(message)
        self.session.commit()
        self.session.refresh(message)
        logger.info(f"Added message {message.id} to conversation {conversation_id}")
        return message

    def get_messages(self, conversation_id: str, limit: int = 50) -> List[Message]:
        """Get messages from a conversation, ordered by created_at."""
        query = select(Message) \
            .where(Message.conversation_id == conversation_id) \
            .order_by(Message.created_at.asc()) \
            .limit(limit)
        return self.session.exec(query).all()

    def get_last_message(self, conversation_id: str) -> Optional[Message]:
        """Get the most recent message in a conversation."""
        query = select(Message) \
            .where(Message.conversation_id == conversation_id) \
            .order_by(Message.created_at.desc()) \
            .limit(1)
        return self.session.exec(query).first()

    def get_all_messages(self, conversation_id: str) -> List[Message]:
        """Get all messages from a conversation, ordered by created_at."""
        query = select(Message) \
            .where(Message.conversation_id == conversation_id) \
            .order_by(Message.created_at.asc())
        return self.session.exec(query).all()

    def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the chat history for a conversation in a format suitable for OpenAI."""
        messages = self.get_messages(conversation_id, limit)
        return [
            {"role": message.role, "content": message.content}
            for message in messages
        ] 