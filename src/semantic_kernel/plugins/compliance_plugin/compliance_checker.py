# src/semantic_kernel/plugins/compliance_plugin/compliance_checker.py

import json
import datetime
from typing import Dict, List, Any, Optional, Tuple
import semantic_kernel as sk
from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter

from utils.logging_utils import get_logger

logger = get_logger("semantic_kernel.plugins.compliance")

class ComplianceCheckerPlugin:
    """
    Plugin for checking mortgage applications against regulatory requirements.
    Provides functions for validating compliance with lending regulations,
    fair lending requirements, and disclosure obligations.
    """
    
    def __init__(self, kernel: Optional[sk.Kernel] = None):
        """
        Initialize the compliance checker plugin.
        
        Args:
            kernel: Optional Semantic Kernel instance
        """
        self.kernel = kernel
        self.logger = logger
        
        # Load regulation definitions
        self.regulations = self._load_regulations()
    
    def _load_regulations(self) -> Dict[str, Any]:
        """Load regulation definitions for compliance checking."""
        # In a production system, these would be loaded from a database or API
        # For now, we'll hardcode some key regulations for the MVP
        return {
            "TILA_RESPA": {
                "name": "TILA-RESPA Integrated Disclosure Rule",
                "description": "Requires lenders to provide loan estimates and closing disclosures.",
                "requirements": [
                    "Loan Estimate must be provided within 3 business days of application",
                    "Closing Disclosure must be provided at least 3 business days before closing",
                    "APR must be accurately disclosed within tolerance limits"
                ]
            },
            "ATR_QM": {
                "name": "Ability-to-Repay/Qualified Mortgage Rule",
                "description": "Requires lenders to verify borrower's ability to repay mortgage loans.",
                "requirements": [
                    "Verify income and assets used to qualify for the loan",
                    "Debt-to-income ratio generally cannot exceed 43% for Qualified Mortgages",
                    "Points and fees cannot exceed 3% of the loan amount for most loans"
                ]
            },
            "ECOA": {
                "name": "Equal Credit Opportunity Act",
                "description": "Prohibits discrimination in credit transactions.",
                "requirements": [
                    "Cannot discriminate based on race, color, religion, national origin, sex, marital status, age, or public assistance status",
                    "Must provide specific reasons for credit denial",
                    "Must consider income from alimony, child support, or separate maintenance payments"
                ]
            },
            "FHA": {
                "name": "Fair Housing Act",
                "description": "Prohibits discrimination in housing-related transactions.",
                "requirements": [
                    "Cannot discriminate based on race, color, national origin, religion, sex, familial status, or disability",
                    "Must provide reasonable accommodations for persons with disabilities",
                    "Cannot engage in steering or redlining practices"
                ]
            },
            "HMDA": {
                "name": "Home Mortgage Disclosure Act",
                "description": "Requires collection and reporting of mortgage lending data.",
                "requirements": [
                    "Must collect demographic information on mortgage applicants",
                    "Must report lending activity data annually",
                    "Must maintain records for monitoring and examination"
                ]
            }
        }
    
    @sk_function(
        description="Check mortgage application for Ability-to-Repay compliance",
        name="checkAbilityToRepay"
    )
    @sk_function_context_parameter(
        name="application_data",
        description="JSON string containing the mortgage application data"
    )
    def check_ability_to_repay(self, context: sk.SKContext) -> str:
        """
        Check mortgage application for compliance with Ability-to-Repay (ATR) requirements.
        
        Args:
            context: Semantic Kernel context with application data
            
        Returns:
            JSON string with ATR compliance results
        """
        application_data = json.loads(context["application_data"])
        
        # Extract key data for ATR evaluation
        loan_amount = self._extract_loan_amount(application_data)
        loan_term_years = self._extract_loan_term(application_data)
        interest_rate = self._extract_interest_rate(application_data)
        monthly_income = self._extract_monthly_income(application_data)
        monthly_debts = self._extract_monthly_debts(application_data)
        
        # Calculate DTI
        if monthly_income > 0:
            dti_ratio = (monthly_debts / monthly_income) * 100
        else:
            dti_ratio = 100  # Cannot calculate, default to maximum
        
        # Calculate monthly payment (P&I only)
        monthly_payment = self._calculate_monthly_payment(loan_amount, interest_rate, loan_term_years)
        
        # Add estimated taxes, insurance, and other housing expenses
        property_value = self._extract_property_value(application_data)
        tax_insurance = property_value * 0.015 / 12  # Rough estimate: 1.5% of property value annually
        total_housing_payment = monthly_payment + tax_insurance
        
        # Calculate housing ratio (Front-end DTI)
        if monthly_income > 0:
            housing_ratio = (total_housing_payment / monthly_income) * 100
        else:
            housing_ratio = 100  # Cannot calculate, default to maximum
        
        # Check verification of income and assets
        income_verified = self._extract_income_verified(application_data)
        assets_verified = self._extract_assets_verified(application_data)
        employment_verified = self._extract_employment_verified(application_data)
        
        # Check if loan is a Qualified Mortgage (QM)
        # For the MVP, we'll use a simplified check
        is_qm = self._is_qualified_mortgage(application_data, dti_ratio)
        
        # Prepare compliance findings
        findings = []
        compliance_issues = []
        
        # Check income verification
        if income_verified:
            findings.append("Income has been appropriately verified")
        else:
            compliance_issues.append("Income verification is required for ATR compliance")
        
        # Check employment verification
        if employment_verified:
            findings.append("Employment has been appropriately verified")
        else:
            compliance_issues.append("Employment verification is required for ATR compliance")
        
        # Check assets verification if applicable
        if assets_verified:
            findings.append("Assets have been appropriately verified")
        
        # Check DTI ratio
        if is_qm and dti_ratio > 43:
            compliance_issues.append("DTI exceeds 43%, which is generally the maximum for a Qualified Mortgage")
        elif dti_ratio > 50:
            compliance_issues.append("DTI exceeds 50%, making ability to repay questionable")
        else:
            findings.append(f"DTI ratio of {dti_ratio:.1f}% is within acceptable limits")
        
        # Check housing ratio
        if housing_ratio > 31:
            findings.append(f"Housing ratio of {housing_ratio:.1f}% exceeds 31% guideline, but may be acceptable with compensating factors")
        else:
            findings.append(f"Housing ratio of {housing_ratio:.1f}% is within acceptable limits")
        
        # Compile results
        compliance_status = "Compliant" if not compliance_issues else "Non-Compliant"
        
        result = {
            "regulation": "Ability-to-Repay (ATR)",
            "compliance_status": compliance_status,
            "compliance_issues": compliance_issues,
            "findings": findings,
            "key_metrics": {
                "dti_ratio": round(dti_ratio, 2),
                "housing_ratio": round(housing_ratio, 2),
                "monthly_payment": round(monthly_payment, 2),
                "total_housing_payment": round(total_housing_payment, 2)
            },
            "verification_status": {
                "income_verified": income_verified,
                "employment_verified": employment_verified,
                "assets_verified": assets_verified
            },
            "is_qualified_mortgage": is_qm,
            "required_actions": []
        }
        
        # Add required actions based on compliance issues
        if not income_verified:
            result["required_actions"].append("Verify applicant income with appropriate documentation")
        
        if not employment_verified:
            result["required_actions"].append("Verify applicant employment with appropriate documentation")
        
        if not assets_verified and self._extract_down_payment(application_data) > 0:
            result["required_actions"].append("Verify assets for down payment with appropriate documentation")
        
        if dti_ratio > 43 and is_qm:
            result["required_actions"].append("Review loan for non-QM status or identify compensating factors")
        
        return json.dumps(result, indent=2)
    
    @sk_function(
        description="Check mortgage application for fair lending compliance",
        name="checkFairLending"
    )
    @sk_function_context_parameter(
        name="application_data",
        description="JSON string containing the mortgage application data"
    )
    def check_fair_lending(self, context: sk.SKContext) -> str:
        """
        Check mortgage application for compliance with fair lending requirements.
        
        Args:
            context: Semantic Kernel context with application data
            
        Returns:
            JSON string with fair lending compliance results
        """
        application_data = json.loads(context["application_data"])
        
        # Extract decision-related data
        decision = self._extract_decision(application_data)
        decision_factors = self._extract_decision_factors(application_data)
        
        # Extract demographic data (if available)
        # Note: This would be used for aggregate analysis only, not individual decisions
        demographics = {
            "race": self._extract_race(application_data),
            "ethnicity": self._extract_ethnicity(application_data),
            "gender": self._extract_gender(application_data),
            "age": self._extract_age(application_data),
            "marital_status": self._extract_marital_status(application_data)
        }
        
        # Extract application data
        credit_score = self._extract_credit_score(application_data)
        income = self._extract_monthly_income(application_data) * 12  # Annual income
        dti_ratio = self._extract_dti_ratio(application_data)
        ltv_ratio = self._extract_ltv_ratio(application_data)
        loan_amount = self._extract_loan_amount(application_data)
        property_type = self._extract_property_type(application_data)
        property_location = self._extract_property_location(application_data)
        
        # Prepare compliance findings
        findings = []
        compliance_issues = []
        
        # Check for prohibited bases
        if "prohibited_basis" in decision_factors:
            compliance_issues.append("Decision factors include prohibited basis characteristics")
        
        # Check for potential disparate treatment indicators
        if decision == "Denied" and credit_score >= 680 and dti_ratio <= 43 and ltv_ratio <= 80:
            findings.append("Application was denied despite strong credit indicators, review for consistency")
        
        # Check for potential redlining indicators
        if property_location and "high_minority_area" in property_location and decision == "Denied":
            findings.append("Application was for property in high-minority area, review for potential redlining")
        
        # Check for appropriate consideration of income
        if "alimony" in application_data or "child_support" in application_data or "separate_maintenance" in application_data:
            if "income_not_considered" in decision_factors:
                compliance_issues.append("Failure to consider alimony, child support, or separate maintenance income")
            else:
                findings.append("Protected income sources appropriately considered")
        
        # Check for denial notification
        if decision == "Denied":
            if "adverse_action_notice" not in application_data or not application_data.get("adverse_action_notice"):
                compliance_issues.append("Adverse action notice required for denied application")
            elif "denial_reasons" not in application_data or not application_data.get("denial_reasons"):
                compliance_issues.append("Specific denial reasons must be provided in adverse action notice")
            else:
                findings.append("Adverse action notice with specific reasons provided")
        
        # Compile results
        compliance_status = "Compliant" if not compliance_issues else "Non-Compliant"
        
        result = {
            "regulation": "Fair Lending (ECOA & FHA)",
            "compliance_status": compliance_status,
            "compliance_issues": compliance_issues,
            "findings": findings,
            "key_demographics": {
                "demographic_data_collected": any(demographics.values())
            },
            "decision_indicators": {
                "decision": decision,
                "credit_score": credit_score,
                "income": round(income, 2),
                "dti_ratio": round(dti_ratio, 2),
                "ltv_ratio": round(ltv_ratio, 2)
            },
            "required_actions": []
        }
        
        # Add required actions based on compliance issues
        if "prohibited_basis" in decision_factors:
            result["required_actions"].append("Remove prohibited basis characteristics from decision factors")
        
        if decision == "Denied" and "adverse_action_notice" not in application_data:
            result["required_actions"].append("Provide adverse action notice with specific denial reasons")
        
        if decision == "Denied" and credit_score >= 680 and dti_ratio <= 43 and ltv_ratio <= 80:
            result["required_actions"].append("Document non-discriminatory reason for denial despite strong indicators")
        
        return json.dumps(result, indent=2)
    
    @sk_function(
        description="Check mortgage application for disclosure compliance",
        name="checkDisclosureCompliance"
    )
    @sk_function_context_parameter(
        name="application_data",
        description="JSON string containing the mortgage application data"
    )
    def check_disclosure_compliance(self, context: sk.SKContext) -> str:
        """
        Check mortgage application for compliance with disclosure requirements.
        
        Args:
            context: Semantic Kernel context with application data
            
        Returns:
            JSON string with disclosure compliance results
        """
        application_data = json.loads(context["application_data"])
        
        # Extract application timeline data
        application_date = self._extract_application_date(application_data)
        loan_estimate_date = self._extract_loan_estimate_date(application_data)
        closing_disclosure_date = self._extract_closing_disclosure_date(application_data)
        closing_date = self._extract_closing_date(application_data)
        
        # Extract loan details
        loan_amount = self._extract_loan_amount(application_data)
        disclosed_apr = self._extract_disclosed_apr(application_data)
        actual_apr = self._extract_actual_apr(application_data)
        disclosed_fees = self._extract_disclosed_fees(application_data)
        actual_fees = self._extract_actual_fees(application_data)
        
        # Prepare compliance findings
        findings = []
        compliance_issues = []
        
        # Check loan estimate timing
        if application_date and loan_estimate_date:
            business_days = self._calculate_business_days(application_date, loan_estimate_date)
            if business_days <= 3:
                findings.append(f"Loan Estimate provided within {business_days} business days of application")
            else:
                compliance_issues.append(f"Loan Estimate provided after {business_days} business days (exceeds 3 business day requirement)")
        elif application_date and not loan_estimate_date:
            compliance_issues.append("No Loan Estimate date recorded")
        
        # Check closing disclosure timing
        if closing_disclosure_date and closing_date:
            business_days = self._calculate_business_days(closing_disclosure_date, closing_date)
            if business_days >= 3:
                findings.append(f"Closing Disclosure provided {business_days} business days before closing")
            else:
                compliance_issues.append(f"Closing Disclosure provided only {business_days} business days before closing (below 3 business day requirement)")
        elif closing_date and not closing_disclosure_date:
            compliance_issues.append("No Closing Disclosure date recorded")
        
        # Check APR accuracy
        if disclosed_apr is not None and actual_apr is not None:
            apr_difference = abs(disclosed_apr - actual_apr)
            
            # APR tolerance is 1/8 of 1% (0.125%) for fixed-rate loans
            # and 1/4 of 1% (0.25%) for adjustable-rate loans
            # Simplified check for MVP
            is_adjustable = self._is_adjustable_rate(application_data)
            tolerance = 0.25 if is_adjustable else 0.125
            
            if apr_difference <= tolerance:
                findings.append(f"APR disclosed within tolerance ({apr_difference:.3f}%)")
            else:
                compliance_issues.append(f"APR disclosure exceeds tolerance: disclosed {disclosed_apr:.3f}%, actual {actual_apr:.3f}%")
        
        # Check fee accuracy
        if disclosed_fees is not None and actual_fees is not None:
            fee_difference = actual_fees - disclosed_fees
            
            # Zero tolerance for certain fees, 10% cumulative tolerance for others
            # Simplified check for MVP
            if fee_difference <= 0:
                findings.append("Actual fees do not exceed disclosed fees")
            elif fee_difference / disclosed_fees <= 0.1:
                findings.append(f"Fee increase ({fee_difference:.2f}) within 10% tolerance")
            else:
                compliance_issues.append(f"Fee increase ({fee_difference:.2f}) exceeds tolerance")
        
        # HMDA reporting check
        if self._requires_hmda_reporting(application_data):
            if not self._has_hmda_data(application_data):
                compliance_issues.append("HMDA reportable loan missing required demographic data")
            else:
                findings.append("HMDA data properly collected")
        
        # Compile results
        compliance_status = "Compliant" if not compliance_issues else "Non-Compliant"
        
        result = {
            "regulation": "Disclosure Requirements (TILA-RESPA)",
            "compliance_status": compliance_status,
            "compliance_issues": compliance_issues,
            "findings": findings,
            "key_dates": {
                "application_date": application_date,
                "loan_estimate_date": loan_estimate_date,
                "closing_disclosure_date": closing_disclosure_date,
                "closing_date": closing_date
            },
            "disclosure_accuracy": {
                "apr_disclosed": disclosed_apr,
                "apr_actual": actual_apr,
                "fees_disclosed": disclosed_fees,
                "fees_actual": actual_fees
            },
            "required_actions": []
        }
        
        # Add required actions based on compliance issues
        if "No Loan Estimate date recorded" in compliance_issues:
            result["required_actions"].append("Document Loan Estimate delivery date")
        
        if "Loan Estimate provided after" in str(compliance_issues):
            result["required_actions"].append("Ensure Loan Estimate is provided within 3 business days of application")
        
        if "No Closing Disclosure date recorded" in compliance_issues:
            result["required_actions"].append("Document Closing Disclosure delivery date")
        
        if "Closing Disclosure provided only" in str(compliance_issues):
            result["required_actions"].append("Ensure Closing Disclosure is provided at least 3 business days before closing")
        
        if "APR disclosure exceeds tolerance" in str(compliance_issues):
            result["required_actions"].append("Redisclose APR and potentially restart waiting period")
        
        if "Fee increase" in str(compliance_issues):
            result["required_actions"].append("Justify fee increases or redisclose with accurate fees")
        
        if "HMDA reportable loan missing required demographic data" in compliance_issues:
            result["required_actions"].append("Collect and record required HMDA demographic data")
        
        return json.dumps(result, indent=2)
    
    @sk_function(
        description="Perform comprehensive compliance check on mortgage application",
        name="performComprehensiveCheck"
    )
    @sk_function_context_parameter(
        name="application_data",
        description="JSON string containing the mortgage application data"
    )
    def perform_comprehensive_check(self, context: sk.SKContext) -> str:
        """
        Perform a comprehensive compliance check covering multiple regulations.
        
        Args:
            context: Semantic Kernel context with application data
            
        Returns:
            JSON string with comprehensive compliance results
        """
        application_data = json.loads(context["application_data"])
        
        # Check all major compliance areas
        atr_context = sk.SKContext({"application_data": context["application_data"]})
        fair_lending_context = sk.SKContext({"application_data": context["application_data"]})
        disclosure_context = sk.SKContext({"application_data": context["application_data"]})
        
        atr_result = json.loads(self.check_ability_to_repay(atr_context))
        fair_lending_result = json.loads(self.check_fair_lending(fair_lending_context))
        disclosure_result = json.loads(self.check_disclosure_compliance(disclosure_context))
        
        # Compile comprehensive results
        all_compliance_issues = (
            atr_result.get("compliance_issues", []) +
            fair_lending_result.get("compliance_issues", []) +
            disclosure_result.get("compliance_issues", [])
        )
        
        all_required_actions = (
            atr_result.get("required_actions", []) +
            fair_lending_result.get("required_actions", []) +
            disclosure_result.get("required_actions", [])
        )
        
        # Determine overall compliance status
        if all_compliance_issues:
            overall_status = "Non-Compliant"
        else:
            overall_status = "Compliant"
        
        # Calculate compliance risk level
        critical_issues = [issue for issue in all_compliance_issues if "prohibited" in issue.lower() or "exceeds" in issue.lower()]
        if critical_issues:
            risk_level = "High"
        elif all_compliance_issues:
            risk_level = "Medium"
        else:
            risk_level = "Low"
        
        # Compile results
        result = {
            "overall_compliance_status": overall_status,
            "risk_level": risk_level,
            "compliance_summary": {
                "total_issues": len(all_compliance_issues),
                "total_required_actions": len(all_required_actions),
                "atr_status": atr_result.get("compliance_status"),
                "fair_lending_status": fair_lending_result.get("compliance_status"),
                "disclosure_status": disclosure_result.get("compliance_status")
            },
            "compliance_issues": all_compliance_issues,
            "required_actions": all_required_actions,
            "detailed_results": {
                "ability_to_repay": atr_result,
                "fair_lending": fair_lending_result,
                "disclosures": disclosure_result
            }
        }
        
        return json.dumps(result, indent=2)
    
    @sk_function(
        description="Generate regulatory compliance checklist for a mortgage application",
        name="generateComplianceChecklist"
    )
    @sk_function_context_parameter(
        name="loan_type",
        description="Type of mortgage loan (e.g., Conventional, FHA, VA)"
    )
    def generate_compliance_checklist(self, context: sk.SKContext) -> str:
        """
        Generate a compliance checklist for a specific loan type.
        
        Args:
            context: Semantic Kernel context with loan type
            
        Returns:
            Text checklist of compliance requirements
        """
        loan_type = context["loan_type"]
        
        # Base checklist items for all loan types
        checklist = [
            "Verify borrower's identity and legal status",
            "Collect and verify income documentation",
            "Collect and verify asset documentation",
            "Verify employment history",
            "Check credit report and credit score",
            "Calculate debt-to-income ratio",
            "Calculate loan-to-value ratio",
            "Verify property value with appraisal",
            "Check property eligibility",
            "Provide Loan Estimate within 3 business days of application",
            "Collect HMDA demographic information",
            "Document rate lock agreement if applicable",
            "Provide list of homeownership counseling organizations",
            "Provide Closing Disclosure at least 3 business days before closing",
            "Perform anti-money laundering check",
            "Check OFAC sanctions list",
            "Document QM/ATR compliance analysis"
        ]
        
        # Add loan-type specific items
        if loan_type.lower() == "conventional":
            checklist.extend([
                "Verify borrower has required down payment",
                "Document private mortgage insurance if LTV > 80%",
                "Verify loan amount is within conforming limits",
                "Check property type is eligible for conventional financing",
                "Verify borrower meets credit score requirements (typically 620+)"
            ])
        elif loan_type.lower() == "fha":
            checklist.extend([
                "Verify borrower meets FHA credit score requirements (typically 500+)",
                "Verify property meets FHA minimum property standards",
                "Document upfront and annual mortgage insurance premium",
                "Verify loan amount is within FHA loan limits",
                "Check borrower has minimum 3.5% down payment (or 10% if credit score 500-579)",
                "Verify property will be primary residence"
            ])
        elif loan_type.lower() == "va":
            checklist.extend([
                "Verify borrower's VA eligibility with Certificate of Eligibility",
                "Verify property meets VA minimum property requirements",
                "Calculate VA funding fee and document exemptions if applicable",
                "Verify loan amount is within VA program limits",
                "Verify veteran's residual income meets VA requirements",
                "Document any previous VA loan usage"
            ])
        elif loan_type.lower() == "usda":
            checklist.extend([
                "Verify property is in USDA eligible rural area",
                "Verify borrower income is within USDA limits",
                "Document USDA guarantee fee",
                "Verify borrower meets credit score requirements (typically 640+)",
                "Verify property will be primary residence",
                "Document that borrower does not own adequate housing"
            ])
        elif loan_type.lower() == "jumbo":
            checklist.extend([
                "Verify loan amount exceeds conforming limits",
                "Document higher down payment requirement (typically 10-20%)",
                "Verify borrower meets higher credit score requirements (typically 700+)",
                "Document substantial cash reserves requirement",
                "Verify property is high-quality and marketable",
                "Perform additional appraisal due diligence (possibly multiple appraisals)"
            ])
        
        # Format the checklist
        checklist_text = f"# Compliance Checklist for {loan_type} Loan\n\n"
        
        for i, item in enumerate(checklist, 1):
            checklist_text += f"{i}. {item}\n"
        
        checklist_text += f"\nNote: This checklist represents common compliance requirements for {loan_type} loans. "
        checklist_text += "Additional requirements may apply based on specific loan characteristics and local regulations."
        
        return checklist_text
    
    # Helper methods
    def _calculate_monthly_payment(self, loan_amount: float, annual_interest_rate: float, loan_term_years: int) -> float:
        """Calculate the monthly mortgage payment."""
        # Convert annual rate to monthly rate
        monthly_rate = annual_interest_rate / 12
        
        # Convert years to number of monthly payments
        num_payments = loan_term_years * 12
        
        # Handle edge case for zero interest rate
        if monthly_rate == 0:
            return loan_amount / num_payments
            
        # Calculate monthly payment using the mortgage formula
        payment = loan_amount * (monthly_rate * pow(1 + monthly_rate, num_payments)) / (pow(1 + monthly_rate, num_payments) - 1)
        
        return payment
    
    def _extract_loan_amount(self, data: Dict[str, Any]) -> float:
        """Extract loan amount from application data."""
        # Try different possible paths to loan amount
        if "loan_amount" in data:
            return float(data["loan_amount"])
        elif "loan_details" in data and "loan_amount" in data["loan_details"]:
            return float(data["loan_details"]["loan_amount"])
        else:
            return 0.0
    
    def _extract_property_value(self, data: Dict[str, Any]) -> float:
        """Extract property value from application data."""
        # Try different possible paths to property value
        if "property_value" in data:
            return float(data["property_value"])
        elif "property_info" in data and "estimated_value" in data["property_info"]:
            return float(data["property_info"]["estimated_value"])
        else:
            return 0.0
    
    def _extract_monthly_income(self, data: Dict[str, Any]) -> float:
        """Extract monthly income from application data."""
        # Try different possible paths to monthly income
        if "monthly_income" in data:
            return float(data["monthly_income"])
        elif "primary_applicant" in data and "annual_income" in data["primary_applicant"]:
            # Convert annual income to monthly
            return float(data["primary_applicant"]["annual_income"]) / 12
        else:
            return 0.0
    
    def _extract_monthly_debts(self, data: Dict[str, Any]) -> float:
        """Extract monthly debts from application data."""
        # Try different possible paths to monthly debts
        if "monthly_debts" in data:
            return float(data["monthly_debts"])
        elif "monthly_debt" in data:
            return float(data["monthly_debt"])
        elif "financial_analysis" in data and "debt_to_income_ratio" in data["financial_analysis"]:
            # If we have DTI and income, calculate debts
            dti = float(data["financial_analysis"]["debt_to_income_ratio"])
            monthly_income = self._extract_monthly_income(data)
            return (dti / 100) * monthly_income
        else:
            return 0.0
    
    def _extract_loan_term(self, data: Dict[str, Any]) -> int:
        """Extract loan term in years from application data."""
        # Try different possible paths to loan term
        if "loan_term_years" in data:
            return int(data["loan_term_years"])
        elif "loan_details" in data and "loan_term_years" in data["loan_details"]:
            return int(data["loan_details"]["loan_term_years"])
        else:
            return 30  # Default to 30-year term
    
    def _extract_interest_rate(self, data: Dict[str, Any]) -> float:
        """Extract interest rate from application data."""
        # Try different possible paths to interest rate
        if "interest_rate" in data:
            return float(data["interest_rate"])
        elif "loan_details" in data and "interest_rate" in data["loan_details"]:
            return float(data["loan_details"]["interest_rate"])
        else:
            return 0.065  # Default to 6.5%
    
    def _extract_down_payment(self, data: Dict[str, Any]) -> float:
        """Extract down payment from application data."""
        # Try different possible paths to down payment
        if "down_payment" in data:
            return float(data["down_payment"])
        elif "loan_details" in data and "down_payment" in data["loan_details"]:
            return float(data["loan_details"]["down_payment"])
        else:
            # Calculate from loan amount and property value
            property_value = self._extract_property_value(data)
            loan_amount = self._extract_loan_amount(data)
            if property_value > 0 and loan_amount > 0:
                return property_value - loan_amount
            return 0.0
    
    def _extract_credit_score(self, data: Dict[str, Any]) -> int:
        """Extract credit score from application data."""
        # Try different possible paths to credit score
        if "credit_score" in data:
            return int(data["credit_score"])
        elif "primary_applicant" in data and "credit_score" in data["primary_applicant"]:
            return int(data["primary_applicant"]["credit_score"])
        else:
            return 0
    
    def _extract_income_verified(self, data: Dict[str, Any]) -> bool:
        """Extract income verification status from application data."""
        # Try different possible paths to income verification
        if "income_verified" in data:
            return bool(data["income_verified"])
        elif "verification" in data and "income_verified" in data["verification"]:
            return bool(data["verification"]["income_verified"])
        else:
            return False
    
    def _extract_assets_verified(self, data: Dict[str, Any]) -> bool:
        """Extract assets verification status from application data."""
        # Try different possible paths to assets verification
        if "assets_verified" in data:
            return bool(data["assets_verified"])
        elif "verification" in data and "assets_verified" in data["verification"]:
            return bool(data["verification"]["assets_verified"])
        else:
            return False
    
    def _extract_employment_verified(self, data: Dict[str, Any]) -> bool:
        """Extract employment verification status from application data."""
        # Try different possible paths to employment verification
        if "employment_verified" in data:
            return bool(data["employment_verified"])
        elif "verification" in data and "employment_verified" in data["verification"]:
            return bool(data["verification"]["employment_verified"])
        else:
            return False
    
    def _is_qualified_mortgage(self, data: Dict[str, Any], dti_ratio: float) -> bool:
        """Determine if the loan is a Qualified Mortgage (QM)."""
        # Simplified QM determination for MVP
        # In reality, this would involve more factors and considerations
        
        # Check for basic QM requirements
        if dti_ratio > 43:
            return False
            
        loan_amount = self._extract_loan_amount(data)
        points_and_fees = data.get("points_and_fees", 0)
        
        # Check points and fees cap (typically 3% for loans > $100k)
        if loan_amount > 100000 and points_and_fees / loan_amount > 0.03:
            return False
            
        # Check for negative amortization, interest-only, balloon payment
        if data.get("negative_amortization", False) or data.get("interest_only", False) or data.get("balloon_payment", False):
            return False
            
        term_years = self._extract_loan_term(data)
        if term_years > 30:
            return False
            
        # If passes all basic checks, consider it a QM
        return True
    
    def _extract_decision(self, data: Dict[str, Any]) -> str:
        """Extract loan decision from application data."""
        # Try different possible paths to decision
        if "decision" in data:
            return str(data["decision"])
        elif "loan_decision" in data:
            return str(data["loan_decision"])
        elif "status" in data:
            status = str(data["status"]).lower()
            if status in ["approved", "conditionally approved"]:
                return "Approved"
            elif status in ["denied", "declined"]:
                return "Denied"
            else:
                return "Pending"
        else:
            return "Unknown"
    
    def _extract_decision_factors(self, data: Dict[str, Any]) -> List[str]:
        """Extract decision factors from application data."""
        # Try different possible paths to decision factors
        if "decision_factors" in data:
            return data["decision_factors"]
        elif "denial_reasons" in data:
            return data["denial_reasons"]
        else:
            return []
    
    def _extract_race(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract race from application data."""
        # Try different possible paths to race
        if "race" in data:
            return data["race"]
        elif "primary_applicant" in data and "race" in data["primary_applicant"]:
            return data["primary_applicant"]["race"]
        elif "demographics" in data and "race" in data["demographics"]:
            return data["demographics"]["race"]
        else:
            return None
    
    def _extract_ethnicity(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract ethnicity from application data."""
        # Try different possible paths to ethnicity
        if "ethnicity" in data:
            return data["ethnicity"]
        elif "primary_applicant" in data and "ethnicity" in data["primary_applicant"]:
            return data["primary_applicant"]["ethnicity"]
        elif "demographics" in data and "ethnicity" in data["demographics"]:
            return data["demographics"]["ethnicity"]
        else:
            return None
    
    def _extract_gender(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract gender from application data."""
        # Try different possible paths to gender
        if "gender" in data:
            return data["gender"]
        elif "primary_applicant" in data and "gender" in data["primary_applicant"]:
            return data["primary_applicant"]["gender"]
        elif "demographics" in data and "gender" in data["demographics"]:
            return data["demographics"]["gender"]
        elif "primary_applicant" in data and "sex" in data["primary_applicant"]:
            return data["primary_applicant"]["sex"]
        else:
            return None
    
    def _extract_age(self, data: Dict[str, Any]) -> Optional[int]:
        """Extract age from application data."""
        # Try different possible paths to age
        if "age" in data:
            return int(data["age"])
        elif "primary_applicant" in data and "age" in data["primary_applicant"]:
            return int(data["primary_applicant"]["age"])
        elif "demographics" in data and "age" in data["demographics"]:
            return int(data["demographics"]["age"])
        elif "primary_applicant" in data and "date_of_birth" in data["primary_applicant"]:
            # Calculate age from date of birth
            dob = data["primary_applicant"]["date_of_birth"]
            try:
                # Simple calculation assuming date format MM/DD/YYYY
                parts = dob.split("/")
                birth_year = int(parts[2])
                current_year = datetime.datetime.now().year
                return current_year - birth_year
            except:
                return None
        else:
            return None
    
    def _extract_marital_status(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract marital status from application data."""
        # Try different possible paths to marital status
        if "marital_status" in data:
            return data["marital_status"]
        elif "primary_applicant" in data and "marital_status" in data["primary_applicant"]:
            return data["primary_applicant"]["marital_status"]
        elif "demographics" in data and "marital_status" in data["demographics"]:
            return# src/semantic_kernel/plugins/compliance_plugin/compliance_checker.py

import json
import datetime
from typing import Dict, List, Any, Optional, Tuple
import semantic_kernel as sk
from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter

from utils.logging_utils import get_logger

logger = get_logger("semantic_kernel.plugins.compliance")

class ComplianceCheckerPlugin:
    """
    Plugin for checking mortgage applications against regulatory requirements.
    Provides functions for validating compliance with lending regulations,
    fair lending requirements, and disclosure obligations.
    """
    
    def __init__(self, kernel: Optional[sk.Kernel] = None):
        """
        Initialize the compliance checker plugin.
        
        Args:
            kernel: Optional Semantic Kernel instance
        """
        self.kernel = kernel
        self.logger = logger
        
        # Load regulation definitions
        self.regulations = self._load_regulations()
    
    def _load_regulations(self) -> Dict[str, Any]:
        """Load regulation definitions for compliance checking."""
        # In a production system, these would be loaded from a database or API
        # For now, we'll hardcode some key regulations for the MVP
        return {
            "TILA_RESPA": {
                "name": "TILA-RESPA Integrated Disclosure Rule",
                "description": "Requires lenders to provide loan estimates and closing disclosures.",
                "requirements": [
                    "Loan Estimate must be provided within 3 business days of application",
                    "Closing Disclosure must be provided at least 3 business days before closing",
                    "APR must be accurately disclosed within tolerance limits"
                ]
            },
            "ATR_QM": {
                "name": "Ability-to-Repay/Qualified Mortgage Rule",
                "description": "Requires lenders to verify borrower's ability to repay mortgage loans.",
                "requirements": [
                    "Verify income and assets used to qualify for the loan",
                    "Debt-to-income ratio generally cannot exceed 43% for Qualified Mortgages",
                    "Points and fees cannot exceed 3% of the loan amount for most loans"
                ]
            },
            "ECOA": {
                "name": "Equal Credit Opportunity Act",
                "description": "Prohibits discrimination in credit transactions.",
                "requirements": [
                    "Cannot discriminate based on race, color, religion, national origin, sex, marital status, age, or public assistance status",
                    "Must provide specific reasons for credit denial",
                    "Must consider income from alimony, child support, or separate maintenance payments"
                ]
            },
            "FHA": {
                "name": "Fair Housing Act",
                "description": "Prohibits discrimination in housing-related transactions.",
                "requirements": [
                    "Cannot discriminate based on race, color, national origin, religion, sex, familial status, or disability",
                    "Must provide reasonable accommodations for persons with disabilities",
                    "Cannot engage in steering or redlining practices"
                ]
            },
            "HMDA": {
                "name": "Home Mortgage Disclosure Act",
                "description": "Requires collection and reporting of mortgage lending data.",
                "requirements": [
                    "Must collect demographic information on mortgage applicants",
                    "Must report lending activity data annually",
                    "Must maintain records for monitoring and examination"
                ]
            }
        }
    
    @sk_function(
        description="Check mortgage application for Ability-to-Repay compliance",
        name="checkAbilityToRepay"
    )
    @sk_function_context_parameter(
        name="application_data",
        description="JSON string containing the mortgage application data"
    )
    def check_ability_to_repay(self, context: sk.SKContext) -> str:
        """
        Check mortgage application for compliance with Ability-to-Repay (ATR) requirements.
        
        Args:
            context: Semantic Kernel context with application data
            
        Returns:
            JSON string with ATR compliance results
        """
        application_data = json.loads(context["application_data"])
        
        # Extract key data for ATR evaluation
        loan_amount = self._extract_loan_amount(application_data)
        loan_term_years = self._extract_loan_term(application_data)
        interest_rate = self._extract_interest_rate(application_data)
        monthly_income = self._extract_monthly_income(application_data)
        monthly_debts = self._extract_monthly_debts(application_data)
        
        # Calculate DTI
        if monthly_income > 0:
            dti_ratio = (monthly_debts / monthly_income) * 100
        else:
            dti_ratio = 100  # Cannot calculate, default to maximum
        
        # Calculate monthly payment (P&I only)
        monthly_payment = self._calculate_monthly_payment(loan_amount, interest_rate, loan_term_years)
        
        # Add estimated taxes, insurance, and other housing expenses
        property_value = self._extract_property_value(application_data)
        tax_insurance = property_value * 0.015 / 12  # Rough estimate: 1.5% of property value annually
        total_housing_payment = monthly_payment + tax_insurance
        
        # Calculate housing ratio (Front-end DTI)
        if monthly_income > 0:
            housing_ratio = (total_housing_payment / monthly_income) * 100
        else:
            housing_ratio = 100  # Cannot calculate, default to maximum
        
        # Check verification of income and assets
        income_verified = self._extract_income_verified(application_data)
        assets_verified = self._extract_assets_verified(application_data)
        employment_verified = self._extract_employment_verified(application_data)
        
        # Check if loan is a Qualified Mortgage (QM)
        # For the MVP, we'll use a simplified check
        is_qm = self._is_qualified_mortgage(application_data, dti_ratio)
        
        # Prepare compliance findings
        findings = []
        compliance_issues = []
        
        # Check income verification
        if income_verified:
            findings.append("Income has been appropriately verified")
        else:
            compliance_issues.append("Income verification is required for ATR compliance")
        
        # Check employment verification
        if employment_verified:
            findings.append("Employment has been appropriately verified")
        else:
            compliance_issues.append("Employment verification is required for ATR compliance")
        
        # Check assets verification if applicable
        if assets_verified:
            findings.append("Assets have been appropriately verified")
        
        # Check DTI ratio
        if is_qm and dti_ratio > 43:
            compliance_issues.append("DTI exceeds 43%, which is generally the maximum for a Qualified Mortgage")
        elif dti_ratio > 50:
            compliance_issues.append("DTI exceeds 50%, making ability to repay questionable")
        else:
            findings.append(f"DTI ratio of {dti_ratio:.1f}% is within acceptable limits")
        
        # Check housing ratio
        if housing_ratio > 31:
            findings.append(f"Housing ratio of {housing_ratio:.1f}% exceeds 31% guideline, but may be acceptable with compensating factors")
        else:
            findings.append(f"Housing ratio of {housing_ratio:.1f}% is within acceptable limits")
        
        # Compile results
        compliance_status = "Compliant" if not compliance_issues else "Non-Compliant"
        
        result = {
            "regulation": "Ability-to-Repay (ATR)",
            "compliance_status": compliance_status,
            "compliance_issues": compliance_issues,
            "findings": findings,
            "key_metrics": {
                "dti_ratio": round(dti
                                   