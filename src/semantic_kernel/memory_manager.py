"""
Memory management for contextual understanding.

This module provides tools for managing application state, conversation history,
and contextual information needed for AI decision-making.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

from src.utils.logging_utils import get_logger
from src.utils.exceptions import MemoryException
from src.semantic_kernel.kernel_setup import get_kernel_manager

logger = get_logger("semantic_kernel.memory")

class MemoryManager:
    """
    Manages contextual memory for the Semantic Kernel.
    
    Provides methods to:
    - Store and retrieve conversation context
    - Maintain application state
    - Track decision history
    - Provide relevant context to semantic functions
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one MemoryManager instance exists."""
        if cls._instance is None:
            cls._instance = super(MemoryManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the MemoryManager if not already initialized."""
        if not hasattr(self, '_initialized') or not self._initialized:
            self._kernel_manager = get_kernel_manager()
            self._memory = self._kernel_manager.memory
            self._context_store = {}  # In-memory context store (can be replaced with Cosmos DB later)
            self.logger = logger
            self._initialized = True
            self.logger.info("Memory Manager initialized")
    
    def store_semantic_memory(self, collection_name: str, text: str, key: str = None, metadata: Dict = None) -> str:
        """
        Store text in semantic memory for similarity search.
        
        Args:
            collection_name: Collection/category to store the memory in
            text: The text content to store
            key: Optional unique identifier (generated if not provided)
            metadata: Optional metadata to associate with the memory
            
        Returns:
            The key of the stored memory
        """
        if key is None:
            key = str(uuid.uuid4())
            
        if metadata is None:
            metadata = {}
            
        # Add timestamp to metadata
        metadata["timestamp"] = datetime.utcnow().isoformat()
        
        try:
            # Note: This is a simplified version since we're not actually storing in a vector database
            # In a production system, this would use the SK memory capabilities
            # For MVP, we'll just store this in our context store
            
            collection_key = f"semantic_memory_{collection_name}"
            if collection_key not in self._context_store:
                self._context_store[collection_key] = {}
                
            self._context_store[collection_key][key] = {
                "text": text,
                "metadata": metadata,
                "timestamp": metadata["timestamp"]
            }
            
            self.logger.info(f"Stored semantic memory: {collection_name}/{key}")
            return key
        except Exception as e:
            self.logger.error(f"Failed to store semantic memory: {str(e)}")
            raise MemoryException(f"Failed to store semantic memory: {str(e)}")
    
    async def retrieve_similar_memories(self, collection_name: str, query: str, limit: int = 5, min_relevance_score: float = 0.7) -> List[Dict]:
        """
        Retrieve semantically similar memories based on a query.
        
        Args:
            collection_name: Collection to search
            query: The query text to find similar memories
            limit: Maximum number of memories to retrieve
            min_relevance_score: Minimum relevance score (0-1)
            
        Returns:
            List of similar memories with their metadata
        """
        try:
            # Note: This is a simplified version since we're not doing actual semantic search
            # In a production system, this would use the SK memory search capabilities
            
            collection_key = f"semantic_memory_{collection_name}"
            if collection_key not in self._context_store:
                return []
            
            # For MVP, we'll do a basic keyword matching (not true semantic search)
            results = []
            query_terms = set(query.lower().split())
            
            for memory_key, memory_data in self._context_store[collection_key].items():
                text = memory_data["text"].lower()
                text_terms = set(text.split())
                
                # Calculate a simple overlap score (not a true semantic similarity)
                if query_terms and text_terms:
                    overlap = len(query_terms.intersection(text_terms))
                    total = len(query_terms.union(text_terms))
                    relevance = overlap / total if total > 0 else 0
                else:
                    relevance = 0
                
                if relevance >= min_relevance_score:
                    results.append({
                        "id": memory_key,
                        "text": memory_data["text"],
                        "relevance": relevance,
                        "metadata": memory_data["metadata"]
                    })
            
            # Sort by relevance and limit results
            results.sort(key=lambda x: x["relevance"], reverse=True)
            return results[:limit]
        except Exception as e:
            self.logger.error(f"Failed to retrieve similar memories: {str(e)}")
            raise MemoryException(f"Failed to retrieve similar memories: {str(e)}")
    
    def store_context(self, context_id: str, context_data: Dict[str, Any], context_type: str = "application") -> None:
        """
        Store application context data.
        
        Args:
            context_id: Unique identifier for the context
            context_data: Dictionary of context data to store
            context_type: Type of context (application, conversation, document, etc.)
        """
        if context_id not in self._context_store:
            self._context_store[context_id] = {
                "type": context_type,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "data": context_data
            }
        else:
            self._context_store[context_id]["updated_at"] = datetime.utcnow().isoformat()
            self._context_store[context_id]["data"] = context_data
            
        self.logger.info(f"Stored context: {context_id} ({context_type})")
    
    def retrieve_context(self, context_id: str, default: Any = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve context data.
        
        Args:
            context_id: Unique identifier for the context
            default: Default value to return if context not found
            
        Returns:
            The context data or default if not found
        """
        if context_id in self._context_store:
            return self._context_store[context_id]["data"]
        return default
    
    def update_context(self, context_id: str, updates: Dict[str, Any], create_if_missing: bool = False) -> None:
        """
        Update existing context data.
        
        Args:
            context_id: Unique identifier for the context
            updates: Dictionary of updates to apply to the context
            create_if_missing: Whether to create the context if it doesn't exist
            
        Raises:
            MemoryException: If context not found and create_if_missing is False
        """
        if context_id not in self._context_store:
            if create_if_missing:
                self.store_context(context_id, updates)
                return
            else:
                raise MemoryException(f"Context not found: {context_id}")
                
        # Update the context data
        self._context_store[context_id]["updated_at"] = datetime.utcnow().isoformat()
        self._context_store[context_id]["data"].update(updates)
        
        self.logger.info(f"Updated context: {context_id}")
    
    def clear_context(self, context_id: str) -> None:
        """
        Clear context data.
        
        Args:
            context_id: Unique identifier for the context to clear
        """
        if context_id in self._context_store:
            del self._context_store[context_id]
            self.logger.info(f"Cleared context: {context_id}")
    
    def store_application_state(self, application_id: str, state_data: Dict[str, Any]) -> None:
        """
        Store application state for a mortgage application.
        
        Args:
            application_id: Unique identifier for the mortgage application
            state_data: Current state of the application
        """
        context_id = f"application_state_{application_id}"
        self.store_context(context_id, state_data, "application_state")
    
    def retrieve_application_state(self, application_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve application state for a mortgage application.
        
        Args:
            application_id: Unique identifier for the mortgage application
            
        Returns:
            The current state data or None if not found
        """
        context_id = f"application_state_{application_id}"
        return self.retrieve_context(context_id)
    
    def store_conversation_memory(self, conversation_id: str, message: Dict[str, Any]) -> None:
        """
        Store a conversation message in memory.
        
        Args:
            conversation_id: Unique identifier for the conversation
            message: The message data to store
        """
        context_id = f"conversation_{conversation_id}"
        
        # Get existing conversation or create new one
        conversation = self.retrieve_context(context_id, {"messages": []})
        
        # Add timestamp to message
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()
        
        # Add message to conversation
        conversation["messages"].append(message)
        
        # Store updated conversation
        self.store_context(context_id, conversation, "conversation")
    
    def retrieve_conversation_history(self, conversation_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history.
        
        Args:
            conversation_id: Unique identifier for the conversation
            limit: Optional limit on number of messages to retrieve
            
        Returns:
            List of conversation messages
        """
        context_id = f"conversation_{conversation_id}"
        conversation = self.retrieve_context(context_id, {"messages": []})
        messages = conversation.get("messages", [])
        
        # Apply limit if specified
        if limit is not None and limit > 0:
            messages = messages[-limit:]
            
        return messages
    
    def store_decision_record(self, application_id: str, decision_data: Dict[str, Any]) -> None:
        """
        Store a decision record for an application.
        
        Args:
            application_id: Unique identifier for the application
            decision_data: Data about the decision
        """
        context_id = f"decisions_{application_id}"
        
        # Get existing decisions or create new record
        decisions = self.retrieve_context(context_id, {"decisions": []})
        
        # Add timestamp to decision
        if "timestamp" not in decision_data:
            decision_data["timestamp"] = datetime.utcnow().isoformat()
        
        # Add decision to record
        decisions["decisions"].append(decision_data)
        
        # Store updated decisions
        self.store_context(context_id, decisions, "decisions")
    
    def retrieve_decision_history(self, application_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve decision history for an application.
        
        Args:
            application_id: Unique identifier for the application
            
        Returns:
            List of decision records
        """
        context_id = f"decisions_{application_id}"
        decisions = self.retrieve_context(context_id, {"decisions": []})
        return decisions.get("decisions", [])