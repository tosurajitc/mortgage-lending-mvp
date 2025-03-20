"""
Collaboration Patterns Module
Defines specialized patterns for agent collaboration in mortgage processing.
"""

from typing import Any, Dict, List, Optional, Tuple
import asyncio
import json
import autogen

from .agent_factory import (
    create_assistant_agent,
    create_user_proxy_agent
)
from .reasoning_agents import (
    get_document_reasoning_agent,
    get_underwriting_reasoning_agent,
    get_compliance_reasoning_agent,
    get_customer_service_reasoning_agent
)
from ..utils.logging_utils import get_logger

logger = get_logger("autogen.collaboration_patterns")


class ConflictResolutionPattern:
    """
    Pattern for resolving conflicts between different agents' analyses.
    Especially useful for handling conflicting information across documents.
    """
    
    def __init__(self):
        self.logger = get_logger("collaboration.conflict_resolution")
        
        # Create specialized agents
        self.conflict_mediator = create_assistant_agent(
            name="conflict_mediator",
            system_message="""
            You are an expert mediator for mortgage lending decisions. Your role is to:
            1. Identify conflicts in information or recommendations
            2. Analyze the reasoning and evidence from each source
            3. Propose resolutions based on credibility, recency, and completeness of information
            4. Make final determinations when agents cannot reach consensus
            
            You should be fair, analytical, and focused on finding the truth rather than
            compromising. When information truly conflicts, determine which source is more
            reliable or whether additional information is needed.
            """
        )
        
        self.evidence_analyst = create_assistant_agent(
            name="evidence_analyst",
            system_message="""
            You are an evidence analysis expert for mortgage lending. Your role is to:
            1. Evaluate the quality and reliability of evidence presented
            2. Identify the strength of different information sources
            3. Detect potential errors, anomalies, or inconsistencies in data
            4. Provide objective analysis of factual claims
            
            Focus on assessing the credibility of evidence rather than making decisions.
            Highlight when evidence is strong, weak, contradictory, or inconclusive.
            """
        )
        
        # Human proxy for terminating conversations
        self.human_proxy = create_user_proxy_agent(
            name="conflict_resolution_proxy",
            human_input_mode="TERMINATE"
        )
    
    async def resolve_document_conflicts(self, conflicts: Dict[str, Any], 
                                       document_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve conflicts between different documents.
        
        Args:
            conflicts: Description of conflicts between documents
            document_results: Results from document analysis
            
        Returns:
            Dict with resolution of conflicts
        """
        self.logger.info("Resolving document conflicts")
        
        # Initial message describing the conflict
        initial_message = f"""
        We need to resolve conflicts between different documents in this mortgage application.
        
        Conflicts identified:
        {json.dumps(conflicts, indent=2)}
        
        Document analysis results:
        {json.dumps(document_results, indent=2)}
        
        We need to:
        1. Identify which information is most reliable
        2. Determine if the conflicts impact the application significantly
        3. Decide what additional information might be needed
        4. Provide a clear resolution for each conflict
        
        Let's start by having the evidence analyst evaluate the quality of the information sources.
        """
        
        # Set up the group chat for conflict resolution
        groupchat = autogen.GroupChat(
            agents=[
                self.conflict_mediator,
                self.evidence_analyst,
                self.human_proxy
            ],
            messages=[],
            max_round=10
        )
        
        manager = autogen.GroupChatManager(groupchat=groupchat)
        
        # Start the conversation
        await self.human_proxy.a_initiate_chat(
            manager,
            message=initial_message
        )
        
        # Extract resolution from conversation
        resolution = self._extract_resolution(groupchat.messages)
        
        return {
            "resolved_conflicts": resolution,
            "conversation_transcript": groupchat.messages
        }
    
    async def resolve_agent_disagreement(self, underwriting_assessment: Dict[str, Any],
                                        compliance_assessment: Dict[str, Any],
                                        application_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve disagreements between underwriting and compliance agents.
        
        Args:
            underwriting_assessment: Assessment from underwriting agent
            compliance_assessment: Assessment from compliance agent
            application_data: Application data
            
        Returns:
            Dict with resolution of disagreement
        """
        self.logger.info("Resolving agent disagreement")
        
        # Initial message describing the disagreement
        initial_message = f"""
        We need to resolve a disagreement between the underwriting and compliance assessments.
        
        Underwriting assessment:
        {json.dumps(underwriting_assessment, indent=2)}
        
        Compliance assessment:
        {json.dumps(compliance_assessment, indent=2)}
        
        Application data:
        {json.dumps(application_data, indent=2)}
        
        We need to:
        1. Identify the root cause of the disagreement
        2. Determine which assessment should take precedence and why
        3. Create a balanced solution that addresses both underwriting and compliance concerns
        4. Provide clear reasoning for the final decision
        
        Let's start by having the evidence analyst evaluate the strengths of each position.
        """
        
        # Create specialized agents for this specific disagreement
        underwriting_advocate = create_assistant_agent(
            name="underwriting_advocate",
            system_message="""
            You represent the underwriting perspective in mortgage lending. Your role is to:
            1. Advocate for sound financial decision-making
            2. Highlight risk factors and mitigating circumstances
            3. Ensure lending standards are maintained
            4. Focus on the financial viability of loans
            
            Present the strongest case for the underwriting position while remaining honest
            about its limitations or weaknesses.
            """
        )
        
        compliance_advocate = create_assistant_agent(
            name="compliance_advocate",
            system_message="""
            You represent the compliance perspective in mortgage lending. Your role is to:
            1. Advocate for regulatory adherence
            2. Highlight legal requirements and potential violations
            3. Ensure fair lending practices are followed
            4. Focus on reputational and legal risks
            
            Present the strongest case for the compliance position while remaining honest
            about its limitations or weaknesses.
            """
        )
        
        # Set up the group chat for resolving disagreement
        groupchat = autogen.GroupChat(
            agents=[
                self.conflict_mediator,
                self.evidence_analyst,
                underwriting_advocate,
                compliance_advocate,
                self.human_proxy
            ],
            messages=[],
            max_round=15
        )
        
        manager = autogen.GroupChatManager(groupchat=groupchat)
        
        # Start the conversation
        await self.human_proxy.a_initiate_chat(
            manager,
            message=initial_message
        )
        
        # Extract resolution from conversation
        resolution, reasoning = self._extract_decision_with_reasoning(groupchat.messages)
        
        return {
            "resolution": resolution,
            "reasoning": reasoning,
            "conversation_transcript": groupchat.messages
        }
    
    def _extract_resolution(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract resolution from conversation messages.
        
        Args:
            messages: Conversation messages
            
        Returns:
            Dict with extracted resolution
        """
        resolution = {}
        
        # Look for resolution message from the mediator
        for message in reversed(messages):
            if message.get("sender") == "conflict_mediator" and "RESOLUTION:" in message.get("content", ""):
                content = message.get("content", "")
                
                # Try to extract JSON data
                try:
                    # Find JSON in the content
                    json_start = content.find("{")
                    json_end = content.rfind("}") + 1
                    
                    if json_start >= 0 and json_end > json_start:
                        json_str = content[json_start:json_end]
                        resolution = json.loads(json_str)
                        break
                except json.JSONDecodeError:
                    # If JSON parsing fails, extract text sections
                    resolution_start = content.find("RESOLUTION:")
                    if resolution_start >= 0:
                        resolution_text = content[resolution_start + 11:].strip()
                        resolution = {"resolution_text": resolution_text}
                        break
        
        # If no structured resolution found, create one from the last mediator message
        if not resolution:
            for message in reversed(messages):
                if message.get("sender") == "conflict_mediator":
                    resolution = {"resolution_text": message.get("content", "")}
                    break
        
        return resolution
    
    def _extract_decision_with_reasoning(self, messages: List[Dict[str, Any]]) -> Tuple[str, str]:
        """
        Extract decision and reasoning from conversation messages.
        
        Args:
            messages: Conversation messages
            
        Returns:
            Tuple of (decision, reasoning)
        """
        decision = "UNRESOLVED"
        reasoning = "No clear resolution was reached."
        
        # Look for decision message from the mediator
        for message in reversed(messages):
            if message.get("sender") == "conflict_mediator" and "FINAL DECISION:" in message.get("content", ""):
                content = message.get("content", "")
                
                # Extract decision
                decision_start = content.find("FINAL DECISION:")
                if decision_start >= 0:
                    decision_text = content[decision_start + 15:].strip()
                    decision_end = decision_text.find("\n")
                    if decision_end >= 0:
                        decision = decision_text[:decision_end].strip()
                    else:
                        decision = decision_text
                
                # Extract reasoning
                reasoning_start = content.find("REASONING:")
                if reasoning_start >= 0:
                    reasoning = content[reasoning_start + 10:].strip()
                
                break
        
        return decision, reasoning


class EscalationPattern:
    """
    Pattern for escalating complex cases to higher-level decision makers.
    Used when standard agent processing is insufficient.
    """
    
    def __init__(self):
        self.logger = get_logger("collaboration.escalation")
        
        # Create specialized agents
        self.senior_underwriter = create_assistant_agent(
            name="senior_underwriter",
            system_message="""
            You are a senior mortgage underwriting expert with 20+ years of experience.
            Your role is to handle complex or unusual loan applications that fall outside
            standard guidelines. You have authority to:
            1. Make exceptions to standard criteria with proper justification
            2. Evaluate compensating factors with nuanced judgment
            3. Assess unusual financial situations or complex income structures
            4. Make final decisions on borderline applications
            
            You should apply deep expertise while maintaining strong risk management.
            Document your reasoning thoroughly and be clear about the basis for any exceptions.
            """
        )
        
        self.risk_committee = create_assistant_agent(
            name="risk_committee",
            system_message="""
            You represent a mortgage lender's risk committee that evaluates high-risk or
            exception cases. Your role is to:
            1. Assess overall portfolio risk implications of approving exceptions
            2. Evaluate precedent-setting aspects of decisions
            3. Consider regulatory and reputation risks beyond compliance minimums
            4. Make final determinations on escalated applications
            
            You should consider both the individual case and broader implications for lending
            practices. Recognize that exceptions should be rare but justified in appropriate cases.
            """
        )
        
        # Human proxy for terminating conversations
        self.human_proxy = create_user_proxy_agent(
            name="escalation_proxy",
            human_input_mode="TERMINATE"
        )
    
    async def process_escalated_application(self, application_data: Dict[str, Any],
                                           escalation_reason: str,
                                           prior_assessments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an application that has been escalated for special handling.
        
        Args:
            application_data: Application data
            escalation_reason: Reason for escalation
            prior_assessments: Previous agent assessments
            
        Returns:
            Dict with escalation decision
        """
        self.logger.info(f"Processing escalated application: {escalation_reason}")
        
        # Initial message for escalation
        initial_message = f"""
        This mortgage application requires senior review due to exceptional circumstances.
        
        Application data:
        {json.dumps(application_data, indent=2)}
        
        Escalation reason:
        {escalation_reason}
        
        Prior assessments:
        {json.dumps(prior_assessments, indent=2)}
        
        We need to:
        1. Review the exceptional aspects of this application
        2. Determine if an exception to standard guidelines is warranted
        3. Assess the risk implications of approval
        4. Make a final determination with clear conditions if approved
        
        Let's start with the senior underwriter's assessment of this case.
        """
        
        # Set up the group chat for escalation
        groupchat = autogen.GroupChat(
            agents=[
                self.senior_underwriter,
                self.risk_committee,
                self.human_proxy
            ],
            messages=[],
            max_round=10
        )
        
        manager = autogen.GroupChatManager(groupchat=groupchat)
        
        # Start the conversation
        await self.human_proxy.a_initiate_chat(
            manager,
            message=initial_message
        )
        
        # Extract decision and conditions from conversation
        decision, conditions = self._extract_escalation_decision(groupchat.messages)
        
        return {
            "decision": decision,
            "conditions": conditions,
            "escalation_reason": escalation_reason,
            "conversation_transcript": groupchat.messages
        }
    
    def _extract_escalation_decision(self, messages: List[Dict[str, Any]]) -> Tuple[str, List[str]]:
        """
        Extract escalation decision and conditions from conversation messages.
        
        Args:
            messages: Conversation messages
            
        Returns:
            Tuple of (decision, conditions list)
        """
        decision = "PENDING"
        conditions = []
        
        # Look for final decision message from the risk committee
        for message in reversed(messages):
            if message.get("sender") == "risk_committee" and "FINAL DECISION:" in message.get("content", ""):
                content = message.get("content", "")
                
                # Extract decision
                if "APPROVED" in content or "APPROVE" in content:
                    decision = "APPROVED"
                elif "DENIED" in content or "REJECT" in content:
                    decision = "REJECTED"
                elif "CONDITIONAL" in content:
                    decision = "CONDITIONALLY_APPROVED"
                
                # Extract conditions
                conditions_start = content.find("CONDITIONS:")
                if conditions_start >= 0:
                    conditions_text = content[conditions_start + 11:].strip()
                    conditions_list = conditions_text.split("\n")
                    # Clean up conditions list
                    conditions = [cond.strip().lstrip("- ") for cond in conditions_list if cond.strip()]
                
                break
        
        return decision, conditions


class AppealReviewPattern:
    """
    Pattern for handling appeals or reconsideration requests.
    Used when applicants dispute initial decisions.
    """
    
    def __init__(self):
        self.logger = get_logger("collaboration.appeal_review")
        
        # Create specialized agents
        self.appeals_manager = create_assistant_agent(
            name="appeals_manager",
            system_message="""
            You are an appeals manager for mortgage lending decisions. Your role is to:
            1. Review appeals of rejected mortgage applications fairly
            2. Evaluate new information or circumstances presented
            3. Determine if the original decision should be reconsidered
            4. Provide clear reasoning for appeal decisions
            
            You should be objective and thorough in reviewing appeals. Look for meaningful
            changes or information that would materially affect the original decision,
            while maintaining appropriate lending standards.
            """
        )
        
        self.original_decision_reviewer = create_assistant_agent(
            name="original_decision_reviewer",
            system_message="""
            You review original mortgage rejection decisions during appeals. Your role is to:
            1. Verify the original rejection was based on sound reasoning
            2. Identify any errors or oversights in the original assessment
            3. Determine if criteria were applied correctly
            4. Evaluate if the rejection factors still apply given new information
            
            You should be thorough and critical in reviewing the original decision process.
            Your goal is to ensure the decision was appropriate based on information available
            at the time and to identify any legitimate grounds for reconsideration.
            """
        )
        
        # Human proxy for terminating conversations
        self.human_proxy = create_user_proxy_agent(
            name="appeal_proxy",
            human_input_mode="TERMINATE"
        )
    
    async def review_appeal(self, application_data: Dict[str, Any],
                          original_decision: Dict[str, Any],
                          appeal_reason: str,
                          new_information: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review an appeal of a rejected application.
        
        Args:
            application_data: Original application data
            original_decision: Original rejection decision
            appeal_reason: Reason for the appeal
            new_information: New information provided in the appeal
            
        Returns:
            Dict with appeal decision
        """
        self.logger.info(f"Reviewing appeal: {appeal_reason}")
        
        # Initial message for appeal review
        initial_message = f"""
        We need to review an appeal of a rejected mortgage application.
        
        Original application data:
        {json.dumps(application_data, indent=2)}
        
        Original rejection decision:
        {json.dumps(original_decision, indent=2)}
        
        Appeal reason:
        {appeal_reason}
        
        New information provided:
        {json.dumps(new_information, indent=2)}
        
        We need to:
        1. Review the original decision and its rationale
        2. Evaluate the new information provided
        3. Determine if the appeal presents sufficient grounds for reconsideration
        4. Make a fair and objective decision on the appeal
        
        Let's start with a review of the original decision.
        """
        
        # Set up the group chat for appeal review
        groupchat = autogen.GroupChat(
            agents=[
                self.appeals_manager,
                self.original_decision_reviewer,
                self.human_proxy
            ],
            messages=[],
            max_round=10
        )
        
        manager = autogen.GroupChatManager(groupchat=groupchat)
        
        # Start the conversation
        await self.human_proxy.a_initiate_chat(
            manager,
            message=initial_message
        )
        
        # Extract appeal decision from conversation
        decision, reasoning = self._extract_appeal_decision(groupchat.messages)
        
        return {
            "appeal_decision": decision,
            "reasoning": reasoning,
            "conversation_transcript": groupchat.messages
        }
    
    def _extract_appeal_decision(self, messages: List[Dict[str, Any]]) -> Tuple[str, str]:
        """
        Extract appeal decision and reasoning from conversation messages.
        
        Args:
            messages: Conversation messages
            
        Returns:
            Tuple of (decision, reasoning)
        """
        decision = "APPEAL_PENDING"
        reasoning = "Appeal review in progress."
        
        # Look for final decision message from the appeals manager
        for message in reversed(messages):
            if message.get("sender") == "appeals_manager" and "APPEAL DECISION:" in message.get("content", ""):
                content = message.get("content", "")
                
                # Extract decision
                if "GRANTED" in content or "APPROVE" in content:
                    decision = "APPEAL_GRANTED"
                elif "DENIED" in content or "REJECT" in content:
                    decision = "APPEAL_DENIED"
                elif "PARTIAL" in content:
                    decision = "APPEAL_PARTIALLY_GRANTED"
                
                # Extract reasoning
                reasoning_start = content.find("REASONING:")
                if reasoning_start >= 0:
                    reasoning = content[reasoning_start + 10:].strip()
                
                break
        
        return decision, reasoning


# Factory functions to get collaboration pattern instances

def get_conflict_resolution_pattern() -> ConflictResolutionPattern:
    """Get a conflict resolution pattern instance."""
    return ConflictResolutionPattern()

def get_escalation_pattern() -> EscalationPattern:
    """Get an escalation pattern instance."""
    return EscalationPattern()

def get_appeal_review_pattern() -> AppealReviewPattern:
    """Get an appeal review pattern instance."""
    return AppealReviewPattern()