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
    pass


def validate_string(value: str, 
                   field_name: str, 
                   min_length: int = 1, 
                   max_length: Optional[int] = None,
                   pattern: Optional[str] = None) -> str:
    """
    Validate a string value.
    
    Args:
        value: String to validate
        field_name: Name of the field (for error messages)
        min_length: Minimum allowed length
        max_length: Maximum allowed length (defaults to MAX_STRING_LENGTH)
        pattern: Optional regex pattern the string must match
        
    Returns:
        The validated string
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")
    
    # Set default max length if not provided
    if max_length is None:
        max_length = MAX_STRING_LENGTH
    
    # Check length constraints
    if len(value) < min_length:
        raise ValidationError(f"{field_name} must be at least {min_length} characters")
    
    if len(value) > max_length:
        raise ValidationError(f"{field_name} exceeds maximum length of {max_length} characters")
    
    # Check pattern if provided
    if pattern and not re.match(pattern, value):
        raise ValidationError(f"{field_name} does not match required format")
    
    # Sanitize the string (remove potential XSS characters)
    sanitized = sanitize_string(value)
    
    return sanitized


def validate_number(value: Union[int, float], 
                   field_name: str,
                   min_value: Optional[Union[int, float]] = None,
                   max_value: Optional[Union[int, float]] = None,
                   allow_zero: bool = True) -> Union[int, float]:
    """
    Validate a numeric value.
    
    Args:
        value: Number to validate
        field_name: Name of the field (for error messages)
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        allow_zero: Whether zero is allowed
        
    Returns:
        The validated number
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{field_name} must be a number")
    
    # Check if zero is allowed
    if not allow_zero and value == 0:
        raise ValidationError(f"{field_name} cannot be zero")
    
    # Check min value if provided
    if min_value is not None and value < min_value:
        raise ValidationError(f"{field_name} must be at least {min_value}")
    
    # Check max value if provided
    if max_value is not None and value > max_value:
        raise ValidationError(f"{field_name} must be at most {max_value}")
    
    return value


def validate_array(value: List[Any], 
                  field_name: str,
                  min_length: int = 0,
                  max_length: Optional[int] = None,
                  item_validator: Optional[Callable[[Any, str], Any]] = None) -> List[Any]:
    """
    Validate an array/list of values.
    
    Args:
        value: List to validate
        field_name: Name of the field (for error messages)
        min_length: Minimum allowed length
        max_length: Maximum allowed length (defaults to MAX_ARRAY_LENGTH)
        item_validator: Optional function to validate each item
        
    Returns:
        The validated list
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, list):
        raise ValidationError(f"{field_name} must be a list")
    
    # Set default max length if not provided
    if max_length is None:
        max_length = MAX_ARRAY_LENGTH
    
    # Check length constraints
    if len(value) < min_length:
        raise ValidationError(f"{field_name} must contain at least {min_length} items")
    
    if len(value) > max_length:
        raise ValidationError(f"{field_name} exceeds maximum length of {max_length} items")
    
    # Validate each item if validator provided
    if item_validator:
        validated_items = []
        for i, item in enumerate(value):
            try:
                validated_item = item_validator(item, f"{field_name}[{i}]")
                validated_items.append(validated_item)
            except ValidationError as e:
                raise ValidationError(f"Invalid item at index {i} in {field_name}: {str(e)}")
        return validated_items
    
    return value


def validate_dict(value: Dict[str, Any], 
                 field_name: str,
                 required_keys: Optional[Set[str]] = None,
                 optional_keys: Optional[Set[str]] = None,
                 value_validators: Optional[Dict[str, Callable[[Any, str], Any]]] = None) -> Dict[str, Any]:
    """
    Validate a dictionary.
    
    Args:
        value: Dictionary to validate
        field_name: Name of the field (for error messages)
        required_keys: Set of keys that must be present
        optional_keys: Set of keys that may be present
        value_validators: Dictionary mapping keys to validation functions
        
    Returns:
        The validated dictionary
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, dict):
        raise ValidationError(f"{field_name} must be an object")
    
    # Check required keys
    if required_keys:
        missing_keys = required_keys - value.keys()
        if missing_keys:
            raise ValidationError(f"{field_name} is missing required keys: {', '.join(missing_keys)}")
    
    # Check for unexpected keys
    if required_keys and optional_keys:
        allowed_keys = required_keys | optional_keys
        unexpected_keys = value.keys() - allowed_keys
        if unexpected_keys:
            raise ValidationError(f"{field_name} contains unexpected keys: {', '.join(unexpected_keys)}")
    
    # Validate values
    if value_validators:
        validated_dict = {}
        for key, val in value.items():
            if key in value_validators:
                try:
                    validated_val = value_validators[key](val, f"{field_name}.{key}")
                    validated_dict[key] = validated_val
                except ValidationError as e:
                    raise ValidationError(f"Invalid value for {key} in {field_name}: {str(e)}")
            else:
                validated_dict[key] = val
        return validated_dict
    
    return value


def validate_email(value: str, field_name: str) -> str:
    """
    Validate an email address.
    
    Args:
        value: Email to validate
        field_name: Name of the field (for error messages)
        
    Returns:
        The validated email
        
    Raises:
        ValidationError: If validation fails
    """
    # Basic email pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    return validate_string(value, field_name, pattern=email_pattern)


def validate_phone(value: str, field_name: str) -> str:
    """
    Validate a phone number.
    
    Args:
        value: Phone number to validate
        field_name: Name of the field (for error messages)
        
    Returns:
        The validated phone number
        
    Raises:
        ValidationError: If validation fails
    """
    # Strip any non-digit characters
    digits_only = re.sub(r'\D', '', value)
    
    # Check if we have a valid number of digits (assuming US numbers)
    if len(digits_only) < 10 or len(digits_only) > 15:
        raise ValidationError(f"{field_name} is not a valid phone number")
    
    # Format as (XXX) XXX-XXXX for US numbers
    if len(digits_only) == 10:
        formatted = f"({digits_only[0:3]}) {digits_only[3:6]}-{digits_only[6:]}"
        return formatted
    
    return value


def validate_ssn_last_four(value: str, field_name: str) -> str:
    """
    Validate the last four digits of a Social Security Number.
    
    Args:
        value: SSN last four to validate
        field_name: Name of the field (for error messages)
        
    Returns:
        The validated SSN last four
        
    Raises:
        ValidationError: If validation fails
    """
    # Strip any non-digit characters
    digits_only = re.sub(r'\D', '', value)
    
    # Check if we have exactly 4 digits
    if len(digits_only) != 4:
        raise ValidationError(f"{field_name} must be exactly 4 digits")
    
    # Check if all characters are digits
    if not digits_only.isdigit():
        raise ValidationError(f"{field_name} must contain only digits")
    
    return digits_only


def validate_date(value: str, field_name: str, format_pattern: str = r'^\d{4}-\d{2}-\d{2}$') -> str:
    """
    Validate a date string.
    
    Args:
        value: Date string to validate
        field_name: Name of the field (for error messages)
        format_pattern: Expected date format pattern
        
    Returns:
        The validated date string
        
    Raises:
        ValidationError: If validation fails
    """
    # Check pattern
    if not re.match(format_pattern, value):
        raise ValidationError(f"{field_name} must be in the format YYYY-MM-DD")
    
    # Further validation could check if it's a valid date
    # This is simplistic for MVP purposes
    
    return value


def validate_file_extension(filename: str, field_name: str) -> str:
    """
    Validate a file's extension against allowed types.
    
    Args:
        filename: Filename to validate
        field_name: Name of the field (for error messages)
        
    Returns:
        The validated filename
        
    Raises:
        ValidationError: If validation fails
    """
    _, extension = os.path.splitext(filename.lower())
    
    if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise ValidationError(
            f"{field_name} has an invalid file extension. Allowed: {', '.join(ALLOWED_DOCUMENT_EXTENSIONS)}"
        )
    
    return filename


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
    
    # Additional sanitization could be performed here
    
    return sanitized


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


def validate_mortgage_application(application_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a complete mortgage application.
    
    Args:
        application_data: Application data to validate
        
    Returns:
        Validated application data
        
    Raises:
        ValidationError: If validation fails
    """
    # Define required and optional top-level keys
    required_keys = {"primary_applicant", "property_info", "loan_details"}
    optional_keys = {"co_applicant", "documents", "notes"}
    
    # Validate the overall structure
    validated_data = validate_dict(
        application_data, 
        "application", 
        required_keys=required_keys,
        optional_keys=optional_keys
    )
    
    # Validate primary applicant
    if "primary_applicant" in validated_data:
        primary_applicant_validators = {
            "first_name": lambda v, f: validate_string(v, f, min_length=2),
            "last_name": lambda v, f: validate_string(v, f, min_length=2),
            "email": validate_email,
            "phone": validate_phone,
            "date_of_birth": validate_date,
            "ssn_last_four": validate_ssn_last_four,
            "employment_status": lambda v, f: validate_string(v, f),
            "annual_income": lambda v, f: validate_number(v, f, min_value=0),
            "years_at_current_job": lambda v, f: validate_number(v, f, min_value=0),
            "credit_score": lambda v, f: validate_number(v, f, min_value=300, max_value=850),
        }
        
        validated_data["primary_applicant"] = validate_dict(
            validated_data["primary_applicant"],
            "primary_applicant",
            required_keys={"first_name", "last_name", "email", "phone", "date_of_birth", "ssn_last_four"},
            optional_keys={"employment_status", "annual_income", "years_at_current_job", "credit_score", "address"},
            value_validators=primary_applicant_validators
        )
        
        # Validate address if present
        if "address" in validated_data["primary_applicant"]:
            address_validators = {
                "street": lambda v, f: validate_string(v, f),
                "city": lambda v, f: validate_string(v, f),
                "state": lambda v, f: validate_string(v, f, min_length=2, max_length=2),
                "zip_code": lambda v, f: validate_string(v, f, pattern=r'^\d{5}(-\d{4})?$'),
                "country": lambda v, f: validate_string(v, f),
            }
            
            validated_data["primary_applicant"]["address"] = validate_dict(
                validated_data["primary_applicant"]["address"],
                "primary_applicant.address",
                required_keys={"street", "city", "state", "zip_code"},
                optional_keys={"country"},
                value_validators=address_validators
            )
    
    # Validate co-applicant if present
    if "co_applicant" in validated_data:
        co_applicant_validators = {
            "first_name": lambda v, f: validate_string(v, f, min_length=2),
            "last_name": lambda v, f: validate_string(v, f, min_length=2),
            "email": validate_email,
            "phone": validate_phone,
            "date_of_birth": validate_date,
            "ssn_last_four": validate_ssn_last_four,
            "employment_status": lambda v, f: validate_string(v, f),
            "annual_income": lambda v, f: validate_number(v, f, min_value=0),
            "years_at_current_job": lambda v, f: validate_number(v, f, min_value=0),
            "credit_score": lambda v, f: validate_number(v, f, min_value=300, max_value=850),
        }
        
        validated_data["co_applicant"] = validate_dict(
            validated_data["co_applicant"],
            "co_applicant",
            required_keys={"first_name", "last_name", "email", "phone", "date_of_birth", "ssn_last_four"},
            optional_keys={"employment_status", "annual_income", "years_at_current_job", "credit_score", "address"},
            value_validators=co_applicant_validators
        )
        
        # Validate address if present
        if "address" in validated_data["co_applicant"]:
            address_validators = {
                "street": lambda v, f: validate_string(v, f),
                "city": lambda v, f: validate_string(v, f),
                "state": lambda v, f: validate_string(v, f, min_length=2, max_length=2),
                "zip_code": lambda v, f: validate_string(v, f, pattern=r'^\d{5}(-\d{4})?$'),
                "country": lambda v, f: validate_string(v, f),
            }
            
            validated_data["co_applicant"]["address"] = validate_dict(
                validated_data["co_applicant"]["address"],
                "co_applicant.address",
                required_keys={"street", "city", "state", "zip_code"},
                optional_keys={"country"},
                value_validators=address_validators
            )
    
    # Validate property info
    if "property_info" in validated_data:
        property_validators = {
            "property_type": lambda v, f: validate_string(v, f),
            "estimated_value": lambda v, f: validate_number(v, f, min_value=0),
            "year_built": lambda v, f: validate_number(v, f, min_value=1800, max_value=2100),
            "square_footage": lambda v, f: validate_number(v, f, min_value=0),
        }
        
        validated_data["property_info"] = validate_dict(
            validated_data["property_info"],
            "property_info",
            required_keys={"address", "property_type", "estimated_value"},
            optional_keys={"year_built", "square_footage"},
            value_validators=property_validators
        )
        
        # Validate property address
        address_validators = {
            "street": lambda v, f: validate_string(v, f),
            "city": lambda v, f: validate_string(v, f),
            "state": lambda v, f: validate_string(v, f, min_length=2, max_length=2),
            "zip_code": lambda v, f: validate_string(v, f, pattern=r'^\d{5}(-\d{4})?$'),
            "country": lambda v, f: validate_string(v, f),
        }
        
        validated_data["property_info"]["address"] = validate_dict(
            validated_data["property_info"]["address"],
            "property_info.address",
            required_keys={"street", "city", "state", "zip_code"},
            optional_keys={"country"},
            value_validators=address_validators
        )
    
    # Validate loan details
    if "loan_details" in validated_data:
        loan_validators = {
            "loan_amount": lambda v, f: validate_number(v, f, min_value=1),
            "loan_term_years": lambda v, f: validate_number(v, f, min_value=1, max_value=50),
            "interest_rate": lambda v, f: validate_number(v, f, min_value=0, max_value=30),
            "loan_type": lambda v, f: validate_string(v, f),
            "down_payment": lambda v, f: validate_number(v, f, min_value=0),
            "is_first_time_homebuyer": lambda v, f: isinstance(v, bool) or ValidationError(f"{f} must be a boolean")
        }
        
        validated_data["loan_details"] = validate_dict(
            validated_data["loan_details"],
            "loan_details",
            required_keys={"loan_amount", "loan_term_years"},
            optional_keys={"interest_rate", "loan_type", "down_payment", "is_first_time_homebuyer"},
            value_validators=loan_validators
        )
    
    # Validate documents if present
    if "documents" in validated_data:
        def validate_document(doc, field_name):
            document_validators = {
                "document_type": lambda v, f: validate_string(v, f),
                "file_name": lambda v, f: validate_file_extension(v, f),
                "content_type": lambda v, f: validate_string(v, f),
                "file_size": lambda v, f: validate_number(v, f, min_value=1),
                "status": lambda v, f: validate_string(v, f)
            }
            
            return validate_dict(
                doc,
                field_name,
                required_keys={"document_type", "file_name", "content_type", "file_size"},
                optional_keys={"status", "metadata", "document_id", "upload_date", "extracted_data"},
                value_validators=document_validators
            )
        
        validated_data["documents"] = validate_array(
            validated_data["documents"],
            "documents",
            item_validator=validate_document
        )
    
    # Validate notes if present
    if "notes" in validated_data:
        def validate_note(note, field_name):
            note_validators = {
                "author": lambda v, f: validate_string(v, f),
                "content": lambda v, f: validate_string(v, f),
                "timestamp": lambda v, f: validate_string(v, f)
            }
            
            return validate_dict(
                note,
                field_name,
                required_keys={"author", "content"},
                optional_keys={"timestamp"},
                value_validators=note_validators
            )
        
        validated_data["notes"] = validate_array(
            validated_data["notes"],
            "notes",
            item_validator=validate_note
        )
    
    return validated_data


def validate_api_request(request_data: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
    """
    Validate an API request.
    
    Args:
        request_data: Request data to validate
        endpoint: API endpoint
        
    Returns:
        Validated request data
        
    Raises:
        ValidationError: If validation fails
    """
    # Different validation logic based on the endpoint
    if endpoint == "submit_application":
        return validate_mortgage_application(request_data)
    
    elif endpoint == "upload_document":
        document_validators = {
            "application_id": lambda v, f: validate_string(v, f),
            "document_type": lambda v, f: validate_string(v, f),
            "file_name": lambda v, f: validate_file_extension(v, f),
            "content_type": lambda v, f: validate_string(v, f),
            "file_size": lambda v, f: validate_number(v, f, min_value=1),
            "file_content": lambda v, f: validate_string(v, f)  # Base64 encoded
        }
        
        return validate_dict(
            request_data,
            "document_upload",
            required_keys={"application_id", "document_type", "file_name", "content_type", "file_size", "file_content"},
            value_validators=document_validators
        )
    
    elif endpoint == "check_status":
        status_validators = {
            "application_id": lambda v, f: validate_string(v, f)
        }
        
        return validate_dict(
            request_data,
            "status_check",
            required_keys={"application_id"},
            value_validators=status_validators
        )
    
    elif endpoint == "add_note":
        note_validators = {
            "application_id": lambda v, f: validate_string(v, f),
            "author": lambda v, f: validate_string(v, f),
            "content": lambda v, f: validate_string(v, f)
        }
        
        return validate_dict(
            request_data,
            "add_note",
            required_keys={"application_id", "author", "content"},
            value_validators=note_validators
        )
    
    else:
        # Generic validation for unknown endpoints
        logger.warning(f"No specific validation logic for endpoint: {endpoint}")
        return request_data