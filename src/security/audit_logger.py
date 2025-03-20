"""
Audit logging functionality for the Mortgage Lending Assistant.

This module provides comprehensive audit logging for security-relevant events,
creating an immutable record of actions for compliance and security purposes.
"""

import json
import logging
import os
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
import hashlib

logger = logging.getLogger(__name__)

# Load security configuration
try:
    with open("config/security_config.json", "r") as f:
        SECURITY_CONFIG = json.load(f)
        AUDIT_CONFIG = SECURITY_CONFIG.get("audit", {})
        LOG_ALL_EVENTS = AUDIT_CONFIG.get("log_all_events", True)
        SENSITIVE_EVENTS = set(AUDIT_CONFIG.get("sensitive_events", []))
        RETENTION_DAYS = AUDIT_CONFIG.get("retention_days", 90)
except Exception as e:
    logger.error(f"Failed to load security configuration: {str(e)}")
    # Default values if config fails to load
    LOG_ALL_EVENTS = True
    SENSITIVE_EVENTS = {
        "application_submission",
        "document_access",
        "decision_made",
        "pii_accessed"
    }
    RETENTION_DAYS = 90


class AuditLogger:
    """
    Provides secure audit logging functionality for the mortgage lending assistant.
    """
    
    def __init__(self, log_dir: str = "logs/audit"):
        """
        Initialize the audit logger.
        
        Args:
            log_dir: Directory to store audit logs
        """
        self.log_dir = log_dir
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Current log file
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.log_file = os.path.join(log_dir, f"audit_{self.current_date}.log")
        
        # Previous log entries hash
        self.previous_hash = self._get_last_hash()
        
        logger.info(f"Audit logger initialized with log file: {self.log_file}")
    
    def _get_last_hash(self) -> str:
        """
        Get the hash of the last audit log entry for chain integrity.
        
        Returns:
            Hash string of the last entry, or a default for new files
        """
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        last_line = lines[-1].strip()
                        # Extract hash from the last line
                        parts = last_line.split('|')
                        if len(parts) >= 6:
                            return parts[5]
            
            # If file doesn't exist or is empty, return a default hash
            return hashlib.sha256(b"initial").hexdigest()
        
        except Exception as e:
            logger.error(f"Error getting last hash: {str(e)}")
            return hashlib.sha256(b"error").hexdigest()
    
    def _compute_entry_hash(self, entry_data: str) -> str:
        """
        Compute a hash for an audit log entry.
        
        Args:
            entry_data: Audit log entry data
            
        Returns:
            SHA-256 hash of the entry
        """
        # Include the previous hash to create a chain
        data_to_hash = f"{self.previous_hash}|{entry_data}"
        return hashlib.sha256(data_to_hash.encode('utf-8')).hexdigest()
    
    def log_event(self, 
                 event_type: str,
                 user_id: Optional[str],
                 agent_id: Optional[str],
                 action: str,
                 resource_id: Optional[str],
                 details: Dict[str, Any],
                 success: bool) -> str:
        """
        Log a security-relevant event.
        
        Args:
            event_type: Type of event
            user_id: ID of the user (if applicable)
            agent_id: ID of the agent (if applicable)
            action: Action performed
            resource_id: ID of the resource affected
            details: Additional details about the event
            success: Whether the action was successful
            
        Returns:
            ID of the audit log entry
        """
        # Check if we should log this event
        if not LOG_ALL_EVENTS and event_type not in SENSITIVE_EVENTS:
            return ""
        
        # Ensure we're using the correct log file for today
        current_date = datetime.now().strftime("%Y-%m-%d")
        if current_date != self.current_date:
            self.current_date = current_date
            self.log_file = os.path.join(self.log_dir, f"audit_{self.current_date}.log")
            self.previous_hash = self._get_last_hash()
        
        # Create unique ID for this log entry
        entry_id = str(uuid.uuid4())
        
        # Format timestamp
        timestamp = datetime.now().isoformat()
        
        # Create sanitized details (no PII)
        sanitized_details = self._sanitize_details(details, event_type in SENSITIVE_EVENTS)
        
        # Create log entry
        entry_data = (
            f"{timestamp}|{entry_id}|{event_type}|"
            f"{user_id or '-'}|{agent_id or '-'}|{action}|"
            f"{resource_id or '-'}|{json.dumps(sanitized_details)}|{success}"
        )
        
        # Compute hash for this entry
        entry_hash = self._compute_entry_hash(entry_data)
        
        # Full log entry with hash
        full_entry = f"{entry_data}|{entry_hash}"
        
        try:
            # Write to log file
            with open(self.log_file, 'a') as f:
                f.write(full_entry + "\n")
            
            # Update previous hash
            self.previous_hash = entry_hash
            
            # Also log to application logger for visibility
            log_message = (
                f"AUDIT: {event_type} - "
                f"User: {user_id or 'N/A'}, Agent: {agent_id or 'N/A'}, "
                f"Action: {action}, Resource: {resource_id or 'N/A'}, "
                f"Success: {success}"
            )
            logger.info(log_message)
            
            return entry_id
        
        except Exception as e:
            logger.error(f"Failed to write audit log entry: {str(e)}")
            return ""
    
    def _sanitize_details(self, details: Dict[str, Any], is_sensitive: bool) -> Dict[str, Any]:
        """
        Sanitize log details to remove sensitive information.
        
        Args:
            details: Original details
            is_sensitive: Whether this is a sensitive event type
            
        Returns:
            Sanitized details
        """
        # For MVP, just do basic sanitization
        # In a production system, this would be more sophisticated
        
        # Make a copy to avoid modifying the original
        sanitized = {}
        
        # List of field names that might contain sensitive data
        sensitive_fields = {
            "ssn", "social_security", "password", "credit_card", "account_number",
            "tax_id", "dob", "date_of_birth", "driver_license", "passport"
        }
        
        for key, value in details.items():
            key_lower = key.lower()
            
            # Check if this is a sensitive field
            if any(sensitive in key_lower for sensitive in sensitive_fields):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_details(value, is_sensitive)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_details(item, is_sensitive) if isinstance(item, dict) else item 
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized
    
    def verify_log_integrity(self, log_file: Optional[str] = None) -> bool:
        """
        Verify the integrity of an audit log file by checking the hash chain.
        
        Args:
            log_file: Path to the log file to verify (defaults to current log file)
            
        Returns:
            True if the log file is intact, False if any tampering is detected
        """
        if log_file is None:
            log_file = self.log_file
        
        try:
            if not os.path.exists(log_file):
                logger.warning(f"Log file does not exist: {log_file}")
                return False
            
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            if not lines:
                logger.warning(f"Log file is empty: {log_file}")
                return True  # Empty file is considered intact
            
            # Start with the initial hash
            current_hash = hashlib.sha256(b"initial").hexdigest()
            
            for i, line in enumerate(lines):
                parts = line.strip().split('|')
                if len(parts) < 6:
                    logger.error(f"Invalid log entry format at line {i+1}")
                    return False
                
                # Extract the stored hash
                stored_hash = parts[-1]
                
                # Compute the expected hash
                entry_data = '|'.join(parts[:-1])
                data_to_hash = f"{current_hash}|{entry_data}"
                expected_hash = hashlib.sha256(data_to_hash.encode('utf-8')).hexdigest()
                
                # Compare hashes
                if expected_hash != stored_hash:
                    logger.error(f"Integrity check failed at line {i+1}: hash mismatch")
                    return False
                
                # Update current hash for next iteration
                current_hash = stored_hash
            
            logger.info(f"Log integrity verified for {log_file}")
            return True
        
        except Exception as e:
            logger.error(f"Error verifying log integrity: {str(e)}")
            return False
    
    def clean_old_logs(self) -> int:
        """
        Clean up audit logs older than the retention period.
        
        Returns:
            Number of log files deleted
        """
        try:
            # Calculate the cutoff date
            cutoff = time.time() - (RETENTION_DAYS * 24 * 60 * 60)
            count = 0
            
            for filename in os.listdir(self.log_dir):
                if filename.startswith("audit_") and filename.endswith(".log"):
                    filepath = os.path.join(self.log_dir, filename)
                    file_time = os.path.getmtime(filepath)
                    
                    if file_time < cutoff:
                        # In a production system, you might archive rather than delete
                        os.remove(filepath)
                        count += 1
                        logger.info(f"Removed old audit log: {filename}")
            
            return count
        
        except Exception as e:
            logger.error(f"Error cleaning old logs: {str(e)}")
            return 0
    
    def search_logs(self, 
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None,
                   event_types: Optional[List[str]] = None,
                   user_id: Optional[str] = None,
                   agent_id: Optional[str] = None,
                   resource_id: Optional[str] = None,
                   action: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search audit logs for specific events.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            event_types: List of event types to include
            user_id: Filter by user ID
            agent_id: Filter by agent ID
            resource_id: Filter by resource ID
            action: Filter by action
            
        Returns:
            List of matching log entries
        """
        results = []
        
        try:
            # Determine date range
            if start_date is None:
                start_date = "1970-01-01"
            if end_date is None:
                end_date = datetime.now().strftime("%Y-%m-%d")
            
            # Convert to datetime objects for comparison
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            # List all log files in the date range
            log_files = []
            for filename in os.listdir(self.log_dir):
                if filename.startswith("audit_") and filename.endswith(".log"):
                    # Extract date from filename
                    try:
                        file_date_str = filename[6:-4]  # Remove "audit_" and ".log"
                        file_date = datetime.strptime(file_date_str, "%Y-%m-%d")
                        
                        if start_dt <= file_date <= end_dt:
                            log_files.append(os.path.join(self.log_dir, filename))
                    except ValueError:
                        # Skip files with invalid date format
                        continue
            
            # Search through each file
            for log_file in log_files:
                with open(log_file, 'r') as f:
                    for line in f:
                        parts = line.strip().split('|')
                        if len(parts) < 9:
                            continue  # Skip invalid entries
                        
                        # Parse entry
                        entry = {
                            "timestamp": parts[0],
                            "entry_id": parts[1],
                            "event_type": parts[2],
                            "user_id": parts[3] if parts[3] != '-' else None,
                            "agent_id": parts[4] if parts[4] != '-' else None,
                            "action": parts[5],
                            "resource_id": parts[6] if parts[6] != '-' else None,
                            "details": json.loads(parts[7]),
                            "success": parts[8].lower() == 'true'
                        }
                        
                        # Apply filters
                        if event_types and entry["event_type"] not in event_types:
                            continue
                        if user_id and entry["user_id"] != user_id:
                            continue
                        if agent_id and entry["agent_id"] != agent_id:
                            continue
                        if resource_id and entry["resource_id"] != resource_id:
                            continue
                        if action and entry["action"] != action:
                            continue
                        
                        results.append(entry)
            
            return results
        
        except Exception as e:
            logger.error(f"Error searching audit logs: {str(e)}")
            return []
    
    def log_application_access(self, 
                              user_id: Optional[str],
                              agent_id: Optional[str],
                              application_id: str,
                              action: str,
                              success: bool,
                              details: Optional[Dict[str, Any]] = None) -> str:
        """
        Log an application access event.
        
        Args:
            user_id: User ID (if a user accessed the application)
            agent_id: Agent ID (if an agent accessed the application)
            application_id: Application ID
            action: Action performed (view, edit, etc.)
            success: Whether the access was successful
            details: Additional details
            
        Returns:
            Audit log entry ID
        """
        return self.log_event(
            event_type="application_access",
            user_id=user_id,
            agent_id=agent_id,
            action=action,
            resource_id=application_id,
            details=details or {},
            success=success
        )
    
    def log_document_access(self,
                           user_id: Optional[str],
                           agent_id: Optional[str],
                           document_id: str,
                           application_id: str,
                           action: str,
                           success: bool,
                           details: Optional[Dict[str, Any]] = None) -> str:
        """
        Log a document access event.
        
        Args:
            user_id: User ID (if a user accessed the document)
            agent_id: Agent ID (if an agent accessed the document)
            document_id: Document ID
            application_id: Associated application ID
            action: Action performed (view, process, etc.)
            success: Whether the access was successful
            details: Additional details
            
        Returns:
            Audit log entry ID
        """
        event_details = details or {}
        event_details["application_id"] = application_id
        
        return self.log_event(
            event_type="document_access",
            user_id=user_id,
            agent_id=agent_id,
            action=action,
            resource_id=document_id,
            details=event_details,
            success=success
        )
    
    def log_decision_event(self,
                          user_id: Optional[str],
                          agent_id: Optional[str],
                          application_id: str,
                          decision: str,
                          success: bool,
                          details: Optional[Dict[str, Any]] = None) -> str:
        """
        Log a decision event.
        
        Args:
            user_id: User ID (if a user made the decision)
            agent_id: Agent ID (if an agent made the decision)
            application_id: Application ID
            decision: Decision made (approve, deny, etc.)
            success: Whether the decision was successfully recorded
            details: Additional details
            
        Returns:
            Audit log entry ID
        """
        event_details = details or {}
        event_details["decision"] = decision
        
        return self.log_event(
            event_type="decision_made",
            user_id=user_id,
            agent_id=agent_id,
            action="make_decision",
            resource_id=application_id,
            details=event_details,
            success=success
        )
    
    def log_auth_event(self,
                      user_id: Optional[str],
                      agent_id: Optional[str],
                      action: str,
                      success: bool,
                      details: Optional[Dict[str, Any]] = None) -> str:
        """
        Log an authentication or authorization event.
        
        Args:
            user_id: User ID (if a user authentication event)
            agent_id: Agent ID (if an agent authentication event)
            action: Action (login, logout, access_denied, etc.)
            success: Whether the authentication was successful
            details: Additional details
            
        Returns:
            Audit log entry ID
        """
        return self.log_event(
            event_type="auth_event",
            user_id=user_id,
            agent_id=agent_id,
            action=action,
            resource_id=None,
            details=details or {},
            success=success
        )
    
    def log_agent_action(self,
                        agent_id: str,
                        action: str,
                        resource_id: Optional[str],
                        success: bool,
                        details: Optional[Dict[str, Any]] = None) -> str:
        """
        Log an action performed by an agent.
        
        Args:
            agent_id: Agent ID
            action: Action performed
            resource_id: ID of the resource affected (if applicable)
            success: Whether the action was successful
            details: Additional details
            
        Returns:
            Audit log entry ID
        """
        return self.log_event(
            event_type="agent_action",
            user_id=None,
            agent_id=agent_id,
            action=action,
            resource_id=resource_id,
            details=details or {},
            success=success
        )
    
    def log_security_event(self,
                          event_subtype: str,
                          user_id: Optional[str],
                          agent_id: Optional[str],
                          action: str,
                          resource_id: Optional[str],
                          success: bool,
                          details: Optional[Dict[str, Any]] = None) -> str:
        """
        Log a security-related event.
        
        Args:
            event_subtype: Specific type of security event (pii_detected, jailbreak_attempt, etc.)
            user_id: User ID (if applicable)
            agent_id: Agent ID (if applicable)
            action: Action related to the security event
            resource_id: ID of the resource affected (if applicable)
            success: Whether the action was successful
            details: Additional details
            
        Returns:
            Audit log entry ID
        """
        event_details = details or {}
        event_details["security_event_type"] = event_subtype
        
        return self.log_event(
            event_type="security_event",
            user_id=user_id,
            agent_id=agent_id,
            action=action,
            resource_id=resource_id,
            details=event_details,
            success=success
        )
    
    def get_event_counts_by_type(self, 
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None) -> Dict[str, int]:
        """
        Get counts of events by type within a date range.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Dictionary mapping event types to counts
        """
        counts = {}
        
        try:
            # Search logs with date range
            events = self.search_logs(start_date=start_date, end_date=end_date)
            
            # Count by event type
            for event in events:
                event_type = event["event_type"]
                counts[event_type] = counts.get(event_type, 0) + 1
            
            return counts
        
        except Exception as e:
            logger.error(f"Error getting event counts: {str(e)}")
            return {}