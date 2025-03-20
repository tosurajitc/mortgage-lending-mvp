"""
Loan Generator

This script generates realistic but fictional loan data for mortgage applications.
It creates various loan types with appropriate terms and conditions.
"""

import json
import random
import datetime
from typing import Dict, Any, List, Tuple, Optional

# Current market rates (as of early 2023)
CURRENT_RATES = {
    "30_year_fixed": (5.75, 6.5),      # Range for 30-year fixed mortgages
    "15_year_fixed": (5.0, 5.75),      # Range for 15-year fixed mortgages
    "5_1_ARM": (4.75, 5.5),            # Range for 5/1 ARM
    "7_1_ARM": (5.0, 5.75),            # Range for 7/1 ARM
    "FHA": (5.85, 6.6),                # Range for FHA loans
    "VA": (5.65, 6.4),                 # Range for VA loans
    "USDA": (5.8, 6.55),               # Range for USDA loans
    "jumbo": (6.0, 6.75)               # Range for jumbo loans
}

# Loan program details
LOAN_PROGRAMS = {
    "Conventional": {
        "min_down_payment": 0.03,      # 3% minimum down payment
        "max_ltv": 0.97,               # 97% max loan-to-value
        "min_credit_score": 620,       # Minimum credit score
        "max_dti": 0.45,               # Maximum debt-to-income ratio
        "pmi_threshold": 0.8,          # PMI required if LTV > 80%
        "terms_available": [15, 20, 30],  # Available loan terms in years
        "loan_limit": 726200,          # Conforming loan limit for 2023
        "income_requirements": "Must document stable income history",
        "pros": ["Flexible down payment options", "Lower rates for good credit", "PMI can be removed"],
        "cons": ["Higher credit score requirements", "PMI needed for <20% down payment"]
    },
    "FHA": {
        "min_down_payment": 0.035,     # 3.5% minimum down payment
        "max_ltv": 0.965,              # 96.5% max loan-to-value
        "min_credit_score": 580,       # Minimum credit score
        "max_dti": 0.50,               # Maximum debt-to-income ratio
        "mortgage_insurance": "Required for the life of the loan with <10% down payment",
        "terms_available": [15, 30],   # Available loan terms in years
        "loan_limit": 472030,          # FHA loan limit for 2023 (varies by county)
        "income_requirements": "Must document stable income for at least 2 years",
        "pros": ["Lower down payment requirements", "More lenient credit requirements"],
        "cons": ["Mortgage insurance for life of loan", "Property must meet FHA standards"]
    },
    "VA": {
        "min_down_payment": 0.0,       # No down payment required
        "max_ltv": 1.0,                # 100% LTV possible
        "min_credit_score": 580,       # Minimum credit score (varies by lender)
        "max_dti": 0.60,               # Maximum debt-to-income ratio
        "funding_fee": "1.4% to 3.6% based on down payment and service history",
        "terms_available": [15, 30],   # Available loan terms in years
        "loan_limit": "None for most borrowers", 
        "eligibility": "Must be qualified service member, veteran, or eligible spouse",
        "pros": ["No down payment required", "No monthly mortgage insurance", "Competitive rates"],
        "cons": ["VA funding fee required", "Limited to eligible veterans and service members"]
    },
    "USDA": {
        "min_down_payment": 0.0,       # No down payment required
        "max_ltv": 1.0,                # 100% LTV possible
        "min_credit_score": 640,       # Minimum credit score
        "max_dti": 0.41,               # Maximum debt-to-income ratio
        "guarantee_fee": "1% upfront, 0.35% annual",
        "terms_available": [30],       # Available loan terms in years
        "income_limit": "Must not exceed 115% of median income for the area",
        "location_requirement": "Property must be in eligible rural area",
        "pros": ["No down payment required", "Lower mortgage insurance costs than FHA"],
        "cons": ["Geographic restrictions", "Income limits", "Only single family residences"]
    },
    "Jumbo": {
        "min_down_payment": 0.10,      # 10% minimum down payment
        "max_ltv": 0.90,               # 90% max loan-to-value
        "min_credit_score": 700,       # Minimum credit score
        "max_dti": 0.43,               # Maximum debt-to-income ratio
        "terms_available": [15, 30],   # Available loan terms in years
        "min_loan_amount": 726200,     # Exceeds conforming loan limit
        "reserve_requirements": "6-12 months of mortgage payments in cash reserves",
        "pros": ["Finance high-value properties", "Competitive rates", "Various term options"],
        "cons": ["Higher down payment requirements", "Stricter qualification criteria"]
    }
}

# ARM (Adjustable Rate Mortgage) details
ARM_DETAILS = {
    "5/1 ARM": {
        "initial_fixed_period": 5,      # Years
        "adjustment_frequency": 1,      # Years
        "typical_margin": 2.75,         # Added to index after fixed period
        "caps": {
            "initial_adjustment": 2.0,  # Maximum first adjustment
            "subsequent_adjustment": 2.0,  # Maximum per-adjustment
            "lifetime": 5.0             # Maximum lifetime adjustment
        }
    },
    "7/1 ARM": {
        "initial_fixed_period": 7,      # Years
        "adjustment_frequency": 1,      # Years
        "typical_margin": 2.5,          # Added to index after fixed period
        "caps": {
            "initial_adjustment": 2.0,  # Maximum first adjustment
            "subsequent_adjustment": 2.0,  # Maximum per-adjustment
            "lifetime": 5.0             # Maximum lifetime adjustment
        }
    },
    "10/1 ARM": {
        "initial_fixed_period": 10,     # Years
        "adjustment_frequency": 1,      # Years
        "typical_margin": 2.25,         # Added to index after fixed period
        "caps": {
            "initial_adjustment": 2.0,  # Maximum first adjustment
            "subsequent_adjustment": 2.0,  # Maximum per-adjustment
            "lifetime": 5.0             # Maximum lifetime adjustment
        }
    }
}

def calculate_interest_rate(loan_program: str, loan_term: int, credit_score: int, 
                           ltv: float, is_arm: bool = False, arm_type: str = None) -> float:
    """
    Calculate a realistic interest rate based on loan factors.
    
    Args:
        loan_program: Type of loan (Conventional, FHA, VA, etc.)
        loan_term: Term of the loan in years
        credit_score: Borrower's credit score
        ltv: Loan-to-value ratio
        is_arm: Whether this is an adjustable rate mortgage
        arm_type: Type of ARM (e.g., "5/1 ARM")
        
    Returns:
        Interest rate as a percentage
    """
    # Determine base rate range based on loan type and term
    if is_arm and arm_type:
        if arm_type == "5/1 ARM":
            base_rate_range = CURRENT_RATES["5_1_ARM"]
        elif arm_type == "7/1 ARM":
            base_rate_range = CURRENT_RATES["7_1_ARM"]
        else:
            base_rate_range = CURRENT_RATES["5_1_ARM"]  # Default to 5/1 ARM
    elif loan_program == "Jumbo":
        base_rate_range = CURRENT_RATES["jumbo"]
    elif loan_program == "FHA":
        base_rate_range = CURRENT_RATES["FHA"]
    elif loan_program == "VA":
        base_rate_range = CURRENT_RATES["VA"]
    elif loan_program == "USDA":
        base_rate_range = CURRENT_RATES["USDA"]
    else:  # Conventional
        if loan_term == 15:
            base_rate_range = CURRENT_RATES["15_year_fixed"]
        else:  # 30-year or other term
            base_rate_range = CURRENT_RATES["30_year_fixed"]
    
    # Start with a rate in the range
    base_rate = random.uniform(base_rate_range[0], base_rate_range[1])
    
    # Adjust for credit score
    if credit_score >= 760:
        credit_adjustment = -0.25
    elif credit_score >= 740:
        credit_adjustment = -0.125
    elif credit_score >= 720:
        credit_adjustment = 0
    elif credit_score >= 700:
        credit_adjustment = 0.125
    elif credit_score >= 680:
        credit_adjustment = 0.25
    elif credit_score >= 660:
        credit_adjustment = 0.5
    elif credit_score >= 640:
        credit_adjustment = 0.75
    else:
        credit_adjustment = 1.0
    
    # Adjust for LTV
    if ltv <= 0.6:
        ltv_adjustment = -0.25
    elif ltv <= 0.7:
        ltv_adjustment = -0.125
    elif ltv <= 0.8:
        ltv_adjustment = 0
    elif ltv <= 0.85:
        ltv_adjustment = 0.125
    elif ltv <= 0.9:
        ltv_adjustment = 0.25
    elif ltv <= 0.95:
        ltv_adjustment = 0.375
    else:
        ltv_adjustment = 0.5
    
    # Calculate final rate
    rate = base_rate + credit_adjustment + ltv_adjustment
    
    # Add some randomness (±0.125%)
    rate += random.choice([-0.125, -0.0625, 0, 0.0625, 0.125])
    
    # Round to nearest 0.125%
    rate = round(rate * 8) / 8
    
    return rate

def calculate_monthly_payment(loan_amount: float, interest_rate: float, loan_term_years: int) -> float:
    """
    Calculate the monthly principal and interest payment.
    
    Args:
        loan_amount: Loan amount in dollars
        interest_rate: Annual interest rate as a percentage
        loan_term_years: Loan term in years
        
    Returns:
        Monthly payment amount
    """
    # Convert annual interest rate to monthly decimal rate
    monthly_rate = (interest_rate / 100) / 12
    
    # Convert term in years to term in months
    term_months = loan_term_years * 12
    
    # Calculate monthly payment using mortgage formula
    if monthly_rate == 0:
        # Edge case: if rate is 0, payment is just principal divided by term
        return loan_amount / term_months
    else:
        # Standard formula: P * (r(1+r)^n) / ((1+r)^n - 1)
        monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** term_months) / ((1 + monthly_rate) ** term_months - 1)
        return monthly_payment

def generate_loan_details(property_value: float, applicant_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate realistic loan details based on property and applicant information.
    
    Args:
        property_value: Estimated value of the property
        applicant_data: Dictionary with applicant information
        
    Returns:
        Dictionary with loan details
    """
    # Extract relevant applicant info
    primary_credit_score = applicant_data["primary_applicant"]["credit_score"]
    primary_income = applicant_data["primary_applicant"]["annual_income"]
    
    # Calculate total income (including co-applicant if available)
    total_income = primary_income
    if "co_applicant" in applicant_data:
        total_income += applicant_data["co_applicant"]["annual_income"]
    
    # Randomly decide loan program based on applicant profile
    # Create weighted probabilities based on credit score and other factors
    loan_program_weights = {
        "Conventional": 0.7,
        "FHA": 0.15,
        "VA": 0.05,
        "USDA": 0.05,
        "Jumbo": 0.05
    }
    
    # Adjust weights based on credit score
    if primary_credit_score < 620:
        loan_program_weights["Conventional"] = 0.1
        loan_program_weights["FHA"] = 0.7
        loan_program_weights["VA"] = 0.1
        loan_program_weights["USDA"] = 0.1
        loan_program_weights["Jumbo"] = 0
    elif primary_credit_score < 680:
        loan_program_weights["Conventional"] = 0.4
        loan_program_weights["FHA"] = 0.4
        loan_program_weights["VA"] = 0.1
        loan_program_weights["USDA"] = 0.1
        loan_program_weights["Jumbo"] = 0
    
    # Adjust weights based on property value (for Jumbo loans)
    if property_value > LOAN_PROGRAMS["Conventional"]["loan_limit"]:
        loan_program_weights["Conventional"] = 0.2
        loan_program_weights["FHA"] = 0.05
        loan_program_weights["VA"] = 0.05
        loan_program_weights["USDA"] = 0.0
        loan_program_weights["Jumbo"] = 0.7
    
    # Select loan program
    loan_programs = list(loan_program_weights.keys())
    weights = list(loan_program_weights.values())
    loan_program = random.choices(loan_programs, weights=weights, k=1)[0]
    
    # Determine loan term
    available_terms = LOAN_PROGRAMS[loan_program]["terms_available"]
    loan_term_years = random.choice(available_terms)
    
    # Determine if ARM or fixed
    is_arm = random.random() < 0.1  # 10% chance of ARM
    arm_type = None
    if is_arm:
        arm_type = random.choice(list(ARM_DETAILS.keys()))
    
    # Calculate down payment percentage (random within typical ranges)
    min_down = LOAN_PROGRAMS[loan_program]["min_down_payment"]
    
    # Higher down payment for higher credit scores, on average
    if primary_credit_score >= 740:
        down_payment_pct = random.uniform(min_down, 0.25)
    elif primary_credit_score >= 700:
        down_payment_pct = random.uniform(min_down, 0.20)
    elif primary_credit_score >= 660:
        down_payment_pct = random.uniform(min_down, 0.15)
    else:
        down_payment_pct = random.uniform(min_down, 0.10)
    
    # Round down payment percentage to nearest 0.5%
    down_payment_pct = round(down_payment_pct * 200) / 200
    
    # Calculate loan amount
    down_payment = property_value * down_payment_pct
    loan_amount = property_value - down_payment
    
    # Calculate LTV
    ltv = loan_amount / property_value
    
    # Calculate interest rate
    interest_rate = calculate_interest_rate(
        loan_program=loan_program,
        loan_term=loan_term_years,
        credit_score=primary_credit_score,
        ltv=ltv,
        is_arm=is_arm,
        arm_type=arm_type
    )
    
    # Calculate monthly payment (principal and interest)
    monthly_payment = calculate_monthly_payment(loan_amount, interest_rate, loan_term_years)
    
    # Calculate PMI (if applicable)
    pmi_monthly = 0
    if loan_program == "Conventional" and ltv > LOAN_PROGRAMS[loan_program]["pmi_threshold"]:
        # Approximate PMI calculation (0.5-1.5% of loan amount annually)
        pmi_rate = 0.005  # 0.5% base
        if ltv > 0.9:
            pmi_rate = 0.01  # 1.0%
        elif ltv > 0.85:
            pmi_rate = 0.0075  # 0.75%
        
        # Adjust for credit score
        if primary_credit_score < 680:
            pmi_rate += 0.002
        elif primary_credit_score < 720:
            pmi_rate += 0.001
        
        pmi_monthly = (loan_amount * pmi_rate) / 12
    
    # Calculate total monthly payment including estimates for taxes and insurance
    property_tax_rate = random.uniform(0.005, 0.025)  # 0.5% to 2.5% annual
    monthly_property_tax = (property_value * property_tax_rate) / 12
    
    homeowners_insurance = (property_value * 0.0035) / 12  # Approximate annual rate of 0.35%
    
    total_monthly_payment = monthly_payment + pmi_monthly + monthly_property_tax + homeowners_insurance
    
    # Calculate front-end DTI (housing costs / income)
    front_end_dti = total_monthly_payment / (total_income / 12)
    
    # Calculate if first-time homebuyer programs might apply
    # (simplified - we'll just use a random flag for this example)
    is_first_time_homebuyer = random.random() < 0.4  # 40% chance
    
    # Create the loan details
    loan_details = {
        "loan_program": loan_program,
        "loan_term_years": loan_term_years,
        "loan_amount": round(loan_amount, 2),
        "down_payment": round(down_payment, 2),
        "down_payment_percentage": round(down_payment_pct * 100, 2),
        "interest_rate": round(interest_rate, 3),
        "loan_to_value_ratio": round(ltv, 3),
        "monthly_principal_interest": round(monthly_payment, 2),
        "monthly_pmi": round(pmi_monthly, 2),
        "monthly_property_tax": round(monthly_property_tax, 2),
        "monthly_insurance": round(homeowners_insurance, 2),
        "total_monthly_payment": round(total_monthly_payment, 2),
        "front_end_dti_ratio": round(front_end_dti, 3),
        "is_first_time_homebuyer": is_first_time_homebuyer
    }
    
    # Add ARM details if applicable
    if is_arm and arm_type:
        arm_info = ARM_DETAILS[arm_type]
        loan_details["is_adjustable_rate"] = True
        loan_details["arm_type"] = arm_type
        loan_details["initial_fixed_period_years"] = arm_info["initial_fixed_period"]
        loan_details["adjustment_frequency_years"] = arm_info["adjustment_frequency"]
        loan_details["margin"] = arm_info["typical_margin"]
        loan_details["rate_caps"] = arm_info["caps"]
    else:
        loan_details["is_adjustable_rate"] = False
    
    # Add program-specific details
    if loan_program == "FHA":
        loan_details["upfront_mip"] = round(loan_amount * 0.0175, 2)  # 1.75% upfront
        loan_details["annual_mip_rate"] = 0.0055  # 0.55% annually for most FHA loans
        loan_details["monthly_mip"] = round((loan_amount * loan_details["annual_mip_rate"]) / 12, 2)
        loan_details["total_monthly_payment"] += loan_details["monthly_mip"]
    
    elif loan_program == "VA":
        # Calculate VA funding fee
        if down_payment_pct >= 0.1:
            funding_fee_rate = 0.014  # 1.4% for 10%+ down
        elif down_payment_pct >= 0.05:
            funding_fee_rate = 0.016  # 1.6% for 5-10% down
        else:
            funding_fee_rate = 0.022  # 2.2% for <5% down
        
        loan_details["va_funding_fee"] = round(loan_amount * funding_fee_rate, 2)
        loan_details["va_funding_fee_financed"] = random.random() < 0.7  # 70% chance of financing
        
        if loan_details["va_funding_fee_financed"]:
            loan_details["loan_amount"] += loan_details["va_funding_fee"]
            
            # Recalculate monthly payment with financed funding fee
            monthly_payment = calculate_monthly_payment(
                loan_details["loan_amount"], interest_rate, loan_term_years
            )
            loan_details["monthly_principal_interest"] = round(monthly_payment, 2)
            loan_details["total_monthly_payment"] = round(
                monthly_payment + monthly_property_tax + homeowners_insurance, 2
            )
    
    elif loan_program == "USDA":
        loan_details["upfront_guarantee_fee"] = round(loan_amount * 0.01, 2)  # 1% upfront
        loan_details["annual_guarantee_fee_rate"] = 0.0035  # 0.35% annually
        loan_details["monthly_guarantee_fee"] = round((loan_amount * loan_details["annual_guarantee_fee_rate"]) / 12, 2)
        loan_details["total_monthly_payment"] += loan_details["monthly_guarantee_fee"]
    
    return loan_details

def generate_loan_scenarios(count: int = 10) -> List[Dict[str, Any]]:
    """
    Generate a diverse set of loan scenarios.
    
    Args:
        count: Number of loan scenarios to generate
        
    Returns:
        List of loan scenarios
    """
    # For standalone testing, create some sample property values and applicant profiles
    property_values = [
        250000, 300000, 350000, 400000, 450000, 500000, 550000, 
        600000, 700000, 800000, 900000, 1000000, 1200000
    ]
    
    # Credit score ranges
    credit_scores = [
        (580, 620), (620, 660), (660, 700), (700, 740), (740, 780), (780, 820)
    ]
    
    # Income ranges
    income_ranges = [
        (40000, 60000), (60000, 80000), (80000, 100000), 
        (100000, 150000), (150000, 200000), (200000, 300000)
    ]
    
    scenarios = []
    
    for _ in range(count):
        # Generate random property value
        property_value = random.choice(property_values)
        
        # Generate random applicant profile
        credit_range = random.choice(credit_scores)
        income_range = random.choice(income_ranges)
        
        # Primary applicant
        primary_credit = random.randint(*credit_range)
        primary_income = random.randint(*income_range)
        
        # Decide if there's a co-applicant
        has_coapplicant = random.random() < 0.6  # 60% chance
        
        applicant_data = {
            "primary_applicant": {
                "credit_score": primary_credit,
                "annual_income": primary_income
            }
        }
        
        if has_coapplicant:
            # Co-applicant usually has similar but slightly different credit score
            coapplicant_credit = min(max(primary_credit + random.randint(-40, 40), 580), 820)
            coapplicant_income = random.randint(*income_range)
            
            applicant_data["co_applicant"] = {
                "credit_score": coapplicant_credit,
                "annual_income": coapplicant_income
            }
        
        # Generate loan details
        loan_details = generate_loan_details(property_value, applicant_data)
        
        # Add property value and applicant data for context
        scenario = {
            "property_value": property_value,
            "applicant_data": applicant_data,
            "loan_details": loan_details
        }
        
        scenarios.append(scenario)
    
    return scenarios

if __name__ == "__main__":
    # Generate and save sample loan data
    loans = generate_loan_scenarios(20)
    
    # Ensure output directory exists
    import os
    os.makedirs("mock_data/sample_data/loans", exist_ok=True)
    
    # Save to file
    with open("mock_data/sample_data/loans/sample_loans.json", "w") as f:
        json.dump(loans, f, indent=2)
    
    print(f"Generated {len(loans)} loan scenarios.")
    
    # Display a sample
    print("\nSample loan scenario:")
    print(json.dumps(loans[0], indent=2))