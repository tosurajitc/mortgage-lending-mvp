"""
Connector between agents and Semantic Kernel.

This module provides functionality for agents to interact with Semantic Kernel
capabilities, including plugins, memory, and prompts.
"""

import json
import logging
from typing import Dict, List, Any, Optional

from src.semantic_kernel.kernel_setup import get_kernel_manager
from src.semantic_kernel.memory_manager import MemoryManager
from src.utils.exceptions import KernelConnectionError, FunctionExecutionError

logger = logging.getLogger(__name__)

class AgentKernelConnector:
    """
    Connector class for agents to interact with Semantic Kernel capabilities.
    
    This class provides methods for agents to execute semantic functions,
    access memory, and utilize Semantic Kernel plugins.
    """
    
    def __init__(self):
        """Initialize the connector with Kernel Manager and Memory Manager."""
        try:
            self.kernel_manager = get_kernel_manager()
            self.memory_manager = MemoryManager()
            self.logger = logger
            self.logger.info("Agent Kernel Connector initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Agent Kernel Connector: {str(e)}")
            raise KernelConnectionError(f"Failed to initialize Agent Kernel Connector: {str(e)}")
    
    def execute_plugin_function(self, 
                              plugin_name: str, 
                              function_name: str, 
                              input_params: Dict[str, Any]) -> str:
        """
        Execute a plugin function in Semantic Kernel.
        
        Args:
            plugin_name: Name of the plugin (e.g., 'document', 'compliance')
            function_name: Name of the function to execute
            input_params: Dictionary of input parameters for the function
            
        Returns:
            Result of the function execution as a string
            
        Raises:
            FunctionExecutionError: If function execution fails
        """
        try:
            result = self.kernel_manager.execute_function(
                plugin_name, function_name, input_params
            )
            return result
        except Exception as e:
            self.logger.error(f"Failed to execute function {plugin_name}.{function_name}: {str(e)}")
            raise FunctionExecutionError(f"Failed to execute function {plugin_name}.{function_name}: {str(e)}")
    
    def execute_semantic_function(self, 
                                plugin_name: str, 
                                function_name: str, 
                                input_text: str) -> str:
        """
        Execute a semantic function with the given input.
        
        Args:
            plugin_name: Name of the semantic plugin
            function_name: Name of the function to execute
            input_text: Input text for the semantic function
            
        Returns:
            The generated result as a string
            
        Raises:
            FunctionExecutionError: If function execution fails
        """
        try:
            result = self.kernel_manager.execute_semantic_function(
                plugin_name, function_name, input_text
            )
            return result
        except Exception as e:
            self.logger.error(f"Failed to execute semantic function {plugin_name}.{function_name}: {str(e)}")
            raise FunctionExecutionError(f"Failed to execute semantic function {plugin_name}.{function_name}: {str(e)}")
    
    def store_in_memory(self, 
                       collection_name: str, 
                       text: str, 
                       key: Optional[str] = None, 
                       metadata: Optional[Dict] = None) -> str:
        """
        Store text in semantic memory for future retrieval.
        
        Args:
            collection_name: Collection/category to store the memory in
            text: The text content to store
            key: Optional unique identifier (generated if not provided)
            metadata: Optional metadata to associate with the memory
            
        Returns:
            The key of the stored memory
        """
        return self.memory_manager.store_semantic_memory(collection_name, text, key, metadata)
    
    async def retrieve_similar_memories(self, 
                                     collection_name: str, 
                                     query: str, 
                                     limit: int = 5) -> List[Dict]:
        """
        Retrieve semantically similar memories based on a query.
        
        Args:
            collection_name: Collection to search
            query: The query text to find similar memories
            limit: Maximum number of memories to retrieve
            
        Returns:
            List of similar memories with their metadata
        """
        return await self.memory_manager.retrieve_similar_memories(collection_name, query, limit)
    
    def store_context(self, context_id: str, context_data: Dict[str, Any], context_type: str = "application") -> None:
        """
        Store application context data.
        
        Args:
            context_id: Unique identifier for the context
            context_data: Dictionary of context data to store
            context_type: Type of context (application, conversation, document, etc.)
        """
        self.memory_manager.store_context(context_id, context_data, context_type)
    
    def retrieve_context(self, context_id: str, default: Any = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve context data.
        
        Args:
            context_id: Unique identifier for the context
            default: Default value to return if context not found
            
        Returns:
            The context data or default if not found
        """
        return self.memory_manager.retrieve_context(context_id, default)
    
    def update_context(self, context_id: str, updates: Dict[str, Any], create_if_missing: bool = False) -> None:
        """
        Update existing context data.
        
        Args:
            context_id: Unique identifier for the context
            updates: Dictionary of updates to apply to the context
            create_if_missing: Whether to create the context if it doesn't exist
        """
        self.memory_manager.update_context(context_id, updates, create_if_missing)
    
    def store_application_state(self, application_id: str, state_data: Dict[str, Any]) -> None:
        """
        Store application state for a mortgage application.
        
        Args:
            application_id: Unique identifier for the mortgage application
            state_data: Current state of the application
        """
        self.memory_manager.store_application_state(application_id, state_data)
    
    def retrieve_application_state(self, application_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve application state for a mortgage application.
        
        Args:
            application_id: Unique identifier for the mortgage application
            
        Returns:
            The current state data or None if not found
        """
        return self.memory_manager.retrieve_application_state(application_id)