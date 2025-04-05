# src/copilot/session_manager.py

from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import asyncio
import uuid
from src.utils.logging_utils import get_logger

logger = get_logger("copilot_session_manager")

class ConversationContext:
    """
    Manages conversation context for Copilot Studio interactions.
    Maintains session state between multiple turns of conversation.
    """
    
    def __init__(self):
        self.sessions = {}  # In-memory storage
        self.session_timeout = 30 * 60  # 30 minutes in seconds
        
        # Start background cleanup task
        asyncio.create_task(self._cleanup_expired_sessions())
    
    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve session data for a given session ID.
        Creates a new session if one doesn't exist.
        
        Args:
            session_id: The unique session identifier
            
        Returns:
            Session data dictionary
        """
        if session_id in self.sessions:
            # Update last access time
            self.sessions[session_id]["_last_accessed"] = datetime.utcnow().timestamp()
            return self.sessions[session_id]
        
        # Create new session
        logger.info(f"Creating new session: {session_id}")
        new_session = {
            "_created": datetime.utcnow().timestamp(),
            "_last_accessed": datetime.utcnow().timestamp()
        }
        self.sessions[session_id] = new_session
        return new_session
    
    async def update_session(self, session_id: str, data: Dict[str, Any]) -> None:
        """
        Update session with new data.
        
        Args:
            session_id: The unique session identifier
            data: New data to add to the session
        """
        session = await self.get_session(session_id)
        session.update(data)
        logger.debug(f"Updated session {session_id}: {len(data)} items")
    
    async def delete_session(self, session_id: str) -> None:
        """
        Delete a session.
        
        Args:
            session_id: The unique session identifier
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
    
    async def _cleanup_expired_sessions(self) -> None:
        """Background task to remove expired sessions"""
        while True:
            try:
                now = datetime.utcnow().timestamp()
                expired_sessions = []
                
                for session_id, session in self.sessions.items():
                    last_accessed = session.get("_last_accessed", 0)
                    if now - last_accessed > self.session_timeout:
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    await self.delete_session(session_id)
                
                if expired_sessions:
                    logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                
                # Check every 5 minutes
                await asyncio.sleep(300)
            except Exception as e:
                logger.error(f"Error in session cleanup: {str(e)}")
                await asyncio.sleep(300)

# Create singleton instance
conversation_context = ConversationContext()