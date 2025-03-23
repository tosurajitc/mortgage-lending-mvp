"""
Base Agent Module
Provides the foundational class for all specialized agents in the mortgage lending system.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from src.utils.logging_utils import get_logger
from security.validation import validate_input
from security.pii_detector import detect_and_mask_pii


class BaseAgent(ABC):
    """
    Abstract base class for all agent implementations.
    Provides common functionality for validation, security, and logging.
    """
    
    def __init__(self, agent_name: str, agent_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base agent.
        
        Args:
            agent_name: Unique identifier for the agent
            agent_config: Configuration dictionary for the agent
        """
        self.agent_name = agent_name
        self.config = agent_config or {}
        self.logger = get_logger(f"agent.{agent_name}")
        self.logger.info(f"Initializing {agent_name} agent")
        
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data and return a result.
        Must be implemented by all agent subclasses.
        
        Args:
            input_data: The data to be processed by the agent
            
        Returns:
            Dict containing the processing results
        """
        pass
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate the input data for security and format correctness.
        
        Args:
            input_data: The data to validate
            
        Returns:
            True if valid, raises exception otherwise
        """
        self.logger.debug(f"Validating input for {self.agent_name}")
        return validate_input(input_data, self.agent_name)
    
    def sanitize_output(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize the output data to ensure no sensitive information is leaked.
        
        Args:
            output_data: The data to sanitize
            
        Returns:
            Sanitized data
        """
        self.logger.debug(f"Sanitizing output for {self.agent_name}")
        # Detect and mask any PII that might be in the output
        sanitized_data = detect_and_mask_pii(output_data)
        return sanitized_data
    
    def log_processing_step(self, step_name: str, details: Optional[Dict[str, Any]] = None):
        """
        Log a processing step with optional details.
        
        Args:
            step_name: Name of the processing step
            details: Optional details about the step (sensitive info should be masked)
        """
        if details:
            # Ensure we don't log any sensitive information
            safe_details = detect_and_mask_pii(details)
            self.logger.info(f"{self.agent_name} - {step_name}: {safe_details}")
        else:
            self.logger.info(f"{self.agent_name} - {step_name}")
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's process with proper validation, error handling, and sanitization.
        
        Args:
            input_data: The data to be processed
            
        Returns:
            Processed and sanitized results
        """
        try:
            # Validate input data
            self.validate_input(input_data)
            
            # Log the beginning of processing
            self.log_processing_step("Processing started")
            
            # Execute the agent-specific processing
            result = await self.process(input_data)
            
            # Sanitize the output data
            sanitized_result = self.sanitize_output(result)
            
            # Log successful completion
            self.log_processing_step("Processing completed")
            
            return sanitized_result
        except Exception as e:
            self.logger.error(f"Error in {self.agent_name}: {str(e)}", exc_info=True)
            raise