"""
Error handling and recovery mechanisms for the mortgage application workflow.

This module provides classes and functions for detecting, handling, and recovering from
errors that may occur during the mortgage application processing workflow.
"""

import logging
from typing import Dict, List, Optional, Any, Callable, Union
import traceback
from enum import Enum
import datetime
import uuid
import json

from src.utils.exceptions import WorkflowError, AgentError, ValidationError
from src.workflow.state_manager import StateManager
from src.workflow.decision_tracker import DecisionTracker
from src.security.audit_logger import AuditLogger


class ErrorSeverity(Enum):
    """Severity levels for errors in the workflow."""
    LOW = "low"           # Minor issue, automatic recovery possible
    MEDIUM = "medium"     # Significant issue, requires attention but not critical
    HIGH = "high"         # Serious issue, requires immediate attention
    CRITICAL = "critical" # System failure, requires emergency intervention


class ErrorCategory(Enum):
    """Categories of errors that can occur in the workflow."""
    VALIDATION = "validation"           # Data validation errors
    DOCUMENT_PROCESSING = "document"    # Document processing errors
    AGENT_FAILURE = "agent"             # Agent processing failure
    COMMUNICATION = "communication"     # Communication failures between components
    SECURITY = "security"               # Security-related issues
    SYSTEM = "system"                   # System-level failures
    INTEGRATION = "integration"         # Integration issues with external systems
    DATA = "data"                       # Data inconsistency or corruption
    UNKNOWN = "unknown"                 # Unclassified errors


class RecoveryAction(Enum):
    """Possible recovery actions for workflow errors."""
    RETRY = "retry"                       # Retry the failed operation
    FALLBACK = "fallback"                 # Use fallback processing path
    ESCALATE = "escalate"                 # Escalate to human operator
    SUSPEND = "suspend"                   # Suspend the application for review
    REVERT = "revert"                     # Revert to a previous state
    RESTART = "restart"                   # Restart the current process
    ALTERNATE = "alternate"               # Use alternative processing method
    IGNORE = "ignore"                     # Ignore the error and continue
    DIAGNOSTIC = "diagnostic"             # Run diagnostic routine


class ErrorRecoveryManager:
    """
    Manages error detection, handling, and recovery for the workflow.
    
    This class provides mechanisms to handle errors gracefully,
    attempt automatic recovery where possible, and track error patterns.
    """
    
    def __init__(self, 
                 state_manager: Optional[StateManager] = None,
                 audit_logger: Optional[AuditLogger] = None):
        """
        Initialize the ErrorRecoveryManager.
        
        Args:
            state_manager: Optional state manager for workflow state access
            audit_logger: Optional audit logger for security logging
        """
        self.state_manager = state_manager
        self.audit_logger = audit_logger or AuditLogger()
        self.logger = logging.getLogger(__name__)
        self.error_store = {}  # In-memory storage for error records
        self.recovery_strategies = {}  # Registered recovery strategies
        
        # Register default recovery strategies
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """Register default error recovery strategies."""
        # Document validation errors
        self.register_recovery_strategy(
            ErrorCategory.VALIDATION,
            self._handle_validation_error
        )
        
        # Agent failures
        self.register_recovery_strategy(
            ErrorCategory.AGENT_FAILURE,
            self._handle_agent_failure
        )
        
        # Communication failures
        self.register_recovery_strategy(
            ErrorCategory.COMMUNICATION,
            self._handle_communication_error
        )
        
        # System errors
        self.register_recovery_strategy(
            ErrorCategory.SYSTEM,
            self._handle_system_error
        )
    
    def register_recovery_strategy(self, 
                                  error_category: ErrorCategory,
                                  handler: Callable[[str, Dict[str, Any]], List[RecoveryAction]]):
        """
        Register a recovery strategy for a specific error category.
        
        Args:
            error_category: The category of error to handle
            handler: Function that returns a list of recovery actions
        """
        self.recovery_strategies[error_category] = handler
        self.logger.info(f"Registered recovery strategy for {error_category.value} errors")
    
    def handle_error(self,
                    application_id: str,
                    error: Exception,
                    context: Dict[str, Any],
                    severity: Optional[ErrorSeverity] = None,
                    category: Optional[ErrorCategory] = None) -> Dict[str, Any]:
        """
        Handle an error that occurred during workflow processing.
        
        Args:
            application_id: The ID of the application being processed
            error: The exception that occurred
            context: Additional context about the error
            severity: Optional severity override (auto-detected if not provided)
            category: Optional category override (auto-detected if not provided)
            
        Returns:
            Dict[str, Any]: Error record with recovery actions
        """
        # Determine error severity if not provided
        if severity is None:
            severity = self._determine_severity(error)
        
        # Determine error category if not provided
        if category is None:
            category = self._determine_category(error)
        
        # Create error record
        error_id = str(uuid.uuid4())
        timestamp = datetime.datetime.utcnow().isoformat()
        
        error_record = {
            "error_id": error_id,
            "application_id": application_id,
            "timestamp": timestamp,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "severity": severity.value,
            "category": category.value,
            "context": context,
            "recovery_attempts": [],
            "status": "detected"
        }
        
        # Store the error record
        if application_id not in self.error_store:
            self.error_store[application_id] = []
        
        self.error_store[application_id].append(error_record)
        
        # Log the error
        self.logger.error(
            f"Error detected: ID {error_id}, application {application_id}, "
            f"type {error_record['error_type']}, message: {error_record['error_message']}"
        )
        
        # Log to audit trail
        self.audit_logger.log_event(
            event_type="error_detected",
            application_id=application_id,
            details={
                "error_id": error_id,
                "error_type": error_record["error_type"],
                "severity": severity.value,
                "category": category.value,
                "timestamp": timestamp
            }
        )
        
        # Determine recovery actions
        recovery_actions = self._determine_recovery_actions(
            application_id, error_record
        )
        
        # Add recovery actions to the record
        error_record["recovery_actions"] = [action.value for action in recovery_actions]
        
        # Update the error record
        self._update_error_record(application_id, error_id, {
            "recovery_actions": error_record["recovery_actions"],
            "status": "recovery_planned"
        })
        
        return error_record
    
    def _determine_severity(self, error: Exception) -> ErrorSeverity:
        """
        Determine the severity of an error based on its type.
        
        Args:
            error: The exception to evaluate
            
        Returns:
            ErrorSeverity: The determined severity level
        """
        if isinstance(error, ValidationError):
            return ErrorSeverity.MEDIUM
        elif isinstance(error, AgentError):
            return ErrorSeverity.HIGH
        elif isinstance(error, WorkflowError):
            return ErrorSeverity.HIGH
        elif isinstance(error, (RuntimeError, SystemError)):
            return ErrorSeverity.CRITICAL
        else:
            return ErrorSeverity.MEDIUM
    
    def _determine_category(self, error: Exception) -> ErrorCategory:
        """
        Determine the category of an error based on its type.
        
        Args:
            error: The exception to evaluate
            
        Returns:
            ErrorCategory: The determined error category
        """
        if isinstance(error, ValidationError):
            return ErrorCategory.VALIDATION
        elif isinstance(error, AgentError):
            return ErrorCategory.AGENT_FAILURE
        elif isinstance(error, ConnectionError):
            return ErrorCategory.COMMUNICATION
        elif isinstance(error, (OSError, SystemError)):
            return ErrorCategory.SYSTEM
        else:
            return ErrorCategory.UNKNOWN
    
    def _determine_recovery_actions(self, 
                                  application_id: str, 
                                  error_record: Dict[str, Any]) -> List[RecoveryAction]:
        """
        Determine appropriate recovery actions for an error.
        
        Args:
            application_id: The ID of the application
            error_record: The error record
            
        Returns:
            List[RecoveryAction]: List of recommended recovery actions
        """
        category = ErrorCategory(error_record["category"])
        
        # If we have a registered strategy for this category, use it
        if category in self.recovery_strategies:
            return self.recovery_strategies[category](application_id, error_record)
        
        # Default recovery strategy based on severity
        severity = ErrorSeverity(error_record["severity"])
        
        if severity == ErrorSeverity.LOW:
            return [RecoveryAction.RETRY]
        elif severity == ErrorSeverity.MEDIUM:
            return [RecoveryAction.RETRY, RecoveryAction.FALLBACK]
        elif severity == ErrorSeverity.HIGH:
            return [RecoveryAction.ESCALATE, RecoveryAction.SUSPEND]
        else:  # CRITICAL
            return [RecoveryAction.ESCALATE, RecoveryAction.SUSPEND]
    
    def _handle_validation_error(self, 
                               application_id: str, 
                               error_record: Dict[str, Any]) -> List[RecoveryAction]:
        """
        Handle validation errors.
        
        Args:
            application_id: The ID of the application
            error_record: The error record
            
        Returns:
            List[RecoveryAction]: List of recommended recovery actions
        """
        # Validation errors typically require returning to data collection
        # or fixing the data issue
        return [RecoveryAction.REVERT, RecoveryAction.ALTERNATE]
    
    def _handle_agent_failure(self, 
                            application_id: str, 
                            error_record: Dict[str, Any]) -> List[RecoveryAction]:
        """
        Handle agent processing failures.
        
        Args:
            application_id: The ID of the application
            error_record: The error record
            
        Returns:
            List[RecoveryAction]: List of recommended recovery actions
        """
        # Agent failures may be temporary or indicate a deeper issue
        severity = ErrorSeverity(error_record["severity"])
        
        if severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM]:
            return [RecoveryAction.RETRY, RecoveryAction.ALTERNATE]
        else:
            return [RecoveryAction.DIAGNOSTIC, RecoveryAction.ESCALATE]
    
    def _handle_communication_error(self, 
                                  application_id: str, 
                                  error_record: Dict[str, Any]) -> List[RecoveryAction]:
        """
        Handle communication errors.
        
        Args:
            application_id: The ID of the application
            error_record: The error record
            
        Returns:
            List[RecoveryAction]: List of recommended recovery actions
        """
        # Communication errors often benefit from retries
        return [RecoveryAction.RETRY, RecoveryAction.FALLBACK]
    
    def _handle_system_error(self, 
                           application_id: str, 
                           error_record: Dict[str, Any]) -> List[RecoveryAction]:
        """
        Handle system-level errors.
        
        Args:
            application_id: The ID of the application
            error_record: The error record
            
        Returns:
            List[RecoveryAction]: List of recommended recovery actions
        """
        # System errors may require more drastic measures
        return [RecoveryAction.ESCALATE, RecoveryAction.SUSPEND]
    
    def execute_recovery(self, 
                        application_id: str, 
                        error_id: str, 
                        action: RecoveryAction) -> bool:
        """
        Execute a specific recovery action for an error.
        
        Args:
            application_id: The ID of the application
            error_id: The ID of the error
            action: The recovery action to execute
            
        Returns:
            bool: True if recovery action was executed successfully
        """
        # Find the error record
        error_record = self._find_error_record(application_id, error_id)
        if not error_record:
            self.logger.error(f"Error ID {error_id} not found for application {application_id}")
            return False
        
        # Log the recovery attempt
        timestamp = datetime.datetime.utcnow().isoformat()
        recovery_attempt = {
            "action": action.value,
            "timestamp": timestamp,
            "result": "pending"
        }
        
        error_record["recovery_attempts"].append(recovery_attempt)
        error_record["status"] = "recovery_in_progress"
        
        self.logger.info(
            f"Executing recovery action {action.value} for error {error_id} "
            f"on application {application_id}"
        )
        
        # Log to audit trail
        self.audit_logger.log_event(
            event_type="recovery_attempt",
            application_id=application_id,
            details={
                "error_id": error_id,
                "action": action.value,
                "timestamp": timestamp
            }
        )
        
        # Execute the appropriate recovery action
        try:
            if action == RecoveryAction.RETRY:
                success = self._execute_retry(application_id, error_record)
            elif action == RecoveryAction.FALLBACK:
                success = self._execute_fallback(application_id, error_record)
            elif action == RecoveryAction.REVERT:
                success = self._execute_revert(application_id, error_record)
            elif action == RecoveryAction.RESTART:
                success = self._execute_restart(application_id, error_record)
            elif action == RecoveryAction.ALTERNATE:
                success = self._execute_alternate(application_id, error_record)
            elif action == RecoveryAction.DIAGNOSTIC:
                success = self._execute_diagnostic(application_id, error_record)
            elif action == RecoveryAction.ESCALATE:
                success = self._execute_escalate(application_id, error_record)
            elif action == RecoveryAction.SUSPEND:
                success = self._execute_suspend(application_id, error_record)
            elif action == RecoveryAction.IGNORE:
                success = self._execute_ignore(application_id, error_record)
            else:
                self.logger.error(f"Unknown recovery action: {action.value}")
                success = False
            
            # Update the recovery attempt result
            recovery_attempt["result"] = "success" if success else "failure"
            
            # Update the error record status
            if success:
                error_record["status"] = "recovery_successful"
            else:
                error_record["status"] = "recovery_failed"
            
            return success
            
        except Exception as e:
            self.logger.exception(
                f"Error executing recovery action {action.value} for error {error_id}: {str(e)}"
            )
            
            # Update the recovery attempt result
            recovery_attempt["result"] = "error"
            recovery_attempt["error"] = str(e)
            
            # Update the error record status
            error_record["status"] = "recovery_error"
            
            return False
    
    def _execute_retry(self, application_id: str, error_record: Dict[str, Any]) -> bool:
        """
        Execute a retry recovery action.
        
        Args:
            application_id: The ID of the application
            error_record: The error record
            
        Returns:
            bool: True if the action was executed successfully
        """
        # In a real implementation, this would retry the failed operation
        # For MVP purposes, we'll just simulate success
        self.logger.info(f"Simulating retry for application {application_id}")
        return True
    
    def _execute_fallback(self, application_id: str, error_record: Dict[str, Any]) -> bool:
        """
        Execute a fallback recovery action.
        
        Args:
            application_id: The ID of the application
            error_record: The error record
            
        Returns:
            bool: True if the action was executed successfully
        """
        # In a real implementation, this would use a fallback processing path
        # For MVP purposes, we'll just simulate success
        self.logger.info(f"Simulating fallback for application {application_id}")
        return True
    
    def _execute_revert(self, application_id: str, error_record: Dict[str, Any]) -> bool:
        """
        Execute a revert recovery action.
        
        Args:
            application_id: The ID of the application
            error_record: The error record
            
        Returns:
            bool: True if the action was executed successfully
        """
        # In a real implementation, this would revert to a previous state
        # For MVP purposes, we'll just simulate success
        self.logger.info(f"Simulating revert for application {application_id}")
        return True
    
    def _execute_restart(self, application_id: str, error_record: Dict[str, Any]) -> bool:
        """
        Execute a restart recovery action.
        
        Args:
            application_id: The ID of the application
            error_record: The error record
            
        Returns:
            bool: True if the action was executed successfully
        """
        # In a real implementation, this would restart the current process
        # For MVP purposes, we'll just simulate success
        self.logger.info(f"Simulating restart for application {application_id}")
        return True
    
    def _execute_alternate(self, application_id: str, error_record: Dict[str, Any]) -> bool:
        """
        Execute an alternate processing method recovery action.
        
        Args:
            application_id: The ID of the application
            error_record: The error record
            
        Returns:
            bool: True if the action was executed successfully
        """
        # In a real implementation, this would use an alternative processing method
        # For MVP purposes, we'll just simulate success
        self.logger.info(f"Simulating alternate processing for application {application_id}")
        return True
    
    def _execute_diagnostic(self, application_id: str, error_record: Dict[str, Any]) -> bool:
        """
        Execute a diagnostic recovery action.
        
        Args:
            application_id: The ID of the application
            error_record: The error record
            
        Returns:
            bool: True if the action was executed successfully
        """
        # In a real implementation, this would run diagnostic routines
        # For MVP purposes, we'll just simulate success
        self.logger.info(f"Simulating diagnostics for application {application_id}")
        return True
    
    def _execute_escalate(self, application_id: str, error_record: Dict[str, Any]) -> bool:
        """
        Execute an escalation recovery action.
        
        Args:
            application_id: The ID of the application
            error_record: The error record
            
        Returns:
            bool: True if the action was executed successfully
        """
        # In a real implementation, this would escalate to a human operator
        # For MVP purposes, we'll just simulate success
        self.logger.info(f"Simulating escalation for application {application_id}")
        return True
    
    def _execute_suspend(self, application_id: str, error_record: Dict[str, Any]) -> bool:
        """
        Execute a suspend recovery action.
        
        Args:
            application_id: The ID of the application
            error_record: The error record
            
        Returns:
            bool: True if the action was executed successfully
        """
        # In a real implementation, this would suspend the application
        # For MVP purposes, we'll just simulate success
        self.logger.info(f"Simulating suspension for application {application_id}")
        return True
    
    def _execute_ignore(self, application_id: str, error_record: Dict[str, Any]) -> bool:
        """
        Execute an ignore recovery action.
        
        Args:
            application_id: The ID of the application
            error_record: The error record
            
        Returns:
            bool: True if the action was executed successfully
        """
        # Simply mark the error as handled and continue
        self.logger.info(f"Ignoring error {error_record['error_id']} for application {application_id}")
        return True
    
    def _find_error_record(self, application_id: str, error_id: str) -> Optional[Dict[str, Any]]:
        """
        Find an error record by ID.
        
        Args:
            application_id: The ID of the application
            error_id: The ID of the error to find
            
        Returns:
            Optional[Dict[str, Any]]: The error record if found, None otherwise
        """
        if application_id not in self.error_store:
            return None
        
        for error_record in self.error_store[application_id]:
            if error_record["error_id"] == error_id:
                return error_record
        
        return None
    
    def _update_error_record(self, application_id: str, error_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an error record.
        
        Args:
            application_id: The ID of the application
            error_id: The ID of the error to update
            updates: Dictionary of fields to update
            
        Returns:
            bool: True if the error record was updated, False otherwise
        """
        error_record = self._find_error_record(application_id, error_id)
        if not error_record:
            return False
        
        # Update the error record
        error_record.update(updates)
        return True
    
    def get_error_history(self, application_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the error history for an application.
        
        Args:
            application_id: The ID of the application
            limit: Maximum number of error records to return
            
        Returns:
            List[Dict[str, Any]]: List of error records
        """
        if application_id not in self.error_store:
            return []
        
        # Sort errors by timestamp (most recent first)
        sorted_errors = sorted(
            self.error_store[application_id],
            key=lambda e: e["timestamp"],
            reverse=True
        )
        
        return sorted_errors[:limit]
    
    def get_error_statistics(self, application_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics on errors.
        
        Args:
            application_id: Optional application ID to filter by
            
        Returns:
            Dict[str, Any]: Error statistics
        """
        stats = {
            "total_errors": 0,
            "by_severity": {},
            "by_category": {},
            "by_status": {},
            "recovery_success_rate": 0.0
        }
        
        # Initialize counters
        for severity in ErrorSeverity:
            stats["by_severity"][severity.value] = 0
        
        for category in ErrorCategory:
            stats["by_category"][category.value] = 0
        
        stats["by_status"] = {
            "detected": 0,
            "recovery_planned": 0,
            "recovery_in_progress": 0,
            "recovery_successful": 0,
            "recovery_failed": 0,
            "recovery_error": 0
        }
        
        # Calculate statistics
        error_records = []
        
        if application_id:
            # Get error records for a specific application
            if application_id in self.error_store:
                error_records = self.error_store[application_id]
        else:
            # Get all error records
            for app_errors in self.error_store.values():
                error_records.extend(app_errors)
        
        # Update counters
        stats["total_errors"] = len(error_records)
        
        for error in error_records:
            # By severity
            if error["severity"] in stats["by_severity"]:
                stats["by_severity"][error["severity"]] += 1
            
            # By category
            if error["category"] in stats["by_category"]:
                stats["by_category"][error["category"]] += 1
            
            # By status
            if error["status"] in stats["by_status"]:
                stats["by_status"][error["status"]] += 1
        
        # Calculate recovery success rate
        recovery_attempts = stats["by_status"]["recovery_successful"] + stats["by_status"]["recovery_failed"]
        if recovery_attempts > 0:
            stats["recovery_success_rate"] = (
                stats["by_status"]["recovery_successful"] / recovery_attempts
            )
        
        return stats