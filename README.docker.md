# 🐳 Docker Setup for BrowserPilot

BrowserPilot can be easily deployed using Docker, which provides a consistent environment with all dependencies pre-installed.

## Quick Start with Docker

### 1. Using Docker Compose (Recommended)

The easiest way to run BrowserPilot is with Docker Compose:

```bash
# Clone the repository
git clone https://github.com/veverkap/BrowserPilot.git
cd BrowserPilot

# Create environment file
echo 'GOOGLE_API_KEY=your_actual_api_key_here' > .env

# Run with Docker Compose
docker-compose up -d
```

The application will be available at `http://localhost:8000`.

### 2. Using Docker Build & Run

If you prefer to use Docker directly:

```bash
# Build the image
docker build -t browserpilot .

# Run the container
docker run -d \
  --name browserpilot \
  -p 8000:8000 \
  -e GOOGLE_API_KEY=your_actual_api_key_here \
  -v $(pwd)/outputs:/app/outputs \
  --shm-size=2g \
  browserpilot
```

## Configuration

### Environment Variables

Set these environment variables for the container:

```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional - Proxy configuration
SCRAPER_PROXIES='[{"server": "http://proxy1:port", "username": "user", "password": "pass"}]'
```

### Volume Mounts

- `./outputs:/app/outputs` - Persist extracted data and downloads
- `./.env:/app/.env:ro` - Mount environment file (optional)

## Production Deployment

For production use, use the production Docker Compose configuration:

```bash
# Production deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

This provides:
- Resource limits (4GB RAM, 2 CPU cores)
- Proper logging configuration
- Restart policies
- Optimized environment settings

## Docker Image Details

### Multi-Stage Build
The Dockerfile uses a multi-stage build process:
1. **Frontend Builder**: Builds the React frontend using Node.js Alpine
2. **Runtime**: Uses Microsoft's Playwright Python image with all browser dependencies

### Features
- ✅ Pre-installed Playwright browsers (Chromium)
- ✅ All system dependencies for browser automation
- ✅ Non-root user for security
- ✅ Health checks included
- ✅ Optimized for container environments

### Image Size
The final image is approximately 2.5GB due to:
- Playwright browsers and dependencies
- Python runtime and packages
- System libraries for browser automation

## Troubleshooting

### Common Issues

**Container exits immediately:**
```bash
# Check logs
docker logs browserpilot

# Common issue: Missing GOOGLE_API_KEY
docker run -e GOOGLE_API_KEY=your_key_here browserpilot
```

**Browser crashes or fails:**
```bash
# Increase shared memory size
docker run --shm-size=2g browserpilot

# Or with Docker Compose (already configured)
docker-compose up
```

**Permission issues with outputs:**
```bash
# Fix output directory permissions
sudo chown -R $(id -u):$(id -g) outputs/
```

### Health Checks

The container includes health checks:
```bash
# Check container health
docker inspect --format='{{.State.Health}}' browserpilot
```

### Performance Tuning

For better performance:
```bash
# Increase resources
docker run \
  --memory=4g \
  --cpus=2 \
  --shm-size=2g \
  browserpilot
```

## Development with Docker

### Live Development
For development with live reload:

```bash
# Mount source code for development
docker run -it \
  -p 8000:8000 \
  -v $(pwd)/backend:/app/backend \
  -v $(pwd)/outputs:/app/outputs \
  -e GOOGLE_API_KEY=your_key_here \
  browserpilot \
  python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Building Custom Images

To customize the Docker image:

```dockerfile
# Extend the base image
FROM browserpilot:latest

# Add custom dependencies
RUN pip install your-custom-package

# Copy custom configurations
COPY custom-config.json /app/
```

## Security Considerations

- The container runs as a non-root user (`pwuser`)
- Uses security options for browser sandbox
- Environment variables are not exposed in the image
- Secrets should be mounted as files or environment variables

## Monitoring and Logging

### Logs
```bash
# View logs
docker logs -f browserpilot

# With timestamps
docker logs -t browserpilot
```

### Monitoring
```bash
# Resource usage
docker stats browserpilot

# Container inspection
docker inspect browserpilot
```