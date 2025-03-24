"""
Workflow Manager for the Mortgage Lending Assistant.

This module provides the WorkflowManager class that coordinates the overall
workflow of the mortgage application process, ensuring transitions between
states and proper task routing across the multi-agent system.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
import uuid
import datetime

from src.workflow.state_manager import StateManager
from src.workflow.task_router import TaskRouter
from src.workflow.decision_tracker import DecisionTracker
from src.agents.orchestrator import OrchestratorAgent
from src.security.audit_logger import AuditLogger
from src.utils.exceptions import WorkflowError, AgentError, ValidationError

# Define workflow states as an Enum for type safety
class WorkflowState(Enum):
    INITIATED = "initiated"
    DOCUMENT_COLLECTION = "document_collection"
    DOCUMENT_VALIDATION = "document_validation"
    DOCUMENT_ANALYSIS = "document_analysis"
    UNDERWRITING = "underwriting"
    COMPLIANCE_CHECK = "compliance_check"
    DECISION_PENDING = "decision_pending"
    APPROVED = "approved"
    CONDITIONALLY_APPROVED = "conditionally_approved"
    DECLINED = "declined"
    SUSPENDED = "suspended"
    COMPLETED = "completed"


class WorkflowStage(Enum):
    """High-level stages of the mortgage application process."""
    APPLICATION_INTAKE = "application_intake"
    DOCUMENT_PROCESSING = "document_processing"
    UNDERWRITING = "underwriting"
    DECISION = "decision"
    POST_DECISION = "post_decision"


class WorkflowManager:
    """
    Manages the end-to-end workflow for mortgage application processing.
    
    This class coordinates the state transitions, task routing, and
    agent interactions throughout the mortgage application lifecycle.
    """
    
    def __init__(self, 
                 orchestrator_agent: OrchestratorAgent,
                 audit_logger: Optional[AuditLogger] = None):
        """
        Initialize the WorkflowManager.
        
        Args:
            orchestrator_agent: The main orchestrator agent that coordinates all other agents
            audit_logger: Logger for audit and security purposes
        """
        self.orchestrator = orchestrator_agent
        self.state_manager = StateManager()
        self.task_router = TaskRouter()
        self.decision_tracker = DecisionTracker()
        self.audit_logger = audit_logger or AuditLogger()
        self.logger = logging.getLogger(__name__)
        
        # Register valid state transitions
        self._register_state_transitions()
        
    def _register_state_transitions(self):
        """Define valid state transitions for the workflow."""
        # From INITIATED state
        self.state_manager.register_transition(
            WorkflowState.INITIATED, 
            WorkflowState.DOCUMENT_COLLECTION
        )
        
        # From DOCUMENT_COLLECTION state
        self.state_manager.register_transition(
            WorkflowState.DOCUMENT_COLLECTION, 
            WorkflowState.DOCUMENT_VALIDATION
        )
        
        # From DOCUMENT_VALIDATION state
        self.state_manager.register_transition(
            WorkflowState.DOCUMENT_VALIDATION, 
            WorkflowState.DOCUMENT_ANALYSIS
        )
        self.state_manager.register_transition(
            WorkflowState.DOCUMENT_VALIDATION, 
            WorkflowState.DOCUMENT_COLLECTION
        )  # Return to collection if validation fails
        
        # From DOCUMENT_ANALYSIS state
        self.state_manager.register_transition(
            WorkflowState.DOCUMENT_ANALYSIS, 
            WorkflowState.UNDERWRITING
        )
        self.state_manager.register_transition(
            WorkflowState.DOCUMENT_ANALYSIS, 
            WorkflowState.DOCUMENT_COLLECTION
        )  # Return to collection if analysis identifies missing docs
        
        # From UNDERWRITING state
        self.state_manager.register_transition(
            WorkflowState.UNDERWRITING, 
            WorkflowState.COMPLIANCE_CHECK
        )
        
        # From COMPLIANCE_CHECK state
        self.state_manager.register_transition(
            WorkflowState.COMPLIANCE_CHECK, 
            WorkflowState.DECISION_PENDING
        )
        self.state_manager.register_transition(
            WorkflowState.COMPLIANCE_CHECK, 
            WorkflowState.UNDERWRITING
        )  # Return to underwriting if compliance issues found
        
        # From DECISION_PENDING state
        self.state_manager.register_transition(
            WorkflowState.DECISION_PENDING, 
            WorkflowState.APPROVED
        )
        self.state_manager.register_transition(
            WorkflowState.DECISION_PENDING, 
            WorkflowState.CONDITIONALLY_APPROVED
        )
        self.state_manager.register_transition(
            WorkflowState.DECISION_PENDING, 
            WorkflowState.DECLINED
        )
        self.state_manager.register_transition(
            WorkflowState.DECISION_PENDING, 
            WorkflowState.SUSPENDED
        )
        
        # From decision states to COMPLETED
        self.state_manager.register_transition(
            WorkflowState.APPROVED, 
            WorkflowState.COMPLETED
        )
        self.state_manager.register_transition(
            WorkflowState.CONDITIONALLY_APPROVED, 
            WorkflowState.COMPLETED
        )
        self.state_manager.register_transition(
            WorkflowState.DECLINED, 
            WorkflowState.COMPLETED
        )
        
        # From SUSPENDED back to processing
        self.state_manager.register_transition(
            WorkflowState.SUSPENDED, 
            WorkflowState.DOCUMENT_COLLECTION
        )
        self.state_manager.register_transition(
            WorkflowState.SUSPENDED, 
            WorkflowState.UNDERWRITING
        )
    
    def create_application(self, applicant_data: Dict[str, Any]) -> str:
        """
        Create a new mortgage application and initiate the workflow.
        
        Args:
            applicant_data: Initial data for the application
            
        Returns:
            application_id: Unique identifier for the new application
        """
        # Generate a unique application ID
        application_id = str(uuid.uuid4())
        
        # Initialize with the INITIATED state
        self.state_manager.set_state(application_id, WorkflowState.INITIATED)
        
        # Log the application creation
        self.audit_logger.log_event(
            event_type="application_created",
            application_id=application_id,
            details={"timestamp": datetime.datetime.utcnow().isoformat()}
        )
        
        # Store the application data
        # Note: In a real implementation, this would use a database
        application_data = {
            "application_id": application_id,
            "applicant_data": applicant_data,
            "status": WorkflowState.INITIATED.value,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "last_updated": datetime.datetime.utcnow().isoformat(),
            "documents": [],
            "decisions": [],
            "notes": []
        }
        
        # In a real implementation, save to database
        # For this MVP, we'll assume the orchestrator maintains application state
        self.orchestrator.store_application_data(application_id, application_data)
        
        # Move to document collection state
        self.transition_state(application_id, WorkflowState.DOCUMENT_COLLECTION)
        
        return application_id
    
    def transition_state(self, 
                         application_id: str, 
                         new_state: WorkflowState,
                         reason: Optional[str] = None) -> bool:
        """
        Transition an application to a new state.
        
        Args:
            application_id: The unique identifier for the application
            new_state: The state to transition to
            reason: Optional reason for the state change
            
        Returns:
            bool: True if transition was successful, False otherwise
        """
        try:
            current_state = self.state_manager.get_state(application_id)
            if current_state is None:
                raise WorkflowError(f"Application {application_id} not found")
            
            # Perform the state transition
            success = self.state_manager.transition(application_id, new_state)
            
            if success:
                # Log the transition
                self.audit_logger.log_event(
                    event_type="state_transition",
                    application_id=application_id,
                    details={
                        "from_state": current_state.value,
                        "to_state": new_state.value,
                        "reason": reason,
                        "timestamp": datetime.datetime.utcnow().isoformat()
                    }
                )
                
                # Update application data
                application_data = self.orchestrator.get_application_data(application_id)
                if application_data:
                    application_data["status"] = new_state.value
                    application_data["last_updated"] = datetime.datetime.utcnow().isoformat()
                    if reason:
                        application_data["notes"].append({
                            "type": "state_change",
                            "content": reason,
                            "timestamp": datetime.datetime.utcnow().isoformat()
                        })
                    self.orchestrator.store_application_data(application_id, application_data)
                
                # Execute any actions required for the new state
                self._execute_state_actions(application_id, new_state)
                
                return True
            else:
                self.logger.error(
                    f"Invalid state transition from {current_state} to {new_state} "
                    f"for application {application_id}"
                )
                return False
                
        except Exception as e:
            self.logger.exception(
                f"Error during state transition for application {application_id}: {str(e)}"
            )
            return False
    
    def _execute_state_actions(self, application_id: str, state: WorkflowState):
        """
        Execute actions associated with a specific workflow state.
        
        Args:
            application_id: The unique identifier for the application
            state: The current state to execute actions for
        """
        # Route to the appropriate handler based on the new state
        try:
            if state == WorkflowState.DOCUMENT_COLLECTION:
                self._handle_document_collection(application_id)
            elif state == WorkflowState.DOCUMENT_VALIDATION:
                self._handle_document_validation(application_id)
            elif state == WorkflowState.DOCUMENT_ANALYSIS:
                self._handle_document_analysis(application_id)
            elif state == WorkflowState.UNDERWRITING:
                self._handle_underwriting(application_id)
            elif state == WorkflowState.COMPLIANCE_CHECK:
                self._handle_compliance_check(application_id)
            elif state == WorkflowState.DECISION_PENDING:
                self._handle_decision(application_id)
            # Additional state handlers would be implemented here
            
        except Exception as e:
            self.logger.exception(
                f"Error executing actions for state {state.value} "
                f"for application {application_id}: {str(e)}"
            )
            # Consider implementing recovery mechanisms here
    
    def _handle_document_collection(self, application_id: str):
        """Handle actions for the document collection state."""
        # Route document collection tasks to the appropriate agent
        self.task_router.route_task(
            task_type="document_collection",
            application_id=application_id,
            orchestrator=self.orchestrator
        )
    
    def _handle_document_validation(self, application_id: str):
        """Handle actions for the document validation state."""
        # Route validation tasks to document agent
        self.task_router.route_task(
            task_type="document_validation",
            application_id=application_id,
            orchestrator=self.orchestrator
        )
    
    def _handle_document_analysis(self, application_id: str):
        """Handle actions for the document analysis state."""
        # Route analysis tasks to document agent
        self.task_router.route_task(
            task_type="document_analysis",
            application_id=application_id,
            orchestrator=self.orchestrator
        )
    
    def _handle_underwriting(self, application_id: str):
        """Handle actions for the underwriting state."""
        # Route underwriting tasks to underwriting agent
        self.task_router.route_task(
            task_type="underwriting",
            application_id=application_id,
            orchestrator=self.orchestrator
        )
    
    def _handle_compliance_check(self, application_id: str):
        """Handle actions for the compliance check state."""
        # Route compliance tasks to compliance agent
        self.task_router.route_task(
            task_type="compliance_check",
            application_id=application_id,
            orchestrator=self.orchestrator
        )
    
    def _handle_decision(self, application_id: str):
        """Handle actions for the decision pending state."""
        # Route decision tasks to decision process
        self.task_router.route_task(
            task_type="decision",
            application_id=application_id,
            orchestrator=self.orchestrator
        )
    
    def process_document(self, 
                         application_id: str, 
                         document_type: str, 
                         document_data: Dict[str, Any]) -> bool:
        """
        Process a submitted document for an application.
        
        Args:
            application_id: The unique identifier for the application
            document_type: Type of document (e.g., "income_verification", "credit_report")
            document_data: Document content and metadata
            
        Returns:
            bool: True if document was successfully processed
        """
        try:
            # Get current application state
            current_state = self.state_manager.get_state(application_id)
            if current_state not in [WorkflowState.DOCUMENT_COLLECTION, 
                                     WorkflowState.DOCUMENT_VALIDATION]:
                self.logger.warning(
                    f"Document submitted in unexpected state {current_state} "
                    f"for application {application_id}"
                )
            
            # Add document to application
            application_data = self.orchestrator.get_application_data(application_id)
            if not application_data:
                raise WorkflowError(f"Application {application_id} not found")
            
            # Add document with metadata
            document_record = {
                "document_id": str(uuid.uuid4()),
                "document_type": document_type,
                "upload_time": datetime.datetime.utcnow().isoformat(),
                "status": "received",
                "data": document_data
            }
            application_data["documents"].append(document_record)
            self.orchestrator.store_application_data(application_id, application_data)
            
            # Log document submission
            self.audit_logger.log_event(
                event_type="document_received",
                application_id=application_id,
                details={
                    "document_type": document_type,
                    "document_id": document_record["document_id"],
                    "timestamp": document_record["upload_time"]
                }
            )
            
            # If in collection state and all required documents received, 
            # move to validation state
            if current_state == WorkflowState.DOCUMENT_COLLECTION:
                # Check if all required documents are present
                # This would typically involve checking against a list of required docs
                required_docs_present = self._check_required_documents(application_id)
                if required_docs_present:
                    self.transition_state(
                        application_id, 
                        WorkflowState.DOCUMENT_VALIDATION,
                        "All required documents received"
                    )
            
            return True
            
        except Exception as e:
            self.logger.exception(
                f"Error processing document for application {application_id}: {str(e)}"
            )
            return False
    
    def _check_required_documents(self, application_id: str) -> bool:
        """
        Check if all required documents are present for an application.
        
        Args:
            application_id: The unique identifier for the application
            
        Returns:
            bool: True if all required documents are present
        """
        # In a real implementation, this would check against required document types
        # For the MVP, we'll implement a simplified version
        application_data = self.orchestrator.get_application_data(application_id)
        if not application_data:
            return False
        
        # Example required document types
        required_types = ["income_verification", "credit_report", "property_appraisal"]
        
        # Get the document types that have been submitted
        submitted_types = set(doc["document_type"] for doc in application_data.get("documents", []))
        
        # Check if all required types are in the submitted types
        return all(req_type in submitted_types for req_type in required_types)
    
    def update_application_status(self, 
                                  application_id: str, 
                                  status_update: Dict[str, Any]) -> bool:
        """
        Update the status of an application based on agent processing results.
        
        Args:
            application_id: The unique identifier for the application
            status_update: Status update details including agent results
            
        Returns:
            bool: True if status was successfully updated
        """
        try:
            # Extract update details
            agent_type = status_update.get("agent_type")
            task_type = status_update.get("task_type")
            result = status_update.get("result")
            details = status_update.get("details", {})
            
            # Log the status update
            self.audit_logger.log_event(
                event_type="status_update",
                application_id=application_id,
                details={
                    "agent_type": agent_type,
                    "task_type": task_type,
                    "result": result,
                    "timestamp": datetime.datetime.utcnow().isoformat()
                }
            )
            
            # Track the decision if one was made
            if "decision" in details:
                self.decision_tracker.record_decision(
                    application_id=application_id,
                    agent_type=agent_type,
                    decision_type=task_type,
                    decision=details["decision"],
                    reasoning=details.get("reasoning", ""),
                    confidence=details.get("confidence", 0.0)
                )
            
            # Determine the next state based on the task type and result
            next_state = self._determine_next_state(
                application_id, task_type, result, details
            )
            
            if next_state:
                return self.transition_state(
                    application_id,
                    next_state,
                    f"Based on {agent_type} {task_type} result: {result}"
                )
            
            return True
            
        except Exception as e:
            self.logger.exception(
                f"Error updating application status for {application_id}: {str(e)}"
            )
            return False
    
    def _determine_next_state(self, 
                             application_id: str,
                             task_type: str,
                             result: str,
                             details: Dict[str, Any]) -> Optional[WorkflowState]:
        """
        Determine the next workflow state based on the task result.
        
        Args:
            application_id: The unique identifier for the application
            task_type: Type of task that was completed
            result: Result of the task (success, failure, etc.)
            details: Additional details about the task result
            
        Returns:
            Optional[WorkflowState]: The next state to transition to, or None if no transition
        """
        current_state = self.state_manager.get_state(application_id)
        if not current_state:
            return None
        
        # Document validation completed
        if task_type == "document_validation":
            if result == "success":
                return WorkflowState.DOCUMENT_ANALYSIS
            elif result == "failure":
                # Missing or invalid documents
                return WorkflowState.DOCUMENT_COLLECTION
        
        # Document analysis completed
        elif task_type == "document_analysis":
            if result == "success":
                return WorkflowState.UNDERWRITING
            elif result == "failure":
                # Analysis revealed missing or inadequate documents
                return WorkflowState.DOCUMENT_COLLECTION
        
        # Underwriting completed
        elif task_type == "underwriting":
            if result == "success":
                return WorkflowState.COMPLIANCE_CHECK
            elif result == "failure":
                # Underwriting uncovered issues requiring more documentation
                return WorkflowState.DOCUMENT_COLLECTION
        
        # Compliance check completed
        elif task_type == "compliance_check":
            if result == "success":
                return WorkflowState.DECISION_PENDING
            elif result == "failure":
                # Compliance issues that need underwriting reconsideration
                return WorkflowState.UNDERWRITING
        
        # Decision rendered
        elif task_type == "decision":
            decision = details.get("decision", "").lower()
            if decision == "approved":
                return WorkflowState.APPROVED
            elif decision == "conditionally_approved":
                return WorkflowState.CONDITIONALLY_APPROVED
            elif decision == "declined":
                return WorkflowState.DECLINED
            elif decision == "suspended":
                return WorkflowState.SUSPENDED
        
        # No state transition needed
        return None
    
    def get_application_status(self, application_id: str) -> Dict[str, Any]:
        """
        Get the current status and details of an application.
        
        Args:
            application_id: The unique identifier for the application
            
        Returns:
            Dict: Application status details
        """
        try:
            # Get the current state
            current_state = self.state_manager.get_state(application_id)
            if not current_state:
                raise WorkflowError(f"Application {application_id} not found")
            
            # Get the application data
            application_data = self.orchestrator.get_application_data(application_id)
            if not application_data:
                raise WorkflowError(f"Application {application_id} data not found")
            
            # Get recent decisions
            recent_decisions = self.decision_tracker.get_decisions(
                application_id, limit=5
            )
            
            # Build the status response
            status_response = {
                "application_id": application_id,
                "current_state": current_state.value,
                "last_updated": application_data.get("last_updated"),
                "document_count": len(application_data.get("documents", [])),
                "recent_decisions": recent_decisions,
                "stage": self._get_stage_from_state(current_state).value
            }
            
            return status_response
            
        except Exception as e:
            self.logger.exception(
                f"Error getting status for application {application_id}: {str(e)}"
            )
            return {
                "application_id": application_id,
                "error": str(e)
            }
    
    def _get_stage_from_state(self, state: WorkflowState) -> WorkflowStage:
        """Map a workflow state to a high-level stage."""
        if state in [WorkflowState.INITIATED, WorkflowState.DOCUMENT_COLLECTION]:
            return WorkflowStage.APPLICATION_INTAKE
            
        elif state in [WorkflowState.DOCUMENT_VALIDATION, WorkflowState.DOCUMENT_ANALYSIS]:
            return WorkflowStage.DOCUMENT_PROCESSING
            
        elif state in [WorkflowState.UNDERWRITING, WorkflowState.COMPLIANCE_CHECK]:
            return WorkflowStage.UNDERWRITING
            
        elif state == WorkflowState.DECISION_PENDING:
            return WorkflowStage.DECISION
            
        else:  # APPROVED, CONDITIONALLY_APPROVED, DECLINED, COMPLETED, SUSPENDED
            return WorkflowStage.POST_DECISION
    
    def handle_exception(self, 
                        application_id: str,
                        exception: Exception,
                        agent_type: Optional[str] = None,
                        task_type: Optional[str] = None) -> bool:
        """
        Handle exceptions that occur during workflow processing.
        
        Args:
            application_id: The unique identifier for the application
            exception: The exception that occurred
            agent_type: The type of agent that raised the exception (if applicable)
            task_type: The type of task being performed (if applicable)
            
        Returns:
            bool: True if exception was handled, False if recovery failed
        """
        try:
            # Log the exception
            self.logger.exception(
                f"Exception in workflow for application {application_id}: {str(exception)}"
            )
            
            # Log to audit trail
            self.audit_logger.log_event(
                event_type="workflow_exception",
                application_id=application_id,
                details={
                    "agent_type": agent_type,
                    "task_type": task_type,
                    "exception_type": type(exception).__name__,
                    "exception_message": str(exception),
                    "timestamp": datetime.datetime.utcnow().isoformat()
                }
            )
            
            # Attempt recovery based on exception type
            if isinstance(exception, ValidationError):
                # Data validation issues often require returning to document collection
                return self.transition_state(
                    application_id,
                    WorkflowState.DOCUMENT_COLLECTION,
                    f"Validation error: {str(exception)}"
                )
                
            elif isinstance(exception, AgentError):
                # Agent processing errors might require manual intervention
                return self.transition_state(
                    application_id,
                    WorkflowState.SUSPENDED,
                    f"Agent processing error: {str(exception)}"
                )
                
            else:
                # Generic error handling - suspend for manual review
                return self.transition_state(
                    application_id,
                    WorkflowState.SUSPENDED,
                    f"System error: {str(exception)}"
                )
                
        except Exception as e:
            # If we can't handle the exception, log it and return False
            self.logger.critical(
                f"Failed to handle exception for application {application_id}: {str(e)}"
            )
            return False