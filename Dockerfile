# Multi-stage Dockerfile for BrowserPilot
# Stage 1: Build the React frontend
FROM node:20-alpine AS frontend-builder

# Set working directory for frontend
WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install all dependencies (including dev dependencies needed for build)
RUN npm config set strict-ssl false && npm install

# Copy frontend source code
COPY frontend/ ./

# Build the frontend
RUN npm run build

# Stage 2: Use Playwright's official Docker image with Python (Ubuntu-based)
FROM mcr.microsoft.com/playwright/python:v1.53.0-jammy

# Set working directory
WORKDIR /app

# Copy Python requirements and install dependencies
COPY requirements.txt .
# Install compatible versions of numpy and pandas for Python 3.10
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --no-cache-dir \
    fastapi==0.111.0 \
    uvicorn[standard]==0.29.0 \
    playwright==1.53.0 \
    google-generativeai==0.5.0 \
    pydantic==2.7.1 \
    bs4==0.0.2 \
    lxml==5.2.1 \
    markdownify==0.11.6 \
    "numpy>=1.24.0,<2.3.0" \
    "pandas>=2.0.0,<2.3.0" \
    python-dateutil==2.9.0.post0 \
    pytz==2025.2 \
    tzdata==2025.2 \
    reportlab==4.4.2

# Copy backend source code
COPY backend/ ./backend/

# Copy built frontend from the frontend-builder stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/

# Create outputs directory
RUN mkdir -p outputs

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose the port the app runs on
EXPOSE 8000

# Create a non-root user for security (the playwright image already has pwuser)
RUN chown -R pwuser:pwuser /app
USER pwuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]