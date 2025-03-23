# src/api/endpoints.py
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Dict, Any, Optional

from src.copilot.actions.application_actions import ApplicationActions
from src.copilot.actions.document_actions import DocumentActions
from security.validation import validate_request
from security.access_control import check_permissions

app = FastAPI(title="Mortgage Lending Assistant API")
application_actions = ApplicationActions()
document_actions = DocumentActions()

# Existing endpoint
@app.post("/api/applications/new")
async def create_application(
    application_data: dict, 
    validated: bool = Depends(validate_request),
    authorized: bool = Depends(check_permissions)
):
    """Endpoint for creating a new application from Copilot Studio"""
    try:
        result = await application_actions.submit_application(
            application_data.get("applicant"),
            application_data.get("loan"),
            application_data.get("property")
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add the following new endpoints

@app.get("/api/applications/{application_id}")
async def check_application_status(
    application_id: str,
    validated: bool = Depends(validate_request),
    authorized: bool = Depends(check_permissions)
):
    """Check the status of an existing application"""
    try:
        result = await application_actions.check_application_status(application_id)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/applications/{application_id}/documents")
async def add_document(
    application_id: str,
    document_data: dict,
    validated: bool = Depends(validate_request),
    authorized: bool = Depends(check_permissions)
):
    """Add a document to an existing application"""
    try:
        result = await application_actions.provide_additional_documents(
            application_id,
            document_data.get("document_type"),
            document_data.get("document_content")
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/documents/validate")
async def validate_document(
    document_data: dict,
    validated: bool = Depends(validate_request),
    authorized: bool = Depends(check_permissions)
):
    """Validate a document before submission"""
    try:
        result = await document_actions.validate_document(
            document_data.get("document_type"),
            document_data.get("document_content")
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/requirements/{document_type}")
async def get_document_requirements(
    document_type: str,
    validated: bool = Depends(validate_request),
    authorized: bool = Depends(check_permissions)
):
    """Get requirements for a specific document type"""
    try:
        result = await document_actions.explain_document_requirements(document_type)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}