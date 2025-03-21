

import abc
import logging
from typing import Dict, List, Any, Optional, Tuple, Union

logger = logging.getLogger(__name__)

class CollaborativeAgent(abc.ABC):
    """
    Base interface for agents that participate in collaboration patterns.
    Agents must implement these methods to work with the collaboration manager.
    """
    
    @abc.abstractmethod
    def get_agent_id(self) -> str:
        """
        Get the unique identifier for this agent.
        
        Returns:
            str: Agent identifier
        """
        pass
    
    @abc.abstractmethod
    def receive_message(self, message: Dict[str, Any]) -> None:
        """
        Receive a message from another agent or the collaboration manager.
        
        Args:
            message (Dict[str, Any]): The message data
        """
        pass
    
    @abc.abstractmethod
    def execute_step(self, step_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific workflow step.
        
        Args:
            step_name (str): Name of the step to execute
            inputs (Dict[str, Any]): Input data for the step
            
        Returns:
            Dict[str, Any]: Result of the step execution with at least:
                - status: "success" or "error"
                - output: Dict of output values (if success)
                - error: Error message (if error)
        """
        pass
    
    @abc.abstractmethod
    def can_handle_step(self, step_name: str) -> bool:
        """
        Check if this agent can handle a specific workflow step.
        
        Args:
            step_name (str): Name of the step
            
        Returns:
            bool: True if the agent can handle this step, False otherwise
        """
        pass
    
    @abc.abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get the capabilities of this agent.
        
        Returns:
            Dict[str, Any]: Agent capabilities
        """
        pass


class BaseCollaborativeAgent(CollaborativeAgent):
    """
    Base implementation of the CollaborativeAgent interface.
    Provides common functionality for collaborative agents.
    """
    
    def __init__(self, agent_id: str, collaboration_manager=None):
        """
        Initialize the base collaborative agent.
        
        Args:
            agent_id (str): Unique identifier for this agent
            collaboration_manager: Optional reference to the collaboration manager
        """
        self.agent_id = agent_id
        self.collaboration_manager = collaboration_manager
        self.message_queue = []
        self.handled_messages = set()
        self.active_steps = {}
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
    
    def get_agent_id(self) -> str:
        """
        Get the unique identifier for this agent.
        
        Returns:
            str: Agent identifier
        """
        return self.agent_id
    
    def set_collaboration_manager(self, collaboration_manager) -> None:
        """
        Set the collaboration manager for this agent.
        
        Args:
            collaboration_manager: Reference to the collaboration manager
        """
        self.collaboration_manager = collaboration_manager
    
    def receive_message(self, message: Dict[str, Any]) -> None:
        """
        Receive a message from another agent or the collaboration manager.
        
        Args:
            message (Dict[str, Any]): The message data
        """
        message_id = message.get("message_id", "unknown")
        
        if message_id in self.handled_messages:
            self.logger.warning(f"Ignoring duplicate message: {message_id}")
            return
        
        self.logger.debug(f"Received message: {message_id} from {message.get('sender')}")
        
        # Add to queue for processing
        self.message_queue.append(message)
        self.handled_messages.add(message_id)
        
        # Process immediately if it's high priority
        if message.get("priority") == "high":
            self.process_next_message()
    
    def process_next_message(self) -> bool:
        """
        Process the next message in the queue.
        
        Returns:
            bool: True if a message was processed, False if queue was empty
        """
        if not self.message_queue:
            return False
        
        message = self.message_queue.pop(0)
        message_type = message.get("message_type", "unknown")
        
        try:
            if message_type == "request":
                self._handle_request_message(message)
            elif message_type == "response":
                self._handle_response_message(message)
            elif message_type == "notification":
                self._handle_notification_message(message)
            elif message_type == "error":
                self._handle_error_message(message)
            elif message_type == "decision":
                self._handle_decision_message(message)
            else:
                self.logger.warning(f"Unknown message type: {message_type}")
        except Exception as e:
            self.logger.error(f"Error processing message {message.get('message_id')}: {str(e)}")
            
            # If we have a collaboration manager, send an error response
            if self.collaboration_manager and message.get("sender") != "collaboration_manager":
                self.send_error_response(message, str(e))
        
        return True
    
    def process_all_messages(self) -> int:
        """
        Process all messages in the queue.
        
        Returns:
            int: Number of messages processed
        """
        count = 0
        while self.process_next_message():
            count += 1
        return count
    
    def _handle_request_message(self, message: Dict[str, Any]) -> None:
        """
        Handle a request message.
        
        Args:
            message (Dict[str, Any]): The message data
        """
        # Default implementation - override in subclasses
        self.logger.info(f"Request message from {message.get('sender')}: {message.get('content', {}).get('request_type')}")
        
        # Send a default response
        self.send_response(message, {"status": "not_implemented"})
    
    def _handle_response_message(self, message: Dict[str, Any]) -> None:
        """
        Handle a response message.
        
        Args:
            message (Dict[str, Any]): The message data
        """
        # Default implementation - override in subclasses
        self.logger.info(f"Response message from {message.get('sender')}: {message.get('content', {}).get('status')}")
    
    def _handle_notification_message(self, message: Dict[str, Any]) -> None:
        """
        Handle a notification message.
        
        Args:
            message (Dict[str, Any]): The message data
        """
        # Default implementation - override in subclasses
        self.logger.info(f"Notification from {message.get('sender')}: {message.get('content', {}).get('notification_type')}")
    
    def _handle_error_message(self, message: Dict[str, Any]) -> None:
        """
        Handle an error message.
        
        Args:
            message (Dict[str, Any]): The message data
        """
        # Default implementation - override in subclasses
        error = message.get("content", {}).get("error", "Unknown error")
        self.logger.warning(f"Error message from {message.get('sender')}: {error}")
    
    def _handle_decision_message(self, message: Dict[str, Any]) -> None:
        """
        Handle a decision message.
        
        Args:
            message (Dict[str, Any]): The message data
        """
        # Default implementation - override in subclasses
        decision = message.get("content", {}).get("decision", "Unknown decision")
        self.logger.info(f"Decision from {message.get('sender')}: {decision}")
    
    def send_message(self, 
                   recipient: str, 
                   message_type: str, 
                   content: Dict[str, Any], 
                   session_id: Optional[str] = None,
                   in_response_to: Optional[str] = None,
                   priority: str = "medium") -> Optional[str]:
        """
        Send a message to another agent.
        
        Args:
            recipient (str): ID of the receiving agent
            message_type (str): Type of message
            content (Dict[str, Any]): Message content
            session_id (str, optional): ID of the associated workflow session
            in_response_to (str, optional): ID of the message this is responding to
            priority (str, optional): Message priority (high, medium, low)
            
        Returns:
            Optional[str]: Message ID if successful, None if failed
        """
        if not self.collaboration_manager:
            self.logger.error("No collaboration manager set - cannot send message")
            return None
        
        return self.collaboration_manager.send_message(
            sender=self.agent_id,
            recipient=recipient,
            message_type=message_type,
            content=content,
            session_id=session_id,
            in_response_to=in_response_to,
            priority=priority
        )
    
    def send_response(self, request_message: Dict[str, Any], response_content: Dict[str, Any]) -> Optional[str]:
        """
        Send a response to a request message.
        
        Args:
            request_message (Dict[str, Any]): Original request message
            response_content (Dict[str, Any]): Response content
            
        Returns:
            Optional[str]: Message ID if successful, None if failed
        """
        return self.send_message(
            recipient=request_message.get("sender"),
            message_type="response",
            content=response_content,
            session_id=request_message.get("context_id"),
            in_response_to=request_message.get("message_id"),
            priority=request_message.get("priority", "medium")
        )
    
    def send_error_response(self, request_message: Dict[str, Any], error_message: str) -> Optional[str]:
        """
        Send an error response to a request message.
        
        Args:
            request_message (Dict[str, Any]): Original request message
            error_message (str): Error message
            
        Returns:
            Optional[str]: Message ID if successful, None if failed
        """
        return self.send_response(
            request_message=request_message,
            response_content={
                "status": "error",
                "error": error_message
            }
        )
    
    def can_handle_step(self, step_name: str) -> bool:
        """
        Check if this agent can handle a specific workflow step.
        
        Args:
            step_name (str): Name of the step
            
        Returns:
            bool: True if the agent can handle this step, False otherwise
        """
        # Default implementation - override in subclasses
        return False
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get the capabilities of this agent.
        
        Returns:
            Dict[str, Any]: Agent capabilities
        """
        # Default implementation - override in subclasses
        return {
            "can_initiate": False,
            "can_finalize_decisions": False,
            "can_resolve_conflicts": False,
            "can_delegate": False,
            "can_monitor": False,
            "priority_level": 3
        }
    
    def execute_step(self, step_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific workflow step.
        
        Args:
            step_name (str): Name of the step to execute
            inputs (Dict[str, Any]): Input data for the step
            
        Returns:
            Dict[str, Any]: Result of the step execution with at least:
                - status: "success" or "error"
                - output: Dict of output values (if success)
                - error: Error message (if error)
        """
        # Default implementation - override in subclasses
        self.logger.error(f"Agent {self.agent_id} does not implement step: {step_name}")
        return {
            "status": "error",
            "error": f"Step {step_name} not implemented by agent {self.agent_id}"
        }
    
    def start_workflow(self, 
                     pattern_name: str, 
                     context_data: Dict[str, Any]) -> Optional[str]:
        """
        Start a new workflow as the initiator.
        
        Args:
            pattern_name (str): Name of the collaboration pattern to use
            context_data (Dict[str, Any]): Initial context data for the workflow
            
        Returns:
            Optional[str]: Session ID if successful, None if failed
        """
        if not self.collaboration_manager:
            self.logger.error("No collaboration manager set - cannot start workflow")
            return None
        
        # Check if agent can initiate workflows
        capabilities = self.get_capabilities()
        if not capabilities.get("can_initiate", False):
            self.logger.error(f"Agent {self.agent_id} is not authorized to initiate workflows")
            return None
        
        return self.collaboration_manager.create_workflow_session(
            pattern_name=pattern_name,
            context_data=context_data,
            initiator=self.agent_id
        )
    
    def get_workflow_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a workflow session.
        
        Args:
            session_id (str): ID of the workflow session
            
        Returns:
            Optional[Dict[str, Any]]: Session status information or None if not found
        """
        if not self.collaboration_manager:
            self.logger.error("No collaboration manager set - cannot get workflow status")
            return None
        
        return self.collaboration_manager.get_session_status(session_id)
    
    def confirm_workflow_step(self, session_id: str, confirmed: bool = True) -> bool:
        """
        Confirm a workflow step that requires confirmation.
        
        Args:
            session_id (str): ID of the workflow session
            confirmed (bool, optional): Whether the step is confirmed or rejected
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.collaboration_manager:
            self.logger.error("No collaboration manager set - cannot confirm step")
            return False
        
        # Check if agent can finalize decisions
        capabilities = self.get_capabilities()
        if not capabilities.get("can_finalize_decisions", False):
            self.logger.error(f"Agent {self.agent_id} is not authorized to confirm workflow steps")
            return False
        
        return self.collaboration_manager.confirm_step(session_id, confirmed)
    
    def resume_workflow(self, 
                      session_id: str, 
                      action: str = "continue", 
                      data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Resume a workflow that is waiting for instruction or intervention.
        
        Args:
            session_id (str): ID of the workflow session
            action (str, optional): Action to take (continue, retry, abort, skip)
            data (Dict[str, Any], optional): Additional data to add to context
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.collaboration_manager:
            self.logger.error("No collaboration manager set - cannot resume workflow")
            return False
        
        # Check if agent can resolve conflicts
        capabilities = self.get_capabilities()
        if not capabilities.get("can_resolve_conflicts", False):
            self.logger.error(f"Agent {self.agent_id} is not authorized to resume workflows")
            return False
        
        return self.collaboration_manager.resume_workflow(session_id, action, data)
    
    def delegate_step(self, 
                    session_id: str, 
                    step_name: str, 
                    delegate_to: str,
                    inputs: Dict[str, Any]) -> bool:
        """
        Delegate a workflow step to another agent.
        
        Args:
            session_id (str): ID of the workflow session
            step_name (str): Name of the step to delegate
            delegate_to (str): ID of the agent to delegate to
            inputs (Dict[str, Any]): Input data for the step
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.collaboration_manager:
            self.logger.error("No collaboration manager set - cannot delegate step")
            return False
        
        # Check if agent can delegate
        capabilities = self.get_capabilities()
        if not capabilities.get("can_delegate", False):
            self.logger.error(f"Agent {self.agent_id} is not authorized to delegate steps")
            return False
        
        # Send delegation message to target agent
        message_id = self.send_message(
            recipient=delegate_to,
            message_type="request",
            content={
                "request_type": "delegation",
                "step_name": step_name,
                "inputs": inputs
            },
            session_id=session_id,
            priority="high"
        )
        
        return message_id is not None