# src/semantic_kernel/plugins/underwriting_plugin/underwriting_evaluator.py

import json
import datetime
from typing import Dict, List, Any, Optional, Tuple
import src.semantic_kernel as sk

from src.utils.logging_utils import get_logger

logger = get_logger("semantic_kernel.plugins.underwriting")

class UnderwritingEvaluatorPlugin:
    """
    Plugin for evaluating mortgage loan applications.
    Provides functions for risk assessment, loan term calculation,
    and overall qualification determination.
    """
    
    def __init__(self, kernel: Optional[sk.Kernel] = None):
        """
        Initialize the underwriting evaluator plugin.
        
        Args:
            kernel: Optional Semantic Kernel instance
        """
        self.kernel = kernel
        self.logger = logger
    
    def calculate_dti(self, context: dict) -> str:
        """
        Calculate the debt-to-income ratio.
        
        Args:
            context: Dictionary with monthly income and debts
            
        Returns:
            DTI ratio as a percentage string
        """
        monthly_income = float(context["monthly_income"])
        monthly_debts = float(context["monthly_debts"])
        
        if monthly_income <= 0:
            return "Error: Monthly income must be greater than zero"
        
        dti_ratio = (monthly_debts / monthly_income) * 100
        return f"{dti_ratio:.2f}%"
    
    def calculate_ltv(self, context: dict) -> str:
        """
        Calculate the loan-to-value ratio for a mortgage application.
        
        Args:
            context: Dictionary with loan amount and property value
            
        Returns:
            LTV ratio as a percentage string
        """
        loan_amount = float(context["loan_amount"])
        property_value = float(context["property_value"])
        
        if property_value <= 0:
            return "Error: Property value must be greater than zero"
        
        ltv_ratio = (loan_amount / property_value) * 100
        return f"{ltv_ratio:.2f}%"
    
    def evaluate_conventional_loan(self, context: dict) -> str:
        """
        Evaluate a loan application against conventional mortgage guidelines.
        
        Args:
            context: Dictionary with application data
            
        Returns:
            JSON string with evaluation results
        """
        application_data = json.loads(context["application_data"])
        
        # Extract key application data
        loan_amount = self._extract_loan_amount(application_data)
        property_value = self._extract_property_value(application_data)
        monthly_income = self._extract_monthly_income(application_data)
        monthly_debts = self._extract_monthly_debts(application_data)
        credit_score = self._extract_credit_score(application_data)
        loan_term_years = self._extract_loan_term(application_data)
        down_payment = self._extract_down_payment(application_data)
        property_type = self._extract_property_type(application_data)
        is_first_time_homebuyer = self._extract_first_time_homebuyer(application_data)
        
        # Calculate key ratios
        if monthly_income > 0:
            dti_ratio = (monthly_debts / monthly_income) * 100
        else:
            dti_ratio = 100  # Unable to calculate, set to maximum
            
        if property_value > 0:
            ltv_ratio = (loan_amount / property_value) * 100
        else:
            ltv_ratio = 100  # Unable to calculate, set to maximum
            
        # Calculate front-end ratio (PITI / Income)
        # Estimate PITI (Principal, Interest, Taxes, Insurance)
        interest_rate = 0.065  # Assuming 6.5% interest rate if not provided
        monthly_payment = self._calculate_monthly_payment(loan_amount, interest_rate, loan_term_years)
        
        # Estimate taxes and insurance
        tax_and_insurance = property_value * 0.015 / 12  # Rough estimate: 1.5% of property value annually
        total_housing_payment = monthly_payment + tax_and_insurance
        
        if monthly_income > 0:
            frontend_ratio = (total_housing_payment / monthly_income) * 100
        else:
            frontend_ratio = 100  # Unable to calculate, set to maximum
        
        # Evaluate against conventional guidelines
        risk_factors = []
        strengths = []
        
        # Credit score evaluation
        if credit_score >= 740:
            strengths.append("Excellent credit score")
        elif credit_score >= 700:
            strengths.append("Good credit score")
        elif credit_score >= 660:
            strengths.append("Acceptable credit score")
        elif credit_score >= 620:
            risk_factors.append("Below average credit score")
        else:
            risk_factors.append("Poor credit score, below conventional minimum")
        
        # DTI evaluation
        if dti_ratio <= 36:
            strengths.append("Strong debt-to-income ratio")
        elif dti_ratio <= 43:
            strengths.append("Acceptable debt-to-income ratio")
        elif dti_ratio <= 50:
            risk_factors.append("High debt-to-income ratio")
        else:
            risk_factors.append("Debt-to-income ratio exceeds guidelines")
        
        # LTV evaluation
        if ltv_ratio <= 80:
            strengths.append("Strong loan-to-value ratio, no PMI required")
        elif ltv_ratio <= 95:
            risk_factors.append("Loan-to-value ratio requires PMI")
        elif ltv_ratio <= 97 and is_first_time_homebuyer:
            risk_factors.append("High loan-to-value ratio, eligible only for first-time homebuyer programs")
        else:
            risk_factors.append("Loan-to-value ratio exceeds conventional guidelines")
        
        # Front-end ratio evaluation
        if frontend_ratio <= 28:
            strengths.append("Strong housing expense ratio")
        elif frontend_ratio <= 36:
            strengths.append("Acceptable housing expense ratio")
        else:
            risk_factors.append("High housing expense ratio")
        
        # Property type evaluation
        if property_type.lower() in ["single_family", "single family", "primary residence"]:
            strengths.append("Standard property type")
        elif property_type.lower() in ["condo", "condominium"]:
            risk_factors.append("Condominium properties may require higher down payment")
        elif property_type.lower() in ["multi_family", "multi family", "2-4 units"]:
            risk_factors.append("Multi-family property requires additional rental income verification")
        
        # Overall qualification assessment
        qualified = True
        loan_recommendation = "Approve"
        
        # Disqualifying factors
        if credit_score < 620:
            qualified = False
            loan_recommendation = "Decline"
        
        if dti_ratio > 50:
            qualified = False
            loan_recommendation = "Decline"
        
        if ltv_ratio > 97:
            qualified = False
            loan_recommendation = "Decline"
        
        # Conditionally qualified
        if qualified and len(risk_factors) >= 3:
            loan_recommendation = "Refer to Underwriter"
        
        # Determine interest rate adjustment based on risk factors
        rate_adjustment = 0.0
        if credit_score < 700:
            rate_adjustment += 0.25
        if credit_score < 660:
            rate_adjustment += 0.25
        if dti_ratio > 43:
            rate_adjustment += 0.125
        if ltv_ratio > 90:
            rate_adjustment += 0.25
        
        # Compile evaluation results
        result = {
            "loan_type": "Conventional",
            "qualified": qualified,
            "loan_recommendation": loan_recommendation,
            "ratios": {
                "dti": round(dti_ratio, 2),
                "ltv": round(ltv_ratio, 2),
                "frontend": round(frontend_ratio, 2)
            },
            "risk_factors": risk_factors,
            "strengths": strengths,
            "estimated_rate": round(interest_rate + rate_adjustment, 3),
            "estimated_monthly_payment": round(total_housing_payment, 2),
            "conditions": []
        }
        
        # Add conditions based on risk factors
        if credit_score < 680 and credit_score >= 620:
            result["conditions"].append("Provide explanation for credit issues")
        
        if dti_ratio > 43 and dti_ratio <= 50:
            result["conditions"].append("Additional cash reserves required (2 months PITI)")
        
        if ltv_ratio > 80:
            result["conditions"].append("Private Mortgage Insurance required")
        
        return json.dumps(result, indent=2)
    
    def evaluate_fha_loan(self, context: dict) -> str:
        """
        Evaluate a loan application against FHA mortgage guidelines.
        
        Args:
            context: Dictionary with application data
            
        Returns:
            JSON string with evaluation results
        """
        application_data = json.loads(context["application_data"])
        
        # Extract key application data
        loan_amount = self._extract_loan_amount(application_data)
        property_value = self._extract_property_value(application_data)
        monthly_income = self._extract_monthly_income(application_data)
        monthly_debts = self._extract_monthly_debts(application_data)
        credit_score = self._extract_credit_score(application_data)
        loan_term_years = self._extract_loan_term(application_data)
        property_type = self._extract_property_type(application_data)
        
        # Calculate key ratios
        if monthly_income > 0:
            dti_ratio = (monthly_debts / monthly_income) * 100
        else:
            dti_ratio = 100  # Unable to calculate, set to maximum
            
        if property_value > 0:
            ltv_ratio = (loan_amount / property_value) * 100
        else:
            ltv_ratio = 100  # Unable to calculate, set to maximum
        
        # Calculate front-end ratio (PITI / Income)
        # Estimate PITI (Principal, Interest, Taxes, Insurance)
        interest_rate = 0.065  # Assuming 6.5% interest rate if not provided
        monthly_payment = self._calculate_monthly_payment(loan_amount, interest_rate, loan_term_years)
        
        # Estimate taxes, insurance, and MIP
        tax_and_insurance = property_value * 0.015 / 12  # Rough estimate: 1.5% of property value annually
        mip_monthly = loan_amount * 0.0055 / 12  # Monthly mortgage insurance premium (0.55% annually)
        upfront_mip = loan_amount * 0.0175  # Upfront MIP (1.75%)
        piti = monthly_payment + tax_and_insurance + mip_monthly
        
        if monthly_income > 0:
            frontend_ratio = (piti / monthly_income) * 100
        else:
            frontend_ratio = 100  # Unable to calculate, set to maximum
        
        # Evaluate against FHA guidelines
        risk_factors = []
        strengths = []
        
        # Credit score evaluation
        if credit_score >= 660:
            strengths.append("Strong credit score for FHA loan")
        elif credit_score >= 580:
            strengths.append("Meets standard FHA credit requirements")
        elif credit_score >= 500:
            risk_factors.append("Low credit score requires 10% down payment")
        else:
            risk_factors.append("Credit score below FHA minimum requirements")
        
        # DTI evaluation
        if dti_ratio <= 43:
            strengths.append("Meets standard FHA debt ratio requirements")
        elif dti_ratio <= 50:
            risk_factors.append("Elevated debt-to-income ratio requires compensating factors")
        else:
            risk_factors.append("Debt-to-income ratio likely exceeds FHA guidelines")
        
        # LTV evaluation
        down_payment_percentage = 100 - ltv_ratio
        if down_payment_percentage >= 10:
            strengths.append("Down payment meets or exceeds 10%")
        elif down_payment_percentage >= 3.5 and credit_score >= 580:
            strengths.append("Meets minimum 3.5% down payment requirement")
        else:
            risk_factors.append("Does not meet minimum down payment requirements")
        
        # Front-end ratio evaluation
        if frontend_ratio <= 31:
            strengths.append("Meets standard housing ratio guideline")
        elif frontend_ratio <= 40:
            risk_factors.append("Elevated housing ratio requires compensating factors")
        else:
            risk_factors.append("Housing ratio likely exceeds FHA guidelines")
        
        # Property type evaluation
        if property_type.lower() in ["single_family", "single family", "primary residence"]:
            strengths.append("Standard property type eligible for FHA")
        elif property_type.lower() in ["condo", "condominium"]:
            risk_factors.append("Condominium must be on FHA approved list")
        elif property_type.lower() in ["multi_family", "multi family", "2-4 units"]:
            risk_factors.append("Multi-family property requires owner occupancy")
        
        # Overall qualification assessment
        qualified = True
        loan_recommendation = "Approve"
        
        # Disqualifying factors
        if credit_score < 500:
            qualified = False
            loan_recommendation = "Decline"
        
        if credit_score < 580 and down_payment_percentage < 10:
            qualified = False
            loan_recommendation = "Decline"
        
        if down_payment_percentage < 3.5:
            qualified = False
            loan_recommendation = "Decline"
        
        # Conditionally qualified
        if qualified and len(risk_factors) >= 3:
            loan_recommendation = "Refer to Underwriter"
        
        # Compile evaluation results
        result = {
            "loan_type": "FHA",
            "qualified": qualified,
            "loan_recommendation": loan_recommendation,
            "ratios": {
                "dti": round(dti_ratio, 2),
                "ltv": round(ltv_ratio, 2),
                "frontend": round(frontend_ratio, 2)
            },
            "risk_factors": risk_factors,
            "strengths": strengths,
            "estimated_rate": round(interest_rate, 3),
            "estimated_monthly_payment": round(piti, 2),
            "upfront_mip": round(upfront_mip, 2),
            "monthly_mip": round(mip_monthly, 2),
            "conditions": []
        }
        
        # Add conditions based on risk factors
        if credit_score < 580:
            result["conditions"].append("Minimum 10% down payment required")
        
        if property_type.lower() in ["condo", "condominium"]:
            result["conditions"].append("Verify condominium is FHA approved")
        
        if dti_ratio > 43 or frontend_ratio > 31:
            result["conditions"].append("Document compensating factors for ratio exceptions")
            
        if frontend_ratio > 31 or dti_ratio > 43:
            result["conditions"].append("Verify significant cash reserves")
        
        return json.dumps(result, indent=2)
    
    def recommend_loan_program(self, context: dict) -> str:
        """
        Recommend the most suitable loan program based on applicant profile.
        
        Args:
            context: Dictionary with application data
            
        Returns:
            JSON string with loan program recommendations
        """
        application_data = json.loads(context["application_data"])
        
        # Extract key application data
        loan_amount = self._extract_loan_amount(application_data)
        property_value = self._extract_property_value(application_data)
        monthly_income = self._extract_monthly_income(application_data)
        monthly_debts = self._extract_monthly_debts(application_data)
        credit_score = self._extract_credit_score(application_data)
        is_first_time_homebuyer = self._extract_first_time_homebuyer(application_data)
        property_type = self._extract_property_type(application_data)
        is_veteran = self._extract_is_veteran(application_data)
        
        # Calculate key ratios
        if monthly_income > 0:
            dti_ratio = (monthly_debts / monthly_income) * 100
        else:
            dti_ratio = 100  # Unable to calculate, set to maximum
            
        if property_value > 0:
            ltv_ratio = (loan_amount / property_value) * 100
            down_payment_percentage = 100 - ltv_ratio
        else:
            ltv_ratio = 100  # Unable to calculate, set to maximum
            down_payment_percentage = 0
        
        # Determine if loan amount exceeds conforming limits
        # This is a simplified version - in reality, conforming limits vary by location
        conforming_limit = 726200  # 2023 conforming loan limit for most of the US
        is_jumbo = loan_amount > conforming_limit
        
        # Calculate PITI for 30-year fixed
        interest_rate_conventional = 0.065  # Example rate
        monthly_payment_conventional = self._calculate_monthly_payment(loan_amount, interest_rate_conventional, 30)
        tax_and_insurance = property_value * 0.015 / 12  # Rough estimate
        piti_conventional = monthly_payment_conventional + tax_and_insurance
        
        # Initialize program scores
        program_scores = {
            "Conventional": 0,
            "FHA": 0,
            "VA": 0,
            "USDA": 0,
            "Jumbo": 0
        }
        
        # Score Conventional loans
        if credit_score >= 620:
            program_scores["Conventional"] += 10
        if credit_score >= 700:
            program_scores["Conventional"] += 10
        if down_payment_percentage >= 20:
            program_scores["Conventional"] += 20
        elif down_payment_percentage >= 5:
            program_scores["Conventional"] += 10
        if dti_ratio <= 36:
            program_scores["Conventional"] += 15
        elif dti_ratio <= 45:
            program_scores["Conventional"] += 5
        if not is_jumbo:
            program_scores["Conventional"] += 10
        
        # Score FHA loans
        if credit_score >= 500:
            program_scores["FHA"] += 5
        if credit_score >= 580:
            program_scores["FHA"] += 10
        if down_payment_percentage >= 3.5:
            program_scores["FHA"] += 15
        if is_first_time_homebuyer:
            program_scores["FHA"] += 10
        if dti_ratio <= 50:
            program_scores["FHA"] += 10
        if ltv_ratio > 80 and ltv_ratio <= 96.5:
            program_scores["FHA"] += 5
        if not is_jumbo:
            program_scores["FHA"] += 5
        
        # Score VA loans
        if is_veteran:
            program_scores["VA"] += 50  # Big bonus for eligibility
            if down_payment_percentage < 10:
                program_scores["VA"] += 20
            if credit_score >= 620:
                program_scores["VA"] += 10
            if dti_ratio <= 41:
                program_scores["VA"] += 10
        
        # Score USDA loans
        # USDA requires the property to be in a rural area and has income limits
        # This is a simplified check - in reality, would need to check property location
        is_rural = False  # Placeholder - would need real property data
        is_under_income_limit = monthly_income * 12 <= 90000  # Simplified income limit
        
        if is_rural and is_under_income_limit:
            program_scores["USDA"] += 30
            if down_payment_percentage < 10:
                program_scores["USDA"] += 20
            if credit_score >= 640:
                program_scores["USDA"] += 10
        
        # Score Jumbo loans
        if is_jumbo:
            program_scores["Jumbo"] += 30
            if credit_score >= 700:
                program_scores["Jumbo"] += 10
            if credit_score >= 740:
                program_scores["Jumbo"] += 10
            if down_payment_percentage >= 20:
                program_scores["Jumbo"] += 20
            if dti_ratio <= 43:
                program_scores["Jumbo"] += 10
        
        # Sort programs by score
        sorted_programs = sorted(program_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Prepare program details
        program_details = []
        
        for program, score in sorted_programs:
            if score > 0:
                details = {
                    "program": program,
                    "score": score,
                    "features": []
                }
                
                if program == "Conventional":
                    details["features"] = [
                        "Down payment as low as 3% for first-time homebuyers",
                        "No upfront mortgage insurance",
                        "PMI can be removed once 20% equity is reached",
                        "Competitive interest rates for good credit scores"
                    ]
                    if down_payment_percentage < 20:
                        details["considerations"] = ["Requires Private Mortgage Insurance (PMI) if down payment is less than 20%"]
                
                elif program == "FHA":
                    details["features"] = [
                        "Down payment as low as 3.5% with 580+ credit score",
                        "More flexible credit requirements",
                        "Good option for first-time homebuyers",
                        "Allows for higher debt-to-income ratios with compensating factors"
                    ]
                    details["considerations"] = [
                        "Requires upfront and annual mortgage insurance premium",
                        "Mortgage insurance remains for the life of the loan if down payment is less than 10%"
                    ]
                
                elif program == "VA":
                    details["features"] = [
                        "No down payment required",
                        "No monthly mortgage insurance",
                        "Competitive interest rates",
                        "Flexible credit requirements"
                    ]
                    details["considerations"] = [
                        "Requires VA funding fee (can be financed)",
                        "Limited to eligible veterans, active duty personnel, and certain surviving spouses"
                    ]
                
                elif program == "USDA":
                    details["features"] = [
                        "No down payment required",
                        "Lower mortgage insurance costs than FHA",
                        "Competitive interest rates"
                    ]
                    details["considerations"] = [
                        "Limited to eligible rural and suburban areas",
                        "Income limits apply",
                        "Requires upfront and annual guarantee fees"
                    ]
                
                elif program == "Jumbo":
                    details["features"] = [
                        "Allows borrowing above conforming loan limits",
                        "Various term options available",
                        "Can finance luxury and high-cost properties"
                    ]
                    details["considerations"] = [
                        "Typically requires larger down payment (10-20%+)",
                        "Stricter credit score requirements (usually 700+)",
                        "May have higher interest rates",
                        "Usually requires significant cash reserves"
                    ]
                
                program_details.append(details)
        
        # Compile recommendation results
        result = {
            "recommended_programs": program_details,
            "financial_profile": {
                "loan_amount": loan_amount,
                "property_value": property_value,
                "ltv_ratio": round(ltv_ratio, 2),
                "down_payment_percentage": round(down_payment_percentage, 2),
                "dti_ratio": round(dti_ratio, 2),
                "credit_score": credit_score
            },
            "estimated_conventional_payment": round(piti_conventional, 2),
            "next_steps": [
                "Compare interest rates and terms from multiple lenders",
                "Consider the long-term costs of each program including mortgage insurance",
                "Evaluate how each program aligns with your financial goals"
            ]
        }
        
        return json.dumps(result, indent=2)
    
    def calculate_monthly_payment(self, context: dict) -> str:
        """
        Calculate the monthly mortgage payment.
        
        Args:
            context: Dictionary with loan details
            
        Returns:
            Monthly payment amount as a string
        """
        loan_amount = float(context["loan_amount"])
        interest_rate = float(context["interest_rate"])
        loan_term_years = int(context["loan_term_years"])
        
        monthly_payment = self._calculate_monthly_payment(loan_amount, interest_rate, loan_term_years)
        return f"${monthly_payment:.2f}"
    
    def calculate_affordability(self, context: dict) -> str:
        """
        Calculate how much house an applicant can afford.
        
        Args:
            context: Dictionary with applicant financial details
            
        Returns:
            JSON string with affordability analysis
        """
        monthly_income = float(context["monthly_income"])
        monthly_debts = float(context["monthly_debts"])
        down_payment = float(context["down_payment"])
        interest_rate = float(context["interest_rate"])
        loan_term_years = int(context["loan_term_years"])
        
        # Calculate maximum DTI-based payment
        # Using 43% as maximum DTI for qualified mortgage
        max_total_monthly_debt = monthly_income * 0.43
        max_housing_payment = max_total_monthly_debt - monthly_debts
        
        # Front-end ratio check (28% rule of thumb)
        max_frontend_payment = monthly_income * 0.28
        
        # Use the lower of the two limits
        max_payment = min(max_housing_payment, max_frontend_payment)
        
        # Estimate taxes and insurance as percentage of home value
        # This is a simplified approach
        tax_insurance_percentage = 0.015 / 12  # Annual 1.5% divided by 12 months
        
        # Calculate how much these tax+insurance costs reduce available payment
        # We need to solve for the maximum loan given the maximum payment
        # Solving for P in the formula: Payment = P * (r(1+r)^n) / ((1+r)^n - 1)
        
        # Monthly interest rate
        monthly_rate = interest_rate / 12
        
        # Number of payments
        n_payments = loan_term_years * 12
        
        # Adjustment for taxes and insurance
        # This is approximate and iterative
        estimated_home_value = 0
        for _ in range(5):  # Few iterations should converge
            estimated_tax_insurance = estimated_home_value * tax_insurance_percentage
            available_for_principal_interest = max_payment - estimated_tax_insurance
            
            if available_for_principal_interest <= 0:
                estimated_home_value = 0
                break
                
            # Calculate loan amount based on available payment for P&I
            if monthly_rate > 0:
                loan_amount = available_for_principal_interest * ((1 + monthly_rate) ** n_payments - 1) / (monthly_rate * (1 + monthly_rate) ** n_payments)
            else:
                loan_amount = available_for_principal_interest * n_payments
                
            # Estimate new home value
            estimated_home_value = loan_amount + down_payment
        
        # Calculate conservative and stretch scenarios
        conservative_home_value = estimated_home_value * 0.9
        stretch_home_value = estimated_home_value * 1.1
        
        # Calculate resulting monthly payments
        conservative_loan = conservative_home_value - down_payment
        stretch_loan = stretch_home_value - down_payment
        
        conservative_pi = self._calculate_monthly_payment(conservative_loan, interest_rate, loan_term_years)
        stretch_pi = self._calculate_monthly_payment(stretch_loan, interest_rate, loan_term_years)
        
        conservative_tax_insurance = conservative_home_value * tax_insurance_percentage
        stretch_tax_insurance = stretch_home_value * tax_insurance_percentage
        
        conservative_payment = conservative_pi + conservative_tax_insurance
        stretch_payment = stretch_pi + stretch_tax_insurance
        
        # Calculate resulting DTI
        conservative_dti = ((monthly_debts + conservative_payment) / monthly_income) * 100
        stretch_dti = ((monthly_debts + stretch_payment) / monthly_income) * 100
        
        # Compile results
        result = {
            "affordability_analysis": {
                "recommended_home_price_range": {
                    "conservative": round(conservative_home_value, 2),
                    "target": round(estimated_home_value, 2),
                    "stretch": round(stretch_home_value, 2)
                },
                "down_payment": down_payment,
                "resulting_loan_amount": {
                    "conservative": round(conservative_loan, 2),
                    "target": round(estimated_home_value - down_payment, 2),
                    "stretch": round(stretch_loan, 2)
                },
                "monthly_payment_estimates": {
                    "conservative": round(conservative_payment, 2),
                    "target": round(max_payment, 2),
                    "stretch": round(stretch_payment, 2)
                },
                "resulting_dti_ratios": {
                    "conservative": round(conservative_dti, 2),
                    "target": 43.0,  # Target is based on max DTI
                    "stretch": round(stretch_dti, 2)
                }
            },
            "assumptions": {
                "property_tax_and_insurance": "1.5% of home value annually",
                "max_dti_ratio": "43% of gross monthly income",
                "front_end_ratio": "28% of gross monthly income",
                "interest_rate": interest_rate,
                "loan_term_years": loan_term_years
            },
            "recommendations": [
                "Stay within the recommended price range to maintain financial flexibility",
                "Consider how other financial goals might be affected by housing costs",
                "Factor in additional costs like maintenance and utilities"
            ]
        }
        
        return json.dumps(result, indent=2)
    

    # Helper methods implementation - Part 2
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

    def _extract_credit_score(self, data: Dict[str, Any]) -> int:
        """Extract credit score from application data."""
        # Try different possible paths to credit score
        if "credit_score" in data:
            return int(data["credit_score"])
        elif "primary_applicant" in data and "credit_score" in data["primary_applicant"]:
            return int(data["primary_applicant"]["credit_score"])
        else:
            return 0

    def _extract_loan_term(self, data: Dict[str, Any]) -> int:
        """Extract loan term in years from application data."""
        # Try different possible paths to loan term
        if "loan_term_years" in data:
            return int(data["loan_term_years"])
        elif "loan_details" in data and "loan_term_years" in data["loan_details"]:
            return int(data["loan_details"]["loan_term_years"])
        else:
            return 30  # Default to 30-year term

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

    def _extract_property_type(self, data: Dict[str, Any]) -> str:
        """Extract property type from application data."""
        # Try different possible paths to property type
        if "property_type" in data:
            return str(data["property_type"])
        elif "property_info" in data and "property_type" in data["property_info"]:
            return str(data["property_info"]["property_type"])
        else:
            return "single_family"  # Default
        


    # Helper methods implementation - Part 3

    def _extract_first_time_homebuyer(self, data: Dict[str, Any]) -> bool:
        """Extract first-time homebuyer status from application data."""
        # Try different possible paths to first-time homebuyer status
        if "is_first_time_homebuyer" in data:
            return bool(data["is_first_time_homebuyer"])
        elif "loan_details" in data and "is_first_time_homebuyer" in data["loan_details"]:
            return bool(data["loan_details"]["is_first_time_homebuyer"])
        else:
            return False  # Default

    def _extract_is_veteran(self, data: Dict[str, Any]) -> bool:
        """Extract veteran status from application data."""
        # Try different possible paths to veteran status
        if "is_veteran" in data:
            return bool(data["is_veteran"])
        elif "primary_applicant" in data and "is_veteran" in data["primary_applicant"]:
            return bool(data["primary_applicant"]["is_veteran"])
        else:
            return False  # Default

    def _is_eligible_for_va(self, data: Dict[str, Any]) -> bool:
        """Determine if the applicant is eligible for a VA loan."""
        # Check veteran status
        is_veteran = self._extract_is_veteran(data)
        
        # Check if they have VA eligibility documentation
        has_coe = False
        if "va_eligibility" in data and data["va_eligibility"].get("certificate_of_eligibility", False):
            has_coe = True
        
        return is_veteran and has_coe

    def _is_eligible_for_fha(self, data: Dict[str, Any]) -> bool:
        """Determine if the applicant is eligible for an FHA loan."""
        # Extract credit score - FHA minimum is 500
        credit_score = self._extract_credit_score(data)
        
        # Extract down payment percentage
        property_value = self._extract_property_value(data)
        down_payment = self._extract_down_payment(data)
        
        if property_value > 0:
            down_payment_percentage = (down_payment / property_value) * 100
        else:
            down_payment_percentage = 0
        
        # FHA eligibility: Credit score 500+ with 10% down or 580+ with 3.5% down
        if credit_score >= 580 and down_payment_percentage >= 3.5:
            return True
        elif credit_score >= 500 and down_payment_percentage >= 10:
            return True
        else:
            return False

    def _is_eligible_for_usda(self, data: Dict[str, Any]) -> bool:
        """Determine if the applicant is eligible for a USDA loan."""
        # Check if property is in rural area
        is_rural = False
        if "property_info" in data and data["property_info"].get("is_rural_area", False):
            is_rural = True
        
        # Check income limits
        income_eligible = False
        monthly_income = self._extract_monthly_income(data)
        annual_income = monthly_income * 12
        
        # Simplified income limit check (actual limits vary by location and household size)
        if annual_income <= 90000:  # Example threshold
            income_eligible = True
        
        return is_rural and income_eligible

    def _format_currency(self, amount: float) -> str:
        """Format an amount as a currency string."""
        return f"${amount:,.2f}"

    def _calculate_pmi_rate(self, ltv_ratio: float, credit_score: int) -> float:
        """Calculate approximate PMI rate based on LTV ratio and credit score."""
        # Base PMI rate
        base_rate = 0.0055  # 0.55% for standard scenarios
        
        # Adjust for LTV
        if ltv_ratio > 95:
            base_rate += 0.0020  # Add 0.20% for high LTV
        elif ltv_ratio > 90:
            base_rate += 0.0010  # Add 0.10% for moderately high LTV
        
        # Adjust for credit score
        if credit_score < 640:
            base_rate += 0.0030  # Add 0.30% for poor credit
        elif credit_score < 680:
            base_rate += 0.0015  # Add 0.15% for fair credit
        elif credit_score < 720:
            base_rate += 0.0005  # Add 0.05% for good credit
        elif credit_score >= 760:
            base_rate -= 0.0010  # Subtract 0.10% for excellent credit
            
        return base_rate

    def _calculate_fha_mip_rate(self, loan_amount: float, ltv_ratio: float, loan_term_years: int) -> Dict[str, float]:
        """Calculate FHA mortgage insurance premium rates."""
        # Upfront MIP rate (currently 1.75% for most FHA loans)
        upfront_rate = 0.0175
        
        # Annual MIP rate based on loan amount, LTV, and term
        annual_rate = 0.0055  # Default 0.55% for 30-year loans with LTV > 95%
        
        if loan_term_years <= 15:
            if ltv_ratio <= 90:
                annual_rate = 0.0045  # 0.45% for 15-year loans with LTV <= 90%
            else:
                annual_rate = 0.0070  # 0.70% for 15-year loans with LTV > 90%
        else:  # 30-year loans
            if ltv_ratio <= 95:
                annual_rate = 0.0050  # 0.50% for 30-year loans with LTV <= 95%
                
        # Calculate actual amounts
        upfront_mip = loan_amount * upfront_rate
        annual_mip = loan_amount * annual_rate
        monthly_mip = annual_mip / 12
        
        return {
            "upfront_rate": upfront_rate,
            "annual_rate": annual_rate,
            "upfront_amount": upfront_mip,
            "monthly_amount": monthly_mip
        }

    def _calculate_va_funding_fee(self, loan_amount: float, down_payment_percentage: float, is_first_use: bool) -> float:
        """Calculate VA funding fee based on down payment and first-time use."""
        # Base rates for first use and subsequent use
        if is_first_use:
            if down_payment_percentage < 5:
                rate = 0.0215  # 2.15% for first use with < 5% down
            elif down_payment_percentage < 10:
                rate = 0.0150  # 1.50% for first use with 5-10% down
            else:
                rate = 0.0125  # 1.25% for first use with 10%+ down
        else:
            if down_payment_percentage < 5:
                rate = 0.0330  # 3.30% for subsequent use with < 5% down
            elif down_payment_percentage < 10:
                rate = 0.0150  # 1.50% for subsequent use with 5-10% down
            else:
                rate = 0.0125  # 1.25% for subsequent use with 10%+ down
        
        # Calculate funding fee amount
        funding_fee = loan_amount * rate
        
        return funding_fee

    def _generate_decision_explanation(self, context: dict) -> str:
        """
        Generate a human-readable explanation for an underwriting decision.
        
        Args:
            context: Dictionary with decision details and factors
        
        Returns:
            String with formatted explanation
        """
        # Extract key decision information
        decision = context.get("decision", "Unknown")
        factors = context.get("factors", [])
        conditions = context.get("conditions", [])
        strengths = context.get("strengths", [])
        risks = context.get("risks", [])
        
        # Start building explanation
        explanation = f"Underwriting Decision: {decision}\n\n"
        
        # Add decision factors
        if factors:
            explanation += "This decision was based on the following factors:\n"
            for factor in factors:
                explanation += f"- {factor}\n"
            explanation += "\n"
        
        # Add strengths if applicable
        if strengths:
            explanation += "Key strengths in your application:\n"
            for strength in strengths:
                explanation += f"- {strength}\n"
            explanation += "\n"
        
        # Add risk factors if applicable
        if risks:
            explanation += "Areas of concern in your application:\n"
            for risk in risks:
                explanation += f"- {risk}\n"
            explanation += "\n"
        
        # Add conditions if applicable
        if conditions:
            explanation += "This approval includes the following conditions:\n"
            for condition in conditions:
                explanation += f"- {condition}\n"
            explanation += "\n"
        
        # Add general closing
        if decision.lower() == "approved":
            explanation += "Congratulations on your loan approval! Please review any conditions listed above, as they will need to be satisfied before closing."
        elif decision.lower() == "conditionally approved":
            explanation += "Your loan has been conditionally approved. Please address the conditions listed above to proceed to final approval."
        else:
            explanation += "At this time, we are unable to approve your loan application. We encourage you to review the factors mentioned above and consider addressing these areas before reapplying."
        
        return explanation