from sqlmodel import Session, select
from typing import List, Optional
from ..models.task import Task, TaskCreate, TaskUpdate, TaskToggleComplete, get_pakistan_time
from ..models.user import User
from datetime import datetime


def create_task(session: Session, task_create: TaskCreate, user_id: str) -> Task:
    db_task = Task(**task_create.dict(), user_id=user_id)
    session.add(db_task)
    session.flush()  # Flush to get the ID without committing
    return db_task


def get_tasks(session: Session, user_id: str, completed: Optional[bool] = None, 
              offset: int = 0, limit: int = 50) -> List[Task]:
    statement = select(Task).where(Task.user_id == user_id)
    if completed is not None:
        statement = statement.where(Task.completed == completed)
    statement = statement.offset(offset).limit(limit)
    return session.exec(statement).all()


def get_task(session: Session, task_id: str, user_id: str) -> Optional[Task]:
    statement = select(Task).where(Task.id == task_id, Task.user_id == user_id)
    return session.exec(statement).first()


def update_task(session: Session, task_id: str, task_update: TaskUpdate, user_id: str) -> Optional[Task]:
    db_task = get_task(session, task_id, user_id)
    if not db_task:
        return None
        
    task_data = task_update.dict(exclude_unset=True)
    for key, value in task_data.items():
        setattr(db_task, key, value)
    
    db_task.updated_at = get_pakistan_time()
    session.add(db_task)
    session.flush()
    return db_task


def delete_task(session: Session, task_id: str, user_id: str) -> bool:
    db_task = get_task(session, task_id, user_id)
    if not db_task:
        return False
        
    session.delete(db_task)
    session.flush()
    return True


def toggle_task_completion(session: Session, task_id: str, toggle_request: TaskToggleComplete, user_id: str) -> Optional[Task]:
    db_task = get_task(session, task_id, user_id)
    if not db_task:
        return None
        
    db_task.completed = toggle_request.completed
    db_task.updated_at = get_pakistan_time()
    session.add(db_task)
    session.flush()
    return db_task