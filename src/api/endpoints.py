"""
API Endpoints for Mortgage Lending System
Provides comprehensive REST API endpoints for mortgage application processing
"""

from fastapi import FastAPI, HTTPException, Body, APIRouter, Request
from typing import Dict, Any, Optional
import logging
import uuid
from datetime import datetime
from fastapi.responses import JSONResponse

# Remove specific dependencies
# from src.security.validation import validate_request
# from src.security.access_control import check_permissions

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
    """Submit a new mortgage application"""
    try:
        logger.info("Received new mortgage application submission")
        
        result = await application_actions.submit_application(
            application_data.get("applicant"),
            application_data.get("loan"),
            application_data.get("property"),
            application_data.get("employment", {}),
            application_data.get("financial", {})
        )
        
        return {
            "applicationId": result.get("application_id", str(uuid.uuid4())),
            "applicationStatus": result.get("status", "INITIATED"),
            "nextSteps": result.get("next_steps", []),
            "requiredDocuments": result.get("required_documents", []),
            "estimatedReviewTime": result.get("estimated_review_time", "1-2 business days")
        }
    except Exception as e:
        logger.error(f"Error submitting mortgage application: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

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
@router.post("/applications/{application_id}/documents/upload")
async def upload_documents(
    application_id: str,
    document_data: dict = Body(...)
):
    """Upload documents for a mortgage application"""
    try:
        logger.info(f"Received document upload request for application {application_id}")
        
        result = await document_actions.upload_document(
            application_id=application_id,
            document_type=document_data.get("documentType"),
            document_year=document_data.get("documentYear"),
            document_description=document_data.get("documentDescription"),
            document_format=document_data.get("documentFormat", "PDF"),
            document_content=document_data.get("documentContent", "")
        )
        
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

# Health Check Endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}