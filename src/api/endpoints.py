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
from src.api.copilot_routes import copilot_router




app = FastAPI(title="Mortgage Lending Assistant API")
app.include_router(copilot_router, prefix="/copilot", tags=["Copilot Studio"])
application_actions = ApplicationActions()
document_actions = DocumentActions()

# Configure logging
logger = get_logger("api_endpoints")

router = APIRouter()


@router.post("/copilot/submit-application")
async def submit_application(request: Request):
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
async def get_application_status(application_id: str):
    orchestrator = OrchestratorAgent()
    result = await orchestrator.process({
        "action": "check_status",
        "application_id": application_id
    })
    
    return result

# 1. SubmitMortgageApplication
@app.post("/api/applications/submit")
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
@app.get("/api/applications/{application_id}/status")
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

# 3. UploadDocuments
@app.post("/api/applications/{application_id}/documents/upload")
async def upload_documents(
    application_id: str,
    document_data: dict = Body(...),
    validated: bool = Depends(validate_request),
    authorized: bool = Depends(check_permissions)
):
    """Upload documents for a mortgage application"""
    try:
        logger.info(f"Received document upload request for application {application_id}")
        
        result = await document_actions.upload_document(
            application_id=application_id,
            document_type=document_data.get("documentType"),
            document_year=document_data.get("documentYear"),
            document_description=document_data.get("documentDescription"),
            document_format=document_data.get("documentFormat"),
            document_content=document_data.get("documentContent", "")
        )
        
        # Format response specifically for Copilot Studio action
        return {
            "applicationId": application_id,
            "uploadStatus": "SUCCESS" if not result.get("error") else "FAILED",
            "documentType": document_data.get("documentType", ""),
            "message": result.get("message", "Document uploaded successfully"),
            "nextSteps": result.get("next_steps", [])
        }
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# 4. LoanTypeRecommendation
@app.post("/api/loan/recommendations")
async def loan_type_recommendation(
    loan_criteria: Dict[str, Any] = Body(...),
    validated: bool = Depends(validate_request),
    authorized: bool = Depends(check_permissions)
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
        
        # Format response for Copilot Studio action
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

# 5. ResolveMortgageIssues
@app.post("/api/applications/{application_id}/issues/resolve")
async def resolve_mortgage_issues(
    application_id: str,
    issue_data: Dict[str, Any] = Body(...),
    validated: bool = Depends(validate_request),
    authorized: bool = Depends(check_permissions)
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
        
        # Format response for Copilot Studio action
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

# 6. LoanEligibilityCalculation
@app.post("/api/loan/eligibility")
async def loan_eligibility_calculation(
    financial_data: Dict[str, Any] = Body(...),
    validated: bool = Depends(validate_request),
    authorized: bool = Depends(check_permissions)
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
        
        # Format response for Copilot Studio action
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

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}








# Add these handler functions to your endpoints.py file where the syntax errors are occurring

async def handle_document_upload_request(payload):
    """Handle document upload requests from Copilot Studio"""
    application_id = payload.get("applicationId", "")
    document_type = payload.get("documentType", "")
    document_content = payload.get("documentContent", "")
    document_description = payload.get("documentDescription", "")
    
    # Use orchestrator or document actions
    orchestrator = OrchestratorAgent()
    result = await orchestrator.process({
        "action": "update_application",
        "update_type": "new_documents",
        "application_id": application_id,
        "documents": [{
            "document_type": document_type,
            "document_description": document_description,
            "content": document_content
        }]
    })
    
    # Format response for Copilot Studio
    return {
        "applicationId": application_id,
        "uploadStatus": "SUCCESS" if not result.get("error") else "FAILED",
        "documentType": document_type,
        "message": result.get("message", "Document uploaded successfully"),
        "nextSteps": result.get("next_steps", [])
    }

async def handle_loan_recommendation_request(payload):
    """Handle loan recommendation requests from Copilot Studio"""
    # Extract loan criteria
    annual_income = payload.get("annualIncome")
    credit_score_range = payload.get("creditScoreRange")
    down_payment_percentage = payload.get("downPaymentPercentage")
    property_type = payload.get("propertyType")
    
    # Use orchestrator or application actions
    orchestrator = OrchestratorAgent()
    result = await orchestrator.process({
        "action": "handle_customer_inquiry",
        "request_type": "loan_recommendation",
        "loan_criteria": {
            "annual_income": annual_income,
            "credit_score_range": credit_score_range,
            "down_payment_percentage": down_payment_percentage,
            "property_type": property_type,
            "home_ownership_plans": payload.get("homeOwnershipPlans"),
            "military_service": payload.get("militaryService", False),
            "property_location": payload.get("propertyLocation"),
            "financial_priority": payload.get("financialPriority")
        }
    })
    
    # Format response for Copilot Studio
    return {
        "recommendedLoanTypes": result.get("recommended_loan_types", []),
        "primaryRecommendation": result.get("primary_recommendation", ""),
        "explanation": result.get("explanation", ""),
        "eligibility": result.get("eligibility", {}),
        "nextSteps": result.get("next_steps", [])
    }

async def handle_eligibility_calculation_request(payload):
    """Handle loan eligibility calculation requests from Copilot Studio"""
    # Extract financial data
    annual_income = payload.get("annualIncome")
    monthly_debts = payload.get("monthlyDebts")
    credit_score_range = payload.get("creditScoreRange")
    employment_status = payload.get("employmentStatus")
    
    # Use orchestrator or application actions
    orchestrator = OrchestratorAgent()
    result = await orchestrator.process({
        "action": "handle_customer_inquiry",
        "request_type": "eligibility_check",
        "financial_data": {
            "annual_income": annual_income,
            "monthly_debts": monthly_debts,
            "credit_score_range": credit_score_range,
            "employment_status": employment_status,
            "down_payment_amount": payload.get("downPaymentAmount"),
            "loan_term_years": payload.get("loanTermYears", 30),
            "property_type": payload.get("propertyType", "SINGLE_FAMILY"),
            "property_location": payload.get("propertyLocation")
        }
    })
    
    # Format response for Copilot Studio
    return {
        "eligibilityStatus": result.get("eligibility_status", ""),
        "maximumLoanAmount": result.get("maximum_loan_amount", 0),
        "estimatedMonthlyPayment": result.get("estimated_monthly_payment", 0),
        "eligibilityFactors": result.get("eligibility_factors", {}),
        "recommendedActions": result.get("recommended_actions", []),
        "affordabilityAnalysis": result.get("affordability_analysis", {})
    }

async def handle_issue_resolution_request(payload):
    """Handle issue resolution requests from Copilot Studio"""
    application_id = payload.get("applicationId", "")
    issue_type = payload.get("issueType", "")
    issue_description = payload.get("issueDescription", "")
    
    # Use orchestrator or application actions
    orchestrator = OrchestratorAgent()
    result = await orchestrator.process({
        "action": "handle_customer_inquiry",
        "request_type": "issue_resolution",
        "application_id": application_id,
        "issue_data": {
            "issue_type": issue_type,
            "issue_description": issue_description,
            "contact_preference": payload.get("contactPreference", "EMAIL"),
            "urgency_level": payload.get("urgencyLevel", "MEDIUM")
        }
    })
    
    # Format response for Copilot Studio
    return {
        "applicationId": application_id,
        "caseNumber": result.get("case_number", f"CASE-{uuid.uuid4().hex[:6].upper()}"),
        "resolutionSteps": result.get("resolution_steps", []),
        "estimatedResolutionTime": result.get("estimated_resolution_time", ""),
        "message": result.get("message", "")
    }

async def handle_user_input(payload):
    """Handle general user input from Copilot Studio"""
    user_input = payload.get("userInput", "")
    session_id = payload.get("sessionId", str(uuid.uuid4()))
    context = payload.get("context", {})
    
    # Use orchestrator
    orchestrator = OrchestratorAgent()
    result = await orchestrator.process({
        "action": "handle_customer_inquiry",
        "request_type": "conversation",
        "user_input": user_input,
        "session_id": session_id,
        "conversation_context": context
    })
    
    # Format response for Copilot Studio
    return {
        "response": result.get("response", "I'm sorry, I couldn't process your request."),
        "context": result.get("updated_context", {}),
        "nextActions": result.get("next_actions", []),
        "requiredInfo": result.get("required_info", []),
        "sessionId": session_id
    }


# Add this to your endpoints.py file (at the end)

# Create a dedicated router for Copilot Studio
copilot_router = APIRouter(prefix="/copilot", tags=["Copilot Studio Integration"])
app.include_router(copilot_router)

@copilot_router.post("/process-input")
async def process_copilot_input(request: Request):
    """
    Process conversational input from Copilot Studio
    """
    try:
        # Extract request data
        body = await request.json()
        user_input = body.get("userInput", "")
        session_id = body.get("sessionId", str(uuid.uuid4()))
        context = body.get("context", {})
        
        # Log the interaction
        logger.info(f"Processing user input: '{user_input[:50]}...' for session {session_id}")
        
        # Process with orchestrator
        orchestrator = OrchestratorAgent()
        result = await orchestrator.process({
            "action": "handle_customer_inquiry",
            "request_type": "conversation",
            "user_input": user_input,
            "session_id": session_id,
            "conversation_context": context
        })
        
        # Format response
        return {
            "response": result.get("response", "I'm sorry, I couldn't process that request."),
            "context": result.get("updated_context", {}),
            "nextActions": result.get("next_actions", []),
            "requiredInfo": result.get("required_info", []),
            "sessionId": session_id
        }
            
    except Exception as e:
        logger.error(f"Error processing user input: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "response": "I'm sorry, but I'm experiencing a technical issue. Please try again in a moment.",
                "error": str(e),
                "sessionId": str(uuid.uuid4()),
                "context": {}
            }
        )

# Add a test endpoint for Copilot Studio connectivity testing
@copilot_router.get("/test-connection")
async def test_copilot_connection():
    """Test endpoint for Copilot Studio integration"""
    return {
        "status": "connected",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Copilot Studio connection is working properly",
        "test_id": str(uuid.uuid4())
    }