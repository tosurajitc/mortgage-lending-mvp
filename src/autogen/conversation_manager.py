"""
Conversation Manager Module
Manages multi-agent conversations and decision-making for the mortgage process.
"""

from typing import Any, Dict, List, Optional, Tuple
import json
import autogen
import asyncio

from .agent_factory import (
    create_assistant_agent,
    create_user_proxy_agent
)
from ..utils.logging_utils import get_logger
from ..workflow.decision_tracker import DecisionTracker

logger = get_logger("autogen.conversation_manager")


class ConversationManager:
    """
    Manages complex multi-agent conversations for mortgage processing tasks.
    Coordinates communication between specialized agents to reach decisions.
    """
    
    def __init__(self):
        self.logger = get_logger("conversation_manager")
        self.decision_tracker = DecisionTracker()
        self._initialize_agents()
        
    def _initialize_agents(self):
        """Initialize the core conversation agents."""
        self.logger.info("Initializing conversation agents")
        
        # Create the orchestrator agent (manages the overall conversation)
        self.orchestrator = create_assistant_agent(
            name="orchestrator",
            system_message="""
            You are the orchestrator of a mortgage application processing system.
            Your role is to coordinate conversations between specialized agents to process mortgage applications.
            You decide which agents to involve, what questions to ask them, and how to synthesize their responses.
            Keep the conversation focused and efficient, making sure all necessary information is gathered.
            """
        )
        
        # Create the specialized agents for different aspects of the mortgage process
        self.document_expert = create_assistant_agent(
            name="document_expert",
            system_message="""
            You are an expert in mortgage documentation. You analyze documents for completeness,
            accuracy, and compliance with requirements. You can identify missing documents, inconsistencies
            across documents, and potential red flags. Provide factual, precise analysis without making
            underwriting judgments.
            """
        )
        
        self.underwriting_expert = create_assistant_agent(
            name="underwriting_expert",
            system_message="""
            You are an expert in mortgage underwriting. You evaluate loan applications based on
            financial criteria, credit history, and property valuation. You provide analysis of risk factors,
            debt ratios, and creditworthiness. Make recommendations based on standard underwriting
            guidelines while considering compensating factors.
            """
        )
        
        self.compliance_expert = create_assistant_agent(
            name="compliance_expert",
            system_message="""
            You are an expert in mortgage regulatory compliance. You ensure applications meet all
            legal and regulatory requirements including fair lending, disclosure requirements, and
            anti-fraud measures. Identify compliance issues, potential violations, and required documentation
            to satisfy regulatory obligations.
            """
        )
        
        self.customer_communication_expert = create_assistant_agent(
            name="customer_communication_expert",
            system_message="""
            You are an expert in customer communication for mortgage lending. You translate complex
            mortgage concepts and decisions into clear, empathetic language for applicants. Craft responses
            that are helpful, transparent, and actionable while maintaining compliance with disclosure requirements.
            """
        )
        
        # Create a human proxy agent (represents the mortgage officer using the system)
        self.human_proxy = create_user_proxy_agent(
            name="mortgage_officer",
            human_input_mode="TERMINATE",  # Only ask for human input at the end of the conversation
            code_execution_config={"use_docker": False}  # Disable Docker for code execution
        )
        
        self.logger.info("Conversation agents initialized")
        
    async def process_complex_application(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a complex or borderline mortgage application through multi-agent deliberation.
        
        Args:
            application_data: Complete application data and document analysis
            
        Returns:
            Dict with results of multi-agent processing
        """
        self.logger.info(f"Processing complex application {application_data.get('application_id')}")
        
        # Prepare the initial prompt for the conversation
        initial_prompt = f"""
        We need to process this complex mortgage application that requires careful consideration.
        
        Application summary:
        {json.dumps(self._prepare_application_summary(application_data), indent=2)}
        
        We need to:
        1. Assess document completeness and consistency
        2. Evaluate financial ratios and credit profile
        3. Check for any compliance issues
        4. Make a final decision with clear reasoning
        5. Prepare an appropriate customer communication
        
        Let's start by having the document expert review the documentation.
        """
        
        # Set up the group chat for multi-agent deliberation
        groupchat = autogen.GroupChat(
            agents=[
                self.orchestrator,
                self.document_expert,
                self.underwriting_expert,
                self.compliance_expert,
                self.customer_communication_expert,
                self.human_proxy
            ],
            messages=[],
            max_round=15  # Limit the conversation to 15 rounds
        )
        
        manager = autogen.GroupChatManager(groupchat=groupchat)
        
        # Start the conversation
        await self.human_proxy.a_initiate_chat(
            manager,
            message=initial_prompt
        )
        
        # Extract the final decision and reasoning from the conversation
        decision, reasoning = self._extract_decision_from_conversation(groupchat.messages)
        
        # Record the decision in the tracker
        application_id = application_data.get("application_id")
        await self.decision_tracker.record_decision(
            application_id=application_id,
            decision_type="complex_application",
            decision=decision,
            factors={"reasoning": reasoning}
        )
        
        # Prepare the final result
        customer_communication = self._extract_customer_communication(groupchat.messages)
        
        return {
            "application_id": application_id,
            "decision": decision,
            "reasoning": reasoning,
            "customer_communication": customer_communication,
            "conversation_transcript": groupchat.messages
        }
    
    async def resolve_underwriting_dilemma(self, application_data: Dict[str, Any], 
                                          dilemma_description: str) -> Dict[str, Any]:
        """
        Resolve a specific underwriting dilemma through multi-agent deliberation.
        
        Args:
            application_data: Application data
            dilemma_description: Description of the underwriting dilemma
            
        Returns:
            Dict with resolution of the dilemma
        """
        self.logger.info(f"Resolving underwriting dilemma for application {application_data.get('application_id')}")
        
        # Prepare the initial prompt for the conversation
        initial_prompt = f"""
        We need to resolve an underwriting dilemma for this mortgage application.
        
        Application summary:
        {json.dumps(self._prepare_application_summary(application_data), indent=2)}
        
        Underwriting dilemma:
        {dilemma_description}
        
        We need to:
        1. Analyze this specific underwriting challenge
        2. Consider compensating factors and exceptions
        3. Consult compliance requirements
        4. Reach a justified decision
        5. Prepare appropriate customer communication
        
        Let's start by having the underwriting expert analyze this dilemma.
        """
        
        # Set up the group chat with a focus on underwriting and compliance
        groupchat = autogen.GroupChat(
            agents=[
                self.orchestrator,
                self.underwriting_expert,
                self.compliance_expert,
                self.customer_communication_expert,
                self.human_proxy
            ],
            messages=[],
            max_round=10  # Limit the conversation to 10 rounds
        )
        
        manager = autogen.GroupChatManager(groupchat=groupchat)
        
        # Start the conversation
        await self.human_proxy.a_initiate_chat(
            manager,
            message=initial_prompt
        )
        
        # Extract the resolution and reasoning from the conversation
        resolution, reasoning = self._extract_resolution_from_conversation(groupchat.messages)
        
        # Record the decision in the tracker
        application_id = application_data.get("application_id")
        await self.decision_tracker.record_decision(
            application_id=application_id,
            decision_type="dilemma_resolution",
            decision=resolution == "APPROVED",
            factors={"dilemma": dilemma_description, "reasoning": reasoning}
        )
        
        # Prepare the final result
        customer_communication = self._extract_customer_communication(groupchat.messages)
        
        return {
            "application_id": application_id,
            "resolution": resolution,
            "reasoning": reasoning,
            "customer_communication": customer_communication,
            "conversation_transcript": groupchat.messages
        }
    
    async def generate_customer_explanation(self, application_data: Dict[str, Any], 
                                           decision_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a detailed, personalized explanation for a customer.
        
        Args:
            application_data: Application data
            decision_data: Decision details to explain
            
        Returns:
            Dict with personalized explanation
        """
        self.logger.info(f"Generating customer explanation for application {application_data.get('application_id')}")
        
        # Prepare the initial prompt for the conversation
        initial_prompt = f"""
        We need to create a clear, personalized explanation of this mortgage decision for the customer.
        
        Application summary:
        {json.dumps(self._prepare_application_summary(application_data), indent=2)}
        
        Decision details:
        {json.dumps(decision_data, indent=2)}
        
        We need to:
        1. Translate technical underwriting factors into plain language
        2. Provide a clear explanation of the decision
        3. Give specific, actionable feedback
        4. Maintain regulatory compliance in our communication
        5. Be empathetic and helpful
        
        Let's start by having the customer communication expert draft an explanation.
        """
        
        # Set up the group chat with a focus on customer communication
        groupchat = autogen.GroupChat(
            agents=[
                self.orchestrator,
                self.customer_communication_expert,
                self.compliance_expert,
                self.human_proxy
            ],
            messages=[],
            max_round=5  # Limit the conversation to 5 rounds
        )
        
        manager = autogen.GroupChatManager(groupchat=groupchat)
        
        # Start the conversation
        await self.human_proxy.a_initiate_chat(
            manager,
            message=initial_prompt
        )
        
        # Extract the explanation from the conversation
        explanation = self._extract_explanation_from_conversation(groupchat.messages)
        
        return {
            "application_id": application_data.get("application_id"),
            "explanation": explanation,
            "conversation_transcript": groupchat.messages
        }
    
    def _prepare_application_summary(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare a concise summary of the application for agent conversations.
        
        Args:
            application_data: Complete application data
            
        Returns:
            Dict with summarized application data
        """
        # Extract only the key information needed for the conversation
        return {
            "application_id": application_data.get("application_id"),
            "loan_amount": application_data.get("loan_amount"),
            "loan_type": application_data.get("loan_type"),
            "property_value": application_data.get("property", {}).get("appraisal_value"),
            "credit_score": application_data.get("credit_score"),
            "income": application_data.get("income"),
            "dti_ratio": application_data.get("dti_ratio"),
            "ltv_ratio": application_data.get("ltv_ratio"),
            "document_issues": application_data.get("document_issues", []),
            "special_circumstances": application_data.get("special_circumstances", [])
        }
    
    def _extract_decision_from_conversation(self, messages: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Extract the final decision and reasoning from the conversation.
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Tuple of (decision as boolean, reasoning as string)
        """
        # Default values
        decision = False
        reasoning = "No clear decision was reached."
        
        # Look for decision messages from the orchestrator near the end of the conversation
        for message in reversed(messages):
            if message.get("sender") == "orchestrator" and "FINAL DECISION:" in message.get("content", ""):
                content = message.get("content", "")
                
                # Extract the decision
                if "APPROVED" in content or "APPROVE" in content:
                    decision = True
                
                # Extract the reasoning
                reasoning_start = content.find("REASONING:")
                if reasoning_start >= 0:
                    reasoning = content[reasoning_start + 10:].strip()
                    reasoning = reasoning.split("\n\n")[0].strip()  # Take just the first paragraph
                
                break
        
        return decision, reasoning
    
    def _extract_resolution_from_conversation(self, messages: List[Dict[str, Any]]) -> Tuple[str, str]:
        """
        Extract the dilemma resolution and reasoning from the conversation.
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Tuple of (resolution as string, reasoning as string)
        """
        # Default values
        resolution = "UNRESOLVED"
        reasoning = "No clear resolution was reached."
        
        # Look for resolution messages from the orchestrator or underwriting expert
        for message in reversed(messages):
            sender = message.get("sender")
            content = message.get("content", "")
            
            if (sender in ["orchestrator", "underwriting_expert"] and 
                ("RESOLUTION:" in content or "FINAL DECISION:" in content)):
                
                # Extract the resolution
                if "APPROVED" in content or "APPROVE" in content:
                    resolution = "APPROVED"
                elif "DENIED" in content or "DENY" in content or "REJECTED" in content:
                    resolution = "DENIED"
                elif "CONDITIONAL" in content:
                    resolution = "CONDITIONALLY_APPROVED"
                
                # Extract the reasoning
                reasoning_start = content.find("REASONING:") if "REASONING:" in content else content.find("RATIONALE:")
                if reasoning_start >= 0:
                    reasoning = content[reasoning_start + 10:].strip()
                    reasoning_end = reasoning.find("\n\n")
                    if reasoning_end >= 0:
                        reasoning = reasoning[:reasoning_end].strip()
                
                break
        
        return resolution, reasoning
    
    def _extract_customer_communication(self, messages: List[Dict[str, Any]]) -> str:
        """
        Extract the customer communication from the conversation.
        
        Args:
            messages: List of conversation messages
            
        Returns:
            String with customer communication
        """
        # Default value
        communication = "We have reviewed your application and will contact you soon with more information."
        
        # Look for customer communication messages
        for message in reversed(messages):
            if message.get("sender") == "customer_communication_expert":
                content = message.get("content", "")
                
                # Look for sections that might contain customer communication
                if "CUSTOMER COMMUNICATION:" in content:
                    comm_start = content.find("CUSTOMER COMMUNICATION:")
                    comm_content = content[comm_start + 23:].strip()
                    communication = comm_content
                    break
                elif "Dear " in content or "Hello " in content:
                    # This looks like a customer letter
                    communication = content
                    break
        
        return communication
    
    def _extract_explanation_from_conversation(self, messages: List[Dict[str, Any]]) -> str:
        """
        Extract the customer explanation from the conversation.
        
        Args:
            messages: List of conversation messages
            
        Returns:
            String with customer explanation
        """
        # Default value
        explanation = "Thank you for your application. Our decision was based on a careful review of your information."
        
        # Look for explanation messages from the customer communication expert
        for message in reversed(messages):
            if message.get("sender") == "customer_communication_expert":
                content = message.get("content", "")
                
                # This is likely the final explanation
                if ("EXPLANATION:" in content or "Dear " in content or 
                    "Hello " in content or "CUSTOMER EXPLANATION:" in content):
                    # Extract the explanation, removing any meta-instructions
                    lines = content.split("\n")
                    explanation_lines = []
                    capturing = False
                    
                    for line in lines:
                        if not capturing:
                            if "EXPLANATION:" in line or "CUSTOMER EXPLANATION:" in line:
                                capturing = True
                                continue
                            if "Dear " in line or "Hello " in line:
                                capturing = True
                        
                        if capturing:
                            explanation_lines.append(line)
                    
                    if explanation_lines:
                        explanation = "\n".join(explanation_lines)
                    else:
                        # If we couldn't parse it cleanly, just use the whole content
                        explanation = content
                    
                    break
        
        return explanation