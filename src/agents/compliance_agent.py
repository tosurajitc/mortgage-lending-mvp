"""
Compliance Agent Module
Ensures mortgage applications meet regulatory requirements and compliance standards.
"""

from typing import Any, Dict, List, Optional
import asyncio

from .base_agent import BaseAgent
from ..semantic_kernel.kernel_setup import get_kernel
from ..autogen.reasoning_agents import get_compliance_reasoning_agent
from ..utils.logging_utils import get_logger


class ComplianceAgent(BaseAgent):
    """
    Agent responsible for checking regulatory compliance of mortgage applications,
    including fair lending, disclosure requirements, and risk assessment.
    """
    
    def __init__(self, agent_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Compliance Agent.
        
        Args:
            agent_config: Configuration for the agent
        """
        super().__init__("compliance", agent_config)
        
        # Initialize Semantic Kernel
        self.kernel = get_kernel()
        
        # Get compliance reasoning agent from AutoGen
        self.reasoning_agent = get_compliance_reasoning_agent()
        
        # Initialize compliance rule sets
        self._initialize_compliance_rules()
        
        self.logger.info("Compliance agent initialized")
    
    def _initialize_compliance_rules(self):
        """Initialize various compliance rule sets."""
        # These would typically be loaded from configuration or a database
        # Using simplified examples for demonstration
        
        # Fair lending rules
        self.fair_lending_rules = {
            "equal_opportunity": "Applications must be evaluated without discrimination based on race, color, religion, sex, etc.",
            "consistent_standards": "Underwriting standards must be applied consistently across all applicants.",
            "adverse_action": "Adverse actions require proper notification and explanation."
        }
        
        # Disclosure requirements
        self.disclosure_requirements = {
            "tila_respa": "Truth in Lending Act and Real Estate Settlement Procedures Act disclosures required.",
            "loan_estimate": "Loan Estimate must be provided within 3 business days of application.",
            "fee_disclosure": "All fees must be properly disclosed and explained."
        }
        
        # Documentation requirements
        self.documentation_requirements = {
            "ability_to_repay": "Verification of income, assets, and employment required.",
            "identity_verification": "Verification of identity through government-issued ID.",
            "property_valuation": "Independent property appraisal required."
        }
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check regulatory compliance of a mortgage application.
        
        Args:
            input_data: Application data and previous processing results:
                - application_id: The ID of the application
                - application_data: Core application data
                - document_analysis: Results from document analysis
                - underwriting_results: Results from underwriting evaluation
                
        Returns:
            Dict containing compliance evaluation results
        """
        application_id = input_data.get("application_id")
        application_data = input_data.get("application_data", {})
        document_analysis = input_data.get("document_analysis", {})
        underwriting_results = input_data.get("underwriting_results", {})
        
        self.log_processing_step(f"Checking compliance for application {application_id}")
        
        try:
            # Run compliance checks in parallel
            check_results = await asyncio.gather(
                self._check_fair_lending(application_data, underwriting_results),
                self._check_required_documents(document_analysis),
                self._check_disclosure_requirements(application_data),
                self._check_high_risk_factors(application_data, underwriting_results),
                self._check_regulatory_limits(application_data, underwriting_results)
            )
            
            # Unpack the results
            fair_lending_results = check_results[0]
            document_results = check_results[1]
            disclosure_results = check_results[2]
            risk_factor_results = check_results[3]
            regulatory_limit_results = check_results[4]
            
            # Determine overall compliance
            is_compliant = all([
                fair_lending_results["passed"],
                document_results["passed"],
                disclosure_results["passed"],
                risk_factor_results["passed"],
                regulatory_limit_results["passed"]
            ])
            
            # Generate detailed compliance explanation
            explanation = await self._generate_compliance_explanation(
                is_compliant,
                [
                    fair_lending_results,
                    document_results,
                    disclosure_results,
                    risk_factor_results,
                    regulatory_limit_results
                ]
            )
            
            # Compile results
            compliance_factors = {}
            if not fair_lending_results["passed"]:
                compliance_factors["fair_lending"] = fair_lending_results["issues"]
            if not document_results["passed"]:
                compliance_factors["missing_documents"] = document_results["issues"]
            if not disclosure_results["passed"]:
                compliance_factors["disclosures"] = disclosure_results["issues"]
            if not risk_factor_results["passed"]:
                compliance_factors["risk_factors"] = risk_factor_results["issues"]
            if not regulatory_limit_results["passed"]:
                compliance_factors["regulatory_limits"] = regulatory_limit_results["issues"]
            
            results = {
                "application_id": application_id,
                "is_compliant": is_compliant,
                "compliance_checks": {
                    "fair_lending": fair_lending_results,
                    "required_documents": document_results,
                    "disclosures": disclosure_results,
                    "high_risk_factors": risk_factor_results,
                    "regulatory_limits": regulatory_limit_results
                },
                "compliance_factors": compliance_factors,
                "explanation": explanation,
                "required_actions": self._determine_required_actions(check_results),
                "timestamp": self._get_current_timestamp()
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error checking compliance for application {application_id}: {str(e)}", exc_info=True)
            raise
    
    async def _check_fair_lending(self, application_data: Dict[str, Any], 
                                 underwriting_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for fair lending compliance.
        
        Args:
            application_data: Core application data
            underwriting_results: Results from underwriting evaluation
            
        Returns:
            Dict with fair lending check results
        """
        self.log_processing_step("Checking fair lending compliance")
        
        # Use reasoning agent to check for fair lending issues
        context = {
            "application_data": application_data,
            "underwriting_results": underwriting_results,
            "fair_lending_rules": self.fair_lending_rules
        }
        
        result = await self.reasoning_agent.check_fair_lending_compliance(context)
        
        return {
            "check_type": "FAIR_LENDING",
            "passed": result.get("passed", False),
            "issues": result.get("issues", []),
            "recommendations": result.get("recommendations", [])
        }
    
    async def _check_required_documents(self, document_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if all required documents are present and valid.
        
        Args:
            document_analysis: Results from document analysis
            
        Returns:
            Dict with document check results
        """
        self.log_processing_step("Checking required documents")
        
        # Check if document analysis shows missing documents
        is_complete = document_analysis.get("is_complete", False)
        missing_documents = document_analysis.get("missing_documents", [])
        
        # Check for inconsistencies in documents
        inconsistencies = document_analysis.get("inconsistencies", [])
        
        # Check document quality and confidence
        overall_confidence = document_analysis.get("overall_confidence", 0)
        low_confidence_threshold = 0.7
        low_confidence_documents = []
        
        if "document_results" in document_analysis:
            for doc_type, doc_result in document_analysis["document_results"].items():
                if doc_result.get("confidence", 0) < low_confidence_threshold:
                    low_confidence_documents.append(doc_type)
        
        # Determine if document requirements are met
        passed = is_complete and not inconsistencies and not low_confidence_documents
        
        # Compile issues
        issues = []
        if missing_documents:
            issues.append(f"Missing required documents: {', '.join(missing_documents)}")
        if inconsistencies:
            issues.append(f"Document inconsistencies detected: {len(inconsistencies)} issues found")
        if low_confidence_documents:
            issues.append(f"Low confidence in document analysis: {', '.join(low_confidence_documents)}")
        
        return {
            "check_type": "REQUIRED_DOCUMENTS",
            "passed": passed,
            "issues": issues,
            "missing_documents": missing_documents,
            "inconsistencies": inconsistencies,
            "low_confidence_documents": low_confidence_documents
        }
    
    async def _check_disclosure_requirements(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if all required disclosures have been provided.
        
        Args:
            application_data: Core application data
            
        Returns:
            Dict with disclosure check results
        """
        self.log_processing_step("Checking disclosure requirements")
        
        # Extract disclosure information from application data
        disclosures = application_data.get("disclosures", {})
        
        # Check which required disclosures are missing
        missing_disclosures = []
        for disclosure_key in self.disclosure_requirements:
            if disclosure_key not in disclosures or not disclosures[disclosure_key].get("provided", False):
                missing_disclosures.append(disclosure_key)
        
        # Check for timing issues with disclosures
        timing_issues = []
        if "tila_respa" in disclosures and "date_provided" in disclosures["tila_respa"]:
            # Check if disclosure was provided within required timeframe
            # This would involve checking against application date
            pass
        
        # Determine if disclosure requirements are met
        passed = not missing_disclosures and not timing_issues
        
        # Compile issues
        issues = []
        if missing_disclosures:
            issues.append(f"Missing required disclosures: {', '.join(missing_disclosures)}")
        if timing_issues:
            issues.append(f"Disclosure timing issues: {', '.join(timing_issues)}")
        
        return {
            "check_type": "DISCLOSURES",
            "passed": passed,
            "issues": issues,
            "missing_disclosures": missing_disclosures,
            "timing_issues": timing_issues
        }
    
    async def _check_high_risk_factors(self, application_data: Dict[str, Any],
                                      underwriting_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for high-risk factors that may require additional scrutiny.
        
        Args:
            application_data: Core application data
            underwriting_results: Results from underwriting evaluation
            
        Returns:
            Dict with risk factor check results
        """
        self.log_processing_step("Checking high-risk factors")
        
        # Use reasoning agent to check for high-risk factors
        context = {
            "application_data": application_data,
            "underwriting_results": underwriting_results
        }
        
        result = await self.reasoning_agent.identify_high_risk_factors(context)
        
        high_risk_factors = result.get("high_risk_factors", [])
        risk_level = result.get("overall_risk_level", "LOW")
        
        # Determine if additional scrutiny is required
        requires_additional_scrutiny = risk_level in ["MEDIUM", "HIGH"]
        
        # Passed means no critical high-risk factors
        passed = risk_level != "HIGH"
        
        # Compile issues
        issues = []
        if high_risk_factors:
            for factor in high_risk_factors:
                if factor.get("severity", "LOW") == "HIGH":
                    issues.append(f"Critical risk factor: {factor.get('description', '')}")
                else:
                    issues.append(f"Risk factor: {factor.get('description', '')}")
        
        return {
            "check_type": "HIGH_RISK_FACTORS",
            "passed": passed,
            "risk_level": risk_level,
            "issues": issues,
            "high_risk_factors": high_risk_factors,
            "requires_additional_scrutiny": requires_additional_scrutiny
        }
    
    async def _check_regulatory_limits(self, application_data: Dict[str, Any],
                                      underwriting_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if the loan adheres to regulatory limits.
        
        Args:
            application_data: Core application data
            underwriting_results: Results from underwriting evaluation
            
        Returns:
            Dict with regulatory limit check results
        """
        self.log_processing_step("Checking regulatory limits")
        
        loan_amount = application_data.get("loan_amount", 0)
        loan_type = application_data.get("loan_type", "CONVENTIONAL")
        
        # Different loan types have different regulatory limits
        limit_violations = []
        
        # Check conforming loan limits
        if loan_type == "CONVENTIONAL":
            # 2024 conforming loan limit (this would be updated annually)
            conforming_limit = 726200
            if loan_amount > conforming_limit:
                limit_violations.append(f"Loan amount exceeds conforming loan limit of ${conforming_limit}")
        
        # Check FHA loan limits
        elif loan_type == "FHA":
            # Simplified FHA limit for example (actual limits vary by county)
            fha_limit = 420680
            if loan_amount > fha_limit:
                limit_violations.append(f"Loan amount exceeds FHA loan limit of ${fha_limit}")
        
        # Check HOEPA high-cost mortgage thresholds
        # This is simplified; actual calculation is more complex
        interest_rate = application_data.get("interest_rate", 0)
        if interest_rate > 10:  # Example threshold
            limit_violations.append("Interest rate exceeds HOEPA high-cost mortgage threshold")
        
        # Check points and fees for QM compliance
        points_and_fees = application_data.get("points_and_fees", 0)
        if points_and_fees / loan_amount > 0.03:  # Simplified threshold for QM
            limit_violations.append("Points and fees exceed QM threshold of 3% of loan amount")
        
        # Determine if regulatory limits are met
        passed = len(limit_violations) == 0
        
        return {
            "check_type": "REGULATORY_LIMITS",
            "passed": passed,
            "issues": limit_violations,
            "limit_violations": limit_violations
        }
    
    async def _generate_compliance_explanation(self, is_compliant: bool, 
                                              check_results: List[Dict[str, Any]]) -> str:
        """
        Generate human-readable explanation of compliance issues.
        
        Args:
            is_compliant: Overall compliance result
            check_results: Results of all compliance checks
            
        Returns:
            String with explanation of compliance status
        """
        self.log_processing_step("Generating compliance explanation")
        
        # Use semantic kernel to generate explanation
        explanation_plugin = self.kernel.plugins.get("compliance_plugin")
        
        # Prepare context for explanation
        context = {
            "is_compliant": is_compliant,
            "check_results": check_results
        }
        
        # Generate explanation using semantic kernel
        try:
            explanation_result = await explanation_plugin.generate_compliance_explanation.invoke_async(
                context=str(context)
            )
            return explanation_result.result
        except Exception as e:
            self.logger.error(f"Error generating explanation: {str(e)}", exc_info=True)
            
            # Fallback to simple explanation if semantic kernel fails
            if is_compliant:
                return "The application is compliant with all regulatory requirements."
            else:
                issues = []
                for check in check_results:
                    if not check.get("passed", True):
                        issues.extend(check.get("issues", []))
                
                if issues:
                    return f"The application has compliance issues: {'; '.join(issues)}"
                else:
                    return "The application has compliance issues that need to be addressed."
    
    def _determine_required_actions(self, check_results: List[Dict[str, Any]]) -> List[str]:
        """
        Determine required actions to address compliance issues.
        
        Args:
            check_results: Results of all compliance checks
            
        Returns:
            List of required action strings
        """
        required_actions = []
        
        for check in check_results:
            if not check.get("passed", True):
                check_type = check.get("check_type", "")
                
                if check_type == "REQUIRED_DOCUMENTS":
                    # Add actions for missing documents
                    for doc in check.get("missing_documents", []):
                        required_actions.append(f"Obtain missing document: {doc}")
                    
                    # Add actions for low confidence documents
                    for doc in check.get("low_confidence_documents", []):
                        required_actions.append(f"Obtain clearer copy of document: {doc}")
                
                elif check_type == "DISCLOSURES":
                    # Add actions for missing disclosures
                    for disclosure in check.get("missing_disclosures", []):
                        required_actions.append(f"Provide required disclosure: {disclosure}")
                
                elif check_type == "HIGH_RISK_FACTORS":
                    # Add actions for high risk factors
                    if check.get("requires_additional_scrutiny", False):
                        required_actions.append("Perform enhanced due diligence review")
                
                elif check_type == "REGULATORY_LIMITS":
                    # Add actions for regulatory limit violations
                    for violation in check.get("limit_violations", []):
                        required_actions.append(f"Address regulatory limit issue: {violation}")
                
                elif check_type == "FAIR_LENDING":
                    # Add actions for fair lending issues
                    for recommendation in check.get("recommendations", []):
                        required_actions.append(f"Fair lending recommendation: {recommendation}")
        
        return required_actions
    
    def _get_current_timestamp(self) -> str:
        """
        Get current timestamp in ISO format.
        
        Returns:
            String with current timestamp
        """
        from datetime import datetime
        return datetime.utcnow().isoformat()