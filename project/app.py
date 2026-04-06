import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, Query

from env.environment import SmartWasteManagementEnvironment
from env.models import Action
from env.tasks import TaskRegistry


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Smart Waste Management Environment",
    description="OpenEnv-compatible waste management simulation",
    version="1.0.0",
)

env: Optional[SmartWasteManagementEnvironment] = None
current_task = "medium"


def serialize_model(model):
    """Support Pydantic v2 JSON serialization without leaking model objects."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def initialize_environment(task_name: str) -> SmartWasteManagementEnvironment:
    task = TaskRegistry.get_task(task_name)
    return SmartWasteManagementEnvironment(task)


def require_environment() -> SmartWasteManagementEnvironment:
    if env is None:
        raise HTTPException(
            status_code=400,
            detail="Environment not initialized. Call /reset first.",
        )
    return env


def parse_action(action: str) -> Action:
    normalized = action.strip().lower()
    if not normalized:
        raise HTTPException(status_code=400, detail="Action query parameter is required.")

    if normalized == "wait":
        return Action(action_type="wait")

    action_type, separator, raw_value = normalized.partition("_")
    if separator == "":
        raise HTTPException(
            status_code=400,
            detail="Action must be formatted as wait, collect_<bin_id>, or move_<location>.",
        )

    try:
        parsed_value = int(raw_value)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Action suffix must be an integer.",
        ) from exc

    if action_type == "collect":
        return Action(action_type="collect", bin_id=parsed_value)
    if action_type == "move":
        return Action(action_type="move", target_location=parsed_value)

    raise HTTPException(
        status_code=400,
        detail="Unsupported action type. Use wait, collect_<bin_id>, or move_<location>.",
    )


@app.on_event("startup")
async def startup():
    """Initialize the default environment when the API boots."""
    global env
    env = initialize_environment(current_task)
    logger.info("Environment initialized with task: %s", current_task)


@app.get("/")
async def root():
    return {
        "status": "running",
        "environment": "Smart Waste Management",
        "version": "1.0.0",
    }


@app.get("/tasks")
async def list_tasks():
    return {
        "tasks": TaskRegistry.list_tasks(),
        "current_task": current_task,
    }


@app.get("/reset")
async def reset_environment(task: Optional[str] = Query(default=None)):
    """Reset the environment to the selected task."""
    global env, current_task

    try:
        if task is not None:
            if task not in TaskRegistry.list_tasks():
                raise HTTPException(status_code=400, detail=f"Unknown task '{task}'.")
            current_task = task

        env = initialize_environment(current_task)
        state = env.reset()
        logger.info("Environment reset with task: %s", current_task)

        return {
            "status": "success",
            "message": f"Environment reset with task: {current_task}",
            "state": serialize_model(state),
            "observation": env.get_observation_dict(),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Reset failed")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/step")
async def step_environment(action: str = Query(..., description="wait, collect_<bin_id>, or move_<location>")):
    """Execute one step using a GET-friendly action query parameter."""
    active_env = require_environment()

    try:
        parsed_action = parse_action(action)
        result = active_env.step(parsed_action)
        return {
            "status": "success",
            "action": action,
            "state": serialize_model(result.state),
            "reward": result.reward,
            "done": result.done,
            "info": result.info,
            "observation": active_env.get_observation_dict(),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Step failed")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/state")
async def get_state():
    active_env = require_environment()

    try:
        state = active_env.state()
        return {
            "status": "success",
            "state": serialize_model(state),
            "observation": active_env.get_observation_dict(),
        }
    except Exception as exc:
        logger.exception("Get state failed")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment_initialized": env is not None,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7860)
