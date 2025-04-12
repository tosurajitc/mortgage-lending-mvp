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
from fastapi import FastAPI

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
# Updated POST endpoint for checking application status
@router.post("/applications/status")
async def check_application_status(
    request_data: Dict[str, Any] = Body(...)
):
    """Check the status of an existing application"""
    try:
        logger.info("Received application status check request")
        
        # Extract required applicationId from request body
        application_id = request_data.get("applicationId")
        if not application_id:
            raise HTTPException(status_code=400, detail="applicationId is required")
            
        # Extract optional applicantName from request body
        applicant_name = request_data.get("applicantName")
        
        # Create the extra_context parameter if applicantName is provided
        extra_context = {"applicant_name": applicant_name} if applicant_name else None
        
        # Call the method with the correct parameters
        result = await application_actions.check_application_status(application_id, extra_context)
            
        if result.get("error"):
            raise HTTPException(status_code=404, detail=result["error"])
            
        # Format the response according to the required JSON structure
        return {
            "applicationId": application_id,
            "applicationStatus": result.get("status", "UNKNOWN").lower(),
            "currentStage": result.get("current_stage", "Processing"),
            "pendingItems": result.get("pending_items", []),
            "estimatedCompletion": result.get("estimated_completion", ""),
            "lastUpdated": result.get("last_updated", datetime.now(timezone.utc).isoformat()),
            "statusExplanation": result.get("status_explanation", "")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking application status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    


# 3. Upload Documents
# Updated document upload endpoint without application_id in URL
@router.post("/applications/documents/upload")
async def upload_documents(
    document_data: dict = Body(...)
):
    """
    Upload a document for a mortgage application using base64 encoded content.
    
    JSON Body Parameters:
    - applicationId: ID of the mortgage application
    - documentType: Type of document being uploaded (e.g., INCOME_VERIFICATION)
    - documentYear: Year the document is for (e.g., tax year) - optional
    - documentDescription: Optional description of the document
    - documentFormat: Format of the document (default: PDF)
    - documentContent: Base64 encoded document content
    
    Returns:
    - Upload status information and next steps
    """
    try:
        # Extract application ID from the body instead of URL
        application_id = document_data.get("applicationId")
        
        # Validate required fields
        if not application_id:
            raise HTTPException(status_code=400, detail="applicationId is required")
            
        if 'documentType' not in document_data:
            raise HTTPException(status_code=400, detail="documentType is required")
            
        if 'documentContent' not in document_data:
            raise HTTPException(status_code=400, detail="documentContent is required")
        
        logger.info(f"Processing document upload for application {application_id}, type: {document_data.get('documentType')}")
        
        # Call the document actions with the provided content
        result = await document_actions.upload_document(
            application_id=application_id,
            document_type=document_data.get("documentType"),
            document_year=document_data.get("documentYear"),
            document_description=document_data.get("documentDescription"),
            document_format=document_data.get("documentFormat", "PDF"),
            document_content=document_data.get("documentContent")
        )
        
        # Get next steps from the result
        next_steps = result.get("next_steps", ["Document received successfully"])
        
        # Create a string version of next steps for Copilot Studio
        next_steps_str = ", ".join(next_steps) if isinstance(next_steps, list) else str(next_steps)
        
        # Build the response
        response = {
            "applicationId": application_id,
            "uploadStatus": "SUCCESS" if not result.get("error") else "FAILED",
            "documentType": document_data.get("documentType"),
            "message": result.get("message", "Document uploaded successfully"),
            "nextSteps": next_steps,
            "output": next_steps_str
        }
        
        logger.info(f"Document upload successful for application {application_id}, type: {document_data.get('documentType')}")
        
        return response
        
    except HTTPException as he:
        raise he
        
    except Exception as e:
        # Extract application ID safely for error response
        application_id = document_data.get("applicationId", "UNKNOWN")
        
        logger.error(f"Error uploading document for application {application_id}: {str(e)}", exc_info=True)
        
        error_response = {
            "applicationId": application_id,
            "uploadStatus": "FAILED",
            "documentType": document_data.get("documentType", "UNKNOWN"),
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
        # Add silent validation without Pydantic
        required_fields = {
            'annualIncome': float,
            'creditScoreRange': str,
            'downPaymentPercentage': (float, int),
            'propertyType': str,
            'homeOwnershipPlans': str,
            'militaryService': str,
            'propertyLocation': str,
            'financialPriority': str
        }
        
        for field, field_type in required_fields.items():
            if field not in loan_criteria:
                logger.warning(f"Missing field: {field}")
            elif not isinstance(loan_criteria[field], field_type):
                if not (field_type == (float, int) and isinstance(loan_criteria[field], (float, int))):
                    logger.warning(f"Type mismatch in {field}. Expected {field_type}, got {type(loan_criteria[field])}")

        # Original unchanged processing ▼
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
        logger.error(f"Error in loan recommendations: {str(e)}", exc_info=True)
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
@router.post("/applications/issues/resolve")
async def resolve_mortgage_issues(
    issue_data: Dict[str, Any] = Body(...)
):
    """Resolve issues with a mortgage application"""
    try:
        # Extract application ID from the request body instead of the URL
        application_id = issue_data.get("applicationId")
        
        if not application_id:
            raise HTTPException(status_code=400, detail="Application ID is required")
            
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
# 1. Fix the customer inquiry endpoint to be consistent with other endpoints
@router.post("/applications/inquiries")
async def process_customer_inquiry(
    inquiry_data: Dict[str, Any] = Body(...)
):
    """Process customer inquiries about a specific application"""
    try:
        logger.info(f"Received customer inquiry")
        
        # Extract application ID from request body
        application_id = inquiry_data.get("applicationId")
        if not application_id:
            raise HTTPException(status_code=400, detail="Application ID is required")
        
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

# 2. Fix duplicated error handling in copilot_upload_document
@router.post("/copilot/upload-document")
async def copilot_upload_document(
    document_data: dict = Body(...)
):
    """
    Special endpoint for Copilot Studio to trigger document uploads.
    This endpoint doesn't actually upload files, but informs the user
    that they need to use the standard upload form.
    """
    try:
        # Extract application ID from the request body
        application_id = document_data.get("applicationId")
        
        if not application_id:
            return {
                "uploadStatus": "FAILED",
                "message": "Application ID is required",
                "nextSteps": ["Please provide a valid application ID"],
                "output": "Please provide a valid application ID to continue."
            }
            
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
            "uploadStatus": "FAILED",
            "message": f"Error: {str(e)}",
            "nextSteps": ["Please try again later"],
            "output": "An error occurred while processing your document upload request."
        }
        
        return error_response

# 8. Copilot Process Input Endpoint
# Updated Copilot document upload endpoint without application_id in URL
@router.post("/copilot/upload-document")
async def copilot_upload_document(
    document_data: dict = Body(...)
):
    """
    Special endpoint for Copilot Studio to trigger document uploads.
    This endpoint doesn't actually upload files, but informs the user
    that they need to use the standard upload form.
    """
    try:
        # Extract application ID from the request body
        application_id = document_data.get("applicationId")
        
        if not application_id:
            return {
                "uploadStatus": "FAILED",
                "message": "Application ID is required",
                "nextSteps": ["Please provide a valid application ID"],
                "output": "Please provide a valid application ID to continue."
            }
            
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
            "uploadStatus": "FAILED",
            "message": f"Error: {str(e)}",
            "nextSteps": ["Please try again later"],
            "output": "An error occurred while processing your document upload request."
        }
        
        return error_response


# Update Copilot Studio integration with fixed method call
@router.post("/copilot/process-input")
async def copilot_process_input(request: Request):
    """
    Universal endpoint for processing inputs from Copilot Studio
    """
    try:
        # Parse the incoming request body
        body = await request.json()
        
        # Log the raw payload for debugging
        logger.debug("Copilot Process Input - Raw Payload:")
        logger.debug(json.dumps(body, indent=2))
        
        # Handle potential 'output' wrapper
        payload = body.get('output', body)
        
        # Determine input type and route accordingly
        request_type = payload.get('request_type', '').lower()
        
        logger.info(f"Request Type Detected: {request_type}")
        
        if request_type == 'submit_application':
            return await submit_mortgage_application(payload)
        elif request_type == 'upload_document':
            # Just pass the payload directly since the upload endpoint now expects the full payload
            return await upload_documents(payload)
        elif request_type == 'check_status':
            # Route to our application status endpoint
            return await check_application_status(payload)
        else:
            logger.warning(f"Unsupported request type: {request_type}")
            return {
                "error": "Unsupported request type",
                "received_type": request_type,
                "received_payload": payload
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


# Update the dedicated Copilot endpoint for application status
@router.post("/copilot/application-status")
async def copilot_application_status(request_data: Dict[str, Any] = Body(...)):
    """
    Dedicated endpoint for Copilot Studio to check application status
    """
    try:
        logger.info("Received Copilot application status check request")
        
        # Extract required applicationId
        application_id = request_data.get("applicationId")
        if not application_id:
            return {
                "error": "applicationId is required",
                "applicationStatus": "ERROR",
                "statusExplanation": "Please provide a valid application ID"
            }
            
        # Extract optional applicantName
        applicant_name = request_data.get("applicantName")
        
        # Create extra_context if applicantName is provided
        extra_context = {"applicant_name": applicant_name} if applicant_name else None
        
        # Get application status with the correct parameters
        result = await application_actions.check_application_status(application_id, extra_context)
        
        # Format the response for Copilot Studio
        if result.get("error"):
            return {
                "error": result["error"],
                "applicationStatus": "NOT_FOUND",
                "statusExplanation": f"Application with ID {application_id} not found"
            }
            
        return {
            "applicationId": application_id,
            "applicationStatus": result.get("status", "UNKNOWN").lower(),
            "currentStage": result.get("current_stage", "Processing"),
            "pendingItems": result.get("pending_items", []),
            "estimatedCompletion": result.get("estimated_completion", ""),
            "lastUpdated": result.get("last_updated", datetime.now(timezone.utc).isoformat()),
            "statusExplanation": result.get("status_explanation", "")
        }
    except Exception as e:
        logger.error(f"Error checking application status for Copilot: {str(e)}", exc_info=True)
        return {
            "error": str(e),
            "applicationStatus": "ERROR",
            "statusExplanation": "An error occurred while checking the application status"
        }