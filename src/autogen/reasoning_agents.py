

import logging
import json
from typing import Dict, List, Any, Optional, Tuple, Union
import src.autogen
from src.autogen.collaboration.agent import BaseCollaborativeAgent

logger = logging.getLogger(__name__)

class ReasoningCapability:
    """Constants for different reasoning capabilities."""
    DOCUMENT_ANALYSIS = "document_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    COMPLIANCE_VERIFICATION = "compliance_verification"
    DECISION_JUSTIFICATION = "decision_justification"
    EXCEPTION_HANDLING = "exception_handling"
    INCONSISTENCY_RESOLUTION = "inconsistency_resolution"
    CUSTOMER_EXPLANATION = "customer_explanation"



class ReasoningAgent(BaseCollaborativeAgent):
    """
    Base class for specialized reasoning agents that provide enhanced
    analytical capabilities for complex mortgage processing scenarios.
    """
    
    def __init__(self, 
                agent_id: str, 
                autogen_agent: src.autogen.collaboration.agent, 
                collaboration_manager=None,
                capabilities: List[str] = None):
        """
        Initialize a reasoning agent.
        
        Args:
            agent_id (str): Unique identifier for this agent
            autogen_agent (autogen.Agent): The AutoGen agent instance
            collaboration_manager: Optional reference to the collaboration manager
            capabilities (List[str], optional): List of reasoning capabilities
        """
        super().__init__(agent_id, collaboration_manager)
        self.autogen_agent = autogen_agent
        self.reasoning_capabilities = capabilities or []
        self.reasoning_history = []
    
    def has_capability(self, capability: str) -> bool:
        """
        Check if this agent has a specific reasoning capability.
        
        Args:
            capability (str): The capability to check
            
        Returns:
            bool: True if the agent has the capability
        """
        return capability in self.reasoning_capabilities
    
    def execute_reasoning(self, 
                        reasoning_type: str, 
                        inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a reasoning task.
        
        Args:
            reasoning_type (str): Type of reasoning task
            inputs (Dict[str, Any]): Input data for reasoning
            
        Returns:
            Dict[str, Any]: Reasoning results
        """
        if not self.has_capability(reasoning_type):
            logger.error(f"Agent {self.agent_id} does not have capability: {reasoning_type}")
            return {
                "status": "error",
                "error": f"Capability not supported: {reasoning_type}"
            }
        
        try:
            # Create prompt for the reasoning task
            prompt = self._create_reasoning_prompt(reasoning_type, inputs)
            
            # Send to AutoGen agent
            response = self._execute_with_autogen(prompt, inputs)
            
            # Parse response
            result = self._parse_reasoning_response(response, reasoning_type)
            
            # Record in history
            self._record_reasoning(reasoning_type, inputs, result)
            
            return {
                "status": "success",
                "reasoning_type": reasoning_type,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error in reasoning task {reasoning_type}: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _create_reasoning_prompt(self, reasoning_type: str, inputs: Dict[str, Any]) -> str:
        """
        Create a prompt for the specific reasoning task.
        
        Args:
            reasoning_type (str): Type of reasoning task
            inputs (Dict[str, Any]): Input data for reasoning
            
        Returns:
            str: Formatted prompt
        """
        # Base prompt structure
        prompt = f"# {reasoning_type.replace('_', ' ').title()} Task\n\n"
        
        if reasoning_type == ReasoningCapability.DOCUMENT_ANALYSIS:
            prompt += self._create_document_analysis_prompt(inputs)
        elif reasoning_type == ReasoningCapability.RISK_ASSESSMENT:
            prompt += self._create_risk_assessment_prompt(inputs)
        elif reasoning_type == ReasoningCapability.COMPLIANCE_VERIFICATION:
            prompt += self._create_compliance_verification_prompt(inputs)
        elif reasoning_type == ReasoningCapability.DECISION_JUSTIFICATION:
            prompt += self._create_decision_justification_prompt(inputs)
        elif reasoning_type == ReasoningCapability.INCONSISTENCY_RESOLUTION:
            prompt += self._create_inconsistency_resolution_prompt(inputs)
        elif reasoning_type == ReasoningCapability.CUSTOMER_EXPLANATION:
            prompt += self._create_customer_explanation_prompt(inputs)
        else:
            # Generic reasoning prompt
            prompt += "Please analyze the following information and provide your reasoning:\n\n"
            for key, value in inputs.items():
                prompt += f"## {key}\n"
                if isinstance(value, dict) or isinstance(value, list):
                    prompt += f"```json\n{json.dumps(value, indent=2)}\n```\n\n"
                else:
                    prompt += f"{value}\n\n"
        
        prompt += "\n## Instructions\n\n"
        prompt += "Please provide a detailed analysis with clear reasoning steps. "
        prompt += "Structure your response with headings for key points and include a summary of your conclusions.\n\n"
        prompt += "Format your final reasoning output as JSON following this structure:\n"
        prompt += "```json\n"
        prompt += "{\n"
        prompt += '  "conclusion": "Your main conclusion",\n'
        prompt += '  "confidence": 0.95,  // A value between 0 and 1\n'
        prompt += '  "key_points": ["Point 1", "Point 2", ...],\n'
        prompt += '  "justification": "Explanation of your reasoning process"\n'
        prompt += "}\n"
        prompt += "```\n"
        
        return prompt
    
    def _create_document_analysis_prompt(self, inputs: Dict[str, Any]) -> str:
        """Create document analysis prompt."""
        prompt = "Please perform a detailed analysis of the following document:\n\n"
        
        if "document_content" in inputs:
            prompt += f"## Document Content\n{inputs['document_content']}\n\n"
        
        if "document_type" in inputs:
            prompt += f"## Document Type\n{inputs['document_type']}\n\n"
        
        prompt += "Please analyze this document to:\n"
        prompt += "1. Extract all relevant information for mortgage processing\n"
        prompt += "2. Identify any inconsistencies or missing information\n"
        prompt += "3. Verify the accuracy and completeness of the information\n"
        prompt += "4. Assess the reliability of the document\n\n"
        
        return prompt
    
    def _create_risk_assessment_prompt(self, inputs: Dict[str, Any]) -> str:
        """Create risk assessment prompt."""
        prompt = "Please assess the risk factors for this mortgage application:\n\n"
        
        if "financial_data" in inputs:
            prompt += f"## Financial Data\n```json\n{json.dumps(inputs['financial_data'], indent=2)}\n```\n\n"
        
        if "credit_history" in inputs:
            prompt += f"## Credit History\n```json\n{json.dumps(inputs['credit_history'], indent=2)}\n```\n\n"
        
        if "property_details" in inputs:
            prompt += f"## Property Details\n```json\n{json.dumps(inputs['property_details'], indent=2)}\n```\n\n"
        
        prompt += "Please assess the following risk factors:\n"
        prompt += "1. Credit risk: Evaluate the applicant's creditworthiness\n"
        prompt += "2. Income stability: Assess the reliability of income sources\n"
        prompt += "3. Debt-to-income ratio: Calculate and evaluate DTI\n"
        prompt += "4. Property valuation: Assess if the property value supports the loan amount\n"
        prompt += "5. Market conditions: Consider current market trends for this property type\n\n"
        
        return prompt
    
    def _create_compliance_verification_prompt(self, inputs: Dict[str, Any]) -> str:
        """Create compliance verification prompt."""
        prompt = "Please verify compliance with mortgage lending regulations:\n\n"
        
        if "application_data" in inputs:
            prompt += f"## Application Data\n```json\n{json.dumps(inputs['application_data'], indent=2)}\n```\n\n"
        
        if "regulations" in inputs:
            prompt += f"## Applicable Regulations\n```json\n{json.dumps(inputs['regulations'], indent=2)}\n```\n\n"
        
        prompt += "Please verify compliance with:\n"
        prompt += "1. Fair lending requirements\n"
        prompt += "2. Disclosure requirements\n"
        prompt += "3. Documentation standards\n"
        prompt += "4. Underwriting criteria consistency\n"
        prompt += "5. Regulatory reporting requirements\n\n"
        
        return prompt
    
    def _create_decision_justification_prompt(self, inputs: Dict[str, Any]) -> str:
        """Create decision justification prompt."""
        prompt = "Please provide a justification for the following mortgage decision:\n\n"
        
        if "decision" in inputs:
            prompt += f"## Decision\n{inputs['decision']}\n\n"
        
        if "application_summary" in inputs:
            prompt += f"## Application Summary\n```json\n{json.dumps(inputs['application_summary'], indent=2)}\n```\n\n"
        
        if "decision_factors" in inputs:
            prompt += f"## Decision Factors\n```json\n{json.dumps(inputs['decision_factors'], indent=2)}\n```\n\n"
        
        prompt += "Please create a clear justification that:\n"
        prompt += "1. Explains the key factors that influenced the decision\n"
        prompt += "2. Provides a logical rationale for the decision\n"
        prompt += "3. Addresses potential counterarguments\n"
        prompt += "4. Ensures the decision is transparent and defensible\n"
        prompt += "5. Uses clear, non-technical language when possible\n\n"
        
        return prompt
    
    def _create_inconsistency_resolution_prompt(self, inputs: Dict[str, Any]) -> str:
        """Create inconsistency resolution prompt."""
        prompt = "Please resolve the following inconsistencies in the mortgage application data:\n\n"
        
        if "inconsistencies" in inputs:
            prompt += f"## Identified Inconsistencies\n```json\n{json.dumps(inputs['inconsistencies'], indent=2)}\n```\n\n"
        
        if "document_sources" in inputs:
            prompt += f"## Document Sources\n```json\n{json.dumps(inputs['document_sources'], indent=2)}\n```\n\n"
        
        prompt += "Please resolve these inconsistencies by:\n"
        prompt += "1. Analyzing the reliability of each data source\n"
        prompt += "2. Determining the most likely correct information\n"
        prompt += "3. Explaining your reasoning for each resolution\n"
        prompt += "4. Recommending any additional verification needed\n"
        prompt += "5. Indicating confidence level for each resolution\n\n"
        
        return prompt
    
    def _create_customer_explanation_prompt(self, inputs: Dict[str, Any]) -> str:
        """Create customer explanation prompt."""
        prompt = "Please create a customer-friendly explanation of the following mortgage information:\n\n"
        
        if "technical_details" in inputs:
            prompt += f"## Technical Details\n```json\n{json.dumps(inputs['technical_details'], indent=2)}\n```\n\n"
        
        if "customer_profile" in inputs:
            prompt += f"## Customer Profile\n```json\n{json.dumps(inputs['customer_profile'], indent=2)}\n```\n\n"
        
        prompt += "Please create an explanation that:\n"
        prompt += "1. Translates technical mortgage terms into plain language\n"
        prompt += "2. Explains key concepts clearly and concisely\n"
        prompt += "3. Is appropriate for the customer's financial literacy level\n"
        prompt += "4. Addresses likely customer questions and concerns\n"
        prompt += "5. Provides actionable next steps if applicable\n\n"
        
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
        # Create a message to send to the agent
        message = {
            "content": prompt,
            "context": context,
            "role": "user"
        }
        
        # Send to AutoGen agent and collect the response
        response = self.autogen_agent.generate_reply(message)
        
        if isinstance(response, dict) and "content" in response:
            return response["content"]
        return str(response)
    
    def _parse_reasoning_response(self, response: str, reasoning_type: str) -> Dict[str, Any]:
        """
        Parse the response from the AutoGen agent.
        
        Args:
            response (str): Raw response from the agent
            reasoning_type (str): Type of reasoning task
            
        Returns:
            Dict[str, Any]: Parsed reasoning results
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
                    result = json.loads(json_content)
                    return result
            
            # If no JSON block, try parsing the whole response
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            # If we couldn't find JSON, extract key information from text
            logger.warning(f"Could not parse JSON from {reasoning_type} response - using text extraction")
            
            # Create a structured result with the full text
            result = {
                "conclusion": "See full analysis",
                "confidence": 0.5,  # Default moderate confidence
                "key_points": [],
                "justification": response,
                "full_response": response
            }
            
            # Try to extract conclusion
            if "conclusion" in response.lower():
                pos = response.lower().find("conclusion")
                end = response.find("\n\n", pos)
                if end > pos:
                    conclusion = response[pos:end].strip()
                    # Remove "Conclusion:" prefix if present
                    if ":" in conclusion:
                        conclusion = conclusion.split(":", 1)[1].strip()
                    result["conclusion"] = conclusion
            
            # Try to extract key points
            key_points = []
            if "key point" in response.lower() or "important point" in response.lower():
                lines = response.split("\n")
                for line in lines:
                    if line.strip().startswith("- ") or line.strip().startswith("* "):
                        key_points.append(line.strip()[2:])
            
            if key_points:
                result["key_points"] = key_points
            
            return result
    
    def _record_reasoning(self, 
                        reasoning_type: str, 
                        inputs: Dict[str, Any], 
                        result: Dict[str, Any]) -> None:
        """
        Record a reasoning task in history.
        
        Args:
            reasoning_type (str): Type of reasoning task
            inputs (Dict[str, Any]): Input data for reasoning
            result (Dict[str, Any]): Reasoning results
        """
        entry = {
            "timestamp": logging.Formatter.formatTime(logging.Formatter(), logging.LogRecord("", 0, "", 0, None, None, None, None)),
            "reasoning_type": reasoning_type,
            "inputs": inputs,
            "result": result
        }
        
        self.reasoning_history.append(entry)
        
        # Keep history at a reasonable size
        if len(self.reasoning_history) > 100:
            self.reasoning_history.pop(0)
    
    def execute_step(self, step_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow step using reasoning capabilities.
        
        Args:
            step_name (str): Name of the step to execute
            inputs (Dict[str, Any]): Input data for the step
            
        Returns:
            Dict[str, Any]: Step execution results
        """
        logger.info(f"Reasoning agent {self.agent_id} executing step: {step_name}")
        
        # Map step names to reasoning capabilities
        reasoning_mapping = {
            "analyze_document": ReasoningCapability.DOCUMENT_ANALYSIS,
            "assess_risk": ReasoningCapability.RISK_ASSESSMENT,
            "verify_compliance": ReasoningCapability.COMPLIANCE_VERIFICATION,
            "justify_decision": ReasoningCapability.DECISION_JUSTIFICATION,
            "resolve_inconsistencies": ReasoningCapability.INCONSISTENCY_RESOLUTION,
            "explain_to_customer": ReasoningCapability.CUSTOMER_EXPLANATION
        }
        
        # If step has a direct reasoning capability mapping
        if step_name in reasoning_mapping:
            reasoning_type = reasoning_mapping[step_name]
            if self.has_capability(reasoning_type):
                result = self.execute_reasoning(reasoning_type, inputs)
                
                if result["status"] == "success":
                    return {
                        "status": "success",
                        "output": result["result"]
                    }
                else:
                    return {
                        "status": "error",
                        "error": result.get("error", "Unknown reasoning error")
                    }
        
        # For steps without direct mapping, use default implementation
        return super().execute_step(step_name, inputs)


class DocumentReasoningAgent(ReasoningAgent):
    """
    Specialized reasoning agent for document analysis and verification.
    """
    
    def __init__(self, agent_id: str, autogen_agent: src.autogen.collaboration.agent, collaboration_manager=None):
        """Initialize document reasoning agent."""
        capabilities = [
            ReasoningCapability.DOCUMENT_ANALYSIS,
            ReasoningCapability.INCONSISTENCY_RESOLUTION
        ]
        super().__init__(agent_id, autogen_agent, collaboration_manager, capabilities)
    
    def can_handle_step(self, step_name: str) -> bool:
        """Check if this agent can handle a specific step."""
        document_steps = [
            "analyze_document",
            "extract_document_data",
            "verify_document_authenticity",
            "resolve_document_inconsistencies",
            "identify_missing_documents"
        ]
        return step_name in document_steps


class UnderwritingReasoningAgent(ReasoningAgent):
    """
    Specialized reasoning agent for underwriting and risk assessment.
    """
    
    def __init__(self, agent_id: str, autogen_agent: src.autogen.collaboration.agent, collaboration_manager=None):
        """Initialize underwriting reasoning agent."""
        capabilities = [
            ReasoningCapability.RISK_ASSESSMENT,
            ReasoningCapability.DECISION_JUSTIFICATION
        ]
        super().__init__(agent_id, autogen_agent, collaboration_manager, capabilities)
    
    def can_handle_step(self, step_name: str) -> bool:
        """Check if this agent can handle a specific step."""
        underwriting_steps = [
            "assess_risk",
            "evaluate_creditworthiness",
            "determine_loan_terms",
            "justify_underwriting_decision",
            "analyze_financial_data"
        ]
        return step_name in underwriting_steps


class ComplianceReasoningAgent(ReasoningAgent):
    """
    Specialized reasoning agent for regulatory compliance verification.
    """
    
    def __init__(self, agent_id: str, autogen_agent: src.autogen.collaboration.agent, collaboration_manager=None):
        """Initialize compliance reasoning agent."""
        capabilities = [
            ReasoningCapability.COMPLIANCE_VERIFICATION,
            ReasoningCapability.DECISION_JUSTIFICATION
        ]
        super().__init__(agent_id, autogen_agent, collaboration_manager, capabilities)
    
    def can_handle_step(self, step_name: str) -> bool:
        """Check if this agent can handle a specific step."""
        compliance_steps = [
            "verify_compliance",
            "check_regulatory_requirements",
            "validate_disclosures",
            "assess_legal_risks",
            "verify_application_completeness"
        ]
        return step_name in compliance_steps


class CustomerExplanationAgent(ReasoningAgent):
    """
    Specialized reasoning agent for creating customer-friendly explanations.
    """
    
    def __init__(self, agent_id: str, autogen_agent: src.autogen.collaboration.agent, collaboration_manager=None):
        """Initialize customer explanation agent."""
        capabilities = [
            ReasoningCapability.CUSTOMER_EXPLANATION
        ]
        super().__init__(agent_id, autogen_agent, collaboration_manager, capabilities)
    
    def can_handle_step(self, step_name: str) -> bool:
        """Check if this agent can handle a specific step."""
        explanation_steps = [
            "explain_to_customer",
            "create_customer_notification",
            "simplify_technical_details",
            "generate_customer_letter",
            "prepare_application_summary"
        ]
        return step_name in explanation_steps


# Factory function to create reasoning agents
def create_reasoning_agents(collaboration_manager=None, llm_config=None) -> Dict[str, ReasoningAgent]:
    """
    Create a set of specialized reasoning agents.
    
    Args:
        collaboration_manager: Optional reference to the collaboration manager
        llm_config (Dict[str, Any], optional): LLM configuration for agents
        
    Returns:
        Dict[str, ReasoningAgent]: Dictionary of reasoning agents
    """
    # Default LLM config if not provided
    if llm_config is None:
        llm_config = {
            "config_list": [{"model": "gpt-4"}],
            "temperature": 0.2  # Lower temperature for more reliable reasoning
        }
    
    # Create AutoGen agents
    document_analysis_agent = autogen.AssistantAgent(
        name="DocumentAnalysisAssistant",
        system_message="You are a specialist in analyzing mortgage documents. You excel at extracting information, identifying inconsistencies, and verifying document authenticity.",
        llm_config=llm_config
    )
    
    underwriting_agent = autogen.AssistantAgent(
        name="UnderwritingAssistant",
        system_message="You are a mortgage underwriting specialist. You excel at risk assessment, evaluating creditworthiness, and determining appropriate loan terms.",
        llm_config=llm_config
    )
    
    compliance_agent = autogen.AssistantAgent(
        name="ComplianceAssistant",
        system_message="You are a mortgage compliance expert. You excel at verifying regulatory compliance, validating disclosures, and assessing legal risks.",
        llm_config=llm_config
    )
    
    customer_agent = autogen.AssistantAgent(
        name="CustomerExplanationAssistant",
        system_message="You are a mortgage communication specialist. You excel at translating technical mortgage concepts into clear, customer-friendly language.",
        llm_config=llm_config
    )
    
    # Create reasoning agents
    reasoning_agents = {
        "document_reasoning": DocumentReasoningAgent(
            agent_id="document_reasoning",
            autogen_agent=document_analysis_agent,
            collaboration_manager=collaboration_manager
        ),
        "underwriting_reasoning": UnderwritingReasoningAgent(
            agent_id="underwriting_reasoning",
            autogen_agent=underwriting_agent,
            collaboration_manager=collaboration_manager
        ),
        "compliance_reasoning": ComplianceReasoningAgent(
            agent_id="compliance_reasoning",
            autogen_agent=compliance_agent,
            collaboration_manager=collaboration_manager
        ),
        "customer_explanation": CustomerExplanationAgent(
            agent_id="customer_explanation",
            autogen_agent=customer_agent,
            collaboration_manager=collaboration_manager
        )
    }
    
    return reasoning_agents

def get_compliance_reasoning_agent(collaboration_manager=None, llm_config=None):
    """
    Create a compliance reasoning agent.
    
    Args:
        collaboration_manager: Optional reference to the collaboration manager
        llm_config (Dict[str, Any], optional): LLM configuration for the agent
        
    Returns:
        ComplianceReasoningAgent: The compliance reasoning agent
    """
    agents = create_reasoning_agents(collaboration_manager, llm_config)
    return agents["compliance_reasoning"]


def get_customer_service_reasoning_agent(collaboration_manager=None, llm_config=None):
    """
    Create a customer service reasoning agent.
    
    Args:
        collaboration_manager: Optional reference to the collaboration manager
        llm_config (Dict[str, Any], optional): LLM configuration for the agent
        
    Returns:
        CustomerExplanationAgent: The customer service reasoning agent
    """
    agents = create_reasoning_agents(collaboration_manager, llm_config)
    return agents["customer_explanation"]

def get_document_reasoning_agent(collaboration_manager=None, llm_config=None):
    """
    Create a document reasoning agent.
    
    Args:
        collaboration_manager: Optional reference to the collaboration manager
        llm_config (Dict[str, Any], optional): LLM configuration for the agent
        
    Returns:
        DocumentReasoningAgent: The document reasoning agent
    """
    agents = create_reasoning_agents(collaboration_manager, llm_config)
    return agents["document_reasoning"]

def get_underwriting_reasoning_agent(collaboration_manager=None, llm_config=None):
    """
    Create an underwriting reasoning agent.
    
    Args:
        collaboration_manager: Optional reference to the collaboration manager
        llm_config (Dict[str, Any], optional): LLM configuration for the agent
        
    Returns:
        UnderwritingReasoningAgent: The underwriting reasoning agent
    """
    agents = create_reasoning_agents(collaboration_manager, llm_config)
    return agents["underwriting_reasoning"]