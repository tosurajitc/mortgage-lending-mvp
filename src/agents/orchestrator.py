"""
Orchestrator Agent Module
Coordinates the workflow between all specialized agents in the mortgage processing system.
"""

import asyncio
from typing import Any, Dict, List, Optional
import uuid  # Add this import
from datetime import datetime
from .base_agent import BaseAgent
from .document_agent import DocumentAnalysisAgent
from .underwriting_agent import UnderwritingAgent
from .compliance_agent import ComplianceAgent
from .customer_agent import CustomerServiceAgent
from src.workflow.state_manager import StateManager
from src.workflow.decision_tracker import DecisionTracker
from src.security.access_control import verify_agent_permissions
from src.data.models import ApplicationStatus


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator Agent that coordinates workflow and communication between specialized agents.
    Acts as the central coordinator for the entire mortgage application process.
    """
    
    def __init__(self, agent_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Orchestrator Agent.
        
        Args:
            agent_config: Configuration for the agent
        """
        super().__init__("orchestrator", agent_config)
        
        # Initialize specialized agents
        self.document_agent = DocumentAnalysisAgent()
        self.underwriting_agent = UnderwritingAgent()
        self.compliance_agent = ComplianceAgent()
        self.customer_agent = CustomerServiceAgent()
        
        # Initialize workflow components
        self.state_manager = StateManager()
        self.decision_tracker = DecisionTracker()
        
        self.logger.info("Orchestrator agent fully initialized")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a mortgage application through the entire pipeline.
        
        Args:
            input_data: Application data and related information
            
        Returns:
            Dict containing the processing results from all agents
        """
        # Extract application ID for tracking
        application_id = input_data.get("application_id")
        if not application_id:
            raise ValueError("Missing application ID in input data")
        
        # Determine the requested action
        action = input_data.get("action", "process_application")
        
        # Route to appropriate handler based on action
        if action == "process_application":
            return await self._process_new_application(input_data)
        elif action == "handle_customer_inquiry":
            return await self._handle_customer_inquiry(input_data)
        elif action == "update_application":
            return await self._update_existing_application(input_data)
        else:
            raise ValueError(f"Unknown action requested: {action}")
    

    async def _process_new_application(self, applicant_data, loan_details, property_info):
        """
        Process a new mortgage application through the entire pipeline.
        
        Args:
            applicant_data: Applicant personal and financial information
            loan_details: Loan-specific details
            property_info: Property information
            
        Returns:
            Dict containing the complete processing results
        """
        # Generate a unique application ID
        application_id = str(uuid.uuid4())
        
        # Prepare comprehensive input data
        input_data = {
            "application_id": application_id,
            "action": "process_application",
            "application_data": {
                "applicant": applicant_data,
                "loan": loan_details,
                "property": property_info
            },
            "documents": []  # Placeholder for initial document handling
        }
        
        # Initialize application state
        self.log_processing_step(f"Starting new application processing for {application_id}")
        
        try:
            # Create initial application state
            await self.state_manager.create_application_state(
                application_id, 
                ApplicationStatus.INITIATED
            )
            
            # Step 1: Document Analysis
            self.log_processing_step("Starting document analysis")
            document_results = await self.document_agent.execute({
                "application_id": application_id,
                "documents": self._prepare_initial_documents(input_data)
            })
            
            # Update application state
            await self.state_manager.update_application_state(
                application_id, 
                ApplicationStatus.DOCUMENTS_PROCESSED,
                {"document_analysis": document_results}
            )
            
            # Check if documents are complete and valid
            if not document_results.get("is_complete", False):
                self.log_processing_step(
                    "Document analysis shows incomplete documentation",
                    {"missing_documents": document_results.get("missing_documents", [])}
                )
                
                # Generate customer response for missing documents
                customer_response = await self.customer_agent.execute({
                    "application_id": application_id,
                    "request_type": "missing_documents",
                    "missing_documents": document_results.get("missing_documents", []),
                    "document_analysis": document_results
                })
                
                return {
                    "application_id": application_id,
                    "status": "INCOMPLETE_DOCUMENTS",
                    "customer_response": customer_response,
                    "missing_documents": document_results.get("missing_documents", [])
                }
            
            # Step 2: Underwriting Evaluation
            self.log_processing_step("Starting underwriting evaluation")
            underwriting_results = await self.underwriting_agent.execute({
                "application_id": application_id,
                "application_data": input_data.get("application_data", {}),
                "document_analysis": document_results
            })
            
            # Update application state
            await self.state_manager.update_application_state(
                application_id, 
                ApplicationStatus.UNDERWRITING_COMPLETED,
                {"underwriting": underwriting_results}
            )
            
            # Track decision factors
            await self.decision_tracker.record_decision(
                application_id,
                "underwriting",
                underwriting_results.get("is_approved", False),
                underwriting_results.get("decision_factors", {})
            )
            
            # Step 3: Compliance Evaluation
            self.log_processing_step("Starting compliance evaluation")
            compliance_results = await self.compliance_agent.execute({
                "application_id": application_id,
                "application_data": input_data.get("application_data", {}),
                "document_analysis": document_results,
                "underwriting_results": underwriting_results
            })
            
            # Update application state
            await self.state_manager.update_application_state(
                application_id, 
                ApplicationStatus.COMPLIANCE_CHECKED,
                {"compliance": compliance_results}
            )
            
            # Track compliance decision
            await self.decision_tracker.record_decision(
                application_id,
                "compliance",
                compliance_results.get("is_compliant", False),
                compliance_results.get("compliance_factors", {})
            )
            
            # Step 4: Generate customer response
            self.log_processing_step("Generating customer response")
            customer_response = await self.customer_agent.execute({
                "application_id": application_id,
                "request_type": "application_decision",
                "underwriting_results": underwriting_results,
                "compliance_results": compliance_results,
                "document_analysis": document_results
            })
            
            # Determine final application status
            final_status = self._determine_final_status(underwriting_results, compliance_results)
            
            # Update application state to final status
            await self.state_manager.update_application_state(
                application_id, 
                final_status,
                {"customer_response": customer_response}
            )
            
            # Compile and return results
            return {
                "application_id": application_id,
                "status": final_status,
                "underwriting_approved": underwriting_results.get("is_approved", False),
                "compliance_approved": compliance_results.get("is_compliant", False),
                "customer_response": customer_response,
                "document_analysis_summary": document_results.get("summary", {}),
                "decision_factors": {
                    "underwriting": underwriting_results.get("decision_factors", {}),
                    "compliance": compliance_results.get("compliance_factors", {})
                }
            }
            
        except Exception as e:
            # Handle errors by updating application state
            self.logger.error(f"Error processing application {application_id}: {str(e)}", exc_info=True)
            await self.state_manager.update_application_state(
                application_id, 
                ApplicationStatus.ERROR,
                {"error": str(e)}
            )
            raise

    async def get_application_status(self, application_id: str) -> Dict[str, Any]:
        """
        Get the current status of an application.
        
        Args:
            application_id: ID of the application
            
        Returns:
            Dict with application status information
        """
        try:
            # Get application state from state manager
            app_state = await self.state_manager.get_application_state(application_id)
            
            if not app_state:
                return {
                    "application_id": application_id,
                    "status": "NOT_FOUND",
                    "message": f"Application with ID {application_id} not found"
                }
            
            # Extract status information
            current_status = app_state.get("status", "UNKNOWN")
            context = app_state.get("context", {})
            history = app_state.get("history", [])
            last_updated = app_state.get("last_updated", "")
            
            # Format status information for response
            result = {
                "application_id": application_id,
                "status": current_status,
                "current_stage": self._get_stage_from_status(current_status),
                "last_updated": last_updated,
                "history": history
            }
            
            # Add additional details based on status
            if current_status == ApplicationStatus.DOCUMENTS_PROCESSED:
                # Add document status
                document_analysis = context.get("document_analysis", {})
                result["missing_documents"] = document_analysis.get("missing_documents", [])
                result["document_summary"] = document_analysis.get("summary", {})
                
            elif current_status in [ApplicationStatus.UNDERWRITING_COMPLETED, ApplicationStatus.COMPLIANCE_CHECKED]:
                # Add decision status
                underwriting = context.get("underwriting", {})
                compliance = context.get("compliance", {})
                
                result["underwriting_approved"] = underwriting.get("is_approved", False)
                result["compliance_approved"] = compliance.get("is_compliant", False)
                
            elif current_status in [ApplicationStatus.APPROVED, ApplicationStatus.REJECTED_COMPLIANCE, ApplicationStatus.REJECTED_UNDERWRITING]:
                # Add final decision details
                underwriting = context.get("underwriting", {})
                compliance = context.get("compliance", {})
                
                result["underwriting_approved"] = underwriting.get("is_approved", False)
                result["compliance_approved"] = compliance.get("is_compliant", False)
                result["decision_factors"] = {
                    "underwriting": underwriting.get("decision_factors", {}),
                    "compliance": compliance.get("compliance_factors", {})
                }
                
            # Generate status explanation
            status_explanation = self._generate_status_explanation(current_status, context)
            result["status_explanation"] = status_explanation
            
            # Estimate completion time
            result["estimated_completion"] = self._estimate_completion_time(current_status)
            
            # Get pending items
            result["pending_items"] = self._get_pending_items(current_status, context)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error retrieving application status: {str(e)}", exc_info=True)
            return {
                "application_id": application_id,
                "status": "ERROR",
                "message": f"Error retrieving application status: {str(e)}"
            }    


    def _get_stage_from_status(self, status: str) -> str:
        """Convert status to a user-friendly stage name."""
        stage_map = {
            ApplicationStatus.INITIATED: "Application Initiated",
            ApplicationStatus.DOCUMENTS_PROCESSED: "Document Review",
            ApplicationStatus.DOCUMENTS_UPDATED: "Document Review",
            ApplicationStatus.UNDERWRITING_COMPLETED: "Underwriting",
            ApplicationStatus.COMPLIANCE_CHECKED: "Compliance Review",
            ApplicationStatus.APPROVED: "Application Approved",
            ApplicationStatus.REJECTED_UNDERWRITING: "Application Rejected",
            ApplicationStatus.REJECTED_COMPLIANCE: "Application Rejected",
            ApplicationStatus.ERROR: "Processing Error"
        }
        return stage_map.get(status, "Processing")

    def _generate_status_explanation(self, status: str, context: Dict[str, Any]) -> str:
        """Generate a user-friendly explanation of the current status."""
        if status == ApplicationStatus.INITIATED:
            return "Your application has been received and is awaiting document review."
        elif status == ApplicationStatus.DOCUMENTS_PROCESSED:
            doc_analysis = context.get("document_analysis", {})
            if not doc_analysis.get("is_complete", True):
                return "We're reviewing your documents and found that some required documents are missing."
            return "Your documents have been processed and are now being reviewed."
        elif status == ApplicationStatus.DOCUMENTS_UPDATED:
            return "Your updated documents have been received and are being processed."
        elif status == ApplicationStatus.UNDERWRITING_COMPLETED:
            underwriting = context.get("underwriting", {})
            if underwriting.get("is_approved", False):
                return "Your application has passed underwriting review and is now in compliance review."
            return "Your application has been reviewed by underwriting and requires additional evaluation."
        elif status == ApplicationStatus.COMPLIANCE_CHECKED:
            compliance = context.get("compliance", {})
            if compliance.get("is_compliant", False):
                return "Your application has passed compliance review and is now in final decision stage."
            return "Your application has been reviewed for compliance and requires additional evaluation."
        elif status == ApplicationStatus.APPROVED:
            return "Congratulations! Your mortgage application has been approved."
        elif status == ApplicationStatus.REJECTED_UNDERWRITING:
            return "We're sorry, but your application did not meet our underwriting criteria."
        elif status == ApplicationStatus.REJECTED_COMPLIANCE:
            return "We're sorry, but your application could not proceed due to compliance requirements."
        elif status == ApplicationStatus.ERROR:
            return "There was an error processing your application. Our team has been notified."
        else:
            return "Your application is being processed. Thank you for your patience."

    def _estimate_completion_time(self, status: str) -> str:
        """Estimate when the application process will be completed."""
        if status == ApplicationStatus.INITIATED:
            return "7-10 business days"
        elif status == ApplicationStatus.DOCUMENTS_PROCESSED:
            return "5-7 business days"
        elif status == ApplicationStatus.UNDERWRITING_COMPLETED:
            return "3-5 business days"
        elif status == ApplicationStatus.COMPLIANCE_CHECKED:
            return "1-2 business days"
        elif status in [ApplicationStatus.APPROVED, ApplicationStatus.REJECTED_UNDERWRITING, ApplicationStatus.REJECTED_COMPLIANCE]:
            return "Processing complete"
        else:
            return "Estimated 7-10 business days"

    def _get_pending_items(self, status: str, context: Dict[str, Any]) -> List[str]:
        """Get pending items based on current status."""
        pending_items = []
        
        if status == ApplicationStatus.INITIATED:
            pending_items.append("Initial document review")
            pending_items.append("Underwriting evaluation")
            pending_items.append("Compliance check")
            
        elif status == ApplicationStatus.DOCUMENTS_PROCESSED:
            doc_analysis = context.get("document_analysis", {})
            missing_docs = doc_analysis.get("missing_documents", [])
            
            if missing_docs:
                for doc in missing_docs:
                    pending_items.append(f"Submit {doc} document")
            
            pending_items.append("Underwriting evaluation")
            pending_items.append("Compliance check")
            
        elif status == ApplicationStatus.UNDERWRITING_COMPLETED:
            underwriting = context.get("underwriting", {})
            
            if underwriting.get("conditions", []):
                for condition in underwriting.get("conditions", []):
                    pending_items.append(f"Satisfy condition: {condition}")
            
            pending_items.append("Compliance check")
            
        elif status == ApplicationStatus.COMPLIANCE_CHECKED:
            compliance = context.get("compliance", {})
            
            if compliance.get("required_actions", []):
                for action in compliance.get("required_actions", []):
                    pending_items.append(action)
            
            pending_items.append("Final decision")
            
        elif status == ApplicationStatus.APPROVED:
            pending_items.append("Sign loan documents")
            pending_items.append("Schedule closing")
            
        return pending_items


    def _prepare_initial_documents(self, input_data):
        """
        Prepare initial documents from input data.
        
        Args:
            input_data: Comprehensive application input data
            
        Returns:
            List of initial documents
        """
        documents = []
        
        # Extract and prepare documents from input data
        applicant_data = input_data.get("application_data", {}).get("applicant", {})
        loan_data = input_data.get("application_data", {}).get("loan", {})
        property_data = input_data.get("application_data", {}).get("property", {})
        
        # Add income verification document
        documents.append({
            "document_type": "INCOME_VERIFICATION",
            "content": {
                "annual_income": applicant_data.get("income"),
                "employer": applicant_data.get("employment", {}).get("employer")
            }
        })
        
        # Add property appraisal document
        documents.append({
            "document_type": "PROPERTY_APPRAISAL",
            "content": {
                "property_value": property_data.get("value"),
                "property_type": property_data.get("type"),
                "property_address": f"{property_data.get('address', '')} {property_data.get('city', '')} {property_data.get('state', '')}"
            }
        })
        
        return documents
    
    async def _handle_customer_inquiry(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a customer inquiry about an existing application.
        
        Args:
            input_data: Inquiry details and application reference
            
        Returns:
            Dict with response to the inquiry
        """
        application_id = input_data["application_id"]
        inquiry_text = input_data.get("inquiry_text", "")
        
        self.log_processing_step(f"Handling customer inquiry for {application_id}")
        
        # Retrieve current application state
        app_state = await self.state_manager.get_application_state(application_id)
        if not app_state:
            raise ValueError(f"No application found with ID {application_id}")
        
        # Get application context for the customer agent
        application_context = await self._get_application_context(application_id)
        
        # Process inquiry through customer service agent
        response = await self.customer_agent.execute({
            "application_id": application_id,
            "request_type": "customer_inquiry",
            "inquiry_text": inquiry_text,
            "application_context": application_context
        })
        
        return {
            "application_id": application_id,
            "inquiry_text": inquiry_text,
            "response": response
        }
    
    async def _update_existing_application(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing application with new information.
        
        Args:
            input_data: Updated application data
            
        Returns:
            Dict with update processing results
        """
        application_id = input_data["application_id"]
        update_type = input_data.get("update_type", "")
        
        self.log_processing_step(f"Updating existing application {application_id}")
        
        # Retrieve current application state
        app_state = await self.state_manager.get_application_state(application_id)
        if not app_state:
            raise ValueError(f"No application found with ID {application_id}")
        
        # Handle different types of updates
        if update_type == "new_documents":
            # Process new documents
            document_results = await self.document_agent.execute({
                "application_id": application_id,
                "documents": input_data.get("documents", []),
                "is_update": True
            })
            
            # Update application state with new document analysis
            current_context = app_state.get("context", {})
            current_context["document_analysis"] = document_results
            
            await self.state_manager.update_application_state(
                application_id, 
                ApplicationStatus.DOCUMENTS_UPDATED,
                current_context
            )
            
            return {
                "application_id": application_id,
                "status": "DOCUMENTS_UPDATED",
                "document_analysis": document_results
            }
            
        elif update_type == "application_data":
            # Update application data and re-process
            # This is a simplified version - in a real system, we might only reprocess affected components
            return await self._process_new_application(input_data)
        
        else:
            raise ValueError(f"Unknown update type: {update_type}")
    
    async def _get_application_context(self, application_id: str) -> Dict[str, Any]:
        """
        Get the full context for an application from state manager.
        
        Args:
            application_id: ID of the application
            
        Returns:
            Dict with full application context
        """
        app_state = await self.state_manager.get_application_state(application_id)
        if not app_state:
            raise ValueError(f"No application found with ID {application_id}")
        
        return app_state.get("context", {})
    
    def _determine_final_status(self, underwriting_results: Dict[str, Any], 
                               compliance_results: Dict[str, Any]) -> str:
        """
        Determine the final application status based on underwriting and compliance.
        
        Args:
            underwriting_results: Results from underwriting agent
            compliance_results: Results from compliance agent
            
        Returns:
            Final application status string
        """
        if not compliance_results.get("is_compliant", False):
            return ApplicationStatus.REJECTED_COMPLIANCE
        
        if not underwriting_results.get("is_approved", False):
            return ApplicationStatus.REJECTED_UNDERWRITING
            
        return ApplicationStatus.APPROVED