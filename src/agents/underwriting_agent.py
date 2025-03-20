"""
Underwriting Agent Module
Evaluates loan applications based on financial criteria and document analysis.
"""

from typing import Any, Dict, List, Optional
import asyncio

from .base_agent import BaseAgent
from ..semantic_kernel.kernel_setup import get_kernel
from ..autogen.reasoning_agents import get_underwriting_reasoning_agent
from ..utils.logging_utils import get_logger


class UnderwritingAgent(BaseAgent):
    """
    Agent responsible for evaluating mortgage applications,
    calculating financial ratios, and making underwriting decisions.
    """
    
    def __init__(self, agent_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Underwriting Agent.
        
        Args:
            agent_config: Configuration for the agent
        """
        super().__init__("underwriting", agent_config)
        
        # Initialize Semantic Kernel
        self.kernel = get_kernel()
        
        # Get underwriting reasoning agent from AutoGen
        self.reasoning_agent = get_underwriting_reasoning_agent()
        
        self.logger.info("Underwriting agent initialized")
    
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
            
            # Evaluate application against underwriting criteria
            criteria_evaluation = await self._evaluate_underwriting_criteria(
                application_data, 
                document_analysis, 
                financial_ratios
            )
            
            # Determine if the application should be approved
            approval_result = await self._determine_approval(criteria_evaluation)
            
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
                approval_result
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
                "timestamp": self._get_current_timestamp()
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error evaluating application {application_id}: {str(e)}", exc_info=True)
            raise
    
    async def _calculate_financial_ratios(self, application_data: Dict[str, Any], 
                                         document_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate key financial ratios used in mortgage underwriting.
        
        Args:
            application_data: Core application data
            document_analysis: Results from document analysis
            
        Returns:
            Dict with calculated financial ratios
        """
        self.log_processing_step("Calculating financial ratios")
        
        # Extract needed data from documents
        doc_results = document_analysis.get("document_results", {})
        income_data = doc_results.get("INCOME_VERIFICATION", {})
        credit_data = doc_results.get("CREDIT_REPORT", {})
        property_data = doc_results.get("PROPERTY_APPRAISAL", {})
        
        # Get annual income from documents
        annual_income = income_data.get("income_amount", 0)
        monthly_income = annual_income / 12 if annual_income else 0
        
        # Get outstanding debts from credit report
        outstanding_debts = credit_data.get("outstanding_debts", [])
        
        # Calculate total monthly debt payments (simplified)
        monthly_debt_payments = self._calculate_monthly_debt_payments(outstanding_debts)
        
        # Get loan details from application
        loan_amount = application_data.get("loan_amount", 0)
        loan_term_years = application_data.get("loan_term_years", 30)
        interest_rate = application_data.get("interest_rate", 0)
        
        # Get property value from appraisal
        property_value = property_data.get("property_value", 0)
        
        # Calculate estimated monthly mortgage payment
        monthly_mortgage_payment = self._calculate_monthly_payment(
            loan_amount, interest_rate, loan_term_years
        )
        
        # Calculate Debt-to-Income Ratio (DTI)
        dti = 0
        if monthly_income > 0:
            dti = (monthly_debt_payments + monthly_mortgage_payment) / monthly_income
        
        # Calculate Loan-to-Value Ratio (LTV)
        ltv = 0
        if property_value > 0:
            ltv = loan_amount / property_value
        
        # Calculate Payment-to-Income Ratio (PTI)
        pti = 0
        if monthly_income > 0:
            pti = monthly_mortgage_payment / monthly_income
        
        # Front-end ratio (housing expenses to income)
        housing_expenses = monthly_mortgage_payment
        # Add property taxes, insurance, HOA if available
        if "property_taxes" in application_data:
            housing_expenses += application_data.get("property_taxes", 0) / 12
        if "insurance" in application_data:
            housing_expenses += application_data.get("insurance", 0) / 12
        if "hoa_fees" in application_data:
            housing_expenses += application_data.get("hoa_fees", 0)
            
        frontend_ratio = 0
        if monthly_income > 0:
            frontend_ratio = housing_expenses / monthly_income
        
        # Assemble the financial ratios
        financial_ratios = {
            "dti": dti,
            "ltv": ltv,
            "pti": pti,
            "frontend_ratio": frontend_ratio,
            "monthly_income": monthly_income,
            "monthly_debt_payments": monthly_debt_payments,
            "monthly_mortgage_payment": monthly_mortgage_payment,
            "housing_expenses": housing_expenses
        }
        
        return financial_ratios
    
    def _calculate_monthly_debt_payments(self, outstanding_debts: List[Dict[str, Any]]) -> float:
        """
        Calculate total monthly debt payments from outstanding debts.
        
        Args:
            outstanding_debts: List of outstanding debt objects
            
        Returns:
            Float representing total monthly debt payments
        """
        total_monthly_payment = 0
        
        for debt in outstanding_debts:
            debt_type = debt.get("type", "")
            amount = debt.get("amount", 0)
            
            # Apply different monthly payment calculations based on debt type
            if debt_type == "CREDIT_CARD":
                # Assume minimum payment is 3% of balance
                total_monthly_payment += amount * 0.03
            elif debt_type == "AUTO_LOAN":
                # Assume 5-year term at 5% for simplicity
                total_monthly_payment += self._calculate_monthly_payment(amount, 5.0, 5)
            elif debt_type == "STUDENT_LOAN":
                # Assume 10-year term at 4% for simplicity
                total_monthly_payment += self._calculate_monthly_payment(amount, 4.0, 10)
            elif debt_type == "MORTGAGE":
                # Use the provided payment if available, otherwise assume 30-year term at current rate
                if "monthly_payment" in debt:
                    total_monthly_payment += debt.get("monthly_payment", 0)
                else:
                    total_monthly_payment += self._calculate_monthly_payment(amount, 6.0, 30)
            else:
                # Generic calculation for other debt types (5% of balance)
                total_monthly_payment += amount * 0.05
        
        return total_monthly_payment
    
    def _calculate_monthly_payment(self, principal: float, annual_rate: float, term_years: int) -> float:
        """
        Calculate monthly mortgage payment using standard amortization formula.
        
        Args:
            principal: Loan amount
            annual_rate: Annual interest rate (%)
            term_years: Loan term in years
            
        Returns:
            Float representing monthly payment
        """
        if principal <= 0 or annual_rate <= 0 or term_years <= 0:
            return 0
            
        # Convert annual interest rate to monthly rate and decimal form
        monthly_rate = (annual_rate / 100) / 12
        
        # Total number of payments
        num_payments = term_years * 12
        
        # Calculate monthly payment using the amortization formula
        if monthly_rate == 0:
            return principal / num_payments
            
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
        
        return monthly_payment
    
    async def _evaluate_underwriting_criteria(self, application_data: Dict[str, Any], 
                                             document_analysis: Dict[str, Any],
                                             financial_ratios: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate the application against standard underwriting criteria.
        
        Args:
            application_data: Core application data
            document_analysis: Results from document analysis
            financial_ratios: Calculated financial ratios
            
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
        
        # Use AI reasoning for borderline cases
        if self._is_borderline_case(criteria_evaluations):
            ai_evaluation = await self._evaluate_borderline_case(
                application_data, document_analysis, financial_ratios, criteria_evaluations
            )
            
            # Add AI evaluation results
            criteria_evaluations["AI_ASSESSMENT"] = ai_evaluation
        
        return criteria_evaluations
    
    def _get_threshold_by_loan_type(self, loan_type: str) -> Dict[str, float]:
        """
        Get threshold values based on loan type.
        
        Args:
            loan_type: Type of loan (CONVENTIONAL, FHA, VA, etc.)
            
        Returns:
            Dict with threshold values
        """
        # Default thresholds for different loan types
        if loan_type == "CONVENTIONAL":
            return {
                "max_dti": 0.43,
                "max_ltv": 0.80,
                "max_frontend_ratio": 0.28,
                "min_credit_score": 640
            }
        elif loan_type == "FHA":
            return {
                "max_dti": 0.50,
                "max_ltv": 0.965,
                "max_frontend_ratio": 0.31,
                "min_credit_score": 580
            }
        elif loan_type == "VA":
            return {
                "max_dti": 0.60,
                "max_ltv": 1.0,
                "max_frontend_ratio": 0.31,
                "min_credit_score": 580
            }
        else:
            # Default to conventional loan thresholds for unknown types
            return {
                "max_dti": 0.43,
                "max_ltv": 0.80,
                "max_frontend_ratio": 0.28,
                "min_credit_score": 640
            }
    
    def _is_borderline_case(self, criteria_evaluations: Dict[str, Dict[str, Any]]) -> bool:
        """
        Determine if an application is a borderline case that needs AI reasoning.
        
        Args:
            criteria_evaluations: Results of criteria evaluation
            
        Returns:
            Boolean indicating if this is a borderline case
        """
        # Count passed and failed criteria
        passed = sum(1 for eval in criteria_evaluations.values() if eval.get("passed", False))
        failed = len(criteria_evaluations) - passed
        
        # Borderline case if some criteria pass and some fail
        if passed > 0 and failed > 0:
            return True
            
        # Or if any criterion is close to the threshold (within 5%)
        for eval in criteria_evaluations.values():
            value = eval.get("value", 0)
            threshold = eval.get("threshold", 0)
            
            if threshold > 0:
                # For ratios where lower is better
                if eval.get("criterion") in ["DTI_RATIO", "LTV_RATIO", "FRONTEND_RATIO"]:
                    if value > threshold * 0.95 and value < threshold * 1.05:
                        return True
                # For scores where higher is better
                else:
                    if value > threshold * 0.95 and value < threshold * 1.05:
                        return True
        
        return False
    
    async def _evaluate_borderline_case(self, application_data: Dict[str, Any],
                                       document_analysis: Dict[str, Any],
                                       financial_ratios: Dict[str, Any],
                                       criteria_evaluations: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Use AI reasoning to evaluate borderline cases.
        
        Args:
            application_data: Core application data
            document_analysis: Results from document analysis
            financial_ratios: Calculated financial ratios
            criteria_evaluations: Standard criteria evaluation results
            
        Returns:
            Dict with AI evaluation results
        """
        self.log_processing_step("Evaluating borderline case with AI reasoning")
        
        # Prepare context for AI evaluation
        context = {
            "application_data": application_data,
            "document_summary": document_analysis.get("summary", {}),
            "financial_ratios": financial_ratios,
            "criteria_evaluations": criteria_evaluations,
            "loan_type": application_data.get("loan_type", "CONVENTIONAL")
        }
        
        # Use reasoning agent to evaluate the borderline case
        reasoning_result = await self.reasoning_agent.evaluate_borderline_application(context)
        
        # Extract and return the assessment
        return {
            "criterion": "AI_ASSESSMENT",
            "passed": reasoning_result.get("should_approve", False),
            "rationale": reasoning_result.get("rationale", ""),
            "compensating_factors": reasoning_result.get("compensating_factors", []),
            "weight": 50  # AI assessment carries significant weight in borderline cases
        }
    
    async def _determine_approval(self, criteria_evaluation: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Determine if the application should be approved based on criteria evaluation.
        
        Args:
            criteria_evaluation: Results of criteria evaluation
            
        Returns:
            Dict with approval decision and details
        """
        self.log_processing_step("Determining approval status")
        
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
    
    def _generate_conditions_for_borderline_approval(self, criteria_evaluation: Dict[str, Dict[str, Any]]) -> List[str]:
        """
        Generate conditions for borderline approvals.
        
        Args:
            criteria_evaluation: Results of criteria evaluation
            
        Returns:
            List of condition strings
        """
        conditions = []
        
        # Add conditions based on failed criteria
        for key, eval in criteria_evaluation.items():
            if key != "AI_ASSESSMENT" and not eval.get("passed", False):
                if key == "DTI_RATIO":
                    conditions.append("Reduce overall debt or increase income before closing")
                elif key == "LTV_RATIO":
                    conditions.append("Increase down payment to reduce loan-to-value ratio")
                elif key == "FRONTEND_RATIO":
                    conditions.append("Provide additional cash reserves")
                elif key == "CREDIT_SCORE":
                    conditions.append("Provide additional collateral or guarantor")
        
        # Add standard conditions for borderline approvals
        conditions.append("Submit updated bank statements before closing")
        conditions.append("Provide letter explaining any recent credit inquiries")
        
        return conditions
    
    async def _calculate_risk_score(self, criteria_evaluation: Dict[str, Dict[str, Any]]) -> float:
        """
        Calculate risk score based on criteria evaluation.
        
        Args:
            criteria_evaluation: Results of criteria evaluation
            
        Returns:
            Float representing risk score (0-100, higher is better)
        """
        # Start with base score
        risk_score = 50.0
        total_weight = 0
        
        # Adjust score based on each criterion
        for key, eval in criteria_evaluation.items():
            if key == "AI_ASSESSMENT":
                continue  # Skip AI assessment, handled separately
                
            weight = eval.get("weight", 0)
            total_weight += weight
            
            value = eval.get("value", 0)
            threshold = eval.get("threshold", 0)
            
            if threshold == 0:
                continue
                
            # Calculate criterion score based on how far it is from the threshold
            criterion_score = 0
            if key in ["DTI_RATIO", "LTV_RATIO", "FRONTEND_RATIO"]:
                # For these criteria, lower is better
                if value <= threshold:
                    # Passed - calculate how much better than threshold (as percentage)
                    criterion_score = 100 - (value / threshold * 100)
                else:
                    # Failed - negative score based on how much worse than threshold
                    criterion_score = -((value - threshold) / threshold * 100)
            else:
                # For credit score, higher is better
                if value >= threshold:
                    # Passed - calculate how much better than threshold (as percentage)
                    criterion_score = ((value - threshold) / threshold * 100)
                else:
                    # Failed - negative score based on how much worse than threshold
                    criterion_score = -((threshold - value) / threshold * 100)
            
            # Adjust overall risk score based on weighted criterion score
            risk_score += (criterion_score * weight / 100)
        
        # Adjust for AI assessment if present
        if "AI_ASSESSMENT" in criteria_evaluation:
            ai_assessment = criteria_evaluation["AI_ASSESSMENT"]
            if ai_assessment.get("passed", False):
                risk_score += 10  # Bonus for positive AI assessment
            else:
                risk_score -= 10  # Penalty for negative AI assessment
        
        # Normalize to 0-100 range
        risk_score = max(0, min(100, risk_score))
        
        return risk_score
    
    async def _calculate_recommended_rate(self, risk_score: float, application_data: Dict[str, Any], 
                                         is_approved: bool) -> Optional[float]:
        """
        Calculate recommended interest rate based on risk score.
        
        Args:
            risk_score: Calculated risk score
            application_data: Core application data
            is_approved: Whether the application is approved
            
        Returns:
            Float representing recommended interest rate or None if not approved
        """
        if not is_approved:
            return None
            
        # Base rate depends on loan type and current market conditions
        loan_type = application_data.get("loan_type", "CONVENTIONAL")
        loan_term = application_data.get("loan_term_years", 30)
        
        # Get base rate for the loan type and term (these would come from current market rates)
        base_rate = self._get_base_rate(loan_type, loan_term)
        
        # Risk adjustment factor (higher risk score = lower rate adjustment)
        risk_adjustment = 0
        
        if risk_score >= 90:
            risk_adjustment = -0.5  # Excellent risk profile
        elif risk_score >= 80:
            risk_adjustment = -0.25  # Very good risk profile
        elif risk_score >= 70:
            risk_adjustment = 0  # Good risk profile
        elif risk_score >= 60:
            risk_adjustment = 0.25  # Moderate risk profile
        elif risk_score >= 50:
            risk_adjustment = 0.5  # Higher risk profile
        else:
            risk_adjustment = 0.75  # Significant risk profile
        
        # Final recommended rate
        recommended_rate = base_rate + risk_adjustment
        
        return round(recommended_rate, 2)
    
    def _get_base_rate(self, loan_type: str, loan_term: int) -> float:
        """
        Get base interest rate for a given loan type and term.
        
        Args:
            loan_type: Type of loan (CONVENTIONAL, FHA, VA, etc.)
            loan_term: Loan term in years
            
        Returns:
            Float representing base interest rate
        """
        # These rates would typically come from a current rate service
        # Using fictional example rates for demonstration
        if loan_type == "CONVENTIONAL":
            return 5.5 if loan_term == 30 else 5.0
        elif loan_type == "FHA":
            return 5.75 if loan_term == 30 else 5.25
        elif loan_type == "VA":
            return 5.25 if loan_term == 30 else 4.75
        else:
            return 6.0  # Default rate for other loan types
    
    async def _calculate_max_loan_amount(self, application_data: Dict[str, Any],
                                        document_analysis: Dict[str, Any],
                                        financial_ratios: Dict[str, Any]) -> float:
        """
        Calculate maximum loan amount based on income, debt, and property value.
        
        Args:
            application_data: Core application data
            document_analysis: Results from document analysis
            financial_ratios: Calculated financial ratios
            
        Returns:
            Float representing maximum loan amount
        """
        # Extract needed data
        loan_type = application_data.get("loan_type", "CONVENTIONAL")
        loan_term = application_data.get("loan_term_years", 30)
        interest_rate = application_data.get("interest_rate", self._get_base_rate(loan_type, loan_term))
        
        # Get property value from appraisal
        doc_results = document_analysis.get("document_results", {})
        property_data = doc_results.get("PROPERTY_APPRAISAL", {})
        property_value = property_data.get("property_value", 0)
        
        # Get monthly income
        monthly_income = financial_ratios.get("monthly_income", 0)
        monthly_debt_payments = financial_ratios.get("monthly_debt_payments", 0)
        
        # Get thresholds based on loan type
        thresholds = self._get_threshold_by_loan_type(loan_type)
        
        # Calculate max loan amount based on income (DTI)
        max_dti = thresholds["max_dti"]
        available_income = monthly_income * max_dti - monthly_debt_payments
        
        # Make sure we have positive available income
        if available_income <= 0:
            return 0
        
        # Calculate maximum monthly payment
        max_monthly_payment = available_income
        
        # Calculate maximum loan amount based on payment
        r = interest_rate / 100 / 12  # Monthly interest rate
        n = loan_term * 12  # Number of payments
        
        # Use present value of annuity formula: PV = PMT * ((1 - (1 + r)^-n) / r)
        max_loan_by_income = max_monthly_payment * ((1 - (1 + r) ** -n) / r) if r > 0 else max_monthly_payment * n
        
        # Calculate max loan amount based on property value (LTV)
        max_ltv = thresholds["max_ltv"]
        max_loan_by_property = property_value * max_ltv
        
        # Return the lower of the two limits
        return min(max_loan_by_income, max_loan_by_property)
    
    async def _generate_decision_explanation(self, application_data: Dict[str, Any],
                                           document_analysis: Dict[str, Any],
                                           financial_ratios: Dict[str, Any],
                                           criteria_evaluation: Dict[str, Dict[str, Any]],
                                           approval_result: Dict[str, Any]) -> str:
        """
        Generate human-readable explanation for the underwriting decision.
        
        Args:
            application_data: Core application data
            document_analysis: Results from document analysis
            financial_ratios: Calculated financial ratios
            criteria_evaluation: Results of criteria evaluation
            approval_result: Approval decision and details
            
        Returns:
            String with explanation of the decision
        """
        self.log_processing_step("Generating decision explanation")
        
        # Use semantic kernel to generate explanation
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
            
            # Fallback to simple explanation if semantic kernel fails
            if approval_result.get("is_approved", False):
                return "Your application has been approved based on our evaluation of your financial information."
            else:
                failed_criteria = approval_result.get("decision_factors", {}).get("failed_criteria", [])
                if failed_criteria:
                    return f"Your application was not approved due to the following: {', '.join(failed_criteria)}"
                else:
                    return "Your application was not approved based on our evaluation of your financial information."
    
    def _get_current_timestamp(self) -> str:
        """
        Get current timestamp in ISO format.
        
        Returns:
            String with current timestamp
        """
        from datetime import datetime
        return datetime.utcnow().isoformat()