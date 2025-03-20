"""
Security module for the Mortgage Lending Assistant.

This module provides comprehensive security functionality including:
- Input validation and sanitization
- PII detection and handling
- Access control between agents and users
- Audit logging of security-relevant events
- Jailbreak prevention
"""

import logging
from .validation import ValidationError
from .pii_detector import PIIDetector
from .access_control import AccessControlManager, AccessDeniedError, AgentType
from .audit_logger import AuditLogger

logger = logging.getLogger(__name__)

# Export key classes
__all__ = [
    'ValidationError',
    'PIIDetector',
    'AccessControlManager',
    'AccessDeniedError',
    'AgentType',
    'AuditLogger',
    'SecurityManager'
]


class SecurityManager:
    """
    Central manager for all security functionality.
    
    This class provides a unified interface to all security components,
    making it easier to apply consistent security measures throughout the application.
    """
    
    def __init__(self):
        """Initialize the security manager and all security components."""
        logger.info("Initializing Security Manager")
        
        self.pii_detector = PIIDetector()
        self.access_control = AccessControlManager()
        self.audit_logger = AuditLogger()
        
        logger.info("Security Manager initialized")
    
    def validate_agent_access(self, session_token: str, resource_type: str, resource_id: str, action: str) -> bool:
        """
        Validate an agent's access to a resource and log the attempt.
        
        Args:
            session_token: Agent session token
            resource_type: Type of resource (application, document, etc.)
            resource_id: ID of the resource
            action: Action being performed
            
        Returns:
            True if access is allowed, False otherwise
        """
        try:
            # First, validate the session
            if not self.access_control.validate_agent_session(session_token):
                self.audit_logger.log_auth_event(
                    user_id=None,
                    agent_id=session_token,  # We don't know the real ID yet
                    action="validate_session",
                    success=False,
                    details={"resource_type": resource_type, "resource_id": resource_id}
                )
                return False
            
            # Get agent details
            agent_session = self.access_control.agent_sessions.get(session_token, {})
            agent_id = agent_session.get("agent_id")
            agent_type = agent_session.get("agent_type")
            
            # For field access, check specific field permissions
            if resource_type == "field":
                has_access = self.access_control.can_agent_access_field(session_token, resource_id)
                
                # Log the access attempt
                self.audit_logger.log_agent_action(
                    agent_id=agent_id,
                    action=f"access_{action}",
                    resource_id=resource_id,
                    success=has_access,
                    details={
                        "agent_type": agent_type,
                        "field_path": resource_id
                    }
                )
                
                return has_access
            
            # For document access
            elif resource_type == "document":
                # In a real system, you'd look up which application this document belongs to
                # and check permissions on that application
                application_id = "unknown"  # Placeholder
                
                # Log the access attempt (simplified for MVP)
                self.audit_logger.log_document_access(
                    user_id=None,
                    agent_id=agent_id,
                    document_id=resource_id,
                    application_id=application_id,
                    action=action,
                    success=True,  # Simplified for MVP
                    details={
                        "agent_type": agent_type
                    }
                )
                
                return True  # Simplified for MVP
            
            # For application access
            elif resource_type == "application":
                # Log the access attempt
                self.audit_logger.log_application_access(
                    user_id=None,
                    agent_id=agent_id,
                    application_id=resource_id,
                    action=action,
                    success=True,  # Simplified for MVP
                    details={
                        "agent_type": agent_type
                    }
                )
                
                return True  # Simplified for MVP
            
            # Default case
            else:
                self.audit_logger.log_agent_action(
                    agent_id=agent_id,
                    action=action,
                    resource_id=f"{resource_type}:{resource_id}",
                    success=False,
                    details={
                        "agent_type": agent_type,
                        "reason": "Unknown resource type"
                    }
                )
                return False
            
        except Exception as e:
            logger.error(f"Error validating agent access: {str(e)}")
            return False
    
    def validate_user_access(self, session_token: str, resource_type: str, resource_id: str, action: str) -> bool:
        """
        Validate a user's access to a resource and log the attempt.
        
        Args:
            session_token: User session token
            resource_type: Type of resource (application, document, etc.)
            resource_id: ID of the resource
            action: Action being performed
            
        Returns:
            True if access is allowed, False otherwise
        """
        try:
            # First, validate the session
            if not self.access_control.validate_user_session(session_token):
                self.audit_logger.log_auth_event(
                    user_id=session_token,  # We don't know the real ID yet
                    agent_id=None,
                    action="validate_session",
                    success=False,
                    details={"resource_type": resource_type, "resource_id": resource_id}
                )
                return False
            
            # Get user details
            user_session = self.access_control.user_sessions.get(session_token, {})
            user_id = user_session.get("user_id")
            role = user_session.get("role")
            
            # For application access
            if resource_type == "application":
                has_access = self.access_control.can_user_access_application(
                    session_token, resource_id, user_id
                )
                
                # Log the access attempt
                self.audit_logger.log_application_access(
                    user_id=user_id,
                    agent_id=None,
                    application_id=resource_id,
                    action=action,
                    success=has_access,
                    details={
                        "role": role
                    }
                )
                
                return has_access
            
            # For document access (simplified for MVP)
            elif resource_type == "document":
                # In a real system, you'd check if this document belongs to an application
                # that the user has access to
                application_id = "unknown"  # Placeholder
                
                # Log the access attempt
                self.audit_logger.log_document_access(
                    user_id=user_id,
                    agent_id=None,
                    document_id=resource_id,
                    application_id=application_id,
                    action=action,
                    success=True,  # Simplified for MVP
                    details={
                        "role": role
                    }
                )
                
                return True  # Simplified for MVP
            
            # Default case
            else:
                self.audit_logger.log_auth_event(
                    user_id=user_id,
                    agent_id=None,
                    action=action,
                    success=False,
                    details={
                        "role": role,
                        "resource_type": resource_type,
                        "resource_id": resource_id,
                        "reason": "Unknown resource type"
                    }
                )
                return False
            
        except Exception as e:
            logger.error(f"Error validating user access: {str(e)}")
            return False
    
    def scan_for_pii(self, data: dict) -> list:
        """
        Scan data for unexpected PII.
        
        Args:
            data: Data to scan
            
        Returns:
            List of PII findings
        """
        findings = self.pii_detector.detect_unexpected_pii(data)
        
        # Log any findings
        if findings:
            self.audit_logger.log_security_event(
                event_subtype="pii_detected",
                user_id=None,
                agent_id=None,
                action="scan_data",
                resource_id=None,
                success=True,
                details={
                    "findings_count": len(findings),
                    "finding_types": list(set(finding[1] for finding in findings))
                }
            )
        
        return findings
    
    def check_for_jailbreak(self, text: str) -> tuple:
        """
        Check text for potential jailbreak attempts.
        
        Args:
            text: Text to check
            
        Returns:
            Tuple of (is_jailbreak, reason)
        """
        from .validation import detect_jailbreak_attempts
        
        is_jailbreak, reason = detect_jailbreak_attempts(text)
        
        # Log any findings
        if is_jailbreak:
            self.audit_logger.log_security_event(
                event_subtype="jailbreak_attempt",
                user_id=None,  # We would add this in a real scenario
                agent_id=None,
                action="process_input",
                resource_id=None,
                success=False,  # We blocked it
                details={
                    "reason": reason,
                    "text_sample": text[:100] + "..." if len(text) > 100 else text
                }
            )
        
        return is_jailbreak, reason
    
    def sanitize_output_for_user(self, data: dict, user_role: str) -> dict:
        """
        Sanitize output data based on user role.
        
        Args:
            data: Data to sanitize
            user_role: Role of the user
            
        Returns:
            Sanitized data appropriate for the user role
        """
        # Simplified for MVP - in a real system, you'd filter based on role permissions
        # For example, customers shouldn't see internal risk assessments
        
        # Always redact any PII that might have leaked through
        redacted_data = self.pii_detector.redact_pii_in_dict(data)
        
        # Filter based on role
        if user_role == "customer":
            # Remove internal fields
            if "internal_notes" in redacted_data:
                del redacted_data["internal_notes"]
            if "risk_assessment" in redacted_data:
                del redacted_data["risk_assessment"]
        
        return redacted_data
    
    def filter_data_for_agent(self, session_token: str, data: dict) -> dict:
        """
        Filter data to only include fields an agent has access to.
        
        Args:
            session_token: Agent session token
            data: Data to filter
            
        Returns:
            Filtered data
        """
        try:
            # Use the access control manager to filter the data
            filtered_data = self.access_control.filter_data_for_agent(session_token, data)
            
            # Get agent details for logging
            agent_session = self.access_control.agent_sessions.get(session_token, {})
            agent_id = agent_session.get("agent_id")
            
            # Log the data access
            self.audit_logger.log_agent_action(
                agent_id=agent_id,
                action="access_data",
                resource_id=None,
                success=True,
                details={
                    "field_count": self._count_fields(filtered_data)
                }
            )
            
            return filtered_data
            
        except Exception as e:
            logger.error(f"Error filtering data for agent: {str(e)}")
            return {}
    
    def _count_fields(self, data: dict) -> int:
        """
        Count the number of fields (leaf nodes) in a nested dictionary.
        
        Args:
            data: Dictionary to count fields in
            
        Returns:
            Number of fields
        """
        count = 0
        
        def _count_recursive(d):
            nonlocal count
            
            if isinstance(d, dict):
                for key, value in d.items():
                    if isinstance(value, (dict, list)):
                        _count_recursive(value)
                    else:
                        count += 1
            elif isinstance(d, list):
                for item in d:
                    if isinstance(item, (dict, list)):
                        _count_recursive(item)
                    else:
                        count += 1
        
        _count_recursive(data)
        return count
    
    def secure_store_application(self, application_data: dict) -> tuple:
        """
        Securely store an application, separating sensitive data.
        
        Args:
            application_data: Application data to store
            
        Returns:
            Tuple of (application_id, success)
        """
        try:
            # Generate application ID (would be done by the database in reality)
            application_id = application_data.get("application_id", "app-" + str(hash(str(application_data)) % 10000))
            
            # Scan for unexpected PII
            pii_findings = self.scan_for_pii(application_data)
            
            # Separate sensitive data for secure storage
            secure_fields = {"primary_applicant.ssn_last_four", "co_applicant.ssn_last_four", "bank_account_number"}
            
            # In a real system, you'd encrypt the sensitive data
            # For MVP, we just log that we would do this
            self.pii_detector.securely_store_pii_data(application_data, secure_fields)
            
            # Log the storage action
            self.audit_logger.log_event(
                event_type="application_submission",
                user_id=None,  # Would be set in real scenario
                agent_id=None,
                action="store_application",
                resource_id=application_id,
                details={
                    "pii_findings": len(pii_findings) > 0,
                    "fields_secured": list(secure_fields)
                },
                success=True
            )
            
            return application_id, True
            
        except Exception as e:
            logger.error(f"Error securing application data: {str(e)}")
            return None, False
    
    def verify_log_integrity(self) -> bool:
        """
        Verify the integrity of audit logs.
        
        Returns:
            True if logs are intact, False if tampering detected
        """
        return self.audit_logger.verify_log_integrity()
    
    def register_agent(self, agent_id: str, agent_type: str, api_key: str) -> str:
        """
        Register an agent with the security system.
        
        Args:
            agent_id: Agent ID
            agent_type: Type of agent
            api_key: API key for authentication
            
        Returns:
            Session token
        """
        session_token = self.access_control.register_agent(agent_id, agent_type, api_key)
        
        # Log the registration
        self.audit_logger.log_agent_action(
            agent_id=agent_id,
            action="register",
            resource_id=None,
            success=True,
            details={
                "agent_type": agent_type
            }
        )
        
        return session_token
    
    def register_user(self, user_id: str, role: str, api_key: str) -> str:
        """
        Register a user with the security system.
        
        Args:
            user_id: User ID
            role: User role
            api_key: API key for authentication
            
        Returns:
            Session token
        """
        session_token = self.access_control.register_user(user_id, role, api_key)
        
        # Log the registration
        self.audit_logger.log_auth_event(
            user_id=user_id,
            agent_id=None,
            action="register",
            success=True,
            details={
                "role": role
            }
        )
        
        return session_token