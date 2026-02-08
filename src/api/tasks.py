from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session
from typing import List
from ..database import engine
from ..models.task import Task, TaskCreate, TaskRead, TaskUpdate, TaskToggleComplete
from ..services.task_service import (
    create_task, get_tasks, get_task, update_task, delete_task, toggle_task_completion
)
from ..api.middleware.auth_middleware import JWTBearer

router = APIRouter()


def get_session():
    with Session(engine) as session:
        yield session


def get_current_user_id(request: Request) -> str:
    """Get user_id from JWT token stored in request state"""
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    return user_id


@router.get("/tasks", response_model=List[TaskRead])
def read_tasks(
    request: Request,
    completed: bool = None,
    offset: int = 0,
    limit: int = 50,
    token: str = Depends(JWTBearer()),
    session: Session = Depends(get_session)
):
    user_id = get_current_user_id(request)
    tasks = get_tasks(session, user_id, completed, offset, limit)
    return tasks


@router.post("/tasks", response_model=TaskRead)
def create_new_task(
    request: Request,
    task: TaskCreate,
    token: str = Depends(JWTBearer()),
    session: Session = Depends(get_session)
):
    user_id = get_current_user_id(request)
    db_task = create_task(session, task, user_id)
    return db_task


@router.get("/tasks/{task_id}", response_model=TaskRead)
def read_task(
    request: Request,
    task_id: str,
    token: str = Depends(JWTBearer()),
    session: Session = Depends(get_session)
):
    user_id = get_current_user_id(request)
    db_task = get_task(session, task_id, user_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@router.put("/tasks/{task_id}", response_model=TaskRead)
def update_existing_task(
    request: Request,
    task_id: str,
    task: TaskUpdate,
    token: str = Depends(JWTBearer()),
    session: Session = Depends(get_session)
):
    user_id = get_current_user_id(request)
    db_task = update_task(session, task_id, task, user_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@router.delete("/tasks/{task_id}")
def delete_existing_task(
    request: Request,
    task_id: str,
    token: str = Depends(JWTBearer()),
    session: Session = Depends(get_session)
):
    user_id = get_current_user_id(request)
    success = delete_task(session, task_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}


@router.patch("/tasks/{task_id}/complete", response_model=TaskRead)
def toggle_task_complete(
    request: Request,
    task_id: str,
    task_toggle: TaskToggleComplete,
    token: str = Depends(JWTBearer()),
    session: Session = Depends(get_session)
):
    user_id = get_current_user_id(request)
    db_task = toggle_task_completion(session, task_id, task_toggle, user_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task