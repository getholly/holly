from sqlalchemy import create_engine, Column, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

SQLALCHEMY_DATABASE_URL = "sqlite:///./conversation.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class ConversationDB(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    messages = relationship("MessageDB", back_populates="conversation")

class MessageDB(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    role = Column(String)
    content = Column(String)
    created_at = Column(DateTime)
    
    conversation = relationship("ConversationDB", back_populates="messages")

def init_db():
    """Initialize database and create all tables."""
    # Import here to avoid circular dependency
    from rest_mcp_client.models.job import Job  # noqa: F401
    Base.metadata.create_all(bind=engine)

# Call init on module load
init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
