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
    PII_TYPES = {"SSN", "CREDIT_CARD", "PHONE_NUMBER", "EMAIL", "DRIVER_LICENSE"}
    REDACTION_ENABLED = True

# PII detection patterns
PII_PATTERNS = {
    "SSN": r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',
    "CREDIT_CARD": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
    "PHONE_NUMBER": r'\b(?:\+\d{1,2}\s)?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}\b',
    "EMAIL": r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
    "DRIVER_LICENSE": r'\b[A-Z]\d{7}\b'  # Example format, varies by state/country
}

# Fields that are expected to contain PII
EXPECTED_PII_FIELDS = {
    "primary_applicant.email": "EMAIL",
    "primary_applicant.phone": "PHONE_NUMBER",
    "primary_applicant.ssn_last_four": "SSN",
    "co_applicant.email": "EMAIL",
    "co_applicant.phone": "PHONE_NUMBER",
    "co_applicant.ssn_last_four": "SSN"
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
        if not REDACTION_ENABLED:
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
        if not REDACTION_ENABLED:
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