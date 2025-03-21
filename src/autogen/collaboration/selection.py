"""
Dynamic Agent Selector Module, this is not an agent but colaborates between Agents and
Intelligently selects and configures agents based on application characteristics.
"""

from typing import Any, Dict, List, Optional, Set
import json
import autogen

from agent_factory import (
    create_assistant_agent,
    create_user_proxy_agent
)
from utils.logging_utils import get_logger
from data.models import LoanType, PropertyType, ApplicationState

logger = get_logger("autogen.dynamic_agent_selector")


class DynamicAgentSelector:
    """
    Selects specialized agents based on the characteristics of a mortgage application.
    Customizes agent groups for different task types and application features.
    """
    
    def __init__(self):
        self.logger = get_logger("dynamic_agent_selector")
        
        # Core agent registry - holds all available specialized agents
        self.agent_registry = {}
        
        # Initialize the registry with specialized agents
        self._initialize_agent_registry()
    
    def _initialize_agent_registry(self) -> None:
        """Initialize the agent registry with all available specialized agents."""
        self.logger.info("Initializing agent registry")
        
        # Document analysis specialists
        self.agent_registry["income_verification_specialist"] = create_assistant_agent(
            name="income_verification_specialist",
            system_message="""
            You are a specialist in income verification documents for mortgage lending.
            You have deep expertise in analyzing W-2s, pay stubs, tax returns, 1099 forms,
            and other income-related documents. You can detect inconsistencies, identify
            income stability patterns, and verify employment history accuracy.
            """
        )
        
        self.agent_registry["self_employment_specialist"] = create_assistant_agent(
            name="self_employment_specialist",
            system_message="""
            You are a specialist in evaluating self-employed income for mortgage lending.
            You have expertise in analyzing business tax returns, profit and loss statements,
            business bank statements, and other self-employment documentation. You understand
            business cash flow patterns, tax write-offs, and sustainable income determination.
            """
        )
        
        self.agent_registry["property_valuation_specialist"] = create_assistant_agent(
            name="property_valuation_specialist",
            system_message="""
            You are a specialist in property valuation for mortgage lending. You have
            expertise in analyzing appraisal reports, comparable sales, property condition
            assessments, and market trends. You can identify valuation inconsistencies,
            property condition issues, and market risk factors.
            """
        )
        
        # Underwriting specialists
        self.agent_registry["conventional_loan_specialist"] = create_assistant_agent(
            name="conventional_loan_specialist",
            system_message="""
            You are a specialist in conventional mortgage loans. You have expertise in
            Fannie Mae and Freddie Mac guidelines, conforming loan requirements, and
            standard underwriting criteria. You understand debt-to-income ratios, credit
            score requirements, and property eligibility for conventional financing.
            """
        )
        
        self.agent_registry["fha_loan_specialist"] = create_assistant_agent(
            name="fha_loan_specialist",
            system_message="""
            You are a specialist in FHA mortgage loans. You have expertise in FHA guidelines,
            including minimum property standards, MIP calculations, debt ratio limits, and
            credit requirements. You understand FHA's more flexible qualification criteria
            and special considerations for first-time homebuyers.
            """
        )
        
        self.agent_registry["va_loan_specialist"] = create_assistant_agent(
            name="va_loan_specialist",
            system_message="""
            You are a specialist in VA mortgage loans. You have expertise in VA guidelines,
            including eligibility requirements, funding fee calculations, debt ratio analysis,
            and residual income requirements. You understand VA's unique approach to qualifying
            veterans and service members.
            """
        )
        
        self.agent_registry["jumbo_loan_specialist"] = create_assistant_agent(
            name="jumbo_loan_specialist",
            system_message="""
            You are a specialist in jumbo mortgage loans. You have expertise in non-conforming
            loan guidelines, high-value property assessment, complex income analysis, and
            higher credit quality standards. You understand the additional scrutiny required
            for loans above conforming limits.
            """
        )
        
        # Compliance specialists
        self.agent_registry["fair_lending_specialist"] = create_assistant_agent(
            name="fair_lending_specialist",
            system_message="""
            You are a specialist in fair lending compliance. You have expertise in Equal
            Credit Opportunity Act, Fair Housing Act, and other fair lending regulations.
            You can identify potential disparate treatment or impact issues, ensure consistent
            application of criteria, and maintain non-discriminatory practices.
            """
        )
        
        self.agent_registry["regulatory_compliance_specialist"] = create_assistant_agent(
            name="regulatory_compliance_specialist",
            system_message="""
            You are a specialist in mortgage regulatory compliance. You have expertise in
            TILA-RESPA Integrated Disclosure rules, QM/ATR requirements, HMDA reporting,
            and other federal and state regulations. You ensure all aspects of the mortgage
            process meet current regulatory standards.
            """
        )
        
        # Customer service specialists
        self.agent_registry["first_time_homebuyer_specialist"] = create_assistant_agent(
            name="first_time_homebuyer_specialist",
            system_message="""
            You are a specialist in assisting first-time homebuyers. You have expertise in
            explaining the mortgage process in simple terms, managing expectations, providing
            educational resources, and addressing common concerns of new homebuyers. You are
            patient, thorough, and encouraging in your communication.
            """
        )
        
        self.agent_registry["adverse_action_specialist"] = create_assistant_agent(
            name="adverse_action_specialist",
            system_message="""
            You are a specialist in explaining adverse actions on mortgage applications.
            You have expertise in communicating rejection reasons clearly and constructively,
            providing guidance on improving future applications, and ensuring regulatory
            compliance in adverse action notices. You are empathetic while remaining clear
            about decision factors.
            """
        )
        
        # Create human proxy for terminating conversations
        self.agent_registry["human_proxy"] = create_user_proxy_agent(
            name="human_proxy",
            human_input_mode="TERMINATE"
        )
    
    def select_document_analysis_team(self, application_data: Dict[str, Any]) -> List[autogen.Agent]:
        """
        Select specialized document analysis agents based on application characteristics.
        
        Args:
            application_data: Application data with loan and applicant details
            
        Returns:
            List of selected agents for document analysis
        """
        self.logger.info("Selecting document analysis team")
        
        selected_agents = [
            # Always include the orchestrator agent
            self.create_orchestrator_agent("document_analysis_coordinator")
        ]
        
        # Add document specialists based on application characteristics
        
        # Check employment type
        employment_type = self._extract_employment_type(application_data)
        if employment_type == "SELF_EMPLOYED":
            selected_agents.append(self.agent_registry["self_employment_specialist"])
        else:
            selected_agents.append(self.agent_registry["income_verification_specialist"])
        
        # Check property type
        property_type = self._extract_property_type(application_data)
        if property_type in [PropertyType.MULTI_FAMILY, PropertyType.CONDO, PropertyType.MANUFACTURED]:
            # Complex property types need specialized valuation
            selected_agents.append(self.agent_registry["property_valuation_specialist"])
        
        # Always add human proxy
        selected_agents.append(self.agent_registry["human_proxy"])
        
        self.logger.info(f"Selected {len(selected_agents)} agents for document analysis team")
        return selected_agents
    
    def select_underwriting_team(self, application_data: Dict[str, Any]) -> List[autogen.Agent]:
        """
        Select specialized underwriting agents based on application characteristics.
        
        Args:
            application_data: Application data with loan and applicant details
            
        Returns:
            List of selected agents for underwriting
        """
        self.logger.info("Selecting underwriting team")
        
        selected_agents = [
            # Always include the orchestrator agent
            self.create_orchestrator_agent("underwriting_coordinator")
        ]
        
        # Add loan type specialists
        loan_type = self._extract_loan_type(application_data)
        
        if loan_type == LoanType.CONVENTIONAL:
            selected_agents.append(self.agent_registry["conventional_loan_specialist"])
        elif loan_type == LoanType.FHA:
            selected_agents.append(self.agent_registry["fha_loan_specialist"])
        elif loan_type == LoanType.VA:
            selected_agents.append(self.agent_registry["va_loan_specialist"])
        elif loan_type == LoanType.JUMBO:
            selected_agents.append(self.agent_registry["jumbo_loan_specialist"])
        else:
            # Default to conventional for unknown types
            selected_agents.append(self.agent_registry["conventional_loan_specialist"])
        
        # Add income specialists based on employment type
        employment_type = self._extract_employment_type(application_data)
        if employment_type == "SELF_EMPLOYED":
            selected_agents.append(self.agent_registry["self_employment_specialist"])
        
        # Always add human proxy
        selected_agents.append(self.agent_registry["human_proxy"])
        
        self.logger.info(f"Selected {len(selected_agents)} agents for underwriting team")
        return selected_agents
    
    def select_compliance_team(self, application_data: Dict[str, Any]) -> List[autogen.Agent]:
        """
        Select specialized compliance agents based on application characteristics.
        
        Args:
            application_data: Application data with loan and applicant details
            
        Returns:
            List of selected agents for compliance checking
        """
        self.logger.info("Selecting compliance team")
        
        selected_agents = [
            # Always include the orchestrator agent
            self.create_orchestrator_agent("compliance_coordinator")
        ]
        
        # Always include regulatory compliance specialist
        selected_agents.append(self.agent_registry["regulatory_compliance_specialist"])
        
        # Add fair lending specialist for demographics that might raise fair lending concerns
        if self._needs_fair_lending_review(application_data):
            selected_agents.append(self.agent_registry["fair_lending_specialist"])
        
        # Always add human proxy
        selected_agents.append(self.agent_registry["human_proxy"])
        
        self.logger.info(f"Selected {len(selected_agents)} agents for compliance team")
        return selected_agents
    
    def select_customer_service_team(self, application_data: Dict[str, Any], 
                                    communication_type: str) -> List[autogen.Agent]:
        """
        Select specialized customer service agents based on application characteristics.
        
        Args:
            application_data: Application data with loan and applicant details
            communication_type: Type of communication (e.g., "explanation", "rejection", "inquiry")
            
        Returns:
            List of selected agents for customer service
        """
        self.logger.info(f"Selecting customer service team for {communication_type}")
        
        selected_agents = [
            # Always include the orchestrator agent
            self.create_orchestrator_agent("customer_service_coordinator")
        ]
        
        # Add specialists based on communication type
        if communication_type == "rejection":
            selected_agents.append(self.agent_registry["adverse_action_specialist"])
        
        # Add specialists based on customer characteristics
        if self._is_first_time_homebuyer(application_data):
            selected_agents.append(self.agent_registry["first_time_homebuyer_specialist"])
        
        # Always add human proxy
        selected_agents.append(self.agent_registry["human_proxy"])
        
        self.logger.info(f"Selected {len(selected_agents)} agents for customer service team")
        return selected_agents
    
    def create_orchestrator_agent(self, name: str) -> autogen.Agent:
        """
        Create a specialized orchestrator agent for a specific team.
        
        Args:
            name: Name for the orchestrator agent
            
        Returns:
            Configured orchestrator agent
        """
        return create_assistant_agent(
            name=name,
            system_message=f"""
            You are the coordinator for a team of mortgage lending specialists. Your role is to:
            1. Guide the conversation between specialized agents
            2. Synthesize insights from different specialists
            3. Ensure all relevant aspects of the application are addressed
            4. Facilitate consensus when specialists have different perspectives
            5. Summarize final decisions and recommendations
            
            Keep the conversation focused and productive. Ask specialists for input when their
            expertise is relevant, and help resolve any conflicting opinions.
            """
        )
    
    def _extract_loan_type(self, application_data: Dict[str, Any]) -> str:
        """Extract loan type from application data."""
        # Try different possible paths to loan type information
        if "loan_type" in application_data:
            return application_data["loan_type"]
        elif "loan" in application_data and "type" in application_data["loan"]:
            return application_data["loan"]["type"]
        elif "loan" in application_data and "loan_type" in application_data["loan"]:
            return application_data["loan"]["loan_type"]
        else:
            return "CONVENTIONAL"  # Default
    
    def _extract_property_type(self, application_data: Dict[str, Any]) -> str:
        """Extract property type from application data."""
        # Try different possible paths to property type information
        if "property_type" in application_data:
            return application_data["property_type"]
        elif "property" in application_data and "type" in application_data["property"]:
            return application_data["property"]["type"]
        elif "property" in application_data and "property_type" in application_data["property"]:
            return application_data["property"]["property_type"]
        else:
            return "SINGLE_FAMILY"  # Default
    
    def _extract_employment_type(self, application_data: Dict[str, Any]) -> str:
        """Extract employment type from application data."""
        # Check for self-employment indicators
        if "employment_type" in application_data:
            return application_data["employment_type"]
        elif "applicants" in application_data:
            for applicant in application_data["applicants"]:
                if "employment" in applicant:
                    for employment in applicant["employment"]:
                        if employment.get("is_self_employed", False):
                            return "SELF_EMPLOYED"
        elif "income" in application_data and "self_employment" in application_data["income"]:
            if application_data["income"]["self_employment"] > 0:
                return "SELF_EMPLOYED"
        
        return "W2_EMPLOYED"  # Default
    
    def _needs_fair_lending_review(self, application_data: Dict[str, Any]) -> bool:
        """Determine if application needs fair lending review."""
        # Check for indicators that might trigger fair lending review
        # This is a simplified example - in reality, this would be more complex
        
        # Check if the loan was denied but has good credit and income
        if (application_data.get("status") == ApplicationState.REJECTED_UNDERWRITING and 
            application_data.get("credit_score", 0) > 700 and
            self._calculate_dti(application_data) < 0.4):
            return True
        
        # Check for demographic information that might require fair lending review
        # Note: In practice, fair lending reviews should apply to all applications,
        # but additional scrutiny might be needed in certain cases
        
        return False
    
    def _is_first_time_homebuyer(self, application_data: Dict[str, Any]) -> bool:
        """Determine if applicant is a first-time homebuyer."""
        # Check for first-time homebuyer indicators
        if "is_first_time_homebuyer" in application_data:
            return application_data["is_first_time_homebuyer"]
        elif "first_time_homebuyer" in application_data:
            return application_data["first_time_homebuyer"]
        else:
            return False  # Default
    
    def _calculate_dti(self, application_data: Dict[str, Any]) -> float:
        """Calculate debt-to-income ratio from application data."""
        # Try to extract monthly income and debt
        monthly_income = 0
        monthly_debt = 0
        
        # Try different possible paths to income information
        if "monthly_income" in application_data:
            monthly_income = application_data["monthly_income"]
        elif "income" in application_data and "monthly" in application_data["income"]:
            monthly_income = application_data["income"]["monthly"]
        elif "income" in application_data and "annual" in application_data["income"]:
            monthly_income = application_data["income"]["annual"] / 12
        
        # Try different possible paths to debt information
        if "monthly_debt" in application_data:
            monthly_debt = application_data["monthly_debt"]
        elif "debt" in application_data and "monthly" in application_data["debt"]:
            monthly_debt = application_data["debt"]["monthly"]
        elif "debts" in application_data:
            for debt in application_data["debts"]:
                monthly_debt += debt.get("monthly_payment", 0)
        
        # Calculate DTI
        if monthly_income > 0:
            return monthly_debt / monthly_income
        else:
            return 1.0  # Default to high DTI if no income