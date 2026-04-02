# Technical Documentation

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Server (app.py)              │
│  /reset    /step    /state    /health    /tasks  /docs  │
└──────────────────────┬──────────────────────────────────┘
                       │
           ┌───────────┴───────────┐
           │                       │
    ┌──────▼─────────┐    ┌────────▼────────┐
    │  Environment   │    │  Inference      │
    │  (env/)        │    │  (inference.py) │
    └────────────────┘    └─────────────────┘
           │
      ┌────┴─────┬──────────┬─────────┐
      │           │          │         │
  ┌───▼──┐  ┌────▼──┐  ┌───▼──┐  ┌───▼──┐
  │Models│  │Environ │  │Tasks │  │Grade │
  │      │  │ment    │  │      │  │      │
  └──────┘  └────────┘  └──────┘  └──────┘
```

## Module Details

### env/models.py
Pydantic V2 models for type safety and validation:
- `WasteBin`: Individual bin state and metadata
- `GarbageTruck`: Truck state with capacity/fuel
- `EnvironmentState`: Complete environment snapshot
- `Action`: Validated action structures
- `StepResult`: Structured step results
- `TaskDefinition`: Task parameters

**Key Features:**
- Field validation with `Field(ge=0.0, le=100.0)`
- Config for frozen/mutability
- Automatic JSON serialization

### env/environment.py
Core simulation engine:

**Key Methods:**
- `reset()`: Initialize environment
- `step(action)`: Execute one action, return StepResult
- `state()`: Get current state
- `get_observation_dict()`: Get dict representation

**Rewards:**
```python
+1.0:  full bin collection
+0.3:  partial collection
+0.2:  truck full bonus
+0.1:  strategic move
-1.0:  overflow
-0.5:  invalid action
```

**Physics:**
- Bins fill: `fill += rate × random(0.5-1.5)` per step
- Truck fuel: `-0.5` per step
- Collection: `min(truck_capacity - load, bin_level)`

### env/tasks.py
Task registry pattern:
```python
class TaskRegistry:
    EASY = TaskDefinition(...)
    MEDIUM = TaskDefinition(...)
    HARD = TaskDefinition(...)
    
    @staticmethod
    def get_task(name: str) -> TaskDefinition
```

**Task Parameters:**
- `num_bins`: Complexity
- `bin_max_fill_rate`: Environment dynamics
- `truck_capacity`: Resource constraint
- `time_limit`: Episode length

### env/grader.py
Performance evaluation with weighted metrics:

```python
score = (
    0.40 * collection_efficiency +
    0.30 * overflow_prevention +
    0.20 * fuel_efficiency +
    0.10 * time_management
)
```

**Scoring Logic:**
- Collection: `waste_reduced / initial_waste`
- Overflow: `-0.1` per overflow (capped)
- Fuel: Based on remaining fuel percentage
- Time: Utilization ratio

### app.py
FastAPI server with OpenAPI documentation:

**Endpoints:**
- `POST /reset`: Initialize environment
- `POST /step`: Execute action
- `GET /state`: Current state snapshot
- `GET /health`: Liveness check
- `GET /tasks`: List available tasks
- `GET /docs`: Interactive API documentation (Swagger)

**Request/Response Pattern:**
```python
# Request
POST /step
{"action_type": "collect", "bin_id": 0}

# Response
{
    "status": "success",
    "state": {...},
    "reward": 0.3,
    "done": false,
    "info": {"collected_amount": 15.2},
    "observation": {...}
}
```

### inference.py
LLM-based agent with fallback:

**Decision Flow:**
```
1. Check if OpenAI client available
2. If yes: Use LLM prompt to decide action
3. If no: Use random action selection
```

**LLM Prompt:**
- Observation state formatting
- Available actions
- Expected JSON response
- Goal statement

**Batch Processing:**
- 3 episodes per task
- Aggregate grading
- Summary statistics

## Data Flow

### Reset Sequence
```
POST /reset 
  ↓
Load task definition from TaskRegistry
  ↓
Create environment.py SmartWasteManagementEnvironment
  ↓
Initialize bins (random fill 10-40%)
  ↓
Initialize truck (0 load, 100% fuel)
  ↓
Return EnvironmentState + observation_dict
```

### Step Sequence
```
POST /step(action)
  ↓
Validate action structure
  ↓
Execute action (_handle_collect, _handle_move, _handle_wait)
  ↓
Calculate reward
  ↓
Update bins (natural fill progression)
  ↓
Check overflow conditions
  ↓
Decrease truck fuel
  ↓
Increment time_step
  ↓
Check done condition (time_limit reached)
  ↓
Return StepResult
```

## Performance Characteristics

### Time Complexity
- `reset()`: O(n_bins) for initialization
- `step()`: O(n_bins) for bin updates
- `grade()`: O(n_bins) for metrics calculation

### Space Complexity
- Per environment: O(n_bins) for state storage
- Per episode: O(time_limit) if recording all steps

### Optimization Tips
1. Use vectorized operations for bin updates
2. Cache observation dict if accessed frequently
3. Batch episodes for inference
4. Use async FastAPI for concurrent requests

## Configuration

### Task Customization
```python
# In env/tasks.py
CUSTOM = TaskDefinition(
    name="custom",
    num_bins=20,
    bin_max_fill_rate=0.12,
    truck_capacity=900.0,
    time_limit=180,
    overflow_penalty=-1.0
)
```

### Reward Customization
Edit `environment.py._handle_collect()`:
```python
reward = 1.0 if fully_collected else 0.3
if truck_full:
    reward += 0.2  # Custom bonus
```

### Grading Customization
Modify weights in `grader.py.grade_episode()`:
```python
0.40 * collection_score +   # Adjust weights
0.30 * overflow_score +
0.20 * fuel_score +
0.10 * time_score
```

## Testing

### Unit Test Example
```python
from env.environment import SmartWasteManagementEnvironment
from env.tasks import TaskRegistry
from env.models import Action

task = TaskRegistry.get_task("easy")
env = SmartWasteManagementEnvironment(task)
env.reset()

action = Action(action_type="move", target_location=1)
result = env.step(action)

assert result.state.truck.location == 1
assert result.reward >= 0.0
assert not result.done
```

### Integration Test Example
```python
import requests
import json

# Reset
resp = requests.post("http://localhost:8000/reset", params={"task": "easy"})
assert resp.status_code == 200

# Step
action = {"action_type": "wait"}
resp = requests.post("http://localhost:8000/step", json=action)
assert resp.status_code == 200

# Get state
resp = requests.get("http://localhost:8000/state")
state = resp.json()["state"]
```

## Extension Points

### Custom Actions
```python
# In action validation
if action.action_type == "custom_action":
    return self._handle_custom(action, info)

def _handle_custom(self, action: Action, info: Dict) -> float:
    # Custom logic
    return reward
```

### Custom Rewards
```python
# Add bonus for specific conditions
if condition:
    reward += bonus_amount
    info["bonus_reason"] = "specific condition met"
```

### Custom Grading
```python
# Add new metric
new_metric = calculate_metric(initial_state, final_state)
score = (...existing weights...) + weight * new_metric
```

## Debugging

### Environment Variables
```bash
DEBUG=True python app.py
DEBUG=True python inference.py
```

### Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("Debug message")
```

### State Inspection
```python
state = env.state()
print(f"Bins: {[b.fill_level for b in state.bins]}")
print(f"Truck: load={state.truck.current_load}, fuel={state.truck.fuel}")
print(f"Time: {state.time_step}")
```

## API Documentation

The FastAPI server automatically generates OpenAPI (Swagger) documentation at:
```
http://localhost:8000/docs
http://localhost:8000/redoc
```

Schema examples are available in the interactive UI.

## Performance Profiling

```bash
# CPU profiling
python -m cProfile -s cumtime inference.py

# Memory profiling
pip install memory-profiler
python -m memory_profiler inference.py

# Line profiling
pip install line_profiler
kernprof -l -v inference.py
```

## Version History

- **1.0.0**: Initial release with easy/medium/hard tasks, OpenAI integration, FastAPI server

## License

MIT - See LICENSE file

---

**Last Updated**: 2024
**Maintainer**: Hackathon Team
