from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from env.environment import SmartWasteManagementEnvironment
from env.tasks import TaskRegistry
from env.models import Action, EnvironmentState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Smart Waste Management Environment",
    description="OpenEnv-compatible waste management simulation",
    version="1.0.0"
)

# Global environment state
env: Optional[SmartWasteManagementEnvironment] = None
current_task: str = "medium"


@app.on_event("startup")
async def startup():
    """Initialize environment on startup."""
    global env, current_task
    task = TaskRegistry.get_task(current_task)
    env = SmartWasteManagementEnvironment(task)
    logger.info(f"Environment initialized with task: {current_task}")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "environment": "Smart Waste Management",
        "version": "1.0.0"
    }


@app.get("/tasks")
async def list_tasks():
    """List available tasks."""
    return {
        "tasks": TaskRegistry.list_tasks(),
        "current_task": current_task
    }


@app.post("/reset")
async def reset_environment(task: Optional[str] = None):
    """Reset the environment to initial state."""
    global env, current_task
    
    try:
        if task and task in TaskRegistry.list_tasks():
            current_task = task
        
        task_obj = TaskRegistry.get_task(current_task)
        env = SmartWasteManagementEnvironment(task_obj)
        state = env.reset()
        
        logger.info(f"Environment reset with task: {current_task}")
        
        return {
            "status": "success",
            "message": f"Environment reset with task: {current_task}",
            "state": state.dict(),
            "observation": env.get_observation_dict()
        }
    except Exception as e:
        logger.error(f"Reset failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/step")
async def step_environment(action_dict: dict):
    """Execute one step in the environment."""
    global env
    
    if env is None:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    
    try:
        action = Action(
            action_type=action_dict.get("action_type", "wait"),
            bin_id=action_dict.get("bin_id", -1),
            target_location=action_dict.get("target_location", -1)
        )
        
        result = env.step(action)
        
        return {
            "status": "success",
            "state": result.state.dict(),
            "reward": result.reward,
            "done": result.done,
            "info": result.info,
            "observation": env.get_observation_dict()
        }
    except Exception as e:
        logger.error(f"Step failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/state")
async def get_state():
    """Get current environment state."""
    global env
    
    if env is None:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    
    try:
        state = env.state()
        return {
            "status": "success",
            "state": state.dict(),
            "observation": env.get_observation_dict()
        }
    except Exception as e:
        logger.error(f"Get state failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "environment_initialized": env is not None,
        "current_task": current_task
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
