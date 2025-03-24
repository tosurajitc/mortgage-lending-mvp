"""
Multi-Agent Orchestration Manager for the Mortgage Lending Assistant.

This module provides the high-level orchestration functionality for
coordinating multiple AI agents in the mortgage lending process.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Union
import time
import traceback
import datetime
import uuid

from src.agents.orchestrator import OrchestratorAgent
from src.workflow.workflow_manager import WorkflowManager, WorkflowState
from src.workflow.error_recovery import ErrorRecoveryManager, ErrorCategory, ErrorSeverity
from src.workflow.monitoring import MonitoringManager, PerformanceTracker, WorkflowMonitoring
from src.autogen.collaboration.feedback import FeedbackLoop, FeedbackType, FeedbackEntry
from src.security.audit_logger import AuditLogger
from src.utils.exceptions import WorkflowError, AgentError, ValidationError


class OrchestrationManager:
    """
    Coordinates the overall multi-agent orchestration system.
    
    This class serves as the main entry point for the mortgage application
    processing system, bringing together workflow management, error handling,
    agent feedback, and monitoring.
    """
    
    def __init__(self, orchestrator_agent: OrchestratorAgent):
        """
        Initialize the OrchestrationManager.
        
        Args:
            orchestrator_agent: The main orchestrator agent
        """
        self.logger = logging.getLogger(__name__)
        self.orchestrator_agent = orchestrator_agent
        self.audit_logger = AuditLogger()
        
        # Initialize components
        self.workflow_manager = WorkflowManager(orchestrator_agent, self.audit_logger)
        self.error_recovery = ErrorRecoveryManager(
            state_manager=self.workflow_manager.state_manager,
            audit_logger=self.audit_logger
        )
        
        # Initialize monitoring
        monitoring, performance_tracker = create_monitoring_system()
        self.monitoring = monitoring
        self.performance_tracker = performance_tracker
        self.workflow_monitoring = WorkflowMonitoring(monitoring, performance_tracker)
        
        # Initialize feedback system
        self.feedback_manager = FeedbackLoop()
        
        # Register callbacks
        self._register_callbacks()
        
        self.logger.info("Orchestration Manager initialized")
    
    def _register_callbacks(self):
        """Register system callbacks and integrations."""
        # Register workflow state change callback for monitoring
        # self.workflow_manager.register_state_change_callback(self._on_state_change)
        
        # Register error handlers
        # self.error_recovery.register_handler(self._on_error_detected)
    
    def process_application(self, 
                          applicant_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Process a new mortgage application.
        
        Args:
            applicant_data: Initial data for the application
            
        Returns:
            Tuple[str, Dict[str, Any]]: (application_id, initial_status)
        """
        try:
            # Start performance tracking
            start_time = time.time()
            
            # Create the application
            application_id = self.workflow_manager.create_application(applicant_data)
            
            # Start monitoring
            self.workflow_monitoring.start_application_tracking(application_id)
            
            # Get initial status
            status = self.workflow_manager.get_application_status(application_id)
            
            # Record performance
            duration = time.time() - start_time
            self.performance_tracker.track_agent_execution(
                agent_type="orchestration_manager",
                operation="process_application",
                duration=duration,
                success=True,
                application_id=application_id
            )
            
            return application_id, status
            
        except Exception as e:
            # Record performance
            duration = time.time() - start_time
            self.performance_tracker.track_agent_execution(
                agent_type="orchestration_manager",
                operation="process_application",
                duration=duration,
                success=False
            )
            
            # Log the error
            self.logger.exception(f"Error processing application: {str(e)}")
            
            # Re-raise
            raise
    
    def submit_document(self,
                      application_id: str,
                      document_type: str,
                      document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit a document for an application.
        
        Args:
            application_id: The ID of the application
            document_type: Type of document
            document_data: Document content and metadata
            
        Returns:
            Dict[str, Any]: Updated application status
        """
        try:
            # Start performance tracking
            start_time = time.time()
            
            # Process the document
            success = self.workflow_manager.process_document(
                application_id=application_id,
                document_type=document_type,
                document_data=document_data
            )
            
            # Get updated status
            status = self.workflow_manager.get_application_status(application_id)
            
            # Record performance
            duration = time.time() - start_time
            self.performance_tracker.track_agent_execution(
                agent_type="orchestration_manager",
                operation="submit_document",
                duration=duration,
                success=success,
                application_id=application_id
            )
            
            return status
            
        except Exception as e:
            # Handle the exception
            self._handle_exception(
                application_id=application_id,
                exception=e,
                operation="submit_document"
            )
            
            # Get status after error handling
            status = self.workflow_manager.get_application_status(application_id)
            return status
    
    def get_application_status(self, application_id: str) -> Dict[str, Any]:
        """
        Get the current status of an application.
        
        Args:
            application_id: The ID of the application
            
        Returns:
            Dict[str, Any]: Application status
        """
        try:
            # Get the status
            status = self.workflow_manager.get_application_status(application_id)
            
            # Enhance with monitoring data
            active_apps = self.workflow_monitoring.get_active_applications_summary()
            if active_apps["total_active"] > 0:
                status["active_applications"] = active_apps["total_active"]
            
            # Add error information if available
            recent_errors = self.error_recovery.get_error_history(application_id, limit=3)
            if recent_errors:
                status["recent_errors"] = [{
                    "error_id": e["error_id"],
                    "error_type": e["error_type"],
                    "error_message": e["error_message"],
                    "timestamp": e["timestamp"]
                } for e in recent_errors]
            
            return status
            
        except Exception as e:
            # Log the error
            self.logger.exception(f"Error getting application status: {str(e)}")
            
            # Return basic error info
            return {
                "application_id": application_id,
                "error": str(e)
            }
    
    def provide_agent_feedback(self,
                             application_id: str,
                             from_agent: str,
                             to_agent: str,
                             feedback_type: str,
                             message: str,
                             score: float = 1.0,
                             context: Optional[Dict[str, Any]] = None) -> str:
        """
        Provide feedback from one agent to another.
        
        Args:
            application_id: The ID of the application
            from_agent: The agent providing feedback
            to_agent: The agent receiving feedback
            feedback_type: Type of feedback
            message: Feedback message
            score: Feedback score (0.0 to 1.0)
            context: Additional context information
            
        Returns:
            str: Feedback ID
        """
        try:
            # Create feedback
            feedback_id = self.feedback_manager.create_feedback(
                application_id=application_id,
                from_agent=from_agent,
                to_agent=to_agent,
                feedback_type=FeedbackType(feedback_type),
                message=message,
                context=context or {},
                priority=FeedbackEntry.MEDIUM,
                requires_response=score < 0.7  # Require response for low scores
            )
            
            # Log the feedback
            self.logger.info(
                f"Feedback provided from {from_agent} to {to_agent} "
                f"for application {application_id}: {message[:50]}..."
            )
            
            # Log to audit trail
            self.audit_logger.log_event(
                event_type="agent_feedback",
                application_id=application_id,
                details={
                    "feedback_id": feedback_id,
                    "from_agent": from_agent,
                    "to_agent": to_agent,
                    "feedback_type": feedback_type,
                    "score": score,
                    "timestamp": datetime.datetime.utcnow().isoformat()
                }
            )
            
            return feedback_id
            
        except Exception as e:
            # Log the error
            self.logger.exception(f"Error providing agent feedback: {str(e)}")
            
            # Return a generated ID anyway
            return str(uuid.uuid4())
    
    def handle_agent_result(self,
                          application_id: str,
                          agent_type: str,
                          task_type: str,
                          result: str,
                          details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a result from an agent.
        
        Args:
            application_id: The ID of the application
            agent_type: Type of agent
            task_type: Type of task
            result: Result of the task (success, failure, etc.)
            details: Additional details about the result
            
        Returns:
            Dict[str, Any]: Updated application status
        """
        try:
            # Start performance tracking
            start_time = time.time()
            
            # Update the application status
            status_update = {
                "agent_type": agent_type,
                "task_type": task_type,
                "result": result,
                "details": details
            }
            
            success = self.workflow_manager.update_application_status(
                application_id=application_id,
                status_update=status_update
            )
            
            # Track step change in monitoring
            current_state = self.workflow_manager.state_manager.get_state(application_id)
            if current_state:
                self.workflow_monitoring.track_step_change(
                    application_id=application_id,
                    new_step=current_state.value
                )
            
            # Get updated status
            status = self.workflow_manager.get_application_status(application_id)
            
            # Record performance
            duration = time.time() - start_time
            self.performance_tracker.track_agent_execution(
                agent_type="orchestration_manager",
                operation="handle_agent_result",
                duration=duration,
                success=success,
                application_id=application_id
            )
            
            return status
            
        except Exception as e:
            # Handle the exception
            self._handle_exception(
                application_id=application_id,
                exception=e,
                operation="handle_agent_result",
                agent_type=agent_type,
                task_type=task_type
            )
            
            # Get status after error handling
            status = self.workflow_manager.get_application_status(application_id)
            return status
    
    def complete_application(self,
                           application_id: str,
                           outcome: str,
                           details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete an application with a final outcome.
        
        Args:
            application_id: The ID of the application
            outcome: Final outcome (approved, declined, etc.)
            details: Additional details about the outcome
            
        Returns:
            Dict[str, Any]: Final application status
        """
        try:
            # Start performance tracking
            start_time = time.time()
            
            # Get the current state
            current_state = self.workflow_manager.state_manager.get_state(application_id)
            if not current_state:
                raise WorkflowError(f"Application {application_id} not found")
            
            # Determine target state based on outcome
            if outcome.lower() == "approved":
                target_state = WorkflowState.APPROVED
            elif outcome.lower() == "conditionally_approved":
                target_state = WorkflowState.CONDITIONALLY_APPROVED
            elif outcome.lower() == "declined":
                target_state = WorkflowState.DECLINED
            else:
                target_state = WorkflowState.SUSPENDED
            
            # Transition to the target state
            success = self.workflow_manager.transition_state(
                application_id=application_id,
                new_state=target_state,
                reason=f"Application {outcome}: {details.get('reason', 'No reason provided')}"
            )
            
            # Complete in monitoring
            self.workflow_monitoring.complete_application(
                application_id=application_id,
                outcome=outcome.lower()
            )
            
            # Then transition to COMPLETED state
            self.workflow_manager.transition_state(
                application_id=application_id,
                new_state=WorkflowState.COMPLETED,
                reason=f"Application processing completed with outcome: {outcome}"
            )
            
            # Get final status
            status = self.workflow_manager.get_application_status(application_id)
            
            # Record performance
            duration = time.time() - start_time
            self.performance_tracker.track_agent_execution(
                agent_type="orchestration_manager",
                operation="complete_application",
                duration=duration,
                success=success,
                application_id=application_id
            )
            
            return status
            
        except Exception as e:
            # Handle the exception
            self._handle_exception(
                application_id=application_id,
                exception=e,
                operation="complete_application"
            )
            
            # Get status after error handling
            status = self.workflow_manager.get_application_status(application_id)
            return status
    
    def resolve_error(self,
                    application_id: str,
                    error_id: str,
                    resolution_action: str,
                    resolution_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve an error that occurred during processing.
        
        Args:
            application_id: The ID of the application
            error_id: The ID of the error to resolve
            resolution_action: Action to take (retry, fallback, etc.)
            resolution_details: Additional details about the resolution
            
        Returns:
            Dict[str, Any]: Updated application status
        """
        try:
            # Start performance tracking
            start_time = time.time()
            
            # Execute the recovery action
            from src.workflow.error_recovery import RecoveryAction
            
            # Parse the action
            try:
                action = RecoveryAction(resolution_action.lower())
            except ValueError:
                action = RecoveryAction.RETRY  # Default to retry
            
            # Execute the recovery
            success = self.error_recovery.execute_recovery(
                application_id=application_id,
                error_id=error_id,
                action=action
            )
            
            # Log the resolution
            self.logger.info(
                f"Error {error_id} for application {application_id} "
                f"resolved with action {action.value}"
            )
            
            # Log to audit trail
            self.audit_logger.log_event(
                event_type="error_resolved",
                application_id=application_id,
                details={
                    "error_id": error_id,
                    "resolution_action": action.value,
                    "resolution_details": resolution_details,
                    "timestamp": datetime.datetime.utcnow().isoformat()
                }
            )
            
            # Get updated status
            status = self.workflow_manager.get_application_status(application_id)
            
            # Record performance
            duration = time.time() - start_time
            self.performance_tracker.track_agent_execution(
                agent_type="orchestration_manager",
                operation="resolve_error",
                duration=duration,
                success=success,
                application_id=application_id
            )
            
            return status
            
        except Exception as e:
            # Log the error
            self.logger.exception(f"Error resolving error {error_id}: {str(e)}")
            
            # Get status
            status = self.workflow_manager.get_application_status(application_id)
            return status
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get the overall system status.
        
        Returns:
            Dict[str, Any]: System status information
        """
        try:
            # Get health status
            health = self.monitoring.get_health_status()
            
            # Get active applications
            active_apps = self.workflow_monitoring.get_active_applications_summary()
            
            # Get step statistics
            step_stats = self.workflow_monitoring.get_step_statistics()
            
            # Get error statistics
            error_stats = self.error_recovery.get_error_statistics()
            
            # Get active alerts
            alerts = self.monitoring.get_active_alerts()
            
            return {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "health": health,
                "active_applications": active_apps,
                "step_statistics": step_stats,
                "error_statistics": error_stats,
                "alerts": [{
                    "alert_id": a["alert_id"],
                    "name": a["name"],
                    "severity": a["severity"],
                    "timestamp": a["timestamp"]
                } for a in alerts[:5]]  # Include only the first 5 alerts
            }
            
        except Exception as e:
            # Log the error
            self.logger.exception(f"Error getting system status: {str(e)}")
            
            # Return basic error info
            return {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    def _handle_exception(self, 
                        application_id: str,
                        exception: Exception,
                        operation: str,
                        agent_type: Optional[str] = None,
                        task_type: Optional[str] = None) -> None:
        """
        Handle an exception in the orchestration system.
        
        Args:
            application_id: The ID of the application
            exception: The exception that occurred
            operation: The operation being performed
            agent_type: Optional agent type
            task_type: Optional task type
        """
        # Record performance
        self.performance_tracker.track_agent_execution(
            agent_type="orchestration_manager",
            operation=operation,
            duration=0.0,  # Unknown duration
            success=False,
            application_id=application_id
        )
        
        # Log the exception
        self.logger.exception(
            f"Error in operation {operation} for application {application_id}: {str(exception)}"
        )
        
        # Create context for error handling
        context = {
            "operation": operation,
            "agent_type": agent_type,
            "task_type": task_type,
            "stack_trace": traceback.format_exc()
        }
        
        # Determine error category and severity
        if isinstance(exception, ValidationError):
            category = ErrorCategory.VALIDATION
            severity = ErrorSeverity.MEDIUM
        elif isinstance(exception, AgentError):
            category = ErrorCategory.AGENT_FAILURE
            severity = ErrorSeverity.HIGH
        elif isinstance(exception, WorkflowError):
            category = ErrorCategory.SYSTEM
            severity = ErrorSeverity.HIGH
        else:
            category = ErrorCategory.UNKNOWN
            severity = ErrorSeverity.MEDIUM
        
        # Handle the error through the error recovery system
        error_record = self.error_recovery.handle_error(
            application_id=application_id,
            error=exception,
            context=context,
            severity=severity,
            category=category
        )
        
        # Let the workflow manager know about the exception
        self.workflow_manager.handle_exception(
            application_id=application_id,
            exception=exception,
            agent_type=agent_type,
            task_type=task_type
        )
        
        # Create an alert for high severity errors
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.monitoring.create_alert(
                name=f"Error in {operation}",
                description=f"Error processing application {application_id}: {str(exception)}",
                severity=AlertSeverity.ERROR if severity == ErrorSeverity.HIGH else AlertSeverity.CRITICAL,
                context={
                    "application_id": application_id,
                    "error_id": error_record["error_id"],
                    "operation": operation
                }
            )


def create_monitoring_system() -> Tuple[MonitoringManager, PerformanceTracker]:
    """
    Create a monitoring system.
    
    Returns:
        Tuple[MonitoringManager, PerformanceTracker]: Monitoring components
    """
    # Import here to avoid circular imports
    from src.workflow.monitoring import MonitoringManager, PerformanceTracker
    
    monitoring = MonitoringManager()
    tracker = PerformanceTracker(monitoring)
    
    # Register basic health checks
    monitoring.register_health_check(
        name="system_resources",
        check_func=lambda: (True, "System resources are healthy"),
        interval_seconds=60
    )
    
    return monitoring, tracker