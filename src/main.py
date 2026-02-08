from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.auth import router as auth_router
from .api.tasks import router as tasks_router
from .api.chat import router as chat_router
from .config.settings import settings
from .database import create_db_and_tables

def create_app():
    # Create database tables
    create_db_and_tables()
    
    app = FastAPI(title=settings.app_name, version=settings.version)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(tasks_router, prefix="", tags=["tasks"])
    app.include_router(chat_router, tags=["chat"])

    @app.get("/")
    def read_root():
        return {"message": "Multi-User Todo Web Application API"}

    @app.get("/health")
    def health_check():
        return {"status": "healthy", "timestamp": "2026-02-04T19:23:00Z"}

    @app.get("/debug/tasks")
    def debug_tasks():
        """Debug endpoint to check database tasks"""
        from .database import engine
        from sqlmodel import Session, select
        from .models.task import Task
        
        try:
            with Session(engine) as session:
                statement = select(Task)
                tasks = session.exec(statement).all()
                
                task_list = []
                for task in tasks:
                    task_list.append({
                        "id": str(task.id),
                        "title": task.title,
                        "description": task.description,
                        "completed": task.completed,
                        "user_id": str(task.user_id),
                        "created_at": task.created_at.isoformat() if task.created_at else None
                    })
                
                return {
                    "total_tasks": len(task_list),
                    "tasks": task_list
                }
        except Exception as e:
            return {"error": str(e)}

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)