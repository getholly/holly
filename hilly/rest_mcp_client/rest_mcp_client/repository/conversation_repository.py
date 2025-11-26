from datetime import datetime
from typing import List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session
from rest_mcp_client.database.database import ConversationDB, MessageDB
from rest_mcp_client.models.conversation import Conversation, Message, ConversationCreate, MessageCreate, ConversationSummary

class ConversationRepository:
    @staticmethod
    def create_conversation(db: Session, conversation_create: Optional[ConversationCreate] = None) -> Conversation:
        """
        Create a new conversation in the database.

        Args:
            db: Database session
            conversation_create: Optional initial message for the conversation

        Returns:
            Conversation: The created conversation
        """
        # Create new conversation
        now = datetime.now()

        # Prefer caller-provided id/title if present so external systems can correlate
        new_id = None
        title = None
        if conversation_create:
            new_id = conversation_create.id or None
            title = conversation_create.title

        if title is None or title == "SSE Chat":
            title = str(Conversation().id)

        db_conversation = ConversationDB(
            id=new_id or Conversation().id,
            title=title,
            created_at=now,
            updated_at=now
        )
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)

        conversation = Conversation(
            id=db_conversation.id,
            title=db_conversation.title,
            created_at=db_conversation.created_at,
            updated_at=db_conversation.updated_at,
            messages=[]
        )

        # Add initial message if provided
        if conversation_create and conversation_create.initial_message:
            message = Message(
                conversation_id=conversation.id,
                role="user",
                content=conversation_create.initial_message,
                created_at=now
            )
            ConversationRepository.add_message(db, message)
            conversation.messages.append(message)

        return conversation

    @staticmethod
    def get_conversation(db: Session, conversation_id: str) -> Optional[Conversation]:
        """
        Get a conversation by its ID.

        Args:
            db: Database session
            conversation_id: The ID of the conversation to retrieve

        Returns:
            Optional[Conversation]: The conversation if found, None otherwise
        """
        db_conversation = db.query(ConversationDB).filter(ConversationDB.id == conversation_id).first()
        if not db_conversation:
            return None

        # Get all messages for this conversation
        db_messages = db.query(MessageDB).filter(MessageDB.conversation_id == conversation_id).all()
        messages = [
            Message(
                id=msg.id,
                conversation_id=msg.conversation_id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at
            ) for msg in db_messages
        ]

        return Conversation(
            id=db_conversation.id,
            title=db_conversation.title,
            created_at=db_conversation.created_at,
            updated_at=db_conversation.updated_at,
            messages=messages
        )

    @staticmethod
    def get_all_conversations(db: Session) -> List[ConversationSummary]:
        """
        Get a list of all conversations with their metadata.

        Args:
            db: Database session

        Returns:
            List[ConversationSummary]: A list of conversation summaries
        """
        conversations = db.query(ConversationDB).order_by(desc(ConversationDB.created_at)).all()
        return [
            ConversationSummary(
                id=conv.id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at
            ) for conv in conversations
        ]

    @staticmethod
    def update_conversation_timestamp(db: Session, conversation_id: str) -> bool:
        """
        Update the updated_at timestamp of a conversation.

        Args:
            db: Database session
            conversation_id: The ID of the conversation to update

        Returns:
            bool: True if the update was successful, False otherwise
        """
        db_conversation = db.query(ConversationDB).filter(ConversationDB.id == conversation_id).first()
        if not db_conversation:
            return False

        db_conversation.updated_at = datetime.now()
        db.commit()
        return True

    @staticmethod
    def add_message(db: Session, message: Message) -> Message:
        """
        Add a message to a conversation.

        Args:
            db: Database session
            message: The message to add

        Returns:
            Message: The added message
        """
        # Add message to database
        db_message = MessageDB(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            created_at=message.created_at
        )
        db.add(db_message)

        # Update conversation's updated_at timestamp
        ConversationRepository.update_conversation_timestamp(db, message.conversation_id)

        db.commit()
        db.refresh(db_message)

        return message
