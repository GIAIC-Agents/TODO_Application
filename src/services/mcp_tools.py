from typing import Dict, Any, Optional
from sqlmodel import Session
from ..models.task import Task, TaskCreate
from ..services.task_service import create_task, get_tasks, update_task, delete_task, toggle_task_completion


class MCPTools:
    """MCP Server Tools for Task Management"""
    
    @staticmethod
    def add_task(session: Session, user_id: str, title: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new task"""
        try:
            print(f"MCP add_task called with user_id: {user_id}, title: {title}, description: {description}")
            # Handle null description by converting to empty string or None
            task_description = description if description and description.strip() else None
            task_data = TaskCreate(title=title, description=task_description)
            task = create_task(session, task_data, user_id)
            return {
                "task_id": str(task.id),
                "status": "created",
                "title": task.title,
                "description": task.description
            }
        except Exception as e:
            print(f"Error in add_task: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def list_tasks(session: Session, user_id: str, status: str = "all") -> Dict[str, Any]:
        """Retrieve tasks from the list"""
        try:
            print(f"MCP list_tasks called with user_id: {user_id}, status: {status}")
            
            # Convert status string to boolean filter
            completed_filter = None
            if status == "completed":
                completed_filter = True
            elif status == "pending":
                completed_filter = False
            
            tasks = get_tasks(session, user_id, completed_filter, offset=0, limit=100)
            print(f"Found {len(tasks)} tasks for user {user_id}")
            
            task_list = []
            for task in tasks:
                task_list.append({
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "completed": task.completed,
                    "created_at": task.created_at.isoformat()
                })
                print(f"Task: {task.title} (completed: {task.completed})")
            
            result = {
                "tasks": task_list
            }
            print(f"Returning result: {result}")
            return result
        except Exception as e:
            print(f"Error in list_tasks: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    @staticmethod
    def _resolve_task_id(session: Session, user_id: str, task_identifier: str) -> Optional[str]:
        """
        Resolve a task identifier (number or UUID) to actual UUID
        If user says 'task 1' or '1', map it to the first task's UUID
        """
        # Check if it's already a valid UUID format
        try:
            from uuid import UUID
            UUID(task_identifier)
            return task_identifier  # It's already a UUID
        except (ValueError, AttributeError):
            pass
        
        # Try to parse as task number (1, 2, 3, etc.)
        try:
            task_number = int(task_identifier)
            # Get user's tasks
            tasks = get_tasks(session, user_id, completed=None, offset=0, limit=100)
            if 1 <= task_number <= len(tasks):
                # Return the UUID of the nth task (1-indexed)
                return str(tasks[task_number - 1].id)
            else:
                return None
        except (ValueError, IndexError):
            return None
    
    @staticmethod
    def complete_task(session: Session, user_id: str, task_id: str) -> Dict[str, Any]:
        """Mark a task as complete"""
        try:
            # Resolve task number to UUID if needed
            resolved_id = MCPTools._resolve_task_id(session, user_id, task_id)
            if not resolved_id:
                return {"error": f"Task '{task_id}' not found"}
            
            from ..models.task import TaskToggleComplete
            toggle_data = TaskToggleComplete(completed=True)
            task = toggle_task_completion(session, resolved_id, toggle_data, user_id)
            if task:
                return {
                    "task_id": task.id,
                    "status": "completed",
                    "title": task.title
                }
            return {"error": "Task not found"}
        except Exception as e:
            print(f"Error in complete_task: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    @staticmethod
    def delete_task(session: Session, user_id: str, task_id: str) -> Dict[str, Any]:
        """Remove a task from the list"""
        try:
            # Resolve task number to UUID if needed
            resolved_id = MCPTools._resolve_task_id(session, user_id, task_id)
            if not resolved_id:
                return {"error": f"Task '{task_id}' not found"}
            
            success = delete_task(session, resolved_id, user_id)
            if success:
                return {
                    "task_id": resolved_id,
                    "status": "deleted"
                }
            return {"error": "Task not found"}
        except Exception as e:
            print(f"Error in delete_task: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    @staticmethod
    def update_task(session: Session, user_id: str, task_id: str, title: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        """Modify task title or description"""
        try:
            # Resolve task number to UUID if needed
            resolved_id = MCPTools._resolve_task_id(session, user_id, task_id)
            if not resolved_id:
                return {"error": f"Task '{task_id}' not found"}
            
            from ..models.task import TaskUpdate
            update_data = TaskUpdate(title=title, description=description)
            task = update_task(session, resolved_id, update_data, user_id)
            if task:
                return {
                    "task_id": task.id,
                    "status": "updated",
                    "title": task.title,
                    "description": task.description
                }
            return {"error": "Task not found"}
        except Exception as e:
            print(f"Error in update_task: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
