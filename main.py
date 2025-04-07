from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.endpoints import app as endpoints_app  # Import the app from endpoints

# Create FastAPI application instance
app = FastAPI(
    title="Mortgage Lending Assistant API",
    description="MVP API for Mortgage Lending Application",
    version="0.1.0"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://copilotstudio.microsoft.com", 
        "https://ispring.azurewebsites.net",
        "https://surajit-hackathon-d3bvddhmfnfkb5aw.canadacentral-01.azurewebsites.net"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the endpoints app
app.mount("/api", endpoints_app)

# Add root path handler
@app.get("/")
async def root():
    return {
        "message": "Mortgage Lending Assistant API",
        "version": "0.1.0",
        "documentation": "/docs",
        "status": "online"
    }

# Optional: Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Optional: If you want to run the app directly (for development)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)