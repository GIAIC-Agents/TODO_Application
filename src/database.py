from sqlmodel import SQLModel, create_engine, Session
from .config.settings import settings
from .models.user import User
from .models.task import Task
from .models.conversation import Conversation, Message

# Create the database engine with connection pooling
engine = create_engine(
    settings.database_url,
    echo=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600
)

def create_db_and_tables():
    """Create database tables"""
    SQLModel.metadata.create_all(engine)
    print("Database tables created successfully!")

def get_session():
    """Get a database session"""
    with Session(engine) as session:
        yield session