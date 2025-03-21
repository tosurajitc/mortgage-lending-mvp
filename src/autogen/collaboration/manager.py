

import os
import json
import time
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path

logger = logging.getLogger(__name__)

class CollaborationManager:
    """
    Manages collaboration patterns between agents in the mortgage application system.
    Handles workflow execution, messaging, decision tracking, and error handling.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the collaboration manager with the specified configuration.
        
        Args:
            config_path (str, optional): Path to the collaboration configuration file.
                If not provided, will use the default configuration.
        """
        self.workflows = {}
        self.active_sessions = {}
        self.agent_registry = {}
        
        # Load collaboration configuration
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        else:
            # Default to config file in standard location
            config_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                'config', 
                'agent_collaboration_config.json'
            )
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                logger.error("Agent collaboration configuration not found")
                raise FileNotFoundError("Agent collaboration configuration not found")
        
        # Extract workflow definitions
        self.collaboration_patterns = self.config.get("collaboration_patterns", {})
        self.agent_capabilities = self.config.get("agent_capabilities", {})
        self.communication_protocols = self.config.get("communication_protocols", {})
        self.decision_governance = self.config.get("decision_governance", {})
        
        logger.info(f"Loaded {len(self.collaboration_patterns)} collaboration patterns")
    
    def register_agent(self, agent_id: str, agent_instance: Any) -> bool:
        """
        Register an agent with the collaboration manager.
        
        Args:
            agent_id (str): Identifier for the agent
            agent_instance (Any): Reference to the agent instance
            
        Returns:
            bool: True if registration was successful, False otherwise
        """
        if agent_id in self.agent_registry:
            logger.warning(f"Agent {agent_id} is already registered")
            return False
        
        if agent_id not in self.agent_capabilities:
            logger.warning(f"Agent {agent_id} capabilities not defined in configuration")
        
        self.agent_registry[agent_id] = agent_instance
        logger.info(f"Agent {agent_id} registered with collaboration manager")
        return True
    
    def create_workflow_session(self, 
                              pattern_name: str, 
                              context_data: Dict[str, Any],
                              initiator: str) -> Optional[str]:
        """
        Create a new workflow session based on a collaboration pattern.
        
        Args:
            pattern_name (str): Name of the collaboration pattern to use
            context_data (Dict[str, Any]): Initial context data for the workflow
            initiator (str): ID of the agent initiating the workflow
            
        Returns:
            Optional[str]: Session ID if successful, None if failed
        """
        if pattern_name not in self.collaboration_patterns:
            logger.error(f"Collaboration pattern '{pattern_name}' not found")
            return None
        
        pattern = self.collaboration_patterns[pattern_name]
        
        # Validate initiator
        if initiator not in pattern["agents"]:
            logger.error(f"Agent {initiator} is not part of the {pattern_name} pattern")
            return None
        
        if pattern["initiator"] != initiator:
            logger.error(f"Agent {initiator} is not authorized to initiate {pattern_name}")
            return None
        
        # Create session
        session_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        workflow_session = {
            "session_id": session_id,
            "pattern_name": pattern_name,
            "initiator": initiator,
            "start_time": timestamp,
            "status": "initialized",
            "current_step_index": 0,
            "steps_completed": [],
            "steps_failed": [],
            "context": context_data,
            "messages": [],
            "decisions": [],
            "errors": []
        }
        
        self.active_sessions[session_id] = workflow_session
        logger.info(f"Created workflow session {session_id} using pattern {pattern_name}")
        
        # Trigger the first step in the workflow
        self._execute_next_step(session_id)
        
        return session_id
    
    def _execute_next_step(self, session_id: str) -> bool:
        """
        Execute the next step in a workflow session.
        
        Args:
            session_id (str): ID of the workflow session
            
        Returns:
            bool: True if step was started, False otherwise
        """
        if session_id not in self.active_sessions:
            logger.error(f"Session {session_id} not found")
            return False
        
        session = self.active_sessions[session_id]
        pattern = self.collaboration_patterns[session["pattern_name"]]
        steps = pattern["steps"]
        
        # Check if workflow is complete
        if session["current_step_index"] >= len(steps):
            self._complete_workflow(session_id)
            return False
        
        current_step = steps[session["current_step_index"]]
        agent_id = current_step["agent"]
        
        # Check if step should be executed based on condition
        if "condition" in current_step and not current_step["required"]:
            condition_met = self._evaluate_condition(current_step["condition"], session["context"])
            if not condition_met:
                logger.info(f"Skipping step {current_step['name']} - condition not met")
                session["current_step_index"] += 1
                return self._execute_next_step(session_id)
        
        # Check if step is event-triggered
        if current_step.get("event_triggered", False):
            # Don't execute now, wait for event
            logger.info(f"Step {current_step['name']} waiting for event {current_step.get('trigger_event')}")
            session["status"] = "waiting_for_event"
            return True
        
        # Prepare step execution
        step_inputs = {}
        if "inputs" in current_step:
            for input_name in current_step["inputs"]:
                if input_name in session["context"]:
                    step_inputs[input_name] = session["context"][input_name]
                else:
                    logger.warning(f"Required input {input_name} not found in context for step {current_step['name']}")
        
        # Get agent
        if agent_id not in self.agent_registry:
            logger.error(f"Agent {agent_id} not registered")
            self._handle_step_error(session_id, f"Agent {agent_id} not registered")
            return False
        
        agent = self.agent_registry[agent_id]
        
        # Execute the step
        try:
            step_execution = {
                "step_name": current_step["name"],
                "step_id": f"{session_id}_{current_step['name']}",
                "agent": agent_id,
                "inputs": step_inputs,
                "start_time": datetime.utcnow().isoformat(),
                "timeout_seconds": current_step.get("timeout_seconds", 60),
                "status": "in_progress"
            }
            
            session["current_step_execution"] = step_execution
            session["status"] = "step_in_progress"
            
            # Actually execute the step (implementation depends on agent interface)
            logger.info(f"Executing step {current_step['name']} with agent {agent_id}")
            
            # This would be an asynchronous call in a real system
            # For the MVP, we'll use a synchronous approach
            step_result = self._execute_agent_step(agent, current_step["name"], step_inputs)
            
            # Handle results
            self._handle_step_completion(session_id, step_result)
            return True
            
        except Exception as e:
            logger.error(f"Error executing step {current_step['name']}: {str(e)}")
            self._handle_step_error(session_id, str(e))
            return False
    
    def _execute_agent_step(self, agent: Any, step_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a step on an agent.
        
        Args:
            agent (Any): Agent instance
            step_name (str): Name of the step to execute
            inputs (Dict[str, Any]): Input data for the step
            
        Returns:
            Dict[str, Any]: Result data from the step
        """
        # This is a placeholder for the actual agent step execution logic
        # In a real system, this would call the appropriate method on the agent
        # based on the step name and handle async behavior
        
        # For the MVP, we'll assume agents have an "execute_step" method
        if hasattr(agent, "execute_step") and callable(agent.execute_step):
            return agent.execute_step(step_name, inputs)
        else:
            # Fallback for testing
            logger.warning(f"Agent does not implement execute_step method - using mock result")
            
            # Mock result for testing
            import random
            result = {
                "status": "success" if random.random() > 0.2 else "error",
                "output": {"result": f"Mock result for {step_name}", "score": random.random()}
            }
            
            # Simulate processing time
            time.sleep(0.5)
            
            return result
    
    def _handle_step_completion(self, session_id: str, result: Dict[str, Any]) -> None:
        """
        Handle the completion of a step.
        
        Args:
            session_id (str): ID of the workflow session
            result (Dict[str, Any]): Result data from the step
        """
        session = self.active_sessions[session_id]
        current_step = session["current_step_execution"]
        pattern = self.collaboration_patterns[session["pattern_name"]]
        step_index = session["current_step_index"]
        step_config = pattern["steps"][step_index]
        
        # Update step execution record
        current_step["end_time"] = datetime.utcnow().isoformat()
        current_step["result"] = result
        
        if result.get("status") == "success":
            current_step["status"] = "completed"
            session["steps_completed"].append(current_step)
            
            # Update context with outputs
            if "output" in result:
                output_data = result["output"]
                for output_name in step_config.get("outputs", []):
                    if output_name in output_data:
                        session["context"][output_name] = output_data[output_name]
            
            # Check if confirmation is required
            if step_config.get("requires_confirmation", False):
                session["status"] = "awaiting_confirmation"
                logger.info(f"Step {step_config['name']} completed but requires confirmation")
                return
            
            # Move to next step
            session["current_step_index"] += 1
            self._execute_next_step(session_id)
        else:
            # Handle step failure
            error_message = result.get("error", "Unknown error")
            self._handle_step_error(session_id, error_message)
    
    def _handle_step_error(self, session_id: str, error_message: str) -> None:
        """
        Handle a step execution error.
        
        Args:
            session_id (str): ID of the workflow session
            error_message (str): Error message
        """
        session = self.active_sessions[session_id]
        current_step = session["current_step_execution"]
        pattern = self.collaboration_patterns[session["pattern_name"]]
        step_index = session["current_step_index"]
        step_config = pattern["steps"][step_index]
        
        # Update step execution record
        current_step["end_time"] = datetime.utcnow().isoformat()
        current_step["status"] = "failed"
        current_step["error"] = error_message
        session["steps_failed"].append(current_step)
        
        # Get error handling configuration
        error_handling = pattern.get("error_handling", {}).get(step_config["name"], {})
        on_error = error_handling.get("on_error", "notify_orchestrator")
        max_retries = error_handling.get("max_retries", 0)
        retry_count = current_step.get("retry_count", 0)
        
        if on_error == "retry" and retry_count < max_retries:
            # Retry the step
            logger.info(f"Retrying step {step_config['name']} (attempt {retry_count + 1}/{max_retries})")
            current_step["retry_count"] = retry_count + 1
            session["status"] = "retrying_step"
            self._execute_next_step(session_id)
        elif on_error == "notify_orchestrator":
            # Notify orchestrator and wait for instruction
            logger.info(f"Notifying orchestrator about step failure: {step_config['name']}")
            session["status"] = "awaiting_orchestrator_instruction"
            self._notify_orchestrator_of_error(session_id, error_message)
        elif on_error == "notify_human":
            # Notify human operator and wait for instruction
            logger.info(f"Notifying human operator about step failure: {step_config['name']}")
            session["status"] = "awaiting_human_intervention"
            self._notify_human_of_error(session_id, error_message)
        else:
            # Use fallback action
            fallback = error_handling.get("fallback", "abort_workflow")
            logger.info(f"Using fallback action '{fallback}' for step {step_config['name']}")
            self._execute_fallback_action(session_id, fallback)
    
    def _execute_fallback_action(self, session_id: str, fallback: str) -> None:
        """
        Execute a fallback action for error handling.
        
        Args:
            session_id (str): ID of the workflow session
            fallback (str): Name of the fallback action
        """
        session = self.active_sessions[session_id]
        
        if fallback == "abort_workflow":
            session["status"] = "aborted"
            logger.info(f"Workflow {session_id} aborted due to error")
        elif fallback == "skip_step":
            session["current_step_index"] += 1
            session["status"] = "in_progress"
            logger.info(f"Skipping failed step and continuing workflow {session_id}")
            self._execute_next_step(session_id)
        elif fallback == "manual_intervention":
            session["status"] = "awaiting_human_intervention"
            logger.info(f"Workflow {session_id} waiting for manual intervention")
        elif fallback == "conservative_assessment":
            # For underwriting or compliance steps, use a conservative assessment
            step_config = self.collaboration_patterns[session["pattern_name"]]["steps"][session["current_step_index"]]
            agent_id = step_config["agent"]
            
            if agent_id == "underwriting_agent":
                session["context"]["risk_assessment"] = "high"
                session["context"]["loan_terms"] = {"approved": False, "reason": "Conservative assessment due to error"}
            elif agent_id == "compliance_agent":
                session["context"]["compliance_results"] = "needs_review"
                session["context"]["compliance_issues"] = ["Automatic compliance check failed"]
            
            session["current_step_index"] += 1
            session["status"] = "in_progress"
            logger.info(f"Applied conservative assessment for {agent_id} and continuing workflow {session_id}")
            self._execute_next_step(session_id)
        else:
            # Custom fallback - would need to be implemented based on application needs
            logger.warning(f"Custom fallback '{fallback}' not implemented")
            session["status"] = "error"
    
    def _notify_orchestrator_of_error(self, session_id: str, error_message: str) -> None:
        """
        Notify the orchestrator agent about a step error.
        
        Args:
            session_id (str): ID of the workflow session
            error_message (str): Error message
        """
        session = self.active_sessions[session_id]
        
        if "orchestrator" not in self.agent_registry:
            logger.error("Orchestrator agent not registered, cannot notify of error")
            session["status"] = "error"
            return
        
        orchestrator = self.agent_registry["orchestrator"]
        current_step = session["current_step_execution"]
        
        # Create notification message
        message = {
            "sender": "collaboration_manager",
            "recipient": "orchestrator",
            "message_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "message_type": "error",
            "content": {
                "session_id": session_id,
                "step_name": current_step["step_name"],
                "error": error_message,
                "context": session["context"]
            },
            "priority": "high"
        }
        
        # Record message in session
        session["messages"].append(message)
        
        # Send to orchestrator
        if hasattr(orchestrator, "receive_message") and callable(orchestrator.receive_message):
            orchestrator.receive_message(message)
        else:
            logger.warning("Orchestrator does not implement receive_message method")
    
    def _notify_human_of_error(self, session_id: str, error_message: str) -> None:
        """
        Notify a human operator about a step error.
        
        Args:
            session_id (str): ID of the workflow session
            error_message (str): Error message
        """
        session = self.active_sessions[session_id]
        current_step = session["current_step_execution"]
        
        # In a real system, this would send a notification to a human operator
        # For the MVP, we'll just log it
        logger.warning(f"HUMAN NOTIFICATION: Workflow {session_id} step {current_step['step_name']} failed: {error_message}")
        logger.warning(f"Workflow is paused until human intervention. Use resume_workflow('{session_id}') to continue.")
    
    def _complete_workflow(self, session_id: str) -> None:
        """
        Complete a workflow session.
        
        Args:
            session_id (str): ID of the workflow session
        """
        if session_id not in self.active_sessions:
            logger.error(f"Session {session_id} not found")
            return
        
        session = self.active_sessions[session_id]
        session["status"] = "completed"
        session["end_time"] = datetime.utcnow().isoformat()
        
        logger.info(f"Workflow {session_id} completed successfully")
        
        # Move from active to completed
        self.workflows[session_id] = session
        del self.active_sessions[session_id]
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """
        Evaluate a condition string against the context.
        
        Args:
            condition (str): Condition string (e.g., "exception_type == 'document'")
            context (Dict[str, Any]): Context data
        
        Returns:
            bool: True if condition is met, False otherwise
        """
        try:
            # Simple condition evaluation - in a real system you'd want to use a more secure method
            # This is a placeholder implementation for the MVP
            local_vars = context.copy()
            result = eval(condition, {"__builtins__": {}}, local_vars)
            return bool(result)
        except Exception as e:
            logger.error(f"Error evaluating condition '{condition}': {str(e)}")
            return False
    
    def send_message(self, 
                    sender: str, 
                    recipient: str, 
                    message_type: str, 
                    content: Dict[str, Any], 
                    session_id: Optional[str] = None,
                    in_response_to: Optional[str] = None,
                    priority: str = "medium") -> Optional[str]:
        """
        Send a message between agents.
        
        Args:
            sender (str): ID of the sending agent
            recipient (str): ID of the receiving agent
            message_type (str): Type of message
            content (Dict[str, Any]): Message content
            session_id (str, optional): ID of the associated workflow session
            in_response_to (str, optional): ID of the message this is responding to
            priority (str, optional): Message priority (high, medium, low)
            
        Returns:
            Optional[str]: Message ID if successful, None if failed
        """
        # Validate inputs
        if sender not in self.agent_registry:
            logger.error(f"Sender {sender} not registered")
            return None
        
        if recipient not in self.agent_registry:
            logger.error(f"Recipient {recipient} not registered")
            return None
        
        protocol = self.communication_protocols.get("agent_messaging", {})
        valid_types = protocol.get("message_types", [])
        if message_type not in valid_types:
            logger.error(f"Invalid message type: {message_type}")
            return None
        
        # Create message
        message_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        message = {
            "sender": sender,
            "recipient": recipient,
            "message_id": message_id,
            "timestamp": timestamp,
            "message_type": message_type,
            "content": content,
            "priority": priority
        }
        
        if session_id:
            message["context_id"] = session_id
        
        if in_response_to:
            message["in_response_to"] = in_response_to
        
        # Record in session if applicable
        if session_id and session_id in self.active_sessions:
            self.active_sessions[session_id]["messages"].append(message)
        
        # Deliver message
        recipient_agent = self.agent_registry[recipient]
        
        if hasattr(recipient_agent, "receive_message") and callable(recipient_agent.receive_message):
            try:
                recipient_agent.receive_message(message)
                logger.debug(f"Message {message_id} sent from {sender} to {recipient}")
                return message_id
            except Exception as e:
                logger.error(f"Error delivering message to {recipient}: {str(e)}")
                return None
        else:
            logger.warning(f"Recipient {recipient} does not implement receive_message method")
            return None
    
    def handle_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Handle an external event that may trigger workflow steps.
        
        Args:
            event_type (str): Type of event
            event_data (Dict[str, Any]): Event data
        """
        logger.info(f"Handling event: {event_type}")
        
        # Check for waiting workflows
        for session_id, session in list(self.active_sessions.items()):
            if session["status"] == "waiting_for_event":
                pattern = self.collaboration_patterns[session["pattern_name"]]
                step_index = session["current_step_index"]
                step = pattern["steps"][step_index]
                
                if step.get("event_triggered", False) and step.get("trigger_event") == event_type:
                    logger.info(f"Event {event_type} triggering step {step['name']} in session {session_id}")
                    
                    # Update context with event data
                    session["context"].update(event_data)
                    
                    # Execute the step
                    session["status"] = "in_progress"
                    self._execute_next_step(session_id)
    
    def confirm_step(self, session_id: str, confirmed: bool = True) -> bool:
        """
        Confirm a step that requires confirmation.
        
        Args:
            session_id (str): ID of the workflow session
            confirmed (bool, optional): Whether the step is confirmed or rejected
            
        Returns:
            bool: True if successful, False otherwise
        """
        if session_id not in self.active_sessions:
            logger.error(f"Session {session_id} not found")
            return False
        
        session = self.active_sessions[session_id]
        
        if session["status"] != "awaiting_confirmation":
            logger.error(f"Session {session_id} is not awaiting confirmation")
            return False
        
        current_step = session["current_step_execution"]
        
        if confirmed:
            logger.info(f"Step {current_step['step_name']} confirmed in session {session_id}")
            session["current_step_index"] += 1
            session["status"] = "in_progress"
            self._execute_next_step(session_id)
        else:
            logger.info(f"Step {current_step['step_name']} rejected in session {session_id}")
            error_message = "Step rejected during confirmation"
            self._handle_step_error(session_id, error_message)
        
        return True
    
    def resume_workflow(self, session_id: str, action: str = "continue", data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Resume a workflow that is waiting for instruction or intervention.
        
        Args:
            session_id (str): ID of the workflow session
            action (str, optional): Action to take (continue, retry, abort, skip)
            data (Dict[str, Any], optional): Additional data to add to context
            
        Returns:
            bool: True if successful, False otherwise
        """
        if session_id not in self.active_sessions:
            logger.error(f"Session {session_id} not found")
            return False
        
        session = self.active_sessions[session_id]
        valid_waiting_statuses = ["awaiting_orchestrator_instruction", "awaiting_human_intervention"]
        
        if session["status"] not in valid_waiting_statuses:
            logger.error(f"Session {session_id} is not waiting for instructions (status: {session['status']})")
            return False
        
        # Update context if data provided
        if data:
            session["context"].update(data)
        
        if action == "continue":
            # Skip the current step and continue
            session["current_step_index"] += 1
            session["status"] = "in_progress"
            logger.info(f"Resuming workflow {session_id} by continuing to next step")
            self._execute_next_step(session_id)
        elif action == "retry":
            # Retry the current step
            session["status"] = "retrying_step"
            logger.info(f"Resuming workflow {session_id} by retrying current step")
            self._execute_next_step(session_id)
        elif action == "abort":
            # Abort the workflow
            session["status"] = "aborted"
            session["end_time"] = datetime.utcnow().isoformat()
            logger.info(f"Workflow {session_id} aborted by instruction")
            
            # Move from active to completed
            self.workflows[session_id] = session
            del self.active_sessions[session_id]
        elif action == "skip":
            # Skip the current step but mark it as completed
            current_step = session["current_step_execution"]
            current_step["status"] = "skipped"
            session["steps_completed"].append(current_step)
            session["current_step_index"] += 1
            session["status"] = "in_progress"
            logger.info(f"Resuming workflow {session_id} by skipping current step")
            self._execute_next_step(session_id)
        else:
            logger.error(f"Invalid resume action: {action}")
            return False
        
        return True
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a workflow session.
        
        Args:
            session_id (str): ID of the workflow session
            
        Returns:
            Optional[Dict[str, Any]]: Session status information or None if not found
        """
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
        elif session_id in self.workflows:
            session = self.workflows[session_id]
        else:
            logger.error(f"Session {session_id} not found")
            return None
        
        # Create a summary to return
        steps_completed = len(session["steps_completed"])
        total_steps = len(self.collaboration_patterns[session["pattern_name"]]["steps"])
        
        return {
            "session_id": session_id,
            "pattern_name": session["pattern_name"],
            "status": session["status"],
            "start_time": session["start_time"],
            "end_time": session.get("end_time"),
            "progress": f"{steps_completed}/{total_steps}",
            "current_step": session.get("current_step_execution", {}).get("step_name") if session["status"] != "completed" else None,
            "errors": len(session["errors"]),
            "message_count": len(session["messages"])
        }
    
    def get_active_sessions(self) -> List[str]:
        """
        Get a list of all active workflow session IDs.
        
        Returns:
            List[str]: List of active session IDs
        """
        return list(self.active_sessions.keys())
    
    def get_completed_sessions(self) -> List[str]:
        """
        Get a list of all completed workflow session IDs.
        
        Returns:
            List[str]: List of completed session IDs
        """
        return list(self.workflows.keys())