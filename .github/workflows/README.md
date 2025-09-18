# GitHub Actions Workflows

## Docker Build (`docker-build.yml`)

This workflow automatically builds and publishes the BrowserPilot Docker image when changes are merged to the main branch.

### Triggers
- **Push to main branch**: When code is merged to main, specifically when these files change:
  - `Dockerfile`
  - `docker-compose*.yml`
  - `backend/**`
  - `frontend/**`
  - `requirements.txt`
- **Pull Requests**: Builds (but doesn't push) images for PRs to test the build process
- **Manual trigger**: Can be run manually from the GitHub Actions tab

### What it does
1. **Builds the Docker image** using the multi-stage Dockerfile
2. **Publishes to GitHub Container Registry** (`ghcr.io`) with multiple tags:
   - `latest` (for main branch)
   - `main` (branch name)
   - `main-<sha>` (commit SHA)
3. **Multi-architecture support**: Builds for both `linux/amd64` and `linux/arm64`
4. **Caching**: Uses GitHub Actions cache for faster builds
5. **Security**: Generates build attestations for supply chain security

### Published Images
The Docker images are published to:
- `ghcr.io/veverkap/browserpilot:latest`
- `ghcr.io/veverkap/browserpilot:main`
- `ghcr.io/veverkap/browserpilot:main-<commit-sha>`

### Usage
Users can pull and run the published images:

```bash
# Pull the latest image
docker pull ghcr.io/veverkap/browserpilot:latest

# Run with Docker
docker run -p 8000:8000 -e GOOGLE_API_KEY=your_key ghcr.io/veverkap/browserpilot:latest

# Or use in docker-compose.yml
services:
  browserpilot:
    image: ghcr.io/veverkap/browserpilot:latest
    # ... other config
```

### Permissions Required
The workflow needs the following permissions (automatically granted):
- `contents: read` - To checkout the repository
- `packages: write` - To publish to GitHub Container Registry

### Optional: Docker Hub Integration
The workflow includes an optional step to update Docker Hub descriptions if you want to also publish to Docker Hub. To enable this:
1. Add `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets to your repository
2. The workflow will automatically update the Docker Hub repository description using `README.docker.md`