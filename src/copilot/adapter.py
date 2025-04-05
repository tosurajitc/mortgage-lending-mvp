# src/copilot/adapter.py

from typing import Dict, Any, Optional
from fastapi import Request
import json
import logging
from src.utils.logging_utils import get_logger
from datetime import datetime
import uuid

# Import your schemas
from src.api.schemas import (
    CopilotUserInputRequest, CopilotUserInputResponse,
    CopilotUploadDocumentSchema, CopilotLoanRecommendationSchema,
    CopilotLoanEligibilitySchema, CopilotIssueResolutionSchema
)

# Import your existing orchestrator
from src.agents.orchestrator import OrchestratorAgent

logger = get_logger("copilot_adapter")

class CopilotAdapter:
    """
    Adapter that handles Copilot Studio integration without modifying existing code.
    """
    
    def __init__(self, session_manager=None):
        self.orchestrator = OrchestratorAgent()
        self.session_manager = session_manager
    
    async def process_user_input(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process conversational input from Copilot Studio
        """
        try:
            # Extract data
            user_input = request_data.get("userInput", "")
            session_id = request_data.get("sessionId", str(uuid.uuid4()))
            context = request_data.get("context", {})
            
            # Log the interaction
            logger.info(f"Processing user input: '{user_input[:50]}...' for session {session_id}")
            
            # Get existing session if available
            session_context = {}
            if self.session_manager:
                session_context = await self.session_manager.get_session(session_id)
                
                # Merge with incoming context
                if context:
                    session_context.update(context)
            
            # Process with orchestrator
            result = await self.orchestrator.process({
                "action": "handle_customer_inquiry",
                "request_type": "conversation",
                "user_input": user_input,
                "session_id": session_id,
                "conversation_context": session_context
            })
            
            # Update session if needed
            if self.session_manager and "updated_context" in result:
                await self.session_manager.update_session(session_id, result["updated_context"])
            
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
            return {
                "response": "I'm sorry, but I'm experiencing a technical issue. Please try again in a moment.",
                "error": str(e),
                "sessionId": request_data.get("sessionId", str(uuid.uuid4())),
                "context": {}
            }
    
    async def check_application_status(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check application status using the orchestrator
        """
        try:
            # Extract data
            application_id = request_data.get("applicationId", "")
            applicant_name = request_data.get("applicantName", "")
            
            # Log the request
            logger.info(f"Checking status for application {application_id}")
            
            # Process with orchestrator
            result = await self.orchestrator.process({
                "action": "handle_customer_inquiry",
                "application_id": application_id,
                "request_type": "application_status",
                "applicant_name": applicant_name
            })
            
            # Format response for Copilot Studio
            return {
                "applicationId": application_id,
                "applicationStatus": result.get("status", "UNKNOWN"),
                "currentStage": result.get("current_stage", "Processing"),
                "pendingItems": result.get("pending_items", []),
                "estimatedCompletion": result.get("estimated_completion", ""),
                "lastUpdated": result.get("last_updated", ""),
                "statusExplanation": result.get("status_explanation", "")
            }
            
        except Exception as e:
            logger.error(f"Error checking application status: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "applicationId": application_id,
                "applicationStatus": "ERROR",
                "statusExplanation": "An error occurred while checking your application status."
            }
    
    async def upload_document(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upload document using the orchestrator
        """
        try:
            # Extract data
            application_id = request_data.get("applicationId", "")
            document_type = request_data.get("documentType", "")
            document_content = request_data.get("documentContent", "")
            
            # Log the request
            logger.info(f"Uploading {document_type} document for application {application_id}")
            
            # Process with orchestrator
            result = await self.orchestrator.process({
                "action": "update_application",
                "update_type": "new_documents",
                "application_id": application_id,
                "documents": [{
                    "document_type": document_type,
                    "document_description": request_data.get("documentDescription", ""),
                    "document_year": request_data.get("documentYear"),
                    "document_format": request_data.get("documentFormat", "PDF"),
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
            
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "applicationId": application_id,
                "uploadStatus": "FAILED",
                "documentType": request_data.get("documentType", ""),
                "message": f"An error occurred while uploading your document: {str(e)}"
            }
    
    async def recommend_loan_types(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get loan recommendations using the orchestrator
        """
        try:
            # Log the request
            logger.info("Processing loan recommendation request")
            
            # Process with orchestrator
            result = await self.orchestrator.process({
                "action": "handle_customer_inquiry",
                "request_type": "loan_recommendation",
                "loan_criteria": {
                    "annual_income": request_data.get("annualIncome"),
                    "credit_score_range": request_data.get("creditScoreRange"),
                    "down_payment_percentage": request_data.get("downPaymentPercentage"),
                    "property_type": request_data.get("propertyType"),
                    "home_ownership_plans": request_data.get("homeOwnershipPlans"),
                    "military_service": request_data.get("militaryService", False),
                    "property_location": request_data.get("propertyLocation"),
                    "financial_priority": request_data.get("financialPriority")
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
            
        except Exception as e:
            logger.error(f"Error getting loan recommendations: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "recommendedLoanTypes": [],
                "primaryRecommendation": "",
                "explanation": "An error occurred while processing your loan recommendation request."
            }
    
    async def calculate_loan_eligibility(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate loan eligibility using the orchestrator
        """
        try:
            # Log the request
            logger.info("Processing loan eligibility calculation request")
            
            # Process with orchestrator
            result = await self.orchestrator.process({
                "action": "handle_customer_inquiry",
                "request_type": "eligibility_check",
                "financial_data": {
                    "annual_income": request_data.get("annualIncome"),
                    "monthly_debts": request_data.get("monthlyDebts"),
                    "credit_score_range": request_data.get("creditScoreRange"),
                    "employment_status": request_data.get("employmentStatus"),
                    "down_payment_amount": request_data.get("downPaymentAmount"),
                    "loan_term_years": request_data.get("loanTermYears", 30),
                    "property_type": request_data.get("propertyType", "SINGLE_FAMILY"),
                    "property_location": request_data.get("propertyLocation")
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
            
        except Exception as e:
            logger.error(f"Error calculating loan eligibility: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "eligibilityStatus": "ERROR",
                "maximumLoanAmount": 0,
                "estimatedMonthlyPayment": 0,
                "recommendedActions": ["Please try again or contact a loan officer for assistance."]
            }
    
    async def resolve_issue(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve issue using the orchestrator
        """
        try:
            # Extract data
            application_id = request_data.get("applicationId", "")
            issue_type = request_data.get("issueType", "")
            issue_description = request_data.get("issueDescription", "")
            
            # Log the request
            logger.info(f"Processing issue resolution for application {application_id}: {issue_type}")
            
            # Process with orchestrator
            result = await self.orchestrator.process({
                "action": "handle_customer_inquiry",
                "request_type": "issue_resolution",
                "application_id": application_id,
                "issue_data": {
                    "issue_type": issue_type,
                    "issue_description": issue_description,
                    "contact_preference": request_data.get("contactPreference", "EMAIL"),
                    "urgency_level": request_data.get("urgencyLevel", "MEDIUM")
                }
            })
            
            # Generate case number if not provided
            case_number = result.get("case_number")
            if not case_number:
                case_number = f"CASE-{uuid.uuid4().hex[:6].upper()}"
            
            # Format response for Copilot Studio
            return {
                "applicationId": application_id,
                "caseNumber": case_number,
                "resolutionSteps": result.get("resolution_steps", []),
                "estimatedResolutionTime": result.get("estimated_resolution_time", ""),
                "message": result.get("message", "Your issue has been recorded and will be addressed shortly.")
            }
            
        except Exception as e:
            logger.error(f"Error resolving issue: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "applicationId": application_id,
                "caseNumber": f"ERROR-{uuid.uuid4().hex[:6].upper()}",
                "message": "An error occurred while processing your issue resolution request."
            }