"""
State Manager Module
Tracks and manages application state throughout the mortgage processing workflow.
"""

from typing import Any, Dict, List, Optional
import asyncio
from datetime import datetime
import json

from src.data.models import ApplicationStatus
from src.data.cosmos_manager import CosmosDBManager
from utils.logging_utils import get_logger

logger = get_logger("workflow.state_manager")


class StateManager:
    """
    Manages the state of mortgage applications throughout the processing workflow.
    Tracks state transitions, stores context, and provides history of application processing.
    """
    
    def __init__(self):
        self.logger = get_logger("state_manager")
        self.cosmos_manager = CosmosDBManager()
        
        # In-memory state cache for faster access
        self.state_cache = {}
        
    async def create_application_state(self, application_id: str, initial_state: str = ApplicationStatus.INITIATED,
                                      initial_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new application state record.
        
        Args:
            application_id: Unique identifier for the application
            initial_state: Initial state of the application
            initial_context: Initial context data for the application
            
        Returns:
            Dict containing the created application state
        """
        self.logger.info(f"Creating application state for {application_id} with initial state {initial_state}")
        
        # Create the initial state record
        now = datetime.utcnow().isoformat()
        state_record = {
            "application_id": application_id,
            "status": initial_state,
            "context": initial_context or {},
            "history": [
                {
                    "status": initial_state,
                    "timestamp": now,
                    "notes": "Application initiated"
                }
            ],
            "last_updated": now
        }
        
        # Store in database
        try:
            await self.cosmos_manager.create_item("application_states", state_record)
            
            # Update cache
            self.state_cache[application_id] = state_record
            
            return state_record
            
        except Exception as e:
            self.logger.error(f"Error creating application state: {str(e)}")
            # Fall back to in-memory only if database fails
            self.state_cache[application_id] = state_record
            return state_record
    
    async def update_application_state(self, application_id: str, new_state: str,
                                      context_updates: Optional[Dict[str, Any]] = None,
                                      notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Update an application's state and context.
        
        Args:
            application_id: Unique identifier for the application
            new_state: New state for the application
            context_updates: Updates to the application context
            notes: Optional notes about the state change
            
        Returns:
            Dict containing the updated application state
        """
        self.logger.info(f"Updating application {application_id} state to {new_state}")
        
        # Get current state
        current_state = await self.get_application_state(application_id)
        
        if not current_state:
            self.logger.warning(f"Application {application_id} not found, creating new state record")
            return await self.create_application_state(application_id, new_state, context_updates)
        
        # Update the state record
        now = datetime.utcnow().isoformat()
        
        # Update context if provided
        if context_updates:
            current_context = current_state.get("context", {})
            current_context.update(context_updates)
            current_state["context"] = current_context
        
        # Update state and timestamp
        current_state["status"] = new_state
        current_state["last_updated"] = now
        
        # Add to history
        history_entry = {
            "status": new_state,
            "timestamp": now,
            "notes": notes or f"State changed to {new_state}"
        }
        
        if "history" not in current_state:
            current_state["history"] = []
        
        current_state["history"].append(history_entry)
        
        # Store in database
        try:
            await self.cosmos_manager.update_item("application_states", current_state)
            
            # Update cache
            self.state_cache[application_id] = current_state
            
            return current_state
            
        except Exception as e:
            self.logger.error(f"Error updating application state: {str(e)}")
            # Fall back to in-memory only if database fails
            self.state_cache[application_id] = current_state
            return current_state
    
    async def get_application_state(self, application_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current state of an application.
        
        Args:
            application_id: Unique identifier for the application
            
        Returns:
            Dict containing the application state or None if not found
        """
        # Check cache first
        if application_id in self.state_cache:
            return self.state_cache[application_id]
        
        # Try to get from database
        try:
            state_record = await self.cosmos_manager.get_item(
                "application_states", 
                {"application_id": application_id}
            )
            
            if state_record:
                # Update cache
                self.state_cache[application_id] = state_record
                return state_record
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting application state: {str(e)}")
            return None
    
    async def get_application_history(self, application_id: str) -> List[Dict[str, Any]]:
        """
        Get the state change history for an application.
        
        Args:
            application_id: Unique identifier for the application
            
        Returns:
            List of state change history entries
        """
        state_record = await self.get_application_state(application_id)
        
        if not state_record:
            return []
        
        return state_record.get("history", [])
    
    async def add_context_data(self, application_id: str, context_data: Dict[str, Any],
                              notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Add data to an application's context without changing state.
        
        Args:
            application_id: Unique identifier for the application
            context_data: Data to add to context
            notes: Optional notes about the context update
            
        Returns:
            Dict containing the updated application state
        """
        self.logger.info(f"Adding context data for application {application_id}")
        
        # Get current state
        current_state = await self.get_application_state(application_id)
        
        if not current_state:
            self.logger.warning(f"Application {application_id} not found, creating new state record")
            return await self.create_application_state(
                application_id, ApplicationStatus.INITIATED, context_data
            )
        
        # Update the context data
        now = datetime.utcnow().isoformat()
        
        current_context = current_state.get("context", {})
        current_context.update(context_data)
        current_state["context"] = current_context
        current_state["last_updated"] = now
        
        # Add to history if notes provided
        if notes:
            history_entry = {
                "status": current_state.get("status"),
                "timestamp": now,
                "notes": notes
            }
            
            if "history" not in current_state:
                current_state["history"] = []
            
            current_state["history"].append(history_entry)
        
        # Store in database
        try:
            await self.cosmos_manager.update_item("application_states", current_state)
            
            # Update cache
            self.state_cache[application_id] = current_state
            
            return current_state
            
        except Exception as e:
            self.logger.error(f"Error updating application context: {str(e)}")
            # Fall back to in-memory only if database fails
            self.state_cache[application_id] = current_state
            return current_state
    
    async def get_applications_by_state(self, state: str) -> List[Dict[str, Any]]:
        """
        Get all applications in a specific state.
        
        Args:
            state: Application state to query for
            
        Returns:
            List of application state records
        """
        try:
            query = f"SELECT * FROM c WHERE c.status = '{state}'"
            result = await self.cosmos_manager.query_items("application_states", query)
            return result
            
        except Exception as e:
            self.logger.error(f"Error querying applications by state: {str(e)}")
            
            # Fall back to in-memory cache
            return [
                state_record for state_record in self.state_cache.values()
                if state_record.get("status") == state
            ]
    
    def clear_cache(self) -> None:
        """Clear the in-memory state cache."""
        self.state_cache = {}
        self.logger.info("State cache cleared")