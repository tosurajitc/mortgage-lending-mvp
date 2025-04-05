"""
PII (Personally Identifiable Information) detection and handling.

This module provides functionality to detect and handle PII in various data sources,
protecting sensitive customer information throughout the mortgage application process.
"""

import re
import json
import logging
from typing import Dict, List, Any, Set, Tuple, Optional, Union
import os

logger = logging.getLogger(__name__)

# Load security configuration
try:
    with open("config/security_config.json", "r") as f:
        SECURITY_CONFIG = json.load(f)
        PII_CONFIG = SECURITY_CONFIG.get("pii_detection", {})
        PII_TYPES = set(PII_CONFIG.get("pii_types", []))
        REDACTION_ENABLED = PII_CONFIG.get("redaction_enabled", True)
except Exception as e:
    logger.error(f"Failed to load security configuration: {str(e)}")
    # Default values if config fails to load
    PII_TYPES = {"SSN", "CREDIT_CARD", "PHONE_NUMBER", "EMAIL", "DRIVER_LICENSE", "ADDRESS", "DOB", "ACCOUNT_NUMBER"}
    REDACTION_ENABLED = True

# PII detection patterns
PII_PATTERNS = {
    "SSN": r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',
    "CREDIT_CARD": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
    "PHONE_NUMBER": r'\b(?:\+\d{1,2}\s)?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}\b',
    "EMAIL": r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
    "DRIVER_LICENSE": r'\b[A-Z]\d{7}\b',  # Example format, varies by state/country
    "ADDRESS": r'\b\d+\s+[A-Za-z0-9\s,.]+(?:Avenue|Ave|Street|St|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way|Place|Pl|Circle|Cir|Terrace|Ter)\b',
    "DOB": r'\b(?:0[1-9]|1[0-2])[\/\-](0[1-9]|[12]\d|3[01])[\/\-](?:19|20)\d{2}\b',
    "ACCOUNT_NUMBER": r'\b[Aa]ccount\s*#?\s*\d{8,}\b'
}

# Fields that are expected to contain PII
EXPECTED_PII_FIELDS = {
    "primary_applicant.email": "EMAIL",
    "primary_applicant.phone": "PHONE_NUMBER",
    "primary_applicant.ssn": "SSN",
    "primary_applicant.ssn_last_four": "SSN",
    "co_applicant.email": "EMAIL",
    "co_applicant.phone": "PHONE_NUMBER",
    "co_applicant.ssn": "SSN",
    "co_applicant.ssn_last_four": "SSN",
    "applicant_email": "EMAIL",
    "applicant_phone": "PHONE_NUMBER",
    "applicant_ssn": "SSN",
    "applicantEmail": "EMAIL",
    "applicantPhone": "PHONE_NUMBER",
    "applicantSSN": "SSN"
}

# Sensitive field names that might contain PII
SENSITIVE_FIELD_NAMES = {
    "ssn", "social_security", "social_security_number", 
    "tax_id", "credit_card", "bank_account",
    "password", "pin", "secret_question", "secret_answer",
    "applicantSSN", "applicant_ssn", "primary_applicant.ssn",
    "co_applicant.ssn", "driver_license", "date_of_birth", "dob",
    "income", "salary", "annual_income", "monthly_income",
    "account_number", "account", "routing_number", "routing",
    "address", "street", "zip_code", "postal_code", "city",
    "email", "phone", "telephone", "mobile", "cell"
}


class PIIDetector:
    """
    Detects and handles PII in various data sources.
    """
    
    def __init__(self):
        """Initialize the PII detector."""
        logger.info("Initializing PII detector")
    
    def detect_pii(self, text: str) -> List[Tuple[str, str]]:
        """
        Detect PII in a text string.
        
        Args:
            text: Text to scan for PII
            
        Returns:
            List of (pii_type, matched_text) tuples
        """
        if not isinstance(text, str):
            return []
            
        results = []
        
        # Only check enabled PII types
        for pii_type in PII_TYPES:
            if pii_type in PII_PATTERNS:
                pattern = PII_PATTERNS[pii_type]
                matches = re.finditer(pattern, text)
                
                for match in matches:
                    results.append((pii_type, match.group(0)))
        
        return results
    
    def detect_pii_in_dict(self, data: Dict[str, Any], parent_key: str = "") -> List[Tuple[str, str, str]]:
        """
        Recursively detect PII in a dictionary.
        
        Args:
            data: Dictionary to scan
            parent_key: Key prefix for nested fields
            
        Returns:
            List of (field_path, pii_type, matched_text) tuples
        """
        if not isinstance(data, dict):
            return []
            
        results = []
        
        for key, value in data.items():
            current_key = f"{parent_key}.{key}" if parent_key else key
            
            # Check if this is an expected PII field
            is_expected_pii = current_key in EXPECTED_PII_FIELDS
            
            if isinstance(value, str):
                # Don't flag expected PII in its designated fields
                if not is_expected_pii:
                    pii_matches = self.detect_pii(value)
                    for pii_type, matched_text in pii_matches:
                        results.append((current_key, pii_type, matched_text))
            
            elif isinstance(value, dict):
                # Recursively check nested dictionaries
                nested_results = self.detect_pii_in_dict(value, current_key)
                results.extend(nested_results)
            
            elif isinstance(value, list):
                # Check items in lists
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        nested_key = f"{current_key}[{i}]"
                        nested_results = self.detect_pii_in_dict(item, nested_key)
                        results.extend(nested_results)
                    elif isinstance(item, str):
                        pii_matches = self.detect_pii(item)
                        for pii_type, matched_text in pii_matches:
                            results.append((f"{current_key}[{i}]", pii_type, matched_text))
        
        return results
    
    def detect_unexpected_pii(self, data: Dict[str, Any]) -> List[Tuple[str, str, str]]:
        """
        Detect PII in unexpected locations in a dictionary.
        
        Args:
            data: Dictionary to scan
            
        Returns:
            List of PII findings in unexpected locations
        """
        all_findings = self.detect_pii_in_dict(data)
        
        # Filter out expected PII in designated fields
        unexpected_findings = []
        for field_path, pii_type, matched_text in all_findings:
            if field_path in EXPECTED_PII_FIELDS:
                expected_type = EXPECTED_PII_FIELDS[field_path]
                if pii_type != expected_type:
                    # Wrong type of PII in an expected field
                    unexpected_findings.append((field_path, pii_type, matched_text))
            else:
                # PII in an unexpected field
                unexpected_findings.append((field_path, pii_type, matched_text))
        
        return unexpected_findings
    
    def redact_pii(self, text: str) -> str:
        """
        Redact PII from a text string.
        
        Args:
            text: Text containing PII
            
        Returns:
            Text with PII redacted
        """
        if not REDACTION_ENABLED or not isinstance(text, str):
            return text
        
        redacted = text
        
        # Redact each type of PII
        for pii_type in PII_TYPES:
            if pii_type in PII_PATTERNS:
                pattern = PII_PATTERNS[pii_type]
                
                # Replace with appropriate redaction text
                if pii_type == "SSN":
                    redacted = re.sub(pattern, "XXX-XX-XXXX", redacted)
                elif pii_type == "CREDIT_CARD":
                    redacted = re.sub(pattern, "XXXX-XXXX-XXXX-XXXX", redacted)
                elif pii_type == "PHONE_NUMBER":
                    redacted = re.sub(pattern, "(XXX) XXX-XXXX", redacted)
                elif pii_type == "EMAIL":
                    # Partially redact email
                    def redact_email(match):
                        email = match.group(0)
                        parts = email.split('@')
                        if len(parts) == 2:
                            username = parts[0]
                            if len(username) > 2:
                                redacted_username = username[0] + 'X' * (len(username) - 2) + username[-1]
                            else:
                                redacted_username = 'X' * len(username)
                            return f"{redacted_username}@{parts[1]}"
                        return "XXXX@XXXX.XXX"
                    
                    redacted = re.sub(pattern, redact_email, redacted)
                elif pii_type == "ADDRESS":
                    redacted = re.sub(pattern, "[REDACTED ADDRESS]", redacted)
                elif pii_type == "DOB":
                    redacted = re.sub(pattern, "XX/XX/XXXX", redacted)
                elif pii_type == "ACCOUNT_NUMBER":
                    redacted = re.sub(pattern, "Account XXXXXXXX", redacted)
                else:
                    # Generic redaction
                    redacted = re.sub(pattern, "[REDACTED]", redacted)
        
        return redacted
    
    def redact_pii_in_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact PII in a dictionary.
        
        Args:
            data: Dictionary containing PII
            
        Returns:
            Dictionary with PII redacted
        """
        if not REDACTION_ENABLED or not isinstance(data, dict):
            return data
        
        # Make a copy to avoid modifying the original
        redacted_data = {}
        
        for key, value in data.items():
            # Check if this key is likely to contain sensitive information by name
            key_is_sensitive = any(sensitive_term in key.lower() for sensitive_term in SENSITIVE_FIELD_NAMES)
            
            if isinstance(value, str):
                # Always redact sensitive fields by name
                if key_is_sensitive:
                    redacted_data[key] = "[REDACTED]"
                else:
                    redacted_data[key] = self.redact_pii(value)
            elif isinstance(value, dict):
                redacted_data[key] = self.redact_pii_in_dict(value)
            elif isinstance(value, list):
                redacted_list = []
                for item in value:
                    if isinstance(item, dict):
                        redacted_list.append(self.redact_pii_in_dict(item))
                    elif isinstance(item, str):
                        redacted_list.append(self.redact_pii(item))
                    else:
                        redacted_list.append(item)
                redacted_data[key] = redacted_list
            else:
                redacted_data[key] = value
        
        return redacted_data
    
    def safe_log_data(self, data: Dict[str, Any], log_level: int = logging.INFO) -> None:
        """
        Safely log data with PII redacted.
        
        Args:
            data: Data to log
            log_level: Logging level
        """
        try:
            # Redact PII
            redacted_data = self.redact_pii_in_dict(data)
            
            # Log the redacted data
            logger.log(log_level, json.dumps(redacted_data, indent=2))
        except Exception as e:
            logger.error(f"Error in safe_log_data: {str(e)}")
            # Log a simple message instead
            logger.log(log_level, f"Data object of type {type(data)}")
    
    def scan_document_content(self, content: str) -> List[Tuple[str, str]]:
        """
        Scan document content for PII.
        
        Args:
            content: Document content to scan
            
        Returns:
            List of PII findings
        """
        return self.detect_pii(content)
    
    def securely_store_pii_data(self, data: Dict[str, Any], secure_fields: Set[str]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Separate and securely store PII data.
        
        Args:
            data: Original data
            secure_fields: Fields that contain PII and should be secured
            
        Returns:
            Tuple of (data with PII removed, secured PII data)
        """
        # This is a simplified implementation for the MVP
        # In a production system, you would encrypt the PII and store it separately
        
        # Make copies to avoid modifying the original
        redacted_data = {}
        secured_pii = {}
        
        for key, value in data.items():
            if key in secure_fields:
                secured_pii[key] = value
                redacted_data[key] = "[SECURED]"
            elif isinstance(value, dict):
                sub_redacted, sub_secured = self.securely_store_pii_data(value, secure_fields)
                redacted_data[key] = sub_redacted
                if sub_secured:
                    secured_pii[key] = sub_secured
            elif isinstance(value, list):
                redacted_list = []
                secured_list = []
                has_secured = False
                
                for item in value:
                    if isinstance(item, dict):
                        sub_redacted, sub_secured = self.securely_store_pii_data(item, secure_fields)
                        redacted_list.append(sub_redacted)
                        if sub_secured:
                            secured_list.append(sub_secured)
                            has_secured = True
                        else:
                            secured_list.append({})
                    else:
                        redacted_list.append(item)
                        secured_list.append(None)
                
                redacted_data[key] = redacted_list
                if has_secured:
                    secured_pii[key] = secured_list
            else:
                redacted_data[key] = value
        
        return redacted_data, secured_pii


# Utility functions that use the PIIDetector class

def is_sensitive_request(data: Dict[str, Any]) -> bool:
    """
    Determine if a request contains potentially sensitive data.
    
    Args:
        data: Request data to check
        
    Returns:
        True if request contains sensitive fields, False otherwise
    """
    # Check if data is a dictionary
    if not isinstance(data, dict):
        return False
        
    # Check for known sensitive field names
    for key in data.keys():
        # Check for direct field match with sensitive fields
        if any(sensitive_term in key.lower() for sensitive_term in SENSITIVE_FIELD_NAMES):
            return True
        
        # Check nested data
        if isinstance(data[key], dict):
            if is_sensitive_request(data[key]):
                return True
        elif isinstance(data[key], list):
            for item in data[key]:
                if isinstance(item, dict) and is_sensitive_request(item):
                    return True
                    
    # Scan for potential PII patterns
    detector = PIIDetector()
    findings = detector.detect_pii_in_dict(data)
    
    return len(findings) > 0

def redact_pii_for_logging(data: Union[Dict[str, Any], List, str]) -> Union[Dict[str, Any], List, str]:
    """
    Create a redacted copy of data suitable for logging.
    
    Args:
        data: Data to redact
        
    Returns:
        Redacted copy of the data
    """
    # Create PIIDetector instance to use its methods
    detector = PIIDetector()
    
    # Handle different data types
    if isinstance(data, dict):
        return detector.redact_pii_in_dict(data)
    elif isinstance(data, str):
        return detector.redact_pii(data)
    elif isinstance(data, list):
        redacted_list = []
        for item in data:
            if isinstance(item, dict):
                redacted_list.append(detector.redact_pii_in_dict(item))
            elif isinstance(item, str):
                redacted_list.append(detector.redact_pii(item))
            else:
                redacted_list.append(item)
        return redacted_list
    else:
        # Return unchanged for other types
        return data

def detect_and_mask_pii(data: Any) -> Any:
    """
    Detect and mask personally identifiable information (PII) in the data.
    
    Args:
        data: The data that might contain PII
        
    Returns:
        The data with PII masked
    """
    # Use PIIDetector class for consistent implementation
    detector = PIIDetector()
    
    # Handle different data types
    if isinstance(data, dict):
        return detector.redact_pii_in_dict(data)
    elif isinstance(data, str):
        return detector.redact_pii(data)
    elif isinstance(data, list):
        # Process each item in the list
        return [detect_and_mask_pii(item) for item in data]
    else:
        # Return unchanged for other types
        return data

def scan_for_pii(data: Any) -> List[Tuple[str, str, str]]:
    """
    Scan data for PII and return findings.
    
    Args:
        data: Data to scan for PII
        
    Returns:
        List of PII findings with location, type, and matched text
    """
    detector = PIIDetector()
    
    if isinstance(data, dict):
        return detector.detect_pii_in_dict(data)
    elif isinstance(data, str):
        return [("text", pii_type, matched_text) for pii_type, matched_text in detector.detect_pii(data)]
    elif isinstance(data, list):
        results = []
        for i, item in enumerate(data):
            if isinstance(item, dict):
                findings = detector.detect_pii_in_dict(item)
                for path, pii_type, matched_text in findings:
                    results.append((f"[{i}].{path}", pii_type, matched_text))
            elif isinstance(item, str):
                for pii_type, matched_text in detector.detect_pii(item):
                    results.append((f"[{i}]", pii_type, matched_text))
        return results
    else:
        return []

def secure_pii_fields(data: Dict[str, Any], fields_to_secure: Set[str] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Secure specified PII fields in a dictionary.
    
    Args:
        data: Dictionary containing data to secure
        fields_to_secure: Set of field paths to secure (defaults to known sensitive fields)
        
    Returns:
        Tuple of (data with PII removed, secured PII data)
    """
    detector = PIIDetector()
    
    # Default to securing known sensitive fields if none specified
    if fields_to_secure is None:
        fields_to_secure = set(EXPECTED_PII_FIELDS.keys())
        
    return detector.securely_store_pii_data(data, fields_to_secure)