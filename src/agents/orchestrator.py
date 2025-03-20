"""
Orchestrator Agent Module
Coordinates the workflow between all specialized agents in the mortgage processing system.
"""

import asyncio
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent
from .document_agent import DocumentAnalysisAgent
from .underwriting_agent import UnderwritingAgent
from .compliance_agent import ComplianceAgent
from .customer_agent import CustomerServiceAgent
from ..workflow.state_manager import StateManager
from ..workflow.decision_tracker import DecisionTracker
from ..security.access_control import verify_agent_permissions
from ..data.models import ApplicationState


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
    
    async def _process_new_application(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a new mortgage application through the entire agent pipeline.
        
        Args:
            input_data: Application data including documents
            
        Returns:
            Dict with the complete processing results
        """
        application_id = input_data["application_id"]
        self.log_processing_step(f"Starting new application processing for {application_id}")
        
        # Initialize application state
        await self.state_manager.create_application_state(application_id, ApplicationState.INITIATED)
        
        try:
            # Step 1: Document Analysis
            self.log_processing_step("Starting document analysis")
            document_results = await self.document_agent.execute({
                "application_id": application_id,
                "documents": input_data.get("documents", [])
            })
            
            # Update application state
            await self.state_manager.update_application_state(
                application_id, 
                ApplicationState.DOCUMENTS_PROCESSED,
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
                ApplicationState.UNDERWRITING_COMPLETED,
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
                ApplicationState.COMPLIANCE_CHECKED,
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
                ApplicationState.ERROR,
                {"error": str(e)}
            )
            raise
    
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
                ApplicationState.DOCUMENTS_UPDATED,
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
            return ApplicationState.REJECTED_COMPLIANCE
        
        if not underwriting_results.get("is_approved", False):
            return ApplicationState.REJECTED_UNDERWRITING
            
        return ApplicationState.APPROVED