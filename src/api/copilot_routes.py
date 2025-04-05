# src/api/copilot_routes.py
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
import uuid

# Configure logging
from src.utils.logging_utils import get_logger
logger = get_logger("copilot_routes")

# Create router
copilot_router = APIRouter()

@copilot_router.get("/test-connection")
async def test_copilot_connection():
    """Simple test endpoint for Copilot Studio connectivity"""
    logger.info("Test connection endpoint called")
    return {
        "status": "connected",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Copilot Studio connection is working properly",
        "test_id": str(uuid.uuid4())
    }

@copilot_router.post("/process-input")
async def process_copilot_input(request: Request):
    """Basic process input endpoint"""
    try:
        body = await request.json()
        user_input = body.get("userInput", "")
        session_id = body.get("sessionId", str(uuid.uuid4()))
        
        logger.info(f"Received input: {user_input[:50]}... for session {session_id}")
        
        # Simple echo response for testing
        return {
            "response": f"You said: {user_input}",
            "sessionId": session_id,
            "context": {}
        }
    except Exception as e:
        logger.error(f"Error processing input: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "message": "An error occurred processing your request"}
        )