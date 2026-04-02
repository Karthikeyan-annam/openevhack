<!-- QUICK START GUIDE -->
# 🚀 Quick Start

## 30-Second Setup

### Windows
```batch
quickstart.bat
python inference.py
```

### Linux / macOS
```bash
./quickstart.sh
python inference.py
```

## What You Get

✅ **Smart Waste Management Simulation** - Real-world optimization environment  
✅ **OpenEnv API** - Standard reset/step/state interface  
✅ **3 Difficulty Levels** - Easy, Medium, Hard tasks  
✅ **LLM Integration** - Uses OpenAI API (or random fallback)  
✅ **FastAPI Server** - REST endpoints for integration  
✅ **Production Ready** - Clean, typed, scalable code  

## Environment Details

**State**: Bin fill levels, truck capacity, fuel, time  
**Actions**: collect, move, wait  
**Reward**: +1 for collection, -1 for overflow, -0.5 for invalid actions  

## Running Modes

### Mode 1: Inference (Recommended First)
```bash
python inference.py
```
Runs 3 episodes each on easy/medium/hard tasks, prints scores.

### Mode 2: API Server
```bash
python -m uvicorn app:app --reload
```
Start web server, then visit `http://localhost:8000/docs` for interactive API.

### Mode 3: Python Script (Advanced)
```python
from env.environment import SmartWasteManagementEnvironment
from env.tasks import TaskRegistry
from env.models import Action

env = SmartWasteManagementEnvironment(TaskRegistry.get_task("medium"))
state = env.reset()

for step in range(50):
    action = Action(action_type="wait")
    result = env.step(action)
    if result.done:
        break
```

## Docker

```bash
# Build
docker build -t waste-env .

# Run
docker run -p 8000:8000 waste-env

# With API key
docker run -p 8000:8000 -e OPENAI_API_KEY="your-key" waste-env
```

## File Structure (Know This)

```
project/
├── env/              # Simulation engine
│   ├── models.py     # Data structures
│   ├── environment.py # Main simulator
│   ├── tasks.py      # Difficulty levels
│   └── grader.py     # Scoring
├── app.py            # REST API
├── inference.py      # LLM agent + runner
└── [docs & config]
```

## Configuration

Set environment variables in `.env`:
```bash
OPENAI_API_KEY=your-key-here
MODEL_NAME=gpt-3.5-turbo
```

Or leave empty to use random agent (no API needed).

## Troubleshooting

**"Module not found"** → Run `pip install -r requirements.txt`  
**"Port 8000 in use"** → Use different port: `--port 8001`  
**"OpenAI error"** → Set API key or leave empty for random agent  
**"Import error"** → Run `python validate.py` to check setup  

## Next Steps

1. ✅ Run `python validate.py` - Verify everything works
2. ✅ Run `python inference.py` - See it in action
3. ✅ Explore API: `python -m uvicorn app:app --reload`
4. ✅ Read `README.md` for full documentation
5. ✅ Check `TECHNICAL.md` for implementation details

## Key URLs

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Reset**: `POST http://localhost:8000/reset?task=easy`
- **Step**: `POST http://localhost:8000/step` + `{"action_type": "wait"}`

## Performance Expectations

| Task | Easy | Medium | Hard |
|------|------|--------|------|
| Bins | 5 | 10 | 15 |
| Fill Rate | Slow | Moderate | Fast |
| Typical Score | 0.45-0.55 | 0.35-0.45 | 0.25-0.35 |
| (Random Agent) | | | |

## Success Criteria

Your setup is working if:
- ✓ `validate.py` passes all 6 tests
- ✓ `inference.py` runs and prints scores
- ✓ API server starts on port 8000
- ✓ Scores are between 0.0 and 1.0

## Customization

Change difficulty in code:
```python
TaskRegistry.get_task("hard")  # Switch tasks
```

Edit reward in `env/environment.py`:
```python
reward = 2.0  # Change bonus amount
```

Modify grading weights in `env/grader.py`:
```python
0.40 * collection +  # Adjust weights
```

## Support

- **Setup issues**: Check `README.md` Setup section
- **API questions**: See `TECHNICAL.md` API docs
- **Deployment**: Read `DEPLOYMENT.md`
- **Code details**: Explore `PROJECT_STRUCTURE.md`

---

**Ready?** Run `quickstart.bat` (Windows) or `./quickstart.sh` (Unix) now! 🎯
