"""
Custom exceptions for the Mortgage Lending Assistant.

This module defines custom exception classes to provide clear error handling
throughout the application.
"""

class BaseMortgageAssistantError(Exception):
    """Base exception class for all mortgage assistant errors."""
    pass


# Security-related exceptions

class SecurityError(BaseMortgageAssistantError):
    """Base class for security-related errors."""
    pass


class ValidationError(SecurityError):
    """Exception raised when input validation fails."""
    pass


class PIIExposureError(SecurityError):
    """Exception raised when PII is detected in an inappropriate context."""
    pass


class AccessDeniedError(SecurityError):
    """Exception raised when access to a resource is denied."""
    pass


class JailbreakAttemptError(SecurityError):
    """Exception raised when a jailbreak attempt is detected."""
    pass


class AuthenticationError(SecurityError):
    """Exception raised when authentication fails."""
    pass


# Data-related exceptions

class DataError(BaseMortgageAssistantError):
    """Base class for data-related errors."""
    pass


class DocumentProcessingError(DataError):
    """Exception raised when document processing fails."""
    pass


class DatabaseError(DataError):
    """Exception raised when database operations fail."""
    pass


class DataIntegrityError(DataError):
    """Exception raised when data integrity is compromised."""
    pass


# Agent-related exceptions

class AgentError(BaseMortgageAssistantError):
    """Base class for agent-related errors."""
    pass


class AgentCommunicationError(AgentError):
    """Exception raised when communication between agents fails."""
    pass


class AgentTimeoutError(AgentError):
    """Exception raised when an agent operation times out."""
    pass


class AgentProcessingError(AgentError):
    """Exception raised when an agent fails to process a request."""
    pass


# Service-related exceptions

class ServiceError(BaseMortgageAssistantError):
    """Base class for service-related errors."""
    pass


class AzureServiceError(ServiceError):
    """Exception raised when an Azure service call fails."""
    pass


class OpenAIError(ServiceError):
    """Exception raised when an OpenAI API call fails."""
    pass


class DocumentIntelligenceError(ServiceError):
    """Exception raised when Azure Document Intelligence fails."""
    pass


class SemanticKernelError(ServiceError):
    """Exception raised when a Semantic Kernel operation fails."""
    pass


class AutoGenError(ServiceError):
    """Exception raised when an AutoGen operation fails."""
    pass


# Application-related exceptions

class ApplicationError(BaseMortgageAssistantError):
    """Base class for application processing errors."""
    pass


class ApplicationIncompleteError(ApplicationError):
    """Exception raised when an application is incomplete."""
    pass


class ApplicationValidationError(ApplicationError):
    """Exception raised when an application fails validation."""
    pass


# Workflow-related exceptions

class WorkflowError(BaseMortgageAssistantError):
    """Base class for workflow-related errors."""
    pass


class WorkflowStateError(WorkflowError):
    """Exception raised when a workflow state transition is invalid."""
    pass


class TaskRoutingError(WorkflowError):
    """Exception raised when task routing fails."""
    pass