"""
Customer Service Agent Module (Enhanced)
Handles customer-facing interactions and generates explanations for the mortgage process.
Added integration with CustomerCommunicatorPlugin for enhanced communication.
"""

from typing import Any, Dict, List, Optional
import asyncio
import json
import logging

from src.data.cosmos_manager import CosmosDBManager
from .base_agent import BaseAgent
from src.semantic_kernel.kernel_setup import get_kernel
from src.autogen.reasoning_agents import get_customer_service_reasoning_agent
from src.utils.logging_utils import get_logger
from src.semantic_kernel.plugins.customer_plugin import CustomerCommunicatorPlugin


class CustomerServiceAgent(BaseAgent):
    """
    Agent responsible for handling customer inquiries, generating explanations,
    and providing guidance throughout the mortgage application process.
    Enhanced with CustomerCommunicatorPlugin for improved communication.
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
        
        # Register CustomerCommunicatorPlugin
        self._register_customer_communicator()
        
        cosmos_manager = CosmosDBManager()
        prompt_manager = None
        
        # Get customer service reasoning agent from AutoGen
        self.reasoning_agent = get_customer_service_reasoning_agent(
            kernel=self.kernel,
            cosmos_manager=cosmos_manager,
            prompt_manager=prompt_manager
        )
        
        self.logger.info("Customer service agent initialized with enhanced communication capabilities")
    
    def _register_customer_communicator(self):
        """
        Register the CustomerCommunicatorPlugin with the semantic kernel.
        """
        try:
            # Create an instance of the CustomerCommunicatorPlugin
            customer_communicator = CustomerCommunicatorPlugin(self.kernel)
            
            # Register the plugin with the kernel
            self.kernel.add_plugin(customer_communicator, "customer_plugin")
            
            self.logger.info("CustomerCommunicatorPlugin registered successfully")
        except Exception as e:
            self.logger.error(f"Error registering CustomerCommunicatorPlugin: {str(e)}")
            # Continue without the plugin to maintain backward compatibility
            self.logger.info("Continuing with default customer service capabilities")
    
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
        Enhanced with CustomerCommunicatorPlugin for better explanations.
        
        Args:
            input_data: Request details including missing documents
            
        Returns:
            Dict with response for missing documents
        """
        application_id = input_data.get("application_id")
        missing_documents = input_data.get("missing_documents", [])
        document_analysis = input_data.get("document_analysis", {})
        applicant_name = self._extract_applicant_name(input_data)
        
        self.log_processing_step(f"Generating missing documents notification for {len(missing_documents)} documents")
        
        # Use enhanced customer communication if available
        if "customer_plugin" in self.kernel.plugins:
            try:
                customer_plugin = self.kernel.plugins.get("customer_plugin")
                
                # Generate personalized notification
                notification_result = await customer_plugin.notify_missing_documents.invoke_async(
                    customer_name=applicant_name or "Valued Customer",
                    missing_documents=json.dumps(missing_documents),
                    deadline_days="10"  # Standard deadline
                )
                
                # Generate document explanations
                document_explanations = []
                for doc_type in missing_documents:
                    explanation = await customer_plugin.explain_mortgage_term.invoke_async(
                        term=doc_type,
                        customer_name=applicant_name
                    )
                    document_explanations.append({
                        "document_type": doc_type,
                        "explanation": explanation.result
                    })
                
                # Generate a checklist for the application
                loan_type = self._extract_loan_type(input_data)
                loan_purpose = self._extract_loan_purpose(input_data)
                
                checklist_result = await customer_plugin.generate_application_checklist.invoke_async(
                    customer_name=applicant_name or "Valued Customer",
                    loan_type=loan_type or "Conventional",
                    loan_purpose=loan_purpose or "Purchase"
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
                    "action_steps": action_steps,
                    "document_checklist": checklist_result.result,
                    "enhanced_communication_used": True
                }
            except Exception as e:
                self.logger.warning(f"Enhanced missing documents notification failed: {str(e)}. Falling back to standard notification.")
                # Continue with standard notification if enhanced notification fails
        
        # Use semantic kernel to generate notification (original approach)
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
        Enhanced with CustomerCommunicatorPlugin for clearer explanations.
        
        Args:
            input_data: Request details including underwriting and compliance results
            
        Returns:
            Dict with response for application decision
        """
        application_id = input_data.get("application_id")
        underwriting_results = input_data.get("underwriting_results", {})
        compliance_results = input_data.get("compliance_results", {})
        document_analysis = input_data.get("document_analysis", {})
        applicant_name = self._extract_applicant_name(input_data)
        
        # Determine overall application status
        is_approved = underwriting_results.get("is_approved", False) and compliance_results.get("is_compliant", False)
        
        self.log_processing_step(f"Generating application decision notification (approved: {is_approved})")
        
        # Use enhanced customer communication if available
        if "customer_plugin" in self.kernel.plugins:
            try:
                customer_plugin = self.kernel.plugins.get("customer_plugin")
                
                # Build a context with relevant information
                decision_context = {
                    "applicant_name": applicant_name,
                    "is_approved": is_approved,
                    "decision_factors": underwriting_results.get("decision_factors", {}),
                    "financial_ratios": underwriting_results.get("financial_ratios", {}),
                    "conditions": underwriting_results.get("conditions", []),
                    "compliance_issues": compliance_results.get("compliance_factors", {})
                }
                
                # Generate a personalized response
                inquiry_result = await customer_plugin.respond_to_inquiry.invoke_async(
                    customer_name=applicant_name or "Valued Customer",
                    inquiry_text=f"What is the status of my application {application_id}?",
                    application_data=json.dumps(decision_context)
                )
                
                # Get next steps based on decision
                next_steps = await self._generate_next_steps(is_approved, underwriting_results, compliance_results)
                
                # For approved applications, also provide loan term explanations
                explanations = []
                if is_approved:
                    # Explain key mortgage terms
                    for term in ["closing_costs", "rate_lock", "piti", "amortization"]:
                        explanation = await customer_plugin.explain_mortgage_term.invoke_async(
                            term=term,
                            customer_name=applicant_name
                        )
                        explanations.append({
                            "term": term,
                            "explanation": explanation.result
                        })
                
                return {
                    "application_id": application_id,
                    "request_type": "application_decision",
                    "success": True,
                    "is_approved": is_approved,
                    "notification": inquiry_result.result,
                    "next_steps": next_steps,
                    "term_explanations": explanations if is_approved else [],
                    "enhanced_communication_used": True
                }
            except Exception as e:
                self.logger.warning(f"Enhanced application decision notification failed: {str(e)}. Falling back to standard notification.")
                # Continue with standard notification if enhanced notification fails
        
        # Use reasoning agent to generate personalized explanation (original approach)
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
        Enhanced with CustomerCommunicatorPlugin for improved responses.
        
        Args:
            input_data: Request details including inquiry text and application context
            
        Returns:
            Dict with response to customer inquiry
        """
        application_id = input_data.get("application_id")
        inquiry_text = input_data.get("inquiry_text", "")
        application_context = input_data.get("application_context", {})
        applicant_name = self._extract_applicant_name(input_data) or self._extract_applicant_name(application_context)
        
        self.log_processing_step(f"Processing customer inquiry: {inquiry_text[:50]}...")
        
        # Use enhanced customer communication if available
        if "customer_plugin" in self.kernel.plugins:
            try:
                customer_plugin = self.kernel.plugins.get("customer_plugin")
                
                # Generate a personalized response
                inquiry_result = await customer_plugin.respond_to_inquiry.invoke_async(
                    customer_name=applicant_name or "Valued Customer",
                    inquiry_text=inquiry_text,
                    application_data=json.dumps(application_context)
                )
                
                # Check if inquiry is about a mortgage term
                if self._is_term_explanation_inquiry(inquiry_text):
                    term = self._extract_mortgage_term(inquiry_text)
                    if term:
                        term_explanation = await customer_plugin.explain_mortgage_term.invoke_async(
                            term=term,
                            customer_name=applicant_name
                        )
                        
                        # Combine term explanation with general response
                        return {
                            "application_id": application_id,
                            "request_type": "customer_inquiry",
                            "success": True,
                            "inquiry": inquiry_text,
                            "response": term_explanation.result,
                            "requires_human_follow_up": False,
                            "recommended_follow_up": "",
                            "enhanced_communication_used": True
                        }
                
                # Check if inquiry is about a process step
                if self._is_process_explanation_inquiry(inquiry_text):
                    step = self._extract_process_step(inquiry_text)
                    if step:
                        step_explanation = await customer_plugin.explain_mortgage_step.invoke_async(
                            step_name=step,
                            customer_name=applicant_name
                        )
                        
                        # Return process step explanation
                        return {
                            "application_id": application_id,
                            "request_type": "customer_inquiry",
                            "success": True,
                            "inquiry": inquiry_text,
                            "response": step_explanation.result,
                            "requires_human_follow_up": False,
                            "recommended_follow_up": "",
                            "enhanced_communication_used": True
                        }
                
                # Return general inquiry response
                return {
                    "application_id": application_id,
                    "request_type": "customer_inquiry",
                    "success": True,
                    "inquiry": inquiry_text,
                    "response": inquiry_result.result,
                    "requires_human_follow_up": False,
                    "recommended_follow_up": "",
                    "enhanced_communication_used": True
                }
            except Exception as e:
                self.logger.warning(f"Enhanced customer inquiry response failed: {str(e)}. Falling back to standard response.")
                # Continue with standard response if enhanced response fails
        
        # Use reasoning agent to generate response (original approach)
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
                "application_id": application_id,
                "request_type": "customer_inquiry",
                "success": False,
                "inquiry": inquiry_text,
                "response": "I apologize, but I'm unable to answer your question at this time. Please contact our support team for assistance.",
                "requires_human_follow_up": True
            }
    
    async def _handle_application_status_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle request for application status update.
        Enhanced with CustomerCommunicatorPlugin for clearer status updates.
        
        Args:
            input_data: Request details including application context
            
        Returns:
            Dict with response for application status
        """
        application_id = input_data.get("application_id")
        application_context = input_data.get("application_context", {})
        applicant_name = self._extract_applicant_name(input_data) or self._extract_applicant_name(application_context)
        
        self.log_processing_step(f"Generating application status update")
        
        # Extract current status from context
        current_status = application_context.get("status", "UNKNOWN")
        
        # Use enhanced customer communication if available
        if "customer_plugin" in self.kernel.plugins:
            try:
                customer_plugin = self.kernel.plugins.get("customer_plugin")
                
                # Generate personalized status update
                status_inquiry = f"What is the current status of my mortgage application?"
                status_result = await customer_plugin.respond_to_inquiry.invoke_async(
                    customer_name=applicant_name or "Valued Customer",
                    inquiry_text=status_inquiry,
                    application_data=json.dumps(application_context)
                )
                
                # Generate application timeline
                timeline_result = await customer_plugin.generate_status_update.invoke_async(
                    customer_name=applicant_name or "Valued Customer",
                    application_data=json.dumps(application_context)
                )
                
                # Explain current process step in detail
                current_step = self._map_status_to_process_step(current_status)
                step_explanation = await customer_plugin.explain_mortgage_step.invoke_async(
                    step_name=current_step,
                    customer_name=applicant_name
                )
                
                return {
                    "application_id": application_id,
                    "request_type": "application_status",
                    "success": True,
                    "status": current_status,
                    "status_explanation": status_result.result,
                    "process_step_explanation": step_explanation.result,
                    "timeline": timeline_result.result,
                    "last_updated": application_context.get("last_updated", ""),
                    "enhanced_communication_used": True
                }
            except Exception as e:
                self.logger.warning(f"Enhanced status update failed: {str(e)}. Falling back to standard update.")
                # Continue with standard status update if enhanced update fails
        
        # Use semantic kernel to generate status update (original approach)
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
        Enhanced with CustomerCommunicatorPlugin for better document explanations.
        
        Args:
            input_data: Request details including document type
            
        Returns:
            Dict with response for document explanation
        """
        application_id = input_data.get("application_id")
        document_type = input_data.get("document_type", "")
        applicant_name = self._extract_applicant_name(input_data)
        
        self.log_processing_step(f"Generating explanation for document: {document_type}")
        
        # Use enhanced customer communication if available
        if "customer_plugin" in self.kernel.plugins:
            try:
                customer_plugin = self.kernel.plugins.get("customer_plugin")
                
                # Generate document explanation
                document_term = document_type.lower().replace("_", " ")
                explanation_result = await customer_plugin.explain_mortgage_term.invoke_async(
                    term=document_term,
                    customer_name=applicant_name
                )
                
                # Generate document checklist
                loan_type = self._extract_loan_type(input_data) or "Conventional"
                loan_purpose = self._extract_loan_purpose(input_data) or "Purchase"
                
                checklist_result = await customer_plugin.generate_application_checklist.invoke_async(
                    customer_name=applicant_name or "Valued Customer",
                    loan_type=loan_type,
                    loan_purpose=loan_purpose
                )
                
                # Check if sample is available
                sample_available = document_type in ["BANK_STATEMENT", "PAY_STUB", "W2"]
                
                # Generate steps for document submission
                steps_result = await self._generate_document_submission_steps(document_type)
                
                return {
                    "application_id": application_id,
                    "request_type": "document_explanation",
                    "success": True,
                    "document_type": document_type,
                    "explanation": explanation_result.result,
                    "submission_steps": steps_result,
                    "document_checklist": checklist_result.result,
                    "sample_available": sample_available,
                    "enhanced_communication_used": True
                }
            except Exception as e:
                self.logger.warning(f"Enhanced document explanation failed: {str(e)}. Falling back to standard explanation.")
                # Continue with standard explanation if enhanced explanation fails
        
        # Use semantic kernel to generate document explanation (original approach)
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
        Enhanced with CustomerCommunicatorPlugin for improved responses.
        
        Args:
            input_data: Request details
            
        Returns:
            Dict with generic response
        """
        application_id = input_data.get("application_id")
        request_details = input_data.get("details", {})
        applicant_name = self._extract_applicant_name(input_data)
        
        self.log_processing_step(f"Processing generic customer service request")
        
        # Use enhanced customer communication if available
        if "customer_plugin" in self.kernel.plugins and "inquiry" in request_details:
            try:
                customer_plugin = self.kernel.plugins.get("customer_plugin")
                
                # Generate a personalized response
                inquiry_result = await customer_plugin.respond_to_inquiry.invoke_async(
                    customer_name=applicant_name or "Valued Customer",
                    inquiry_text=request_details.get("inquiry", "How can I help you?"),
                    application_data=json.dumps(request_details.get("context", {}))
                )
                
                return {
                    "application_id": application_id,
                    "request_type": "generic",
                    "success": True,
                    "response": inquiry_result.result,
                    "requires_human_follow_up": False,
                    "enhanced_communication_used": True
                }
            except Exception as e:
                self.logger.warning(f"Enhanced generic response failed: {str(e)}. Falling back to standard response.")
                # Continue with standard response if enhanced response fails
        
        # Use reasoning agent to generate response (original approach)
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
        Enhanced with CustomerCommunicatorPlugin for clearer steps.
        
        Args:
            missing_documents: List of missing document types
            
        Returns:
            List of action step dictionaries
        """
        action_steps = []
        
        # Check if enhanced plugin is available
        if "customer_plugin" in self.kernel.plugins:
            try:
                customer_plugin = self.kernel.plugins.get("customer_plugin")
                
                for doc_type in missing_documents:
                    # Generate steps for document
                    steps_result = await self._generate_document_submission_steps(doc_type)
                    
                    action_steps.append({
                        "document_type": doc_type,
                        "steps": steps_result
                    })
                
                return action_steps
            except Exception as e:
                self.logger.warning(f"Enhanced action steps generation failed: {str(e)}. Falling back to standard generation.")
                # Continue with standard generation if enhanced generation fails
        
        # Original implementation
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
        Enhanced with more personalized and detailed steps.
        
        Args:
            is_approved: Whether the application was approved
            underwriting_results: Results from underwriting evaluation
            compliance_results: Results from compliance evaluation
            
        Returns:
            List of next step strings
        """
        # Try enhanced next steps generation if customer plugin is available
        if "customer_plugin" in self.kernel.plugins:
            try:
                # Build context for detailed next steps
                context = {
                    "is_approved": is_approved,
                    "underwriting_results": underwriting_results,
                    "compliance_results": compliance_results,
                    "decision_factors": underwriting_results.get("decision_factors", {}),
                    "conditions": underwriting_results.get("conditions", []),
                    "recommended_rate": underwriting_results.get("recommended_interest_rate", 0)
                }
                
                next_steps = []
                
                if is_approved:
                    # Standard steps for approval
                    next_steps = [
                        "Review and sign your loan documents",
                        "Schedule closing with your loan officer",
                        "Prepare for closing costs payment"
                    ]
                    
                    # Add any conditions from underwriting
                    if "conditions" in underwriting_results:
                        for condition in underwriting_results["conditions"]:
                            next_steps.append(f"Satisfy condition: {condition}")
                
                else:
                    # More detailed steps for rejection based on specific factors
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
                                next_steps.append("Work on reducing existing debt to improve debt-to-income ratio")
                                next_steps.append("Consider increasing income or providing documentation of additional income sources")
                            elif criterion == "LTV_RATIO":
                                next_steps.append("Consider increasing your down payment to improve loan-to-value ratio")
                                next_steps.append("Explore down payment assistance programs if eligible")
                            elif criterion == "CREDIT_SCORE":
                                next_steps.append("Take steps to improve your credit score")
                                next_steps.append("Request a copy of your credit report to identify areas for improvement")
                                next_steps.append("Pay down credit card balances to reduce credit utilization")
                            elif criterion == "FRONTEND_RATIO":
                                next_steps.append("Consider a property with a lower purchase price to reduce housing expense ratio")
                    
                    elif compliance_results.get("is_compliant", False) == False:
                        # Compliance rejection
                        compliance_factors = compliance_results.get("compliance_factors", {})
                        
                        if "missing_documents" in compliance_factors:
                            next_steps.append("Submit all required documentation promptly")
                        
                        if "regulatory_limits" in compliance_factors:
                            next_steps.append("Consider a different loan type or loan amount that meets regulatory requirements")
                    
                    # Add option to speak with loan officer
                    next_steps.append("Schedule a call with a loan officer to discuss options and alternatives")
                
                return next_steps
                
            except Exception as e:
                self.logger.warning(f"Enhanced next steps generation failed: {str(e)}. Falling back to standard generation.")
                # Continue with standard next steps if enhanced generation fails
        
        # Original implementation
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

    async def _generate_document_submission_steps(self, document_type: str) -> str:
        """
        Generate specific steps for document submission.
        Enhanced with more detailed instructions.
        
        Args:
            document_type: Type of document
            
        Returns:
            String with document submission steps
        """
        # Try enhanced document steps if customer plugin is available
        if "customer_plugin" in self.kernel.plugins:
            try:
                customer_plugin = self.kernel.plugins.get("customer_plugin")
                
                # Generate term explanation which includes submission guidelines
                document_term = document_type.lower().replace("_", " ")
                term_result = await customer_plugin.explain_mortgage_term.invoke_async(
                    term=document_term
                )
                
                # Add submission instructions
                submission_instructions = (
                    f"To submit your {document_type.replace('_', ' ').title()}:\n\n"
                    f"1. Log in to your mortgage portal\n"
                    f"2. Navigate to the 'Documents' section\n"
                    f"3. Select '{document_type.replace('_', ' ').title()}' from the dropdown menu\n"
                    f"4. Upload a clear, complete copy of the document\n"
                    f"5. Ensure all pages are included and information is legible\n"
                    f"6. Click 'Submit' to complete the upload"
                )
                
                return submission_instructions
                
            except Exception as e:
                self.logger.warning(f"Enhanced document submission steps failed: {str(e)}. Falling back to standard steps.")
                # Continue with standard steps if enhanced steps fail
        
        # Original implementation or fallback
        document_steps = (
            f"Please upload a clear, complete copy of your {document_type.replace('_', ' ').title()} "
            f"through our secure portal. Ensure all pages are included and all information is clearly visible."
        )
        
        return document_steps
    
    # Helper methods for enhanced functionality
    
    def _extract_applicant_name(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract applicant name from data."""
        if "applicant_name" in data:
            return data["applicant_name"]
        elif "application_context" in data and "applicant_name" in data["application_context"]:
            return data["application_context"]["applicant_name"]
        elif "application_data" in data and "applicant" in data["application_data"]:
            applicant = data["application_data"]["applicant"]
            if "name" in applicant:
                return applicant["name"]
        elif "document_analysis" in data and "summary" in data["document_analysis"]:
            summary = data["document_analysis"]["summary"]
            if "applicant" in summary and "name" in summary["applicant"]:
                return summary["applicant"]["name"]
        
        return None
    
    def _extract_loan_type(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract loan type from data."""
        if "loan_type" in data:
            return data["loan_type"]
        elif "application_context" in data and "loan_type" in data["application_context"]:
            return data["application_context"]["loan_type"]
        elif "application_data" in data and "loan" in data["application_data"]:
            loan = data["application_data"]["loan"]
            if "type" in loan:
                return loan["type"]
            elif "loan_type" in loan:
                return loan["loan_type"]
        
        return "Conventional"  # Default value
    
    def _extract_loan_purpose(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract loan purpose from data."""
        if "loan_purpose" in data:
            return data["loan_purpose"]
        elif "application_context" in data and "loan_purpose" in data["application_context"]:
            return data["application_context"]["loan_purpose"]
        elif "application_data" in data and "loan" in data["application_data"]:
            loan = data["application_data"]["loan"]
            if "purpose" in loan:
                return loan["purpose"]
            elif "loan_purpose" in loan:
                return loan["loan_purpose"]
        
        return "Purchase"  # Default value
    
    def _is_term_explanation_inquiry(self, inquiry: str) -> bool:
        """Check if inquiry is asking for a term explanation."""
        inquiry_lower = inquiry.lower()
        explanation_patterns = [
            "what is", "what's", "what does", "explain", "meaning of", "define",
            "stand for", "understand", "definition"
        ]
        
        return any(pattern in inquiry_lower for pattern in explanation_patterns)
    
    def _extract_mortgage_term(self, inquiry: str) -> Optional[str]:
        """Extract mortgage term from inquiry."""
        inquiry_lower = inquiry.lower()
        
        # Common mortgage terms to check for
        mortgage_terms = [
            "apr", "piti", "escrow", "ltv", "dti", "pmi", "amortization",
            "rate lock", "points", "underwriting", "closing costs", "pre-approval",
            "pre-qualification", "refinance", "heloc", "arm", "fixed rate",
            "jumbo loan", "fha loan", "va loan", "closing", "appraisal"
        ]
        
        for term in mortgage_terms:
            if term in inquiry_lower:
                return term
        
        return None
    
    def _is_process_explanation_inquiry(self, inquiry: str) -> bool:
        """Check if inquiry is asking about a process step."""
        inquiry_lower = inquiry.lower()
        process_patterns = [
            "process", "step", "what happens", "how does", "procedure",
            "stage", "what is the", "explain the", "how long"
        ]
        
        return any(pattern in inquiry_lower for pattern in process_patterns)
    
    def _extract_process_step(self, inquiry: str) -> Optional[str]:
        """Extract process step from inquiry."""
        inquiry_lower = inquiry.lower()
        
        # Common process steps
        process_steps = [
            "pre-qualification", "pre-approval", "application", "processing",
            "underwriting", "conditional approval", "closing disclosure",
            "closing", "rate lock", "appraisal"
        ]
        
        for step in process_steps:
            if step in inquiry_lower:
                return step
        
        return None
    
    def _map_status_to_process_step(self, status: str) -> str:
        """Map application status to process step name."""
        status_map = {
            "INITIATED": "application",
            "DOCUMENTS_PROCESSED": "processing",
            "DOCUMENTS_UPDATED": "processing",
            "UNDERWRITING_COMPLETED": "underwriting",
            "COMPLIANCE_CHECKED": "conditional approval",
            "APPROVED": "closing",
            "REJECTED_UNDERWRITING": "underwriting",
            "REJECTED_COMPLIANCE": "compliance",
            "ERROR": "processing"
        }
        
        return status_map.get(status, "processing")