"""
Main FastAPI application for Generative UI Browser Backend
"""

from dotenv import load_dotenv
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from datetime import datetime

from .api.routes.generate import router as generate_router
from .api.routes.scrape import router as scrape_router
from app.api.routes.refine import router as refine_router
from app.api.routes.entity_matcher import router as entity_matcher_router

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
if api_key:
    print(f"✓ API Key loaded")
else:
    print("✗ Warning: No API key found!")

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""

    app = FastAPI(
        title="Generative UI Browser Backend",
        description="Backend API for generating custom UIs from web content",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Initialize rate limiter
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Add rate limiting middleware
    app.add_middleware(SlowAPIMiddleware)

    # Custom exception handler for rate limiting
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        """
        Custom handler for rate limit exceeded errors.

        Args:
            request: FastAPI request object
            exc: Rate limit exceeded exception

        Returns:
            JSONResponse: Error response with retry information
        """
        response = JSONResponse(
            status_code=429,
            content={
                "error": "Rate Limit Exceeded",
                "detail": "Too many requests. Please try again later.",
                "url": str(request.url),
                "timestamp": datetime.now().isoformat()
            }
        )

        # Add Retry-After header
        retry_after = getattr(exc, 'retry_after', 60)
        response.headers["Retry-After"] = str(retry_after)

        return response

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(
        generate_router,
        prefix="/api",
        tags=["generation"]
    )
    
    # Configure rate limiter for scrape router
    scrape_limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = scrape_limiter
    
    app.include_router(
        scrape_router,
        prefix="/api",
        tags=["scraping"]
    )
    app.include_router(refine_router, prefix="/api", tags=["refine"])
    app.include_router(entity_matcher_router, prefix="/api", tags=["entity-matching"])

    return app


# Create the app instance
app = create_app()


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with API information"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Generative UI Browser Backend</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 2rem;
                line-height: 1.6;
            }
            .container {
                background: #f8f9fa;
                padding: 2rem;
                border-radius: 8px;
                margin: 1rem 0;
            }
            .endpoint {
                background: #e9ecef;
                padding: 1rem;
                margin: 0.5rem 0;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
            }
            .method {
                color: #007bff;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Generative UI Browser Backend</h1>
            <p>Welcome to the backend API for the Generative UI Browser. This service analyzes web content and generates custom user interfaces.</p>

            <h2>Available Endpoints</h2>

            <div class="endpoint">
                <span class="method">POST</span> /api/generate
                <br>Generate a custom UI for a given URL
            </div>

            <div class="endpoint">
                <span class="method">POST</span> /api/scrape
                <br>Scrape content from a web URL (rate limited)
            </div>

            <div class="endpoint">
                <span class="method">GET</span> /api/scrape/health
                <br>Scraping service health check
            </div>

            <div class="endpoint">
                <span class="method">GET</span> /api/health
                <br>General health check endpoint
            </div>

            <div class="endpoint">
                <span class="method">GET</span> /docs
                <br>Interactive API documentation (Swagger UI)
            </div>

            <h2>🔧 Configuration</h2>
            <p>Set the following environment variables:</p>
            <ul>
                <li><code>OPENROUTER_API_KEY</code> - For Claude LLM access</li>
                <li><code>OPENAI_API_KEY</code> - For GPT LLM access</li>
            </ul>

            <h2>🚀 Getting Started</h2>
            <ol>
                <li>Set your LLM API keys</li>
                <li>Start the server: <code>uvicorn app.main:app --reload</code></li>
                <li>Open <a href="/docs">/docs</a> for interactive API testing</li>
            </ol>
        </div>
    </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "generative-ui-backend",
        "version": "0.1.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
