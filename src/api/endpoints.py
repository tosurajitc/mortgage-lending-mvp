"""
API Endpoints for Mortgage Lending System
Provides comprehensive REST API endpoints for mortgage application processing
"""

from fastapi import FastAPI, HTTPException, Body, APIRouter, Request, File, UploadFile, Form
from typing import Dict, Any, Optional
import logging
import uuid
import json
from datetime import datetime, timezone
from fastapi.responses import JSONResponse

# Import from your existing architecture
from src.copilot.actions.application_actions import ApplicationActions
from src.copilot.actions.document_actions import DocumentActions
from src.utils.logging_utils import get_logger

# Create a router
router = APIRouter()

# Configure logging
logger = get_logger("api_endpoints")

# Initialize action handlers
application_actions = ApplicationActions()
document_actions = DocumentActions()

# 1. Submit Mortgage Application
@router.post("/applications/submit")
async def submit_mortgage_application(application_data: dict):
    try:
        result = await application_actions.submit_application(
            applicantName=application_data.get("applicantName", ""),
            applicantEmail=application_data.get("applicantEmail", ""),
            applicantPhone=application_data.get("applicantPhone", ""),
            applicantAddress=application_data.get("applicantAddress", ""),
            applicantSSN=application_data.get("applicantSSN", ""),
            propertyType=application_data.get("propertyType", ""),
            propertyAddress=application_data.get("propertyAddress", ""),
            propertyValue=application_data.get("propertyValue", 0),
            loanAmount=application_data.get("loanAmount", 0),
            employmentStatus=application_data.get("employmentStatus", ""),
            employmentType=application_data.get("employmentType", ""),
            employmentLength=application_data.get("employmentLength", ""),
            annualIncome=application_data.get("annualIncome", 0),
            creditScoreRange=application_data.get("creditScoreRange", ""),
            existingMortgages=application_data.get("existingMortgages", None)
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Endpoint error: {str(e)}")
        return {
            "applicationId": str(uuid.uuid4()),
            "applicationStatus": "ERROR",
            "nextSteps": [],
            "requiredDocuments": [],
            "estimatedReviewTime": "Unable to determine"
        }




# 2. Check Application Status
@router.get("/applications/{application_id}/status")
async def check_application_status(
    application_id: str,
    applicant_name: Optional[str] = None
):
    """Check the status of an existing application"""
    try:
        logger.info(f"Received status check request for application {application_id}")
        
        # Add a default applicant name if not provided
        if not applicant_name:
            applicant_name = "Applicant"
        
        result = await application_actions.check_application_status(
            application_id, 
            {"applicant_name": applicant_name}
        )
            
        if result.get("error"):
            raise HTTPException(status_code=404, detail=result["error"])
            
        return {
            "applicationId": application_id,
            "applicationStatus": result.get("status", "UNKNOWN"),
            "currentStage": result.get("current_stage", "Processing"),
            "pendingItems": result.get("pending_items", []),
            "estimatedCompletion": result.get("estimated_completion", ""),
            "lastUpdated": result.get("last_updated", ""),
            "statusExplanation": result.get("status_explanation", "")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking application status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# 3. Upload Documents
# Simplified document upload endpoint
@router.post("/applications/{application_id}/documents/upload")
async def upload_documents(
    application_id: str,
    document_type: str = Form(...),
    document_year: Optional[str] = Form(None),
    document_description: Optional[str] = Form(None),
    document_format: str = Form("PDF"),
    file: UploadFile = File(...)
):
    """
    Upload a document for a mortgage application.
    
    Parameters:
    - application_id: ID of the mortgage application
    - document_type: Type of document being uploaded (e.g., INCOME_VERIFICATION)
    - document_year: Year the document is for (e.g., tax year)
    - document_description: Optional description of the document
    - document_format: Format of the document (default: PDF)
    - file: The actual document file to upload
    
    Returns:
    - Upload status information and next steps
    """
    try:
        logger.info(f"Processing document upload for application {application_id}, type: {document_type}")
        
        # Read file content
        content = await file.read()
        
        # Convert to base64 for internal processing
        import base64
        document_content = base64.b64encode(content).decode('utf-8')
        
        # Call the document actions with the file content
        result = await document_actions.upload_document(
            application_id=application_id,
            document_type=document_type,
            document_year=document_year,
            document_description=document_description,
            document_format=document_format,
            document_content=document_content
        )
        
        # Get next steps from the result
        next_steps = result.get("next_steps", ["Document received successfully"])
        
        # Create a string version of next steps for Copilot Studio
        next_steps_str = ", ".join(next_steps) if isinstance(next_steps, list) else str(next_steps)
        
        # Build the response
        response = {
            "applicationId": application_id,
            "uploadStatus": "SUCCESS" if not result.get("error") else "FAILED",
            "documentType": document_type,
            "message": result.get("message", "Document uploaded successfully"),
            "nextSteps": next_steps,
            "output": next_steps_str
        }
        
        logger.info(f"Document upload successful for application {application_id}, type: {document_type}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}", exc_info=True)
        
        error_response = {
            "applicationId": application_id,
            "uploadStatus": "FAILED",
            "documentType": document_type,
            "message": f"Error: {str(e)}",
            "nextSteps": ["Please try uploading again", "Contact support if the issue persists"],
            "output": "Error occurred during document upload"
        }
        
        return error_response

# 4. Loan Type Recommendation
@router.post("/loan/recommendations")
async def loan_type_recommendation(
    loan_criteria: Dict[str, Any] = Body(...)
):
    """Get loan type recommendations based on applicant criteria"""
    try:
        logger.info("Received loan type recommendation request")
        
        result = await application_actions.recommend_loan_types(
            annual_income=loan_criteria.get("annualIncome"),
            credit_score_range=loan_criteria.get("creditScoreRange"),
            down_payment_percentage=loan_criteria.get("downPaymentPercentage"),
            property_type=loan_criteria.get("propertyType"),
            homeownership_plans=loan_criteria.get("homeOwnershipPlans"),
            military_service=loan_criteria.get("militaryService"),
            property_location=loan_criteria.get("propertyLocation"),
            financial_priority=loan_criteria.get("financialPriority")
        )
        
        return {
            "recommendedLoanTypes": result.get("recommended_loan_types", []),
            "primaryRecommendation": result.get("primary_recommendation", ""),
            "explanation": result.get("explanation", ""),
            "eligibility": result.get("eligibility", {}),
            "nextSteps": result.get("next_steps", [])
        }
    except Exception as e:
        logger.error(f"Error getting loan type recommendations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# 5. Loan Eligibility Calculation
@router.post("/loan/eligibility")
async def loan_eligibility_calculation(
    financial_data: Dict[str, Any] = Body(...)
):
    """Calculate loan eligibility and pre-approval amount"""
    try:
        logger.info("Received loan eligibility calculation request")
        
        result = await application_actions.calculate_loan_eligibility(
            annual_income=financial_data.get("annualIncome"),
            monthly_debts=financial_data.get("monthlyDebts"),
            credit_score_range=financial_data.get("creditScoreRange"),
            employment_status=financial_data.get("employmentStatus"),
            down_payment_amount=financial_data.get("downPaymentAmount"),
            loan_term_years=financial_data.get("loanTermYears"),
            property_type=financial_data.get("propertyType"),
            property_location=financial_data.get("propertyLocation")
        )
        
        return {
            "eligibilityStatus": result.get("eligibility_status", ""),
            "maximumLoanAmount": result.get("maximum_loan_amount", 0),
            "estimatedMonthlyPayment": result.get("estimated_monthly_payment", 0),
            "eligibilityFactors": result.get("eligibility_factors", {}),
            "recommendedActions": result.get("recommended_actions", []),
            "affordabilityAnalysis": result.get("affordability_analysis", {})
        }
    except Exception as e:
        logger.error(f"Error calculating loan eligibility: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# 6. Resolve Mortgage Issues
@router.post("/applications/{application_id}/issues/resolve")
async def resolve_mortgage_issues(
    application_id: str,
    issue_data: Dict[str, Any] = Body(...)
):
    """Resolve issues with a mortgage application"""
    try:
        logger.info(f"Received issue resolution request for application {application_id}")
        
        result = await application_actions.resolve_issue(
            application_id=application_id,
            issue_type=issue_data.get("issueType"),
            issue_description=issue_data.get("issueDescription"),
            contact_preference=issue_data.get("contactPreference"),
            urgency_level=issue_data.get("urgencyLevel")
        )
        
        return {
            "applicationId": application_id,
            "caseNumber": result.get("case_number", f"CASE-{uuid.uuid4().hex[:6].upper()}"),
            "resolutionSteps": result.get("resolution_steps", []),
            "estimatedResolutionTime": result.get("estimated_resolution_time", ""),
            "message": result.get("message", "")
        }
    except Exception as e:
        logger.error(f"Error resolving mortgage issue: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# 7. Customer Inquiry
@router.post("/applications/{application_id}/inquiries")
async def process_customer_inquiry(
    application_id: str,
    inquiry_data: Dict[str, Any] = Body(...)
):
    """Process customer inquiries about a specific application"""
    try:
        logger.info(f"Received inquiry for application {application_id}")
        
        result = await application_actions.process_customer_inquiry(
            application_id=application_id,
            inquiry_text=inquiry_data.get("inquiryText"),
            inquiry_category=inquiry_data.get("inquiryCategory"),
            contact_preference=inquiry_data.get("contactPreference")
        )
        
        return {
            "applicationId": application_id,
            "response": result.get("response", ""),
            "requiresHumanFollowUp": result.get("requires_human_follow_up", False),
            "recommendedFollowUp": result.get("recommended_follow_up", "")
        }
    except Exception as e:
        logger.error(f"Error processing customer inquiry: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# 8. Copilot Process Input Endpoint
# Special route for Copilot Studio document uploads
@router.post("/copilot/upload-document/{application_id}")
async def copilot_upload_document(
    application_id: str,
    document_data: dict = Body(...)
):
    """
    Special endpoint for Copilot Studio to trigger document uploads.
    This endpoint doesn't actually upload files, but informs the user
    that they need to use the standard upload form.
    """
    try:
        logger.info(f"Copilot document upload request for application {application_id}")
        
        # Extract document information from the request
        document_type = document_data.get("documentType", "")
        document_year = document_data.get("documentYear")
        document_description = document_data.get("documentDescription")
        
        # Create a response with instructions for uploading
        response = {
            "applicationId": application_id,
            "uploadStatus": "PENDING",
            "documentType": document_type,
            "message": "Please upload the document file using our secure document upload form.",
            "nextSteps": [
                "Go to the document upload page",
                f"Select document type: {document_type}",
                "Choose the file from your device",
                "Click 'Upload' to complete the process"
            ],
            "output": "Please upload the actual document file using our secure document upload form."
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error handling Copilot document upload request: {str(e)}", exc_info=True)
        
        error_response = {
            "applicationId": application_id,
            "uploadStatus": "FAILED",
            "message": f"Error: {str(e)}",
            "nextSteps": ["Please try again later"],
            "output": "An error occurred while processing your document upload request."
        }
        
        return error_response

# Update Copilot Process Input Endpoint
@router.post("/copilot/process-input")
async def copilot_process_input(request: Request):
    """
    Universal endpoint for processing inputs from Copilot Studio
    """
    try:
        # Parse the incoming request body
        body = await request.json()
        
        # Log the payload for debugging
        logger.info("Copilot Process Input - Raw Payload:")
        logger.info(json.dumps(body, indent=2))
        
        # Handle potential 'output' wrapper
        payload = body.get('output', body)
        
        # Determine input type and route accordingly
        request_type = payload.get('request_type', '').lower()
        
        logger.info(f"Request Type Detected: {request_type}")
        
        if request_type == 'submit_application':
            return await submit_mortgage_application(payload)
        elif request_type == 'upload_document':
            # For document uploads through Copilot, use the special handler
            application_id = payload.get('application_id', '')
            return await copilot_upload_document(application_id, payload)
        elif request_type == 'check_status':
            return await check_application_status(payload.get('application_id'))
        else:
            logger.warning(f"Unsupported request type: {request_type}")
            return {
                "error": "Unsupported request type",
                "received_type": request_type,
                "supported_types": ["submit_application", "upload_document", "check_status"]
            }
    except Exception as e:
        logger.error(f"Copilot processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# 9. Copilot Test Connection
@router.get("/copilot/test-connection")
async def copilot_test_connection():
    """
    Simple health check for Copilot Studio connection
    """
    return {
        "status": "healthy",
        "service": "Mortgage Lending Assistant",
        "copilot_ready": True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# Health Check Endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}