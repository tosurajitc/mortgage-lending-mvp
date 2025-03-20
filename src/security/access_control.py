"""
Access control functionality for the Mortgage Lending Assistant.

This module provides access control between agents and for different user roles,
implementing the principle of least privilege to protect sensitive data.
"""

import json
import logging
from typing import Dict, List, Set, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

# Load security configuration
try:
    with open("config/security_config.json", "r") as f:
        SECURITY_CONFIG = json.load(f)
        ACCESS_CONTROL_CONFIG = SECURITY_CONFIG.get("access_control", {})
        ROLE_PERMISSIONS = ACCESS_CONTROL_CONFIG.get("roles", {})
except Exception as e:
    logger.error(f"Failed to load security configuration: {str(e)}")
    # Default values if config fails to load
    ROLE_PERMISSIONS = {
        "admin": {"can_access_all": True},
        "loan_officer": {
            "can_view_applications": True,
            "can_modify_applications": True,
            "can_access_documents": True,
            "can_make_decisions": True
        },
        "customer": {
            "can_view_own_application": True,
            "can_submit_documents": True,
            "can_update_own_info": True
        }
    }


class AgentType(str, Enum):
    """Types of agents in the system."""
    ORCHESTRATOR = "orchestrator"
    DOCUMENT = "document"
    UNDERWRITING = "underwriting"
    COMPLIANCE = "compliance"
    CUSTOMER = "customer"


# Define which data each agent type can access
AGENT_ACCESS_RIGHTS = {
    AgentType.ORCHESTRATOR: {
        "can_access_all": True  # Orchestrator needs access to everything
    },
    AgentType.DOCUMENT: {
        "can_access": ["documents", "primary_applicant.name", "co_applicant.name", 
                      "property_info", "application_id", "status"],
        "can_modify": ["documents", "document_analysis_results"]
    },
    AgentType.UNDERWRITING: {
        "can_access": ["primary_applicant", "co_applicant", "property_info", 
                      "loan_details", "document_analysis_results", "application_id", "status"],
        "can_modify": ["financial_analysis", "risk_assessment", "decision"]
    },
    AgentType.COMPLIANCE: {
        "can_access": ["primary_applicant", "co_applicant", "property_info", 
                      "loan_details", "document_analysis_results", "financial_analysis", 
                      "application_id", "status"],
        "can_modify": ["compliance_check", "regulatory_flags"]
    },
    AgentType.CUSTOMER: {
        "can_access": ["primary_applicant.name", "co_applicant.name", "status", 
                      "loan_details.loan_amount", "loan_details.loan_term_years", 
                      "application_id", "document_status", "decision.outcome"],
        "can_modify": ["customer_communications", "customer_questions"]
    }
}


class AccessDeniedError(Exception):
    """Exception raised when access is denied."""
    pass


class AccessControlManager:
    """
    Manages access control for the mortgage lending assistant.
    """
    
    def __init__(self):
        """Initialize the access control manager."""
        logger.info("Initializing Access Control Manager")
        self.agent_sessions = {}  # Store authenticated agent sessions
        self.user_sessions = {}   # Store authenticated user sessions
    
    def register_agent(self, agent_id: str, agent_type: AgentType, api_key: str) -> str:
        """
        Register an agent with the access control system.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_type: Type of agent
            api_key: API key for authentication
            
        Returns:
            Session token for the agent
        """
        # In a real system, you'd validate the API key against a secure store
        # For MVP, we'll just generate a simple session token
        session_token = f"{agent_id}-{hash(api_key) % 10000}"
        
        self.agent_sessions[session_token] = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "access_rights": AGENT_ACCESS_RIGHTS.get(agent_type, {})
        }
        
        logger.info(f"Agent registered: {agent_id} as {agent_type}")
        return session_token
    
    def register_user(self, user_id: str, role: str, api_key: str) -> str:
        """
        Register a user with the access control system.
        
        Args:
            user_id: Unique identifier for the user
            role: User role
            api_key: API key for authentication
            
        Returns:
            Session token for the user
        """
        # In a real system, you'd validate the API key against a secure store
        # For MVP, we'll just generate a simple session token
        session_token = f"{user_id}-{hash(api_key) % 10000}"
        
        self.user_sessions[session_token] = {
            "user_id": user_id,
            "role": role,
            "permissions": ROLE_PERMISSIONS.get(role, {})
        }
        
        logger.info(f"User registered: {user_id} with role {role}")
        return session_token
    
    def validate_agent_session(self, session_token: str) -> bool:
        """
        Validate an agent session token.
        
        Args:
            session_token: Session token to validate
            
        Returns:
            True if valid, False otherwise
        """
        return session_token in self.agent_sessions
    
    def validate_user_session(self, session_token: str) -> bool:
        """
        Validate a user session token.
        
        Args:
            session_token: Session token to validate
            
        Returns:
            True if valid, False otherwise
        """
        return session_token in self.user_sessions
    
    def get_agent_access_rights(self, session_token: str) -> Dict[str, Any]:
        """
        Get access rights for an agent.
        
        Args:
            session_token: Agent session token
            
        Returns:
            Access rights dictionary
            
        Raises:
            AccessDeniedError: If session token is invalid
        """
        if not self.validate_agent_session(session_token):
            raise AccessDeniedError("Invalid agent session token")
        
        return self.agent_sessions[session_token]["access_rights"]
    
    def get_user_permissions(self, session_token: str) -> Dict[str, Any]:
        """
        Get permissions for a user.
        
        Args:
            session_token: User session token
            
        Returns:
            Permissions dictionary
            
        Raises:
            AccessDeniedError: If session token is invalid
        """
        if not self.validate_user_session(session_token):
            raise AccessDeniedError("Invalid user session token")
        
        return self.user_sessions[session_token]["permissions"]
    
    def can_agent_access_field(self, session_token: str, field_path: str) -> bool:
        """
        Check if an agent can access a field.
        
        Args:
            session_token: Agent session token
            field_path: Path to the field (dot notation)
            
        Returns:
            True if agent can access the field, False otherwise
            
        Raises:
            AccessDeniedError: If session token is invalid
        """
        access_rights = self.get_agent_access_rights(session_token)
        
        # Full access
        if access_rights.get("can_access_all", False):
            return True
        
        # Check specific field access
        accessible_fields = access_rights.get("can_access", [])
        
        # Check exact match
        if field_path in accessible_fields:
            return True
        
        # Check parent paths
        for accessible_field in accessible_fields:
            # If the accessible field is a parent of the requested field
            if field_path.startswith(f"{accessible_field}."):
                return True
            
            # Handle array indexing
            if "[" in field_path:
                # Strip array indices for comparison
                base_field = field_path.split("[")[0]
                if base_field == accessible_field or base_field.startswith(f"{accessible_field}."):
                    return True
        
        return False
    
    def can_agent_modify_field(self, session_token: str, field_path: str) -> bool:
        """
        Check if an agent can modify a field.
        
        Args:
            session_token: Agent session token
            field_path: Path to the field (dot notation)
            
        Returns:
            True if agent can modify the field, False otherwise
            
        Raises:
            AccessDeniedError: If session token is invalid
        """
        access_rights = self.get_agent_access_rights(session_token)
        
        # Full access
        if access_rights.get("can_access_all", False):
            return True
        
        # Check specific field modification rights
        modifiable_fields = access_rights.get("can_modify", [])
        
        # Check exact match
        if field_path in modifiable_fields:
            return True
        
        # Check parent paths
        for modifiable_field in modifiable_fields:
            # If the modifiable field is a parent of the requested field
            if field_path.startswith(f"{modifiable_field}."):
                return True
            
            # Handle array indexing
            if "[" in field_path:
                # Strip array indices for comparison
                base_field = field_path.split("[")[0]
                if base_field == modifiable_field or base_field.startswith(f"{modifiable_field}."):
                    return True
        
        return False
    
    def filter_data_for_agent(self, session_token: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter data to include only fields accessible to an agent.
        
        Args:
            session_token: Agent session token
            data: Original data
            
        Returns:
            Filtered data
            
        Raises:
            AccessDeniedError: If session token is invalid
        """
        access_rights = self.get_agent_access_rights(session_token)
        
        # Full access
        if access_rights.get("can_access_all", False):
            return data
        
        # Recursive function to filter nested dictionaries
        def filter_dict(d, parent_path=""):
            filtered = {}
            for key, value in d.items():
                current_path = f"{parent_path}.{key}" if parent_path else key
                
                if self.can_agent_access_field(session_token, current_path):
                    if isinstance(value, dict):
                        filtered[key] = filter_dict(value, current_path)
                    elif isinstance(value, list):
                        filtered[key] = filter_list(value, current_path)
                    else:
                        filtered[key] = value
            return filtered
        
        # Filter lists of dictionaries
        def filter_list(lst, parent_path):
            filtered = []
            for i, item in enumerate(lst):
                if isinstance(item, dict):
                    indexed_path = f"{parent_path}[{i}]"
                    filtered.append(filter_dict(item, indexed_path))
                else:
                    filtered.append(item)
            return filtered
        
        return filter_dict(data)
    
    def can_user_access_application(self, session_token: str, application_id: str, user_id: Optional[str] = None) -> bool:
        """
        Check if a user can access an application.
        
        Args:
            session_token: User session token
            application_id: Application ID
            user_id: Optional user ID to override the session user
            
        Returns:
            True if user can access the application, False otherwise
            
        Raises:
            AccessDeniedError: If session token is invalid
        """
        permissions = self.get_user_permissions(session_token)
        
        # Full access for admins
        if permissions.get("can_access_all", False):
            return True
        
        # For loan officers or other staff
        if permissions.get("can_view_applications", False):
            return True
        
        # For customers - can only view their own applications
        if permissions.get("can_view_own_application", False):
            session_user_id = user_id or self.user_sessions[session_token]["user_id"]
            
            # In a real system, you'd check if the application belongs to this user
            # For MVP, we'll just check that the IDs match (simplified)
            application_owner_id = application_id.split("-")[0]  # Simplified for MVP
            return session_user_id == application_owner_id
        
        return False
    
    def audit_access(self, session_token: str, action: str, resource: str, success: bool) -> None:
        """
        Log an access attempt for auditing.
        
        Args:
            session_token: Session token
            action: Action attempted
            resource: Resource accessed
            success: Whether access was successful
        """
        # Determine if this is a user or agent
        session_type = "unknown"
        session_entity = None
        
        if self.validate_agent_session(session_token):
            session_type = "agent"
            session_entity = self.agent_sessions[session_token]["agent_id"]
        elif self.validate_user_session(session_token):
            session_type = "user"
            session_entity = self.user_sessions[session_token]["user_id"]
        
        # Log the access attempt
        log_message = (
            f"Access {'granted' if success else 'denied'}: "
            f"{session_type} {session_entity} attempted to {action} on {resource}"
        )
        
        logger.info(log_message)
        
        # In a real system, you'd also write this to a secure audit log