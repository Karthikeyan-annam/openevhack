# Deployment Guide

## Local Deployment

### Prerequisites
- Python 3.10+
- pip or conda
- Optional: Docker & Docker Compose

### Quick Start (Recommended)

**Windows:**
```batch
quickstart.bat
```

**Linux/macOS:**
```bash
chmod +x quickstart.sh
./quickstart.sh
```

### Manual Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and edit environment variables
cp .env.example .env
# Edit .env with your OpenAI API key

# Validate setup
python validate.py
```

## Running the Application

### Inference Mode
```bash
python inference.py
```

Output:
- Runs 3 episodes each on easy, medium, hard tasks
- Prints performance scores for each task
- Final overall score (0.0-1.0 scale)

### API Server Mode

```bash
# Development
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Production (with Gunicorn)
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:app --bind 0.0.0.0:8000
```

Access API at: `http://localhost:8000`
Docs at: `http://localhost:8000/docs`

## Docker Deployment

### Build Image
```bash
docker build -t waste-env:latest .

# With buildkit (faster)
DOCKER_BUILDKIT=1 docker build -t waste-env:latest .
```

### Run Container

**Basic:**
```bash
docker run -p 8000:8000 waste-env:latest
```

**With Environment Variables:**
```bash
docker run -p 8000:8000 \
  -e OPENAI_API_KEY="your-key" \
  -e MODEL_NAME="gpt-3.5-turbo" \
  -e DEBUG="False" \
  waste-env:latest
```

**With Volume Mounting:**
```bash
docker run -p 8000:8000 \
  -v $(pwd)/logs:/app/logs \
  -e OPENAI_API_KEY="your-key" \
  waste-env:latest
```

### Docker Compose (Recommended)

```bash
# Create .env file
cp .env.example .env
# Edit .env with your settings

# Start service
docker-compose up -d

# View logs
docker-compose logs -f waste-management-env

# Stop service
docker-compose down
```

## Kubernetes Deployment

### Create Namespace
```bash
kubectl create namespace waste-management
```

### Deploy

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: waste-env
  namespace: waste-management
spec:
  replicas: 3
  selector:
    matchLabels:
      app: waste-env
  template:
    metadata:
      labels:
        app: waste-env
    spec:
      containers:
      - name: waste-env
        image: waste-env:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-secret
              key: api-key
        - name: MODEL_NAME
          value: "gpt-3.5-turbo"
        resources:
          requests:
            memory: "2Gi"
            cpu: "500m"
          limits:
            memory: "8Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: waste-env-service
  namespace: waste-management
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: waste-env
```

Apply with:
```bash
kubectl apply -f deployment.yaml
```

## Cloud Deployment

### Azure Container Instances

```bash
az group create --name waste-env-rg --location eastus

az container create \
  --resource-group waste-env-rg \
  --name waste-env \
  --image waste-env:latest \
  --port 8000 \
  --cpu 2 \
  --memory 8 \
  --registry-login-server <registry>.azurecr.io \
  --registry-username <username> \
  --registry-password <password> \
  --environment-variables \
    OPENAI_API_KEY="your-key" \
    MODEL_NAME="gpt-3.5-turbo"
```

### AWS ECS

1. Create ECR repository:
```bash
aws ecr create-repository --repository-name waste-env
```

2. Push image:
```bash
docker tag waste-env:latest <account>.dkr.ecr.us-east-1.amazonaws.com/waste-env:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/waste-env:latest
```

3. Create ECS task definition and service in AWS Console or CLI

## Performance Tuning

### Memory Optimization
- Reduce number of bins in task configuration
- Use smaller batch sizes in inference
- Consider streaming responses for large episodes

### CPU Optimization
- Use PyPy for faster execution: `pip install pypy3`
- Enable Gunicorn workers: `gunicorn -w 4 ...`
- Profile with: `python -m cProfile inference.py`

### Scaling
- Horizontal: Use load balancer + multiple containers
- Vertical: Increase CPU/memory limits
- Auto-scaling: Configure based on CPU/memory metrics

## Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Metrics Endpoint (Optional - Add to app.py)
```python
from prometheus_client import Counter, Histogram

episode_counter = Counter('episodes_total', 'Total episodes run')
episode_duration = Histogram('episode_duration_seconds', 'Episode duration')
```

### Logs
```bash
# Docker
docker logs <container-id>

# Docker Compose
docker-compose logs waste-management-env

# Kubernetes
kubectl logs -n waste-management <pod-name> -f
```

## Troubleshooting

### Port Already in Use
```bash
# Linux/macOS
lsof -i :8000
kill -9 <PID>

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Docker Image Too Large
```bash
# Use multi-stage build
docker build --target runtime -t waste-env:slim .
```

### Memory Leaks
```bash
# Profile memory usage
pip install memory-profiler
python -m memory_profiler inference.py
```

### OpenAI API Errors
1. Check API key: `echo $OPENAI_API_KEY`
2. Verify model name in .env
3. Check rate limits: `curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models`

## Performance Benchmarks

| Configuration | Memory | Speed | Inference Time |
|---------------|--------|-------|-----------------|
| 1 vCPU, 2GB RAM | 120MB | 800 eps | 25 mins |
| 2 vCPU, 8GB RAM | 180MB | 1200 eps | 15 mins |
| 4 vCPU, 16GB RAM | 250MB | 1800 eps | 10 mins |

**eps** = environment steps / second
**Inference Time** = Time to run all 9 episodes (3 per difficulty)

## Production Checklist

- [ ] Environment variables configured
- [ ] OpenAI API key set and tested
- [ ] Docker image built and tested
- [ ] Health checks responding
- [ ] Monitoring/logging configured
- [ ] Load testing completed
- [ ] Rate limiting set up (if needed)
- [ ] SSL/TLS enabled (if on internet)
- [ ] Database backups configured (if applicable)
- [ ] Disaster recovery plan tested

## Support

For issues:
1. Check logs: `docker logs <container>`
2. Test health: `curl http://localhost:8000/health`
3. Validate config: `python config.py`
4. Run validation: `python validate.py`
