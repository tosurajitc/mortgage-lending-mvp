"""
Input validation functionality for the Mortgage Lending Assistant.

This module provides functions to validate and sanitize inputs to prevent
security issues such as injection attacks, overflow attacks, and other vulnerabilities.
"""

import re
import json
import logging
from typing import Any, Dict, List, Optional, Union, Set, Tuple, Type, Callable
import os
import cerberus  # Optional: For schema-based validation, add to requirements.txt if used

logger = logging.getLogger(__name__)

# Load security configuration
try:
    with open("config/security_config.json", "r") as f:
        SECURITY_CONFIG = json.load(f)
        INPUT_VALIDATION_CONFIG = SECURITY_CONFIG.get("input_validation", {})
        MAX_STRING_LENGTH = INPUT_VALIDATION_CONFIG.get("max_string_length", 1000)
        MAX_ARRAY_LENGTH = INPUT_VALIDATION_CONFIG.get("max_array_length", 100)
        ALLOWED_DOCUMENT_EXTENSIONS = set(INPUT_VALIDATION_CONFIG.get("allowed_document_extensions", [".pdf", ".jpg", ".png"]))
except Exception as e:
    logger.error(f"Failed to load security configuration: {str(e)}")
    # Default values if config fails to load
    MAX_STRING_LENGTH = 1000
    MAX_ARRAY_LENGTH = 100
    ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".jpg", ".png", ".docx", ".xlsx"}


class ValidationError(Exception):
    """Exception raised for validation errors."""
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.field = field
        self.details = details or {}
        super().__init__(self.message)

# Main validation function - preserving your existing interface
def validate_input(input_data, agent_name=None):
    """
    Validate input data for security and format correctness.
    
    Args:
        input_data: The data to validate
        agent_name: Optional name of the agent performing validation
        
    Returns:
        True if valid, raises exception otherwise
    """
    # Perform basic validation checks
    if not isinstance(input_data, dict):
        raise ValidationError(f"Input must be a dictionary, got {type(input_data)}")
    
    # Agent-specific validation logic
    if agent_name:
        # Agent-specific validation logic
        if agent_name == "document_analysis":
            return validate_document_agent_input(input_data)
        elif agent_name == "underwriting":
            return validate_underwriting_agent_input(input_data)
        elif agent_name == "compliance":
            return validate_compliance_agent_input(input_data)
        elif agent_name == "customer_service":
            return validate_customer_service_agent_input(input_data)
        elif agent_name == "orchestrator":
            return validate_orchestrator_agent_input(input_data)
    
    # Basic security checks for all inputs
    for key, value in input_data.items():
        if isinstance(value, str):
            # Check for potential injection or malicious content
            if len(value) > MAX_STRING_LENGTH:
                raise ValidationError(f"Input too large for key {key}", key)
            
            # Sanitize string inputs
            input_data[key] = sanitize_string(value)
        elif isinstance(value, dict):
            # Recursively validate nested dictionaries
            validate_input(value)
        elif isinstance(value, list):
            # Validate lists
            if len(value) > MAX_ARRAY_LENGTH:
                raise ValidationError(f"Array too large for key {key}", key)
            
            # Validate list items
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    validate_input(item)
                elif isinstance(item, str):
                    # Sanitize string items
                    value[i] = sanitize_string(item)
    
    return True

def validate_request(request=None):
    """
    Validate a FastAPI request
    
    Args:
        request: The FastAPI request object
        
    Returns:
        bool: True if the request is valid, False otherwise
    """
    # For now, just return True
    # In a real implementation, you would add validation logic here
    return True

def sanitize_string(value: str) -> str:
    """
    Sanitize a string to prevent XSS and injection attacks.
    
    Args:
        value: String to sanitize
        
    Returns:
        Sanitized string
    """
    # Replace potentially dangerous HTML characters
    sanitized = value
    sanitized = sanitized.replace("<", "&lt;")
    sanitized = sanitized.replace(">", "&gt;")
    sanitized = sanitized.replace("&", "&amp;")
    sanitized = sanitized.replace("\"", "&quot;")
    sanitized = sanitized.replace("'", "&#x27;")
    
    # Remove any potential SQL injection patterns
    sql_patterns = [
        r'(?i)(\b|_)(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)(\b|_)',
        r'(?i)(\b|_)(UNION|JOIN|OR|AND)(\b|_).*?(\b|_)(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)(\b|_)',
        r'--',
        r';.*?$',
        r'\/\*.*?\*\/',
        r'xp_.*?'
    ]
    
    for pattern in sql_patterns:
        sanitized = re.sub(pattern, '[FILTERED]', sanitized)
    
    return sanitized

# Enhanced validation functions for specific types

def validate_string(value: str, field_name: str, min_length: int = 1, 
                  max_length: int = MAX_STRING_LENGTH, pattern: Optional[str] = None) -> str:
    """
    Validate a string field.
    
    Args:
        value: String to validate
        field_name: Name of the field (for error messages)
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        pattern: Optional regex pattern to match
        
    Returns:
        Validated string or raises ValidationError
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string", field_name)
    
    if len(value) < min_length:
        raise ValidationError(f"{field_name} must be at least {min_length} characters", field_name)
    
    if len(value) > max_length:
        raise ValidationError(f"{field_name} cannot exceed {max_length} characters", field_name)
    
    if pattern and not re.match(pattern, value):
        raise ValidationError(f"{field_name} has invalid format", field_name)
    
    # Sanitize string input
    value = sanitize_string(value)
    
    return value

def validate_numeric(value: Union[int, float], field_name: str, 
                    min_value: Optional[Union[int, float]] = None, 
                    max_value: Optional[Union[int, float]] = None) -> Union[int, float]:
    """
    Validate a numeric field.
    
    Args:
        value: Number to validate
        field_name: Name of the field (for error messages)
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        
    Returns:
        Validated number or raises ValidationError
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{field_name} must be a number", field_name)
    
    if min_value is not None and value < min_value:
        raise ValidationError(f"{field_name} must be at least {min_value}", field_name)
    
    if max_value is not None and value > max_value:
        raise ValidationError(f"{field_name} cannot exceed {max_value}", field_name)
    
    return value

def validate_date_string(value: str, field_name: str, 
                        format_str: str = "%Y-%m-%d") -> str:
    """
    Validate a date string.
    
    Args:
        value: Date string to validate
        field_name: Name of the field (for error messages)
        format_str: Expected date format
        
    Returns:
        Validated date string or raises ValidationError
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string", field_name)
    
    # Check if string matches a date pattern
    date_pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(date_pattern, value):
        raise ValidationError(f"{field_name} must be in format YYYY-MM-DD", field_name)
    
    # Further validation could check if it's a valid date
    # using datetime.strptime(value, format_str)
    
    return value

def validate_email(value: str, field_name: str = "email") -> str:
    """
    Validate an email address.
    
    Args:
        value: Email to validate
        field_name: Name of the field (for error messages)
        
    Returns:
        Validated email or raises ValidationError
    """
    email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string", field_name)
    
    if not re.match(email_pattern, value):
        raise ValidationError(f"{field_name} is not a valid email address", field_name)
    
    return value.lower()

def validate_phone(value: str, field_name: str = "phone") -> str:
    """
    Validate a phone number.
    
    Args:
        value: Phone number to validate
        field_name: Name of the field (for error messages)
        
    Returns:
        Validated phone number or raises ValidationError
    """
    # Accept formats: XXX-XXX-XXXX, (XXX) XXX-XXXX, XXXXXXXXXX
    phone_pattern = r'^(?:\d{3}-\d{3}-\d{4}|\(\d{3}\)\s\d{3}-\d{4}|\d{10})$'
    
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string", field_name)
    
    # Strip any non-digit characters for simplified validation
    digits_only = re.sub(r'\D', '', value)
    
    # Check if we have a valid number of digits (assuming US numbers)
    if len(digits_only) < 10 or len(digits_only) > 15:
        raise ValidationError(f"{field_name} is not a valid phone number", field_name)
    
    return value

def validate_ssn(value: str, field_name: str = "ssn") -> str:
    """
    Validate a Social Security Number.
    
    Args:
        value: SSN to validate
        field_name: Name of the field (for error messages)
        
    Returns:
        Validated SSN or raises ValidationError
    """
    # Accept formats: XXX-XX-XXXX or XXXXXXXXX
    ssn_pattern = r'^(?:\d{3}-\d{2}-\d{4}|\d{9})$'
    
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string", field_name)
    
    if not re.match(ssn_pattern, value):
        raise ValidationError(f"{field_name} must be in format XXX-XX-XXXX or XXXXXXXXX", field_name)
    
    # Validate that SSN is not using invalid patterns
    if value.replace('-', '') in ['000000000', '111111111', '999999999']:
        raise ValidationError(f"{field_name} contains an invalid pattern", field_name)
    
    return value

def validate_file_extension(filename: str, field_name: str = "file") -> str:
    """
    Validate a file's extension against allowed types.
    
    Args:
        filename: Filename to validate
        field_name: Name of the field (for error messages)
        
    Returns:
        The validated filename
    """
    _, extension = os.path.splitext(filename.lower())
    
    if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise ValidationError(
            f"{field_name} has an invalid file extension. Allowed: {', '.join(ALLOWED_DOCUMENT_EXTENSIONS)}",
            field_name
        )
    
    return filename

def validate_enum(value: Any, field_name: str, allowed_values: Set[Any]) -> Any:
    """
    Validate that a value is one of an allowed set.
    
    Args:
        value: Value to validate
        field_name: Name of the field (for error messages)
        allowed_values: Set of allowed values
        
    Returns:
        Validated value or raises ValidationError
    """
    if value not in allowed_values:
        allowed_str = ", ".join(str(v) for v in allowed_values)
        raise ValidationError(
            f"{field_name} must be one of: {allowed_str}", 
            field_name
        )
    
    return value

# Agent-specific validation functions

def validate_document_agent_input(input_data: Dict[str, Any]) -> bool:
    """
    Validate input data for document analysis agent.
    
    Args:
        input_data: Data to validate
        
    Returns:
        True if valid, raises ValidationError otherwise
    """
    # Validate required fields
    if "application_id" not in input_data:
        raise ValidationError("Missing required field: application_id", "application_id")
    
    validate_string(input_data["application_id"], "application_id", max_length=50)
    
    # Validate documents array if present
    if "documents" in input_data:
        if not isinstance(input_data["documents"], list):
            raise ValidationError("documents must be an array", "documents")
        
        for i, doc in enumerate(input_data["documents"]):
            if not isinstance(doc, dict):
                raise ValidationError(f"Document at index {i} must be an object", f"documents[{i}]")
            
            if "document_type" not in doc:
                raise ValidationError(f"Document at index {i} is missing document_type", f"documents[{i}].document_type")
            
            validate_string(doc["document_type"], f"documents[{i}].document_type")
            
            if "content" in doc:
                # Basic content validation - could be expanded based on document type
                if not isinstance(doc["content"], str) and not isinstance(doc["content"], dict):
                    raise ValidationError(f"Document content at index {i} must be a string or object", f"documents[{i}].content")
    
    # Validate is_update flag if present
    if "is_update" in input_data:
        if not isinstance(input_data["is_update"], bool):
            raise ValidationError("is_update must be a boolean", "is_update")
    
    return True

def validate_underwriting_agent_input(input_data: Dict[str, Any]) -> bool:
    """
    Validate input data for underwriting agent.
    
    Args:
        input_data: Data to validate
        
    Returns:
        True if valid, raises ValidationError otherwise
    """
    # Validate required fields
    if "application_id" not in input_data:
        raise ValidationError("Missing required field: application_id", "application_id")
    
    validate_string(input_data["application_id"], "application_id", max_length=50)
    
    # Validate application_data if present
    if "application_data" in input_data:
        if not isinstance(input_data["application_data"], dict):
            raise ValidationError("application_data must be an object", "application_data")
        
        app_data = input_data["application_data"]
        
        # Validate financial fields
        if "loan_amount" in app_data:
            validate_numeric(app_data["loan_amount"], "application_data.loan_amount", min_value=0)
        
        if "loan_term_years" in app_data:
            validate_numeric(app_data["loan_term_years"], "application_data.loan_term_years", min_value=1, max_value=50)
        
        if "interest_rate" in app_data:
            validate_numeric(app_data["interest_rate"], "application_data.interest_rate", min_value=0, max_value=30)
        
        if "loan_type" in app_data:
            validate_enum(
                app_data["loan_type"], 
                "application_data.loan_type", 
                {"CONVENTIONAL", "FHA", "VA", "USDA", "JUMBO"}
            )
    
    # Validate document_analysis if present
    if "document_analysis" in input_data:
        if not isinstance(input_data["document_analysis"], dict):
            raise ValidationError("document_analysis must be an object", "document_analysis")
    
    return True

def validate_compliance_agent_input(input_data: Dict[str, Any]) -> bool:
    """
    Validate input data for compliance agent.
    
    Args:
        input_data: Data to validate
        
    Returns:
        True if valid, raises ValidationError otherwise
    """
    # Validate required fields
    if "application_id" not in input_data:
        raise ValidationError("Missing required field: application_id", "application_id")
    
    validate_string(input_data["application_id"], "application_id", max_length=50)
    
    # Similar validations as for underwriting agent
    if "application_data" in input_data:
        if not isinstance(input_data["application_data"], dict):
            raise ValidationError("application_data must be an object", "application_data")
    
    if "document_analysis" in input_data:
        if not isinstance(input_data["document_analysis"], dict):
            raise ValidationError("document_analysis must be an object", "document_analysis")
    
    if "underwriting_results" in input_data:
        if not isinstance(input_data["underwriting_results"], dict):
            raise ValidationError("underwriting_results must be an object", "underwriting_results")
    
    return True

def validate_customer_service_agent_input(input_data: Dict[str, Any]) -> bool:
    """
    Validate input data for customer service agent.
    
    Args:
        input_data: Data to validate
        
    Returns:
        True if valid, raises ValidationError otherwise
    """
    # Validate required fields
    if "application_id" not in input_data:
        raise ValidationError("Missing required field: application_id", "application_id")
    
    validate_string(input_data["application_id"], "application_id", max_length=50)
    
    if "request_type" not in input_data:
        raise ValidationError("Missing required field: request_type", "request_type")
    
    validate_string(input_data["request_type"], "request_type", max_length=50)
    
    # Validate request-specific fields
    request_type = input_data["request_type"]
    
    if request_type == "missing_documents":
        if "missing_documents" not in input_data:
            raise ValidationError("Missing required field for missing_documents request: missing_documents", "missing_documents")
        
        if not isinstance(input_data["missing_documents"], list):
            raise ValidationError("missing_documents must be an array", "missing_documents")
    
    elif request_type == "application_decision":
        if "underwriting_results" not in input_data:
            raise ValidationError("Missing required field for application_decision request: underwriting_results", "underwriting_results")
        
        if not isinstance(input_data["underwriting_results"], dict):
            raise ValidationError("underwriting_results must be an object", "underwriting_results")
    
    elif request_type == "customer_inquiry":
        if "inquiry_text" not in input_data:
            raise ValidationError("Missing required field for customer_inquiry request: inquiry_text", "inquiry_text")
        
        validate_string(input_data["inquiry_text"], "inquiry_text", max_length=5000)
    
    elif request_type == "document_explanation":
        if "document_type" not in input_data:
            raise ValidationError("Missing required field for document_explanation request: document_type", "document_type")
        
        validate_string(input_data["document_type"], "document_type", max_length=50)
    
    return True

def validate_orchestrator_agent_input(input_data: Dict[str, Any]) -> bool:
    """
    Validate input data for orchestrator agent.
    
    Args:
        input_data: Data to validate
        
    Returns:
        True if valid, raises ValidationError otherwise
    """
    # Validate required fields
    if "application_id" not in input_data:
        raise ValidationError("Missing required field: application_id", "application_id")
    
    validate_string(input_data["application_id"], "application_id", max_length=50)
    
    # Validate action if present
    if "action" in input_data:
        validate_enum(
            input_data["action"], 
            "action", 
            {"process_application", "handle_customer_inquiry", "update_application"}
        )
    
    # Further validation based on the action
    action = input_data.get("action", "process_application")
    
    if action == "process_application":
        # Validate application data for new applications
        if "application_data" not in input_data:
            raise ValidationError("Missing required field for process_application action: application_data", "application_data")
        
        if not isinstance(input_data["application_data"], dict):
            raise ValidationError("application_data must be an object", "application_data")
        
        # Validate basic applicant data if present
        if "applicant" in input_data["application_data"]:
            applicant = input_data["application_data"]["applicant"]
            
            if not isinstance(applicant, dict):
                raise ValidationError("applicant must be an object", "application_data.applicant")
            
            if "name" in applicant:
                validate_string(applicant["name"], "application_data.applicant.name", max_length=100)
            
            if "email" in applicant:
                validate_email(applicant["email"], "application_data.applicant.email")
            
            if "phone" in applicant:
                validate_phone(applicant["phone"], "application_data.applicant.phone")
    
    elif action == "handle_customer_inquiry":
        if "inquiry_text" not in input_data:
            raise ValidationError("Missing required field for handle_customer_inquiry action: inquiry_text", "inquiry_text")
        
        validate_string(input_data["inquiry_text"], "inquiry_text", max_length=5000)
    
    elif action == "update_application":
        if "update_type" not in input_data:
            raise ValidationError("Missing required field for update_application action: update_type", "update_type")
        
        validate_enum(
            input_data["update_type"], 
            "update_type", 
            {"new_documents", "application_data"}
        )
    
    return True

def detect_jailbreak_attempts(value: str) -> Tuple[bool, Optional[str]]:
    """
    Detect potential jailbreak attempts in user input.
    
    Args:
        value: String to check
        
    Returns:
        Tuple of (is_jailbreak, reason)
    """
    # Load jailbreak patterns from config
    jailbreak_patterns = SECURITY_CONFIG.get("jailbreak_prevention", {}).get("blocked_patterns", [])
    
    # Check for jailbreak patterns
    for pattern in jailbreak_patterns:
        if pattern.lower() in value.lower():
            return True, f"Input contains blocked pattern: {pattern}"
    
    # Check for attempts to manipulate the model
    if re.search(r'ignore (previous|above|all) instructions', value, re.IGNORECASE):
        return True, "Input attempts to override instructions"
    
    if re.search(r'(bypass|ignore|override) (restrictions|limitations|rules|policies)', value, re.IGNORECASE):
        return True, "Input attempts to bypass system restrictions"
    
    # Additional checks could be added here
    
    return False, None

def validate_json_string(json_string: str) -> Dict[str, Any]:
    """
    Validate and parse a JSON string.
    
    Args:
        json_string: JSON string to validate
        
    Returns:
        Parsed JSON object or raises ValidationError
    """
    try:
        parsed = json.loads(json_string)
        return parsed
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON format: {str(e)}")

def validate_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate data against a schema using Cerberus.
    
    Args:
        data: Data to validate
        schema: Schema definition
        
    Returns:
        Validated data or raises ValidationError
    """
    v = cerberus.Validator(schema)
    if not v.validate(data):
        errors = v.errors
        error_details = {field: msgs for field, msgs in errors.items()}
        raise ValidationError(
            "Schema validation failed", 
            details=error_details
        )
    
    return data