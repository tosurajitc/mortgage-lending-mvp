"""
PII (Personally Identifiable Information) detection and handling.

This module provides functionality to detect and handle PII in various data sources,
protecting sensitive customer information throughout the mortgage application process.
"""

import re
import json
import logging
from typing import Dict, List, Any, Set, Tuple, Optional
import os

# Set up logging
logger = logging.getLogger("src.security.pii_detector")

# PII detection patterns
PII_PATTERNS = {
    "SSN": r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',
    "CREDIT_CARD": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
    "PHONE_NUMBER": r'\b\d{3}[-\s]?\d{3}[-\s]?\d{4}\b',  # More lenient phone pattern
    "EMAIL": r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
    "DRIVER_LICENSE": r'\b[A-Z]?\d{6,8}\b',  # More lenient driver's license pattern
    "ADDRESS": r'\b\d+\s+[A-Za-z0-9\s,\.]+(?:Road|Rd|Street|St|Avenue|Ave|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Plaza|Plz|Square|Sq|Trail|Trl|Parkway|Pkwy|Way)\b'
}

# Fields that are expected to contain PII
EXPECTED_PII_FIELDS = {
    "applicant.email": "EMAIL",
    "applicant.phone": "PHONE_NUMBER",
    "applicant.ssn": "SSN",
    "email": "EMAIL",
    "phone": "PHONE_NUMBER",
    "ssn": "SSN",
    "address": "ADDRESS"
}

class PIIDetector:
    """
    Detects and handles PII in various data sources.
    """
    
    def __init__(self):
        """Initialize the PII detector."""
        logger.info("Initializing PII detector")
        self.pii_types = set(PII_PATTERNS.keys())
        self.redaction_enabled = True
    
    def detect_pii(self, text: str) -> List[Tuple[str, str]]:
        """
        Detect PII in a text string.
        
        Args:
            text: Text to scan for PII
            
        Returns:
            List of (pii_type, matched_text) tuples
        """
        results = []
        
        if not text or not isinstance(text, str):
            return results
        
        # Check each PII pattern
        for pii_type, pattern in PII_PATTERNS.items():
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
        results = []
        
        if not isinstance(data, dict):
            return results
        
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
    
    def redact_pii(self, text: str) -> str:
        """
        Redact PII from a text string.
        
        Args:
            text: Text containing PII
            
        Returns:
            Text with PII redacted
        """
        if not self.redaction_enabled or not text or not isinstance(text, str):
            return text
        
        redacted = text
        
        # Redact each type of PII
        for pii_type, pattern in PII_PATTERNS.items():
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
        if not self.redaction_enabled or not isinstance(data, dict):
            return data
        
        # Make a copy to avoid modifying the original
        redacted_data = {}
        
        for key, value in data.items():
            if isinstance(value, str):
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


# Module-level convenience functions

# Create a singleton detector instance
_detector = PIIDetector()

def detect_and_mask_pii(data: Any) -> Any:
    """
    Detect and mask personally identifiable information (PII) in the data.
    
    Args:
        data: The data that might contain PII
        
    Returns:
        object: The data with PII masked
    """
    if isinstance(data, dict):
        return _detector.redact_pii_in_dict(data)
    elif isinstance(data, str):
        return _detector.redact_pii(data)
    elif isinstance(data, list):
        return [detect_and_mask_pii(item) for item in data]
    else:
        return data

def is_sensitive_request(data: Dict[str, Any]) -> bool:
    """
    Determine if a request contains sensitive PII data.
    
    Args:
        data: Request data to check
        
    Returns:
        Boolean indicating if sensitive data was found
    """
    if not isinstance(data, dict):
        return False
        
    # Check for certain fields that indicate sensitive data
    sensitive_field_names = {
        "ssn", "social_security", "tax_id", "credit_card", "account_number", 
        "routing_number", "password", "secret"
    }
    
    # Check for fields directly in the data
    for field in sensitive_field_names:
        if field in data:
            return True
    
    # Check for these fields in nested objects
    for key, value in data.items():
        if isinstance(value, dict):
            if is_sensitive_request(value):
                return True
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and is_sensitive_request(item):
                    return True
    
    # Check for PII in unexpected locations
    pii_findings = _detector.detect_pii_in_dict(data)
    if pii_findings:
        return True
    
    return False

def redact_pii_for_logging(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a redacted copy of data suitable for logging.
    
    Args:
        data: Data to redact
        
    Returns:
        Redacted copy of the data
    """
    return detect_and_mask_pii(data)