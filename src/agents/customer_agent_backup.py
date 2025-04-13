"""
Customer Service Agent Module
Handles customer-facing interactions and generates explanations for the mortgage process.
"""

from typing import Any, Dict, List, Optional
import asyncio
from src.data.cosmos_manager import CosmosDBManager
from .base_agent import BaseAgent
from src.semantic_kernel.kernel_setup import get_kernel
from src.autogen.reasoning_agents import get_customer_service_reasoning_agent
from src.utils.logging_utils import get_logger


class CustomerServiceAgent(BaseAgent):
    """
    Agent responsible for handling customer inquiries, generating explanations,
    and providing guidance throughout the mortgage application process.
    """
    
    def __init__(self, agent_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Customer Service Agent.
        
        Args:
            agent_config: Configuration for the agent
        """
        super().__init__("customer_service", agent_config)
        
        # Initialize Semantic Kernel
        self.kernel = get_kernel()
        cosmos_manager = CosmosDBManager()
        prompt_manager = None
        
        # Get customer service reasoning agent from AutoGen
        self.reasoning_agent = get_customer_service_reasoning_agent(
            kernel=self.kernel,
            cosmos_manager=cosmos_manager,
            prompt_manager=prompt_manager
        )
        
        self.logger.info("Customer service agent initialized")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a customer service request.
        
        Args:
            input_data: Request details and context:
                - application_id: The ID of the application
                - request_type: Type of customer service request
                - Additional data specific to the request type
                
        Returns:
            Dict containing the response
        """
        application_id = input_data.get("application_id")
        request_type = input_data.get("request_type", "")
        
        self.log_processing_step(f"Processing {request_type} request for application {application_id}")
        
        try:
            # Route to appropriate handler based on request type
            if request_type == "missing_documents":
                return await self._handle_missing_documents_request(input_data)
            elif request_type == "application_decision":
                return await self._handle_application_decision_request(input_data)
            elif request_type == "customer_inquiry":
                return await self._handle_customer_inquiry(input_data)
            elif request_type == "application_status":
                return await self._handle_application_status_request(input_data)
            elif request_type == "document_explanation":
                return await self._handle_document_explanation_request(input_data)
            else:
                return await self._handle_generic_request(input_data)
                
        except Exception as e:
            self.logger.error(f"Error processing customer service request: {str(e)}", exc_info=True)
            
            # Provide a generic error response
            return {
                "application_id": application_id,
                "request_type": request_type,
                "success": False,
                "message": "We apologize, but we encountered an error processing your request. Please try again or contact our support team directly.",
                "error": str(e)
            }
    
    async def _handle_missing_documents_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle request for missing documents notification.
        
        Args:
            input_data: Request details including missing documents
            
        Returns:
            Dict with response for missing documents
        """
        application_id = input_data.get("application_id")
        missing_documents = input_data.get("missing_documents", [])
        document_analysis = input_data.get("document_analysis", {})
        
        self.log_processing_step(f"Generating missing documents notification for {len(missing_documents)} documents")
        
        # Use semantic kernel to generate notification
        notification_plugin = self.kernel.plugins.get("customer_plugin")
        
        try:
            # Generate explanation for each missing document
            document_explanations = []
            for doc_type in missing_documents:
                explanation = await notification_plugin.explain_required_document.invoke_async(
                    documentType=doc_type
                )
                document_explanations.append({
                    "document_type": doc_type,
                    "explanation": explanation.result
                })
            
            # Generate overall notification
            notification_result = await notification_plugin.generate_missing_documents_notification.invoke_async(
                applicationId=application_id,
                missingDocuments=str(missing_documents),
                documentExplanations=str(document_explanations)
            )
            
            # Generate action steps for the customer
            action_steps = await self._generate_action_steps_for_documents(missing_documents)
            
            return {
                "application_id": application_id,
                "request_type": "missing_documents",
                "success": True,
                "notification": notification_result.result,
                "missing_documents": missing_documents,
                "document_explanations": document_explanations,
                "action_steps": action_steps
            }
            
        except Exception as e:
            self.logger.error(f"Error generating missing documents notification: {str(e)}", exc_info=True)
            
            # Fallback to simpler notification
            return {
                "application_id": application_id,
                "request_type": "missing_documents",
                "success": True,
                "notification": f"Your mortgage application requires additional documentation. Please provide the following documents: {', '.join(missing_documents)}",
                "missing_documents": missing_documents
            }
    
    async def _handle_application_decision_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle request for application decision notification.
        
        Args:
            input_data: Request details including underwriting and compliance results
            
        Returns:
            Dict with response for application decision
        """
        application_id = input_data.get("application_id")
        underwriting_results = input_data.get("underwriting_results", {})
        compliance_results = input_data.get("compliance_results", {})
        document_analysis = input_data.get("document_analysis", {})
        
        # Determine overall application status
        is_approved = underwriting_results.get("is_approved", False) and compliance_results.get("is_compliant", False)
        
        self.log_processing_step(f"Generating application decision notification (approved: {is_approved})")
        
        # Use reasoning agent to generate personalized explanation
        context = {
            "application_id": application_id,
            "is_approved": is_approved,
            "underwriting_results": underwriting_results,
            "compliance_results": compliance_results,
            "document_analysis": document_analysis
        }
        
        try:
            reasoning_result = await self.reasoning_agent.generate_decision_notification(context)
            
            # Get next steps based on decision
            next_steps = await self._generate_next_steps(is_approved, underwriting_results, compliance_results)
            
            return {
                "application_id": application_id,
                "request_type": "application_decision",
                "success": True,
                "is_approved": is_approved,
                "notification": reasoning_result.get("notification", ""),
                "explanation": reasoning_result.get("explanation", ""),
                "next_steps": next_steps
            }
            
        except Exception as e:
            self.logger.error(f"Error generating application decision notification: {str(e)}", exc_info=True)
            
            # Fallback to simpler notification
            if is_approved:
                notification = "Congratulations! Your mortgage application has been approved."
            else:
                notification = "We regret to inform you that your mortgage application has not been approved at this time."
            
            return {
                "application_id": application_id,
                "request_type": "application_decision",
                "success": True,
                "is_approved": is_approved,
                "notification": notification,
                "explanation": underwriting_results.get("explanation", "")
            }
    
    async def _handle_customer_inquiry(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a customer inquiry about their application.
        
        Args:
            input_data: Request details including inquiry text and application context
            
        Returns:
            Dict with response to customer inquiry
        """
        application_id = input_data.get("application_id")
        inquiry_text = input_data.get("inquiry_text", "")
        application_context = input_data.get("application_context", {})
        
        self.log_processing_step(f"Processing customer inquiry: {inquiry_text[:50]}...")
        
        # Use reasoning agent to generate response
        context = {
            "application_id": application_id,
            "inquiry": inquiry_text,
            "application_context": application_context
        }
        
        try:
            reasoning_result = await self.reasoning_agent.answer_customer_inquiry(context)
            
            return {
                "application_id": application_id,
                "request_type": "customer_inquiry",
                "success": True,
                "inquiry": inquiry_text,
                "response": reasoning_result.get("response", ""),
                "requires_human_follow_up": reasoning_result.get("requires_human_follow_up", False),
                "recommended_follow_up": reasoning_result.get("recommended_follow_up", "")
            }
            
        except Exception as e:
            self.logger.error(f"Error processing customer inquiry: {str(e)}", exc_info=True)
            
            # Fallback to generic response
            return {
                "application_id": input_data.get("application_id"),
                "request_type": "customer_inquiry",
                "success": False,
                "inquiry": inquiry_text,
                "response": "I apologize, but I'm unable to answer your question at this time. Please contact our support team for assistance.",
                "requires_human_follow_up": True
            }
    
    async def _handle_application_status_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle request for application status update.
        
        Args:
            input_data: Request details including application context
            
        Returns:
            Dict with response for application status
        """
        application_id = input_data.get("application_id")
        application_context = input_data.get("application_context", {})
        
        self.log_processing_step(f"Generating application status update")
        
        # Extract current status from context
        current_status = application_context.get("status", "UNKNOWN")
        
        # Use semantic kernel to generate status update
        status_plugin = self.kernel.plugins.get("customer_plugin")
        
        try:
            # Generate status explanation
            status_result = await status_plugin.explain_application_status.invoke_async(
                applicationId=application_id,
                status=current_status,
                context=str(application_context)
            )
            
            # Generate estimated timeline
            timeline_result = await status_plugin.generate_application_timeline.invoke_async(
                status=current_status,
                context=str(application_context)
            )
            
            return {
                "application_id": application_id,
                "request_type": "application_status",
                "success": True,
                "status": current_status,
                "status_explanation": status_result.result,
                "estimated_timeline": timeline_result.result,
                "last_updated": application_context.get("last_updated", "")
            }
            
        except Exception as e:
            self.logger.error(f"Error generating application status update: {str(e)}", exc_info=True)
            
            # Fallback to simpler status update
            return {
                "application_id": application_id,
                "request_type": "application_status",
                "success": True,
                "status": current_status,
                "status_explanation": f"Your application is currently in {current_status} status."
            }
    
    async def _handle_document_explanation_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle request for document explanation.
        
        Args:
            input_data: Request details including document type
            
        Returns:
            Dict with response for document explanation
        """
        application_id = input_data.get("application_id")
        document_type = input_data.get("document_type", "")
        
        self.log_processing_step(f"Generating explanation for document: {document_type}")
        
        # Use semantic kernel to generate document explanation
        document_plugin = self.kernel.plugins.get("customer_plugin")
        
        try:
            # Generate document explanation
            explanation_result = await document_plugin.explain_required_document.invoke_async(
                documentType=document_type
            )
            
            # Generate sample document if available
            sample_available = document_type in ["BANK_STATEMENT", "PAY_STUB", "W2"]
            sample_info = None
            
            if sample_available:
                sample_result = await document_plugin.provide_document_sample_info.invoke_async(
                    documentType=document_type
                )
                sample_info = sample_result.result
            
            return {
                "application_id": application_id,
                "request_type": "document_explanation",
                "success": True,
                "document_type": document_type,
                "explanation": explanation_result.result,
                "sample_available": sample_available,
                "sample_info": sample_info
            }
            
        except Exception as e:
            self.logger.error(f"Error generating document explanation: {str(e)}", exc_info=True)
            
            # Fallback to simpler explanation
            return {
                "application_id": application_id,
                "request_type": "document_explanation",
                "success": True,
                "document_type": document_type,
                "explanation": f"This document is required to verify information in your mortgage application."
            }
    
    async def _handle_generic_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle generic customer service request.
        
        Args:
            input_data: Request details
            
        Returns:
            Dict with generic response
        """
        application_id = input_data.get("application_id")
        request_details = input_data.get("details", {})
        
        self.log_processing_step(f"Processing generic customer service request")
        
        # Use reasoning agent to generate response
        try:
            reasoning_result = await self.reasoning_agent.process_generic_request({
                "application_id": application_id,
                "request_details": request_details
            })
            
            return {
                "application_id": application_id,
                "request_type": "generic",
                "success": True,
                "response": reasoning_result.get("response", ""),
                "requires_human_follow_up": reasoning_result.get("requires_human_follow_up", False)
            }
            
        except Exception as e:
            self.logger.error(f"Error processing generic request: {str(e)}", exc_info=True)
            
            # Fallback to generic response
            return {
                "application_id": application_id,
                "request_type": "generic",
                "success": True,
                "response": "Thank you for your inquiry. Our team is reviewing your application and will respond to your specific request shortly.",
                "requires_human_follow_up": True
            }
    
    async def _generate_action_steps_for_documents(self, missing_documents: List[str]) -> List[Dict[str, Any]]:
        """
        Generate action steps for providing missing documents.
        
        Args:
            missing_documents: List of missing document types
            
        Returns:
            List of action step dictionaries
        """
        action_steps = []
        
        for doc_type in missing_documents:
            # Use semantic kernel to generate action steps
            steps_plugin = self.kernel.plugins.get("customer_plugin")
            
            try:
                steps_result = await steps_plugin.generate_document_submission_steps.invoke_async(
                    documentType=doc_type
                )
                
                action_steps.append({
                    "document_type": doc_type,
                    "steps": steps_result.result
                })
                
            except Exception as e:
                self.logger.error(f"Error generating action steps for {doc_type}: {str(e)}", exc_info=True)
                
                # Fallback to generic steps
                action_steps.append({
                    "document_type": doc_type,
                    "steps": "Please upload a clear, complete copy of this document through our secure portal."
                })
        
        return action_steps
    
    async def _generate_next_steps(self, is_approved: bool, underwriting_results: Dict[str, Any],
                                  compliance_results: Dict[str, Any]) -> List[str]:
        """
        Generate next steps based on application decision.
        
        Args:
            is_approved: Whether the application was approved
            underwriting_results: Results from underwriting evaluation
            compliance_results: Results from compliance evaluation
            
        Returns:
            List of next step strings
        """
        if is_approved:
            # Generate next steps for approved application
            next_steps = [
                "Review and sign your loan documents",
                "Schedule closing with your loan officer",
                "Prepare for closing costs payment"
            ]
            
            # Add any conditions from underwriting
            if "conditions" in underwriting_results:
                for condition in underwriting_results["conditions"]:
                    next_steps.append(f"Satisfy condition: {condition}")
            
            return next_steps
            
        else:
            # Generate next steps for rejected application
            next_steps = [
                "Review the explanation for the decision",
                "Consider addressing the issues identified"
            ]
            
            # Add specific steps based on rejection reason
            if underwriting_results.get("is_approved", False) == False:
                # Underwriting rejection
                decision_factors = underwriting_results.get("decision_factors", {})
                failed_criteria = decision_factors.get("failed_criteria", [])
                
                for criterion in failed_criteria:
                    if criterion == "DTI_RATIO":
                        next_steps.append("Work on reducing your existing debt")
                    elif criterion == "LTV_RATIO":
                        next_steps.append("Consider increasing your down payment")
                    elif criterion == "CREDIT_SCORE":
                        next_steps.append("Take steps to improve your credit score")
            
            elif compliance_results.get("is_compliant", False) == False:
                # Compliance rejection
                compliance_factors = compliance_results.get("compliance_factors", {})
                
                if "missing_documents" in compliance_factors:
                    next_steps.append("Submit all required documentation")
                
                if "regulatory_limits" in compliance_factors:
                    next_steps.append("Consider a different loan type or amount")
            
            # Add option to speak with loan officer
            next_steps.append("Schedule a call with a loan officer to discuss options")
            
            return next_steps