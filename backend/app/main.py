"""
FastAPI main application for Issue Tracker API.
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.exc import IntegrityError
from app import database
from app.routers import users, labels, issues, reports, imports

# Initialize database only if not in testing
import os
if os.environ.get("TESTING") != "true":
    database.init_db()

# Create FastAPI app
app = FastAPI(
    title="Issue Tracker API",
    description="Production-quality issue tracking system with optimistic locking, bulk operations, and reporting",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(IntegrityError)
async def integrity_error_handler(request, exc):
    """Handle database integrity errors."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Database constraint violation"}
    )


# Health check endpoint
@app.get("/health", tags=["health"])
def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok", "message": "Issue Tracker API is running"}


# Include routers
app.include_router(users.router)
app.include_router(labels.router)
app.include_router(issues.router)
app.include_router(reports.router)
app.include_router(imports.router)


# API documentation
@app.get("/", tags=["documentation"])
def root():
    """
    Welcome to Issue Tracker API.
    
    Visit /docs for interactive API documentation (Swagger UI)
    Visit /redoc for alternative documentation (ReDoc)
    """
    return {
        "message": "Welcome to Issue Tracker API",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "version": "1.0.0"
    }


# Redirect root to /docs for better user experience
@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    """Redirect root URL to API documentation"""
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
