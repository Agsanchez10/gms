from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from config import settings
from database import init_db
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Gym Management System API",
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"⚠️ Database connection failed (this is OK for development): {e}")
        logger.warning("The server will continue running, but database operations will fail until PostgreSQL is configured.")


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Gym Management System API is running"}


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "application": "Gym Management System API",
        "version": settings.api_version,
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


# Import and include routers
from routes import members, staff, classes, machines, usage, plans, manager, trainer, memberships

app.include_router(members.router, prefix="/api/v1/members", tags=["Members"])
app.include_router(staff.router, prefix="/api/v1/staff", tags=["Staff"])
app.include_router(classes.router, prefix="/api/v1/classes", tags=["Classes"])
app.include_router(machines.router, prefix="/api/v1/machines", tags=["Machines"])
app.include_router(usage.router, prefix="/api/v1", tags=["Machine Usage"])
app.include_router(plans.router, prefix="/api/v1/plans", tags=["Member Plans"])
app.include_router(memberships.router, prefix="/api/v1/memberships", tags=["Memberships"])
app.include_router(manager.router, prefix="/api/v1/manager", tags=["Manager Dashboard"])
app.include_router(trainer.router, prefix="/api/v1/trainer", tags=["Trainer Dashboard"])


# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions"""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
