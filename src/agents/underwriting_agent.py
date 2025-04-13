"""
Underwriting Agent Module (Enhanced)
Evaluates loan applications based on financial criteria and document analysis.
Added integration with UnderwritingEvaluatorPlugin for enhanced reasoning.
"""

from typing import Any, Dict, List, Optional
import asyncio
import json
import logging

from .base_agent import BaseAgent
from src.semantic_kernel.kernel_setup import get_kernel
from src.autogen.reasoning_agents import get_underwriting_reasoning_agent
from src.utils.logging_utils import get_logger
from src.data.cosmos_manager import CosmosDBManager
from src.semantic_kernel.plugins.underwriting_plugin.underwriting_evaluator import UnderwritingEvaluatorPlugin


class UnderwritingAgent(BaseAgent):
    """
    Agent responsible for evaluating mortgage applications,
    calculating financial ratios, and making underwriting decisions.
    Enhanced with UnderwritingEvaluatorPlugin for improved reasoning.
    """
    
    def __init__(self, agent_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Underwriting Agent.
        
        Args:
            agent_config: Configuration for the agent
        """

        super().__init__("underwriting")
        
        # Initialize Semantic Kernel
        self.kernel = get_kernel()
        
        # Register UnderwritingEvaluatorPlugin
        self._register_underwriting_evaluator()
        
        # Get underwriting reasoning agent from AutoGen
        cosmos_manager = CosmosDBManager() 
        prompt_manager = None

        self.reasoning_agent = get_underwriting_reasoning_agent(
            kernel=self.kernel,
            cosmos_manager=cosmos_manager,
            prompt_manager=prompt_manager
        )
        
        self.logger.info("Underwriting agent initialized with enhanced evaluation capabilities")
    
    def _register_underwriting_evaluator(self):
        """
        Register the UnderwritingEvaluatorPlugin with the semantic kernel.
        """
        try:
            # Create an instance of the UnderwritingEvaluatorPlugin
            underwriting_evaluator = UnderwritingEvaluatorPlugin(self.kernel)
            
            # Register the plugin with the kernel
            self.kernel.add_plugin(underwriting_evaluator, "underwriting_plugin")
            
            self.logger.info("UnderwritingEvaluatorPlugin registered successfully")
        except Exception as e:
            self.logger.error(f"Error registering UnderwritingEvaluatorPlugin: {str(e)}")
            # Continue without the plugin to maintain backward compatibility
            self.logger.info("Continuing with default underwriting capabilities")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a mortgage application.
        
        Args:
            input_data: Application data and document analysis results:
                - application_id: The ID of the application
                - application_data: Core application data
                - document_analysis: Results from document analysis
                
        Returns:
            Dict containing underwriting evaluation results
        """
        application_id = input_data.get("application_id")
        application_data = input_data.get("application_data", {})
        document_analysis = input_data.get("document_analysis", {})
        
        self.log_processing_step(f"Evaluating application {application_id}")
        
        try:
            # Calculate key financial ratios
            financial_ratios = await self._calculate_financial_ratios(application_data, document_analysis)
            
            # Use enhanced reasoning if available
            enhanced_evaluation = await self._perform_enhanced_evaluation(application_data, document_analysis, financial_ratios)
            
            # Evaluate application against underwriting criteria
            # This maintains the original logic while also considering enhanced evaluation
            criteria_evaluation = await self._evaluate_underwriting_criteria(
                application_data, 
                document_analysis, 
                financial_ratios,
                enhanced_evaluation
            )
            
            # Determine if the application should be approved
            approval_result = await self._determine_approval(criteria_evaluation, enhanced_evaluation)
            
            # Calculate risk score
            risk_score = await self._calculate_risk_score(criteria_evaluation)
            
            # Calculate recommended interest rate if approved
            recommended_rate = await self._calculate_recommended_rate(
                risk_score, 
                application_data, 
                approval_result["is_approved"]
            )
            
            # Calculate maximum loan amount based on applicant's financials
            max_loan_amount = await self._calculate_max_loan_amount(
                application_data, 
                document_analysis, 
                financial_ratios
            )
            
            # Generate explanation for the decision
            explanation = await self._generate_decision_explanation(
                application_data,
                document_analysis,
                financial_ratios,
                criteria_evaluation,
                approval_result,
                enhanced_evaluation
            )
            
            # Compile results
            results = {
                "application_id": application_id,
                "is_approved": approval_result["is_approved"],
                "approval_type": approval_result.get("approval_type"),
                "risk_score": risk_score,
                "financial_ratios": financial_ratios,
                "criteria_evaluation": criteria_evaluation,
                "decision_factors": approval_result.get("decision_factors", {}),
                "conditions": approval_result.get("conditions", []),
                "recommended_interest_rate": recommended_rate,
                "max_loan_amount": max_loan_amount,
                "explanation": explanation,
                "enhanced_evaluation": enhanced_evaluation.get("summary", {}),
                "timestamp": self._get_current_timestamp()
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error evaluating application {application_id}: {str(e)}", exc_info=True)
            raise
    
    async def _perform_enhanced_evaluation(self, application_data: Dict[str, Any],
                                        document_analysis: Dict[str, Any],
                                        financial_ratios: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform enhanced evaluation using the UnderwritingEvaluatorPlugin.
        Falls back gracefully if the plugin is not available.
        
        Args:
            application_data: Core application data
            document_analysis: Results from document analysis
            financial_ratios: Calculated financial ratios
            
        Returns:
            Dict with enhanced evaluation results or empty dict if not available
        """
        try:
            # Check if the plugin is available
            if "underwriting_plugin" not in self.kernel.plugins:
                return {"available": False}
                
            underwriting_plugin = self.kernel.plugins.get("underwriting_plugin")
            
            # Prepare data for the plugin
            loan_type = application_data.get("loan_type", "CONVENTIONAL").upper()
            
            # Combine relevant data into a single context
            combined_data = {
                "loan_amount": application_data.get("loan_amount", 0),
                "loan_term_years": application_data.get("loan_term_years", 30),
                "interest_rate": application_data.get("interest_rate", 0),
                "property_value": self._extract_property_value(application_data, document_analysis),
                "credit_score": self._extract_credit_score(application_data, document_analysis),
                "monthly_income": financial_ratios.get("monthly_income", 0),
                "monthly_debts": financial_ratios.get("monthly_debts", 0),
                "property_type": application_data.get("property_type", "single_family"),
                "is_first_time_homebuyer": application_data.get("is_first_time_homebuyer", False),
                "is_veteran": application_data.get("is_veteran", False),
                "down_payment": self._extract_down_payment(application_data, document_analysis),
                # Add financial ratios for more accurate evaluation
                "dti_ratio": financial_ratios.get("dti", 0) * 100,  # Convert from decimal to percentage
                "ltv_ratio": financial_ratios.get("ltv", 0) * 100,  # Convert from decimal to percentage
                "frontend_ratio": financial_ratios.get("frontend_ratio", 0) * 100  # Convert from decimal to percentage
            }
            
            # Serialize data for the plugin
            application_data_json = json.dumps(combined_data)
            
            # Choose the right evaluation function based on loan type
            if loan_type == "FHA":
                evaluation_function = underwriting_plugin.evaluate_fha_loan
            else:
                evaluation_function = underwriting_plugin.evaluate_conventional_loan
                
            # Invoke the plugin function
            evaluation_result = await evaluation_function.invoke_async(
                application_data=application_data_json
            )
            
            # Also get a recommendation for best loan program
            recommendation_result = await underwriting_plugin.recommend_loan_program.invoke_async(
                application_data=application_data_json
            )
            
            # Parse the results
            evaluation = json.loads(evaluation_result.result) if evaluation_result.result else {}
            recommendation = json.loads(recommendation_result.result) if recommendation_result.result else {}
            
            # Combine and return the enhanced evaluation
            return {
                "available": True,
                "evaluation": evaluation,
                "recommendation": recommendation,
                "summary": {
                    "qualified": evaluation.get("qualified", False),
                    "loan_recommendation": evaluation.get("loan_recommendation", ""),
                    "risk_factors": evaluation.get("risk_factors", []),
                    "strengths": evaluation.get("strengths", []),
                    "estimated_rate": evaluation.get("estimated_rate", 0),
                    "recommended_programs": [p.get("program") for p in recommendation.get("recommended_programs", [])][:2]
                }
            }
            
        except Exception as e:
            self.logger.warning(f"Enhanced evaluation failed: {str(e)}. Falling back to standard evaluation.")
            return {"available": False, "error": str(e)}
    
    async def _evaluate_underwriting_criteria(self, application_data: Dict[str, Any], 
                                             document_analysis: Dict[str, Any],
                                             financial_ratios: Dict[str, Any],
                                             enhanced_evaluation: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Evaluate the application against standard underwriting criteria.
        Incorporates enhanced evaluation when available.
        
        Args:
            application_data: Core application data
            document_analysis: Results from document analysis
            financial_ratios: Calculated financial ratios
            enhanced_evaluation: Results from enhanced evaluation
            
        Returns:
            Dict with evaluation results for each criterion
        """
        self.log_processing_step("Evaluating against underwriting criteria")
        
        # Get loan type to determine appropriate criteria
        loan_type = application_data.get("loan_type", "CONVENTIONAL")
        
        # Extract credit score from documents
        doc_results = document_analysis.get("document_results", {})
        credit_data = doc_results.get("CREDIT_REPORT", {})
        credit_score = credit_data.get("credit_score", 0)
        
        # Define criteria thresholds based on loan type
        thresholds = self._get_threshold_by_loan_type(loan_type)
        
        # Evaluate each criterion
        dti_evaluation = {
            "criterion": "DTI_RATIO",
            "value": financial_ratios.get("dti", 0),
            "threshold": thresholds["max_dti"],
            "passed": financial_ratios.get("dti", 0) <= thresholds["max_dti"],
            "weight": 25
        }
        
        ltv_evaluation = {
            "criterion": "LTV_RATIO",
            "value": financial_ratios.get("ltv", 0),
            "threshold": thresholds["max_ltv"],
            "passed": financial_ratios.get("ltv", 0) <= thresholds["max_ltv"],
            "weight": 25
        }
        
        frontend_evaluation = {
            "criterion": "FRONTEND_RATIO",
            "value": financial_ratios.get("frontend_ratio", 0),
            "threshold": thresholds["max_frontend_ratio"],
            "passed": financial_ratios.get("frontend_ratio", 0) <= thresholds["max_frontend_ratio"],
            "weight": 15
        }
        
        credit_evaluation = {
            "criterion": "CREDIT_SCORE",
            "value": credit_score,
            "threshold": thresholds["min_credit_score"],
            "passed": credit_score >= thresholds["min_credit_score"],
            "weight": 35
        }
        
        # Check for edge cases that might require AI reasoning
        criteria_evaluations = {
            "DTI_RATIO": dti_evaluation,
            "LTV_RATIO": ltv_evaluation,
            "FRONTEND_RATIO": frontend_evaluation,
            "CREDIT_SCORE": credit_evaluation
        }
        
        # Incorporate enhanced evaluation if available
        if enhanced_evaluation and enhanced_evaluation.get("available", False):
            evaluation = enhanced_evaluation.get("evaluation", {})
            
            # Add enhanced AI assessment
            enhanced_ai_evaluation = {
                "criterion": "ENHANCED_AI_ASSESSMENT",
                "value": 1 if evaluation.get("qualified", False) else 0,
                "threshold": 1,
                "passed": evaluation.get("qualified", False),
                "weight": 40,  # High weight for the AI assessment
                "risk_factors": evaluation.get("risk_factors", []),
                "strengths": evaluation.get("strengths", [])
            }
            
            criteria_evaluations["ENHANCED_AI_ASSESSMENT"] = enhanced_ai_evaluation
        
        # Use AI reasoning for borderline cases
        if self._is_borderline_case(criteria_evaluations):
            ai_evaluation = await self._evaluate_borderline_case(
                application_data, document_analysis, financial_ratios, criteria_evaluations
            )
            
            # Add AI evaluation results
            criteria_evaluations["AI_ASSESSMENT"] = ai_evaluation
        
        return criteria_evaluations
    
    async def _determine_approval(self, criteria_evaluation: Dict[str, Dict[str, Any]],
                               enhanced_evaluation: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Determine if the application should be approved based on criteria evaluation.
        Incorporates enhanced evaluation when available.
        
        Args:
            criteria_evaluation: Results of criteria evaluation
            enhanced_evaluation: Results from enhanced evaluation
            
        Returns:
            Dict with approval decision and details
        """
        self.log_processing_step("Determining approval status")
        
        # Consider enhanced evaluation if available
        if enhanced_evaluation and enhanced_evaluation.get("available", False):
            enhanced_result = enhanced_evaluation.get("evaluation", {})
            if "qualified" in enhanced_result:
                recommendation = enhanced_result.get("loan_recommendation", "")
                
                if enhanced_result["qualified"]:
                    return {
                        "is_approved": True,
                        "approval_type": "APPROVED_WITH_CONDITIONS" if recommendation == "Refer to Underwriter" else "APPROVED",
                        "decision_factors": {
                            "primary_factor": "ENHANCED_EVALUATION",
                            "strengths": enhanced_result.get("strengths", []),
                            "risk_factors": enhanced_result.get("risk_factors", [])
                        },
                        "conditions": enhanced_result.get("conditions", [])
                    }
                else:
                    return {
                        "is_approved": False,
                        "approval_type": "REJECTED",
                        "decision_factors": {
                            "primary_factor": "ENHANCED_EVALUATION",
                            "risk_factors": enhanced_result.get("risk_factors", [])
                        }
                    }
        
        # Check if AI assessment is present (borderline case)
        if "AI_ASSESSMENT" in criteria_evaluation:
            ai_assessment = criteria_evaluation["AI_ASSESSMENT"]
            
            if ai_assessment.get("passed", False):
                # AI recommends approval despite some standard criteria failures
                return {
                    "is_approved": True,
                    "approval_type": "APPROVED_WITH_CONDITIONS",
                    "decision_factors": {
                        "primary_factor": "AI_ASSESSMENT",
                        "compensating_factors": ai_assessment.get("compensating_factors", [])
                    },
                    "conditions": self._generate_conditions_for_borderline_approval(criteria_evaluation)
                }
            else:
                # AI does not recommend approval
                return {
                    "is_approved": False,
                    "approval_type": "REJECTED",
                    "decision_factors": {
                        "primary_factor": "AI_ASSESSMENT",
                        "rationale": ai_assessment.get("rationale", "")
                    }
                }
        
        # Standard evaluation for non-borderline cases
        # Count failed criteria
        failed_criteria = [key for key, eval in criteria_evaluation.items() 
                          if not eval.get("passed", False)]
        
        if not failed_criteria:
            # All criteria passed
            return {
                "is_approved": True,
                "approval_type": "APPROVED",
                "decision_factors": {
                    "primary_factor": "ALL_CRITERIA_PASSED"
                }
            }
        else:
            # Some criteria failed
            return {
                "is_approved": False,
                "approval_type": "REJECTED",
                "decision_factors": {
                    "primary_factor": "FAILED_CRITERIA",
                    "failed_criteria": failed_criteria
                }
            }
    
    async def _generate_decision_explanation(self, application_data: Dict[str, Any],
                                           document_analysis: Dict[str, Any],
                                           financial_ratios: Dict[str, Any],
                                           criteria_evaluation: Dict[str, Dict[str, Any]],
                                           approval_result: Dict[str, Any],
                                           enhanced_evaluation: Dict[str, Any] = None) -> str:
        """
        Generate human-readable explanation for the underwriting decision.
        Incorporates enhanced evaluation when available.
        
        Args:
            application_data: Core application data
            document_analysis: Results from document analysis
            financial_ratios: Calculated financial ratios
            criteria_evaluation: Results of criteria evaluation
            approval_result: Approval decision and details
            enhanced_evaluation: Results from enhanced evaluation
            
        Returns:
            String with explanation of the decision
        """
        self.log_processing_step("Generating decision explanation")
        
        # Use enhanced explanation if available
        if enhanced_evaluation and enhanced_evaluation.get("available", False):
            enhanced_result = enhanced_evaluation.get("evaluation", {})
            
            # Use semantic kernel to generate enhanced explanation
            explanation_plugin = self.kernel.plugins.get("underwriting_plugin")
            
            # Prepare context with all available data
            context = {
                "application_data": application_data,
                "document_analysis": document_analysis.get("summary", {}),
                "financial_ratios": financial_ratios,
                "criteria_evaluation": criteria_evaluation,
                "approval_result": approval_result,
                "enhanced_evaluation": enhanced_result,
                "loan_recommendation": enhanced_result.get("loan_recommendation", ""),
                "risk_factors": enhanced_result.get("risk_factors", []),
                "strengths": enhanced_result.get("strengths", [])
            }
            
            try:
                # Generate enhanced explanation
                explanation_result = await explanation_plugin.generate_decision_explanation.invoke_async(
                    context=str(context)
                )
                return explanation_result.result
            except Exception as e:
                self.logger.warning(f"Enhanced explanation failed: {str(e)}. Falling back to standard explanation.")
                # Continue with standard explanation if enhanced explanation fails
        
        # Use standard semantic kernel to generate explanation
        explanation_plugin = self.kernel.plugins.get("underwriting_plugin")
        
        # Prepare context for explanation
        context = {
            "application_data": application_data,
            "document_analysis": document_analysis.get("summary", {}),
            "financial_ratios": financial_ratios,
            "criteria_evaluation": criteria_evaluation,
            "approval_result": approval_result
        }
        
        # Generate explanation using semantic kernel
        try:
            explanation_result = await explanation_plugin.generate_decision_explanation.invoke_async(
                context=str(context)
            )
            return explanation_result.result
        except Exception as e:
            self.logger.error(f"Error generating explanation: {str(e)}", exc_info=True)
            
            # Fallback to simpler explanation if semantic kernel fails
            if approval_result.get("is_approved", False):
                return "Your application has been approved based on our evaluation of your financial information."
            else:
                failed_criteria = approval_result.get("decision_factors", {}).get("failed_criteria", [])
                if failed_criteria:
                    return f"Your application was not approved due to the following: {', '.join(failed_criteria)}"
                else:
                    return "Your application was not approved based on our evaluation of your financial information."
    
    # Helper method to extract property value from combined sources
    def _extract_property_value(self, application_data: Dict[str, Any], document_analysis: Dict[str, Any]) -> float:
        """Extract property value from application data and document analysis."""
        # Try from application data first
        if "property_value" in application_data:
            return float(application_data["property_value"])
            
        # Then try from document analysis
        doc_results = document_analysis.get("document_results", {})
        property_data = doc_results.get("PROPERTY_APPRAISAL", {})
        if "property_value" in property_data:
            return float(property_data["property_value"])
            
        # Default to 0 if not found
        return 0.0
        
    # Helper method to extract credit score from combined sources
    def _extract_credit_score(self, application_data: Dict[str, Any], document_analysis: Dict[str, Any]) -> int:
        """Extract credit score from application data and document analysis."""
        # Try from application data first
        if "credit_score" in application_data:
            return int(application_data["credit_score"])
            
        # Then try from document analysis
        doc_results = document_analysis.get("document_results", {})
        credit_data = doc_results.get("CREDIT_REPORT", {})
        if "credit_score" in credit_data:
            return int(credit_data["credit_score"])
            
        # Default to 0 if not found
        return 0
        
    # Helper method to extract down payment from combined sources
    def _extract_down_payment(self, application_data: Dict[str, Any], document_analysis: Dict[str, Any]) -> float:
        """Extract down payment from application data and document analysis."""
        # Try from application data first
        if "down_payment" in application_data:
            return float(application_data["down_payment"])
            
        # Calculate from loan amount and property value
        loan_amount = application_data.get("loan_amount", 0)
        property_value = self._extract_property_value(application_data, document_analysis)
        
        if property_value > 0 and loan_amount > 0:
            return property_value - loan_amount
            
        # Default to 0 if not found
        return 0.0
    
    # The rest of the class remains unchanged
    # Include all existing methods from the original UnderwritingAgent class here
    
    # These are placeholder references for the required methods
    async def _calculate_financial_ratios(self, application_data, document_analysis):
        # Use existing implementation...
        pass

    def _get_threshold_by_loan_type(self, loan_type):
        # Use existing implementation...
        pass
        
    def _is_borderline_case(self, criteria_evaluations):
        # Use existing implementation...
        pass
        
    async def _evaluate_borderline_case(self, application_data, document_analysis, financial_ratios, criteria_evaluations):
        # Use existing implementation...
        pass
        
    def _generate_conditions_for_borderline_approval(self, criteria_evaluation):
        # Use existing implementation...
        pass
        
    async def _calculate_risk_score(self, criteria_evaluation):
        # Use existing implementation...
        pass
        
    async def _calculate_recommended_rate(self, risk_score, application_data, is_approved):
        # Use existing implementation...
        pass
        
    async def _calculate_max_loan_amount(self, application_data, document_analysis, financial_ratios):
        # Use existing implementation...
        pass
        
    def _get_current_timestamp(self):
        # Use existing implementation...
        pass