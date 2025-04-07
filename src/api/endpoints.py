"""
API Endpoints for Mortgage Lending System
Provides REST API endpoints aligned with Copilot Studio actions
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Body, APIRouter, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import uuid
from datetime import datetime
from fastapi.responses import JSONResponse

# Import from your existing architecture
from src.copilot.actions.application_actions import ApplicationActions
from src.copilot.actions.document_actions import DocumentActions
from src.utils.logging_utils import get_logger
from src.security.validation import validate_request
from src.security.access_control import check_permissions
from src.agents.orchestrator import OrchestratorAgent

# Create a router instead of an app
router = APIRouter()

# Configure logging
logger = get_logger("api_endpoints")

application_actions = ApplicationActions()
document_actions = DocumentActions()

# 1. SubmitMortgageApplication
@router.post("/applications/submit")
async def submit_mortgage_application(
    application_data: dict, 
    validated: bool = Depends(validate_request),
    authorized: bool = Depends(check_permissions)
):
    """Submit a new mortgage application from Copilot Studio"""
    try:
        logger.info("Received new mortgage application submission")
        
        result = await application_actions.submit_application(
            application_data.get("applicant"),
            application_data.get("loan"),
            application_data.get("property"),
            application_data.get("employment", {}),
            application_data.get("financial", {})
        )
        
        # Format response for Copilot Studio
        return {
            "applicationId": result.get("application_id", ""),
            "applicationStatus": result.get("status", "INITIATED"),
            "nextSteps": result.get("next_steps", []),
            "requiredDocuments": result.get("required_documents", []),
            "estimatedReviewTime": result.get("estimated_review_time", "1-2 business days")
        }
    except Exception as e:
        logger.error(f"Error submitting mortgage application: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# 2. CheckApplicationStatus
@router.get("/applications/{application_id}/status")
async def check_application_status(
    application_id: str,
    applicant_name: str,
    validated: bool = Depends(validate_request),
    authorized: bool = Depends(check_permissions)
):
    """Check the status of an existing application"""
    try:
        logger.info(f"Received status check request for application {application_id}")
        
        # Call with applicant name for verification
        result = await application_actions.check_application_status(
            application_id, 
            {"applicant_name": applicant_name}
        )
            
        if result.get("error"):
            raise HTTPException(status_code=404, detail=result["error"])
            
        # Format the response specifically for Copilot Studio action
        response = {
            "applicationId": application_id,
            "applicationStatus": result.get("status", "UNKNOWN"),
            "currentStage": result.get("current_stage", "Processing"),
            "pendingItems": result.get("pending_items", []),
            "estimatedCompletion": result.get("estimated_completion", ""),
            "lastUpdated": result.get("last_updated", ""),
            "statusExplanation": result.get("status_explanation", "")
        }
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking application status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Include other existing routes like document upload, loan recommendations, etc.
# (keep the other routes from the original file)

# For Copilot Studio specific routes
@router.post("/copilot/submit-application")
async def copilot_submit_application(request: Request):
    # Extract payload from Copilot Studio
    payload = await request.json()
    
    # Use Orchestrator Agent to process
    orchestrator = OrchestratorAgent()
    result = await orchestrator.process({
        "action": "process_application",
        "application_data": payload
    })
    
    return result

@router.get("/copilot/application-status/{application_id}")
async def copilot_get_application_status(application_id: str):
    orchestrator = OrchestratorAgent()
    result = await orchestrator.process({
        "action": "check_status",
        "application_id": application_id
    })
    
    return result

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}