

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
import src.autogen

from src.autogen.collaboration.agent import BaseCollaborativeAgent
from src.autogen.collaboration.manager import CollaborationManager

logger = logging.getLogger(__name__)

class AutoGenCollaborativeAgent(BaseCollaborativeAgent):
    """
    Wrapper for AutoGen agents to make them work with the collaboration system.
    Bridges between the AutoGen agent framework and our collaboration patterns.
    """
    
    def __init__(self, agent_id: str, autogen_agent: autogen.Agent, collaboration_manager=None):
        """
        Initialize AutoGen collaborative agent wrapper.
        
        Args:
            agent_id (str): Unique identifier for this agent
            autogen_agent (autogen.Agent): The AutoGen agent instance
            collaboration_manager: Optional reference to the collaboration manager
        """
        super().__init__(agent_id, collaboration_manager)
        self.autogen_agent = autogen_agent
        self.capabilities = {}
        self.implemented_steps = {}
        
        # Load agent capabilities from config
        self._load_capabilities()
    
    def _load_capabilities(self):
        """Load agent capabilities from configuration."""
        if not self.collaboration_manager:
            logger.warning(f"No collaboration manager set for {self.agent_id} - using default capabilities")
            return
        
        config = self.collaboration_manager.agent_capabilities.get(self.agent_id, {})
        self.capabilities = config
        
        # Find implemented steps across all patterns
        for pattern_name, pattern in self.collaboration_manager.collaboration_patterns.items():
            for step in pattern["steps"]:
                if step["agent"] == self.agent_id:
                    self.implemented_steps[step["name"]] = {
                        "pattern": pattern_name,
                        "description": step.get("description", ""),
                        "inputs": step.get("inputs", []),
                        "outputs": step.get("outputs", [])
                    }
    
    def can_handle_step(self, step_name: str) -> bool:
        """
        Check if this agent can handle a specific workflow step.
        
        Args:
            step_name (str): Name of the step
            
        Returns:
            bool: True if the agent can handle this step, False otherwise
        """
        return step_name in self.implemented_steps
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get the capabilities of this agent.
        
        Returns:
            Dict[str, Any]: Agent capabilities
        """
        return self.capabilities
    
    def execute_step(self, step_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific workflow step using the AutoGen agent.
        
        Args:
            step_name (str): Name of the step to execute
            inputs (Dict[str, Any]): Input data for the step
            
        Returns:
            Dict[str, Any]: Result of the step execution
        """
        if not self.can_handle_step(step_name):
            logger.error(f"Agent {self.agent_id} cannot handle step: {step_name}")
            return {
                "status": "error",
                "error": f"Step {step_name} not implemented by agent {self.agent_id}"
            }
        
        step_info = self.implemented_steps[step_name]
        logger.info(f"Executing step {step_name} with agent {self.agent_id}")
        
        try:
            # Create message for AutoGen agent
            prompt = self._create_step_prompt(step_name, step_info, inputs)
            
            # Execute using AutoGen
            response = self._execute_with_autogen(prompt, inputs)
            
            # Parse outputs
            outputs = self._parse_autogen_response(response, step_info["outputs"])
            
            return {
                "status": "success",
                "output": outputs
            }
        except Exception as e:
            logger.error(f"Error executing step {step_name}: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _create_step_prompt(self, step_name: str, step_info: Dict[str, Any], inputs: Dict[str, Any]) -> str:
        """
        Create a prompt for the AutoGen agent based on the step.
        
        Args:
            step_name (str): Name of the step to execute
            step_info (Dict[str, Any]): Information about the step
            inputs (Dict[str, Any]): Input data for the step
            
        Returns:
            str: Formatted prompt for the AutoGen agent
        """
        # Create a prompt that includes:
        # 1. Description of the task
        # 2. Required inputs and outputs
        # 3. Input data (formatted nicely)
        # 4. Instructions for formatting the response
        
        prompt = f"# {step_name.replace('_', ' ').title()}\n\n"
        prompt += f"{step_info['description']}\n\n"
        
        prompt += "## Input Data\n\n"
        for input_name, input_value in inputs.items():
            prompt += f"### {input_name}\n"
            if isinstance(input_value, dict) or isinstance(input_value, list):
                prompt += f"```json\n{json.dumps(input_value, indent=2)}\n```\n\n"
            else:
                prompt += f"{input_value}\n\n"
        
        prompt += "## Required Outputs\n\n"
        for output_name in step_info["outputs"]:
            prompt += f"- {output_name}\n"
        
        prompt += "\n## Instructions\n\n"
        prompt += "Please provide your analysis and response based on the input data. "
        prompt += "Format your output as JSON with the required output fields.\n\n"
        
        return prompt
    
    def _execute_with_autogen(self, prompt: str, context: Dict[str, Any]) -> str:
        """
        Execute a prompt with the AutoGen agent.
        
        Args:
            prompt (str): The prompt to send to the agent
            context (Dict[str, Any]): Additional context data
            
        Returns:
            str: Agent response
        """
        # This implementation depends on how your AutoGen agent is configured
        # Here's a simplified version assuming a standard conversational agent
        
        # Create a message to send to the agent
        message = {
            "content": prompt,
            "context": context,
            "role": "user"
        }
        
        # Send to AutoGen agent and collect the response
        # The exact API call depends on your AutoGen setup
        response = self.autogen_agent.generate_reply(message)
        
        if isinstance(response, dict) and "content" in response:
            return response["content"]
        return str(response)
    
    def _parse_autogen_response(self, response: str, required_outputs: List[str]) -> Dict[str, Any]:
        """
        Parse the response from the AutoGen agent to extract required outputs.
        
        Args:
            response (str): Raw response from the agent
            required_outputs (List[str]): List of required output field names
            
        Returns:
            Dict[str, Any]: Parsed outputs matching the required fields
        """
        # Try to extract JSON content from the response
        try:
            # Look for JSON blocks in the response
            json_start = response.find("```json")
            if json_start >= 0:
                json_start = response.find("\n", json_start) + 1
                json_end = response.find("```", json_start)
                if json_end >= 0:
                    json_content = response[json_start:json_end].strip()
                    outputs = json.loads(json_content)
                    return outputs
            
            # If no JSON block, try parsing the whole response
            outputs = json.loads(response)
            return outputs
        except json.JSONDecodeError:
            # If we couldn't find JSON, try to extract key-value pairs from text
            logger.warning("Could not parse JSON from response - attempting text extraction")
            outputs = {}
            
            # Add the full response as a fallback
            outputs["full_response"] = response
            
            # Try to extract simple key-value pairs
            for output_name in required_outputs:
                marker = f"{output_name}:"
                if marker in response:
                    start = response.find(marker) + len(marker)
                    end = response.find("\n", start)
                    if end < 0:
                        end = len(response)
                    value = response[start:end].strip()
                    outputs[output_name] = value
            
            return outputs


class AutoGenCollaborationManager:
    """
    Manages AutoGen agents within the collaboration framework.
    Provides factory methods for creating and configuring collaborative AutoGen agents.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize AutoGen collaboration manager.
        
        Args:
            config_path (str, optional): Path to collaboration configuration file
        """
        self.collaboration_manager = CollaborationManager(config_path)
        self.autogen_agents = {}
        self.collaborative_agents = {}
    
    def register_autogen_agent(self, 
                             agent_id: str, 
                             autogen_agent: autogen.Agent) -> AutoGenCollaborativeAgent:
        """
        Register an AutoGen agent with the collaboration system.
        
        Args:
            agent_id (str): Unique identifier for the agent
            autogen_agent (autogen.Agent): The AutoGen agent instance
            
        Returns:
            AutoGenCollaborativeAgent: The collaborative agent wrapper
        """
        # Create a collaborative agent wrapper
        collab_agent = AutoGenCollaborativeAgent(
            agent_id=agent_id,
            autogen_agent=autogen_agent,
            collaboration_manager=self.collaboration_manager
        )
        
        # Register with the collaboration manager
        self.collaboration_manager.register_agent(agent_id, collab_agent)
        
        # Store references
        self.autogen_agents[agent_id] = autogen_agent
        self.collaborative_agents[agent_id] = collab_agent
        
        return collab_agent
    
    def create_workflow(self, 
                      pattern_name: str, 
                      context_data: Dict[str, Any],
                      initiator: str) -> Optional[str]:
        """
        Create a new workflow using the specified collaboration pattern.
        
        Args:
            pattern_name (str): Name of the collaboration pattern to use
            context_data (Dict[str, Any]): Initial context data for the workflow
            initiator (str): ID of the agent initiating the workflow
            
        Returns:
            Optional[str]: Session ID if successful, None if failed
        """
        return self.collaboration_manager.create_workflow_session(
            pattern_name=pattern_name,
            context_data=context_data,
            initiator=initiator
        )
    
    def get_workflow_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a workflow session.
        
        Args:
            session_id (str): ID of the workflow session
            
        Returns:
            Optional[Dict[str, Any]]: Session status information or None if not found
        """
        return self.collaboration_manager.get_session_status(session_id)
    
    def get_agent(self, agent_id: str) -> Optional[AutoGenCollaborativeAgent]:
        """
        Get a collaborative agent by ID.
        
        Args:
            agent_id (str): Agent ID
            
        Returns:
            Optional[AutoGenCollaborativeAgent]: The collaborative agent or None if not found
        """
        return self.collaborative_agents.get(agent_id)
    
    def create_assistant_agent(self,
                             agent_id: str,
                             name: str,
                             system_message: str,
                             llm_config: Optional[Dict[str, Any]] = None) -> AutoGenCollaborativeAgent:
        """
        Create and register an AutoGen AssistantAgent.
        
        Args:
            agent_id (str): Unique identifier for the agent
            name (str): Display name for the agent
            system_message (str): System message for the agent
            llm_config (Dict[str, Any], optional): LLM configuration
            
        Returns:
            AutoGenCollaborativeAgent: The collaborative agent wrapper
        """
        # Create AutoGen assistant agent
        assistant = autogen.AssistantAgent(
            name=name,
            system_message=system_message,
            llm_config=llm_config or {}
        )
        
        # Register with collaboration system
        return self.register_autogen_agent(agent_id, assistant)
    
    def create_user_proxy_agent(self,
                              agent_id: str,
                              name: str,
                              human_input_mode: str = "NEVER",
                              system_message: Optional[str] = None) -> AutoGenCollaborativeAgent:
        """
        Create and register an AutoGen UserProxyAgent.
        
        Args:
            agent_id (str): Unique identifier for the agent
            name (str): Display name for the agent
            human_input_mode (str, optional): Human input mode (NEVER, TERMINATE, ALWAYS)
            system_message (str, optional): System message for the agent
            
        Returns:
            AutoGenCollaborativeAgent: The collaborative agent wrapper
        """
        # Create AutoGen user proxy agent
        user_proxy = autogen.UserProxyAgent(
            name=name,
            human_input_mode=human_input_mode,
            system_message=system_message
        )
        
        # Register with collaboration system
        return self.register_autogen_agent(agent_id, user_proxy)


# Example of creating an agent factory function
def create_agent_system(config_path: Optional[str] = None) -> Tuple[AutoGenCollaborationManager, Dict[str, AutoGenCollaborativeAgent]]:
    """
    Create a complete multi-agent system for mortgage processing.
    
    Args:
        config_path (str, optional): Path to collaboration configuration file
        
    Returns:
        Tuple[AutoGenCollaborationManager, Dict[str, AutoGenCollaborativeAgent]]:
            The collaboration manager and a dictionary of all created agents
    """
    # Create collaboration manager
    manager = AutoGenCollaborationManager(config_path)
    
    # LLM configuration (would be customized for your specific setup)
    llm_config = {
        "config_list": [{"model": "gpt-4", "api_key": "your-api-key"}],
        "temperature": 0.7
    }
    
    # Create orchestrator agent
    orchestrator = manager.create_assistant_agent(
        agent_id="orchestrator",
        name="Orchestrator",
        system_message="You are the orchestrator agent responsible for coordinating the mortgage application process. "
                      "You make final decisions based on inputs from specialized agents.",
        llm_config=llm_config
    )
    
    # Create document agent
    document_agent = manager.create_assistant_agent(
        agent_id="document_agent",
        name="Document Analyst",
        system_message="You analyze mortgage application documents to extract key information and verify completeness. "
                      "You identify missing documents and validate submitted information.",
        llm_config=llm_config
    )
    
    # Create underwriting agent
    underwriting_agent = manager.create_assistant_agent(
        agent_id="underwriting_agent",
        name="Underwriter",
        system_message="You evaluate mortgage applications based on financial criteria. "
                      "You assess risk and determine appropriate loan terms.",
        llm_config=llm_config
    )
    
    # Create compliance agent
    compliance_agent = manager.create_assistant_agent(
        agent_id="compliance_agent",
        name="Compliance Officer",
        system_message="You ensure mortgage applications comply with all regulatory requirements. "
                      "You identify compliance issues and suggest remediation steps.",
        llm_config=llm_config
    )
    
    # Create customer service agent
    customer_agent = manager.create_assistant_agent(
        agent_id="customer_agent",
        name="Customer Service",
        system_message="You interact with mortgage applicants to gather information and provide updates. "
                      "You explain decisions and next steps to customers.",
        llm_config=llm_config
    )
    
    # Return the manager and all created agents
    agents = {
        "orchestrator": orchestrator,
        "document_agent": document_agent,
        "underwriting_agent": underwriting_agent,
        "compliance_agent": compliance_agent,
        "customer_agent": customer_agent
    }
    
    return manager, agents