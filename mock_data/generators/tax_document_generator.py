"""
Tax Document Generator

This module generates mock tax-related documents for mortgage applications:
- Tax returns (1040 summary)

These are simplified representations with the key data that would be extracted
by the document processing agent.
"""

import random
import uuid
from typing import Dict, Any, Optional

def generate_tax_return(applicant_data: Dict[str, Any], tax_year: int) -> Dict[str, Any]:
    """
    Generate a mock tax return summary for an applicant.
    
    Args:
        applicant_data: Applicant information
        tax_year: Tax year for the return
        
    Returns:
        Dictionary representing key tax return data
    """
    first_name = applicant_data["first_name"]
    last_name = applicant_data["last_name"]
    address = applicant_data["address"]
    annual_income = applicant_data.get("annual_income", 75000)  # Default if not provided
    
    # Determine filing status
    has_coapplicant = "co_applicant" in applicant_data
    filing_status = "Married Filing Jointly" if has_coapplicant else random.choice(
        ["Single", "Head of Household"]
    )
    
    # Calculate income components
    wages = annual_income
    
    # Add some additional income sources
    interest_income = round(random.uniform(0, 5000), 2)
    dividend_income = round(random.uniform(0, 7500), 2)
    
    # Calculate total income
    total_income = wages + interest_income + dividend_income
    
    # Calculate adjustments
    ira_deduction = 0
    if random.random() < 0.4:  # 40% chance of IRA contribution
        ira_deduction = min(6000, round(random.uniform(1000, 6000), 2))
    
    student_loan_interest = 0
    if random.random() < 0.3:  # 30% chance of student loan interest
        student_loan_interest = min(2500, round(random.uniform(500, 2500), 2))
    
    total_adjustments = ira_deduction + student_loan_interest
    
    # Calculate adjusted gross income (AGI)
    agi = total_income - total_adjustments
    
    # Calculate deductions
    standard_deduction = 12950 if filing_status == "Single" else 25900 if filing_status == "Married Filing Jointly" else 19400
    itemized_deduction = round(standard_deduction * random.uniform(0.7, 1.3), 2)
    uses_itemized = itemized_deduction > standard_deduction
    
    deduction = itemized_deduction if uses_itemized else standard_deduction
    
    # Calculate taxable income
    taxable_income = max(0, agi - deduction)
    
    # Simplified tax calculation (just an approximation)
    if filing_status == "Single":
        if taxable_income <= 10275:
            tax_rate = 0.10
        elif taxable_income <= 41775:
            tax_rate = 0.12
        elif taxable_income <= 89075:
            tax_rate = 0.22
        elif taxable_income <= 170050:
            tax_rate = 0.24
        elif taxable_income <= 215950:
            tax_rate = 0.32
        elif taxable_income <= 539900:
            tax_rate = 0.35
        else:
            tax_rate = 0.37
    else:  # Married or Head of Household (simplified)
        if taxable_income <= 20550:
            tax_rate = 0.10
        elif taxable_income <= 83550:
            tax_rate = 0.12
        elif taxable_income <= 178150:
            tax_rate = 0.22
        elif taxable_income <= 340100:
            tax_rate = 0.24
        elif taxable_income <= 431900:
            tax_rate = 0.32
        elif taxable_income <= 647850:
            tax_rate = 0.35
        else:
            tax_rate = 0.37
    
    # Calculate tax
    calculated_tax = round(taxable_income * tax_rate, 2)
    
    # Tax credits
    child_tax_credit = 0
    if random.random() < 0.3:  # 30% chance of having dependents
        num_children = random.randint(1, 3)
        child_tax_credit = num_children * 2000
    
    total_credits = child_tax_credit
    
    # Calculate tax after credits
    tax_after_credits = max(0, calculated_tax - total_credits)
    
    # Calculate payments made
    tax_withheld = round(wages * random.uniform(0.15, 0.25), 2)
    estimated_tax_payments = 0
    
    total_payments = tax_withheld + estimated_tax_payments
    
    # Calculate refund or amount owed
    if total_payments > tax_after_credits:
        refund_amount = total_payments - tax_after_credits
        amount_owed = 0
    else:
        refund_amount = 0
        amount_owed = tax_after_credits - total_payments
    
    # Generate document
    document = {
        "document_type": "Tax Return",
        "form": "1040",
        "tax_year": tax_year,
        "filing_status": filing_status,
        "taxpayer": {
            "name": f"{first_name} {last_name}",
            "ssn_last_four": applicant_data.get("ssn_last_four", "XXXX"),
            "address": address
        },
        "income": {
            "wages": wages,
            "interest": interest_income,
            "dividends": dividend_income,
            "total_income": total_income
        },
        "adjustments": {
            "ira_deduction": ira_deduction,
            "student_loan_interest": student_loan_interest,
            "total_adjustments": total_adjustments
        },
        "agi": agi,
        "deductions": {
            "standard_deduction": standard_deduction,
            "itemized_deduction": itemized_deduction if uses_itemized else 0,
            "deduction_used": "itemized" if uses_itemized else "standard",
            "total_deduction": deduction
        },
        "taxable_income": taxable_income,
        "tax": {
            "calculated_tax": calculated_tax,
            "child_tax_credit": child_tax_credit,
            "total_credits": total_credits,
            "tax_after_credits": tax_after_credits
        },
        "payments": {
            "tax_withheld": tax_withheld,
            "estimated_tax_payments": estimated_tax_payments,
            "total_payments": total_payments
        },
        "refund_or_owed": {
            "refund_amount": refund_amount,
            "amount_owed": amount_owed
        },
        "metadata": {
            "document_id": str(uuid.uuid4()),
            "extraction_confidence": random.uniform(0.85, 0.99)
        }
    }
    
    # Add spouse info if married filing jointly
    if filing_status == "Married Filing Jointly" and "co_applicant" in applicant_data:
        spouse_first_name = applicant_data["co_applicant"]["first_name"]
        spouse_last_name = applicant_data["co_applicant"]["last_name"]
        spouse_ssn_last_four = applicant_data["co_applicant"].get("ssn_last_four", "XXXX")
        
        document["spouse"] = {
            "name": f"{spouse_first_name} {spouse_last_name}",
            "ssn_last_four": spouse_ssn_last_four
        }
    
    return document

def generate_tax_returns_set(applicant_data: Dict[str, Any], current_year: int, num_years: int = 2) -> Dict[int, Dict[str, Any]]:
    """
    Generate a set of tax returns for multiple years.
    
    Args:
        applicant_data: Applicant information
        current_year: The current year
        num_years: Number of years to generate (going backwards from current_year - 1)
        
    Returns:
        Dictionary mapping years to tax returns
    """
    tax_returns = {}
    
    # Adjust income for previous years (decrease by 3-5% per year)
    adjusted_applicant = applicant_data.copy()
    
    for i in range(num_years):
        tax_year = current_year - 1 - i
        
        # Adjust income for previous years
        if i > 0 and "annual_income" in adjusted_applicant:
            decrease_factor = random.uniform(0.03, 0.05)  # 3-5% decrease per year
            adjusted_applicant["annual_income"] = adjusted_applicant["annual_income"] * (1 - decrease_factor)
            
            # Also adjust co-applicant income if present
            if "co_applicant" in adjusted_applicant and "annual_income" in adjusted_applicant["co_applicant"]:
                adjusted_applicant["co_applicant"]["annual_income"] = adjusted_applicant["co_applicant"]["annual_income"] * (1 - decrease_factor)
        
        # Generate tax return for this year
        tax_returns[tax_year] = generate_tax_return(adjusted_applicant, tax_year)
    
    return tax_returns

if __name__ == "__main__":
    # Test function - generate sample documents
    sample_applicant = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "(555) 123-4567",
        "date_of_birth": "1980-05-15",
        "ssn_last_four": "1234",
        "address": {
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip_code": "90210",
            "country": "USA"
        },
        "employment_status": "Employed",
        "employer_name": "Tech Company Inc.",
        "years_at_current_job": 5.5,
        "annual_income": 85000,
        "credit_score": 720
    }
    
    import json
    
    # Generate single tax return
    tax_return = generate_tax_return(sample_applicant, 2022)
    print("Tax Return:")
    print(json.dumps(tax_return, indent=2))
    
    # Generate tax returns for multiple years
    print("\nGenerating tax returns for multiple years...")
    tax_returns = generate_tax_returns_set(sample_applicant, 2023, 2)
    for year, tax_return in tax_returns.items():
        print(f"\nTax Return for {year}:")
        print(f"AGI: ${tax_return['agi']}")
        print(f"Taxable Income: ${tax_return['taxable_income']}")