"""
Income Document Generator

This module generates mock income-related documents for mortgage applications:
- W-2 forms
- Pay stubs

These are simplified representations with the key data that would be extracted
by the document processing agent.
"""

import random
import datetime
import uuid
from typing import Dict, Any, List, Optional

def generate_w2_form(applicant_data: Dict[str, Any], tax_year: int) -> Dict[str, Any]:
    """
    Generate a mock W-2 form for an applicant.
    
    Args:
        applicant_data: Applicant information
        tax_year: Tax year for the W-2
    
    Returns:
        Dictionary representing a W-2 form
    """
    first_name = applicant_data["first_name"]
    last_name = applicant_data["last_name"]
    address = applicant_data["address"]
    annual_income = applicant_data.get("annual_income", 75000)  # Default if not provided
    
    # Generate employer info if not in applicant data
    employer_name = applicant_data.get("employer_name", "Example Corporation")
    
    # Generate employer address if not provided
    employer_address = {
        "street": "1000 Corporate Way",
        "city": "Business City",
        "state": "CA",
        "zip_code": "90210",
        "country": "USA"
    }
    
    # Calculate income components
    wages = annual_income
    federal_tax_withheld = round(wages * random.uniform(0.15, 0.28), 2)
    social_security_wages = wages
    social_security_tax = round(social_security_wages * 0.062, 2)
    medicare_wages = wages
    medicare_tax = round(medicare_wages * 0.0145, 2)
    state_tax_withheld = round(wages * random.uniform(0.04, 0.095), 2)
    
    # Generate document
    document = {
        "document_type": "W-2",
        "tax_year": tax_year,
        "employee": {
            "name": f"{first_name} {last_name}",
            "ssn_last_four": applicant_data.get("ssn_last_four", "XXXX"),
            "address": address
        },
        "employer": {
            "name": employer_name,
            "ein": f"{random.randint(10, 99)}-{random.randint(1000000, 9999999)}",
            "address": employer_address
        },
        "earnings": {
            "wages_tips_other": wages,
            "federal_income_tax_withheld": federal_tax_withheld,
            "social_security_wages": social_security_wages,
            "social_security_tax_withheld": social_security_tax,
            "medicare_wages_and_tips": medicare_wages,
            "medicare_tax_withheld": medicare_tax,
            "state_wages": wages,
            "state_income_tax": state_tax_withheld
        },
        "metadata": {
            "document_id": str(uuid.uuid4()),
            "extraction_confidence": random.uniform(0.85, 0.99)
        }
    }
    
    return document

def generate_pay_stub(applicant_data: Dict[str, Any], pay_date: str) -> Dict[str, Any]:
    """
    Generate a mock pay stub for an applicant.
    
    Args:
        applicant_data: Applicant information
        pay_date: Pay date for the stub
        
    Returns:
        Dictionary representing a pay stub
    """
    first_name = applicant_data["first_name"]
    last_name = applicant_data["last_name"]
    annual_income = applicant_data.get("annual_income", 75000)  # Default if not provided
    
    # Determine pay frequency (bi-weekly is most common)
    pay_frequencies = ["Weekly", "Bi-weekly", "Semi-monthly", "Monthly"]
    frequencies_weights = [0.2, 0.6, 0.15, 0.05]
    pay_frequency = random.choices(pay_frequencies, frequencies_weights, k=1)[0]
    
    # Calculate pay period details
    if pay_frequency == "Weekly":
        pay_periods_per_year = 52
        period_label = "Weekly"
    elif pay_frequency == "Bi-weekly":
        pay_periods_per_year = 26
        period_label = "Bi-weekly"
    elif pay_frequency == "Semi-monthly":
        pay_periods_per_year = 24
        period_label = "Semi-monthly"
    else:  # Monthly
        pay_periods_per_year = 12
        period_label = "Monthly"
    
    # Calculate gross pay for this period
    period_gross_pay = round(annual_income / pay_periods_per_year, 2)
    
    # Calculate deductions
    federal_tax = round(period_gross_pay * random.uniform(0.15, 0.28), 2)
    state_tax = round(period_gross_pay * random.uniform(0.04, 0.095), 2)
    social_security = round(period_gross_pay * 0.062, 2)
    medicare = round(period_gross_pay * 0.0145, 2)
    
    # Optional deductions
    has_health_insurance = random.random() < 0.8  # 80% chance
    health_insurance = round(random.uniform(50, 250), 2) if has_health_insurance else 0
    
    has_401k = random.random() < 0.7  # 70% chance
    contribution_pct = random.uniform(0.03, 0.1) if has_401k else 0
    retirement_contribution = round(period_gross_pay * contribution_pct, 2)
    
    # Calculate net pay
    total_deductions = federal_tax + state_tax + social_security + medicare + health_insurance + retirement_contribution
    net_pay = period_gross_pay - total_deductions
    
    # Calculate YTD values (assuming this pay period is included)
    current_date = datetime.datetime.strptime(pay_date, "%Y-%m-%d")
    start_of_year = datetime.datetime(current_date.year, 1, 1)
    days_passed = (current_date - start_of_year).days
    days_in_year = 366 if current_date.year % 4 == 0 else 365
    
    # Approximate how many pay periods have passed
    pay_periods_passed = max(1, round((days_passed / days_in_year) * pay_periods_per_year))
    
    # Calculate YTD totals
    # Add some noise to make it look realistic (±5%)
    noise_factor = random.uniform(0.95, 1.05)
    ytd_gross = round(period_gross_pay * pay_periods_passed * noise_factor, 2)
    ytd_federal_tax = round(federal_tax * pay_periods_passed * noise_factor, 2)
    ytd_state_tax = round(state_tax * pay_periods_passed * noise_factor, 2)
    ytd_social_security = round(social_security * pay_periods_passed * noise_factor, 2)
    ytd_medicare = round(medicare * pay_periods_passed * noise_factor, 2)
    ytd_health_insurance = round(health_insurance * pay_periods_passed * noise_factor, 2)
    ytd_retirement = round(retirement_contribution * pay_periods_passed * noise_factor, 2)
    ytd_net = ytd_gross - (ytd_federal_tax + ytd_state_tax + ytd_social_security + ytd_medicare + ytd_health_insurance + ytd_retirement)
    
    # Generate employer info if not in applicant data
    employer_name = applicant_data.get("employer_name", "Example Corporation")
    
    # Generate document
    document = {
        "document_type": "Pay Stub",
        "pay_date": pay_date,
        "pay_period": f"{period_label}",
        "employee": {
            "name": f"{first_name} {last_name}",
            "ssn_last_four": applicant_data.get("ssn_last_four", "XXXX"),
            "employee_id": f"EMP{random.randint(10000, 99999)}"
        },
        "employer": {
            "name": employer_name,
            "ein": f"{random.randint(10, 99)}-{random.randint(1000000, 9999999)}"
        },
        "earnings": {
            "pay_rate_type": "Salary",
            "pay_frequency": pay_frequency,
            "gross_pay_current": period_gross_pay,
            "gross_pay_ytd": ytd_gross
        },
        "deductions": {
            "federal_tax_current": federal_tax,
            "federal_tax_ytd": ytd_federal_tax,
            "state_tax_current": state_tax,
            "state_tax_ytd": ytd_state_tax,
            "social_security_current": social_security,
            "social_security_ytd": ytd_social_security,
            "medicare_current": medicare,
            "medicare_ytd": ytd_medicare
        },
        "net_pay": {
            "current": net_pay,
            "ytd": ytd_net
        },
        "metadata": {
            "document_id": str(uuid.uuid4()),
            "extraction_confidence": random.uniform(0.85, 0.99)
        }
    }
    
    # Add optional deductions if present
    if has_health_insurance:
        document["deductions"]["health_insurance_current"] = health_insurance
        document["deductions"]["health_insurance_ytd"] = ytd_health_insurance
    
    if has_401k:
        document["deductions"]["retirement_contribution_current"] = retirement_contribution
        document["deductions"]["retirement_contribution_ytd"] = ytd_retirement
        document["deductions"]["retirement_contribution_percent"] = round(contribution_pct * 100, 1)
    
    return document

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
    
    # Generate W-2
    w2 = generate_w2_form(sample_applicant, 2022)
    print("W-2 Form:")
    print(json.dumps(w2, indent=2))
    
    # Generate pay stub
    pay_stub = generate_pay_stub(sample_applicant, "2023-05-15")
    print("\nPay Stub:")
    print(json.dumps(pay_stub, indent=2))