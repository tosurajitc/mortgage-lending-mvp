"""
Credit Document Generator

This module generates mock credit-related documents for mortgage applications:
- Credit reports

These are simplified representations with the key data that would be extracted
by the document processing agent.
"""

import random
import datetime
import uuid
from typing import Dict, Any, List, Optional

def generate_credit_report(applicant_data: Dict[str, Any], report_date: str) -> Dict[str, Any]:
    """
    Generate a mock credit report for an applicant.
    
    Args:
        applicant_data: Applicant information
        report_date: Date of the credit report
        
    Returns:
        Dictionary representing a credit report
    """
    first_name = applicant_data["first_name"]
    last_name = applicant_data["last_name"]
    credit_score = applicant_data.get("credit_score", 720)  # Default if not provided
    
    # Generate basic information
    credit_bureau = random.choice(["Experian", "Equifax", "TransUnion"])
    
    # Generate account information based on credit score
    num_accounts = random.randint(3, 15)
    accounts = []
    
    # Determine appropriate account mix and payment history based on credit score
    if credit_score >= 740:  # Excellent credit
        late_payment_probability = 0.05
        high_utilization_probability = 0.1
        account_age_range = (2, 20)  # Years
        closed_account_probability = 0.2
    elif credit_score >= 700:  # Good credit
        late_payment_probability = 0.1
        high_utilization_probability = 0.2
        account_age_range = (1, 15)
        closed_account_probability = 0.3
    elif credit_score >= 650:  # Fair credit
        late_payment_probability = 0.2
        high_utilization_probability = 0.4
        account_age_range = (1, 10)
        closed_account_probability = 0.3
    else:  # Poor credit
        late_payment_probability = 0.4
        high_utilization_probability = 0.6
        account_age_range = (0, 8)
        closed_account_probability = 0.4
    
    # Account types to generate
    account_types = [
        # (account_type, credit_limit_range, typical_balance_range)
        ("Credit Card", (1000, 20000), (0, 0.9)),
        ("Auto Loan", (10000, 50000), (0, 1.0)),
        ("Personal Loan", (5000, 25000), (0, 1.0)),
        ("Student Loan", (5000, 100000), (0.5, 1.0)),
        ("Mortgage", (100000, 500000), (0.7, 1.0))
    ]
    
    # Generate accounts
    for i in range(num_accounts):
        # Select account type with weighting
        if i == 0:  # Ensure at least one credit card
            account_type, limit_range, balance_range = account_types[0]
        else:
            account_type, limit_range, balance_range = random.choice(account_types)
        
        # Generate account details
        account_status = "Closed" if random.random() < closed_account_probability else "Open"
        
        if account_type == "Credit Card":
            credit_limit = random.randint(*limit_range)
            current_balance = round(credit_limit * random.uniform(*balance_range)) if account_status == "Open" else 0
            credit_utilization = round(current_balance / credit_limit, 2) if credit_limit > 0 else 0
        else:
            original_amount = random.randint(*limit_range)
            current_balance = round(original_amount * random.uniform(*balance_range)) if account_status == "Open" else 0
            credit_limit = original_amount
            credit_utilization = None
        
        # Account age
        account_age_years = random.randint(*account_age_range)
        report_date_obj = datetime.datetime.strptime(report_date, "%Y-%m-%d")
        open_date = (report_date_obj - datetime.timedelta(days=account_age_years*365)).strftime("%Y-%m-%d")
        
        # Generate payment history
        payment_history = []
        history_months = min(24, account_age_years * 12)
        
        for month in range(history_months):
            is_late = random.random() < late_payment_probability
            payment_status = random.choice(["30", "60", "90"]) if is_late else "OK"
            payment_history.append(payment_status)
        
        # Reverse so most recent is first
        payment_history.reverse()
        
        # Create account entry
        account = {
            "account_type": account_type,
            "creditor_name": random.choice([
                "Chase Bank", "Bank of America", "Wells Fargo", "Citibank", 
                "Capital One", "Discover", "American Express", "US Bank",
                "PNC Bank", "TD Bank", "Synchrony Financial"
            ]),
            "account_number_last_four": f"{random.randint(1000, 9999)}",
            "open_date": open_date,
            "status": account_status,
            "credit_limit": credit_limit,
            "current_balance": current_balance,
            "payment_history": payment_history
        }
        
        if credit_utilization is not None:
            account["credit_utilization"] = credit_utilization
        
        accounts.append(account)
    
    # Calculate totals
    total_accounts = len(accounts)
    open_accounts = sum(1 for account in accounts if account["status"] == "Open")
    closed_accounts = total_accounts - open_accounts
    
    total_balance = sum(account["current_balance"] for account in accounts)
    
    # Determine public records based on credit score
    public_records = []
    if credit_score < 650 and random.random() < 0.3:
        public_records.append({
            "record_type": random.choice(["Collection", "Tax Lien", "Civil Judgment"]),
            "status": random.choice(["Paid", "Unpaid"]),
            "date_filed": (report_date_obj - datetime.timedelta(days=random.randint(365, 1825))).strftime("%Y-%m-%d"),
            "amount": round(random.uniform(500, 10000), 2)
        })
    
    # Determine inquiries
    num_inquiries = 0
    if credit_score >= 740:
        num_inquiries = random.randint(0, 2)
    elif credit_score >= 700:
        num_inquiries = random.randint(1, 3)
    elif credit_score >= 650:
        num_inquiries = random.randint(2, 5)
    else:
        num_inquiries = random.randint(3, 8)
    
    inquiries = []
    for _ in range(num_inquiries):
        inquiry_date = (report_date_obj - datetime.timedelta(days=random.randint(1, 730))).strftime("%Y-%m-%d")
        inquiries.append({
            "date": inquiry_date,
            "creditor": random.choice([
                "Auto Lender", "Credit Card Company", "Bank", "Mortgage Company",
                "Department Store", "Credit Union", "Finance Company"
            ])
        })
    
    # Generate credit score factors
    positive_factors = []
    negative_factors = []
    
    # Potential factors
    all_positive_factors = [
        "Length of credit history",
        "Payment history",
        "Credit utilization",
        "Credit mix",
        "Recent credit behavior",
        "Available credit"
    ]
    
    all_negative_factors = [
        "High credit utilization",
        "Recent late payments",
        "Limited credit history",
        "Too many recent inquiries",
        "High loan balances",
        "Limited credit mix",
        "Recent delinquency"
    ]
    
    # Select factors based on credit score
    if credit_score >= 740:
        positive_count = random.randint(3, 5)
        negative_count = random.randint(0, 1)
    elif credit_score >= 700:
        positive_count = random.randint(2, 4)
        negative_count = random.randint(1, 2)
    elif credit_score >= 650:
        positive_count = random.randint(1, 3)
        negative_count = random.randint(2, 3)
    else:
        positive_count = random.randint(0, 2)
        negative_count = random.randint(3, 5)
    
    positive_factors = random.sample(all_positive_factors, min(positive_count, len(all_positive_factors)))
    negative_factors = random.sample(all_negative_factors, min(negative_count, len(all_negative_factors)))
    
    # Generate document
    document = {
        "document_type": "Credit Report",
        "report_date": report_date,
        "credit_bureau": credit_bureau,
        "personal_info": {
            "name": f"{first_name} {last_name}",
            "ssn_last_four": applicant_data.get("ssn_last_four", "XXXX"),
            "current_address": applicant_data.get("address", {})
        },
        "credit_score": {
            "score": credit_score,
            "model": "FICO Score 8",
            "range": "300-850",
            "factors": {
                "positive": positive_factors,
                "negative": negative_factors
            }
        },
        "accounts": {
            "total_accounts": total_accounts,
            "open_accounts": open_accounts,
            "closed_accounts": closed_accounts,
            "total_balance": total_balance,
            "account_details": accounts
        },
        "public_records": public_records,
        "inquiries": {
            "total_inquiries": num_inquiries,
            "inquiry_details": inquiries
        },
        "metadata": {
            "document_id": str(uuid.uuid4()),
            "extraction_confidence": random.uniform(0.85, 0.99)
        }
    }
    
    # Calculate average account age
    if accounts:
        report_date_obj = datetime.datetime.strptime(report_date, "%Y-%m-%d")
        account_ages = []
        
        for account in accounts:
            open_date_obj = datetime.datetime.strptime(account["open_date"], "%Y-%m-%d")
            age_days = (report_date_obj - open_date_obj).days
            account_ages.append(age_days / 365.25)  # Convert to years
        
        avg_account_age = round(sum(account_ages) / len(account_ages), 1)
        document["accounts"]["average_age_years"] = avg_account_age
    
    # Calculate overall utilization for credit cards
    credit_cards = [account for account in accounts if account["account_type"] == "Credit Card" and account["status"] == "Open"]
    if credit_cards:
        total_limits = sum(card["credit_limit"] for card in credit_cards)
        total_balances = sum(card["current_balance"] for card in credit_cards)
        
        if total_limits > 0:
            overall_utilization = round(total_balances / total_limits, 2)
            document["accounts"]["overall_credit_utilization"] = overall_utilization
    
    return document

def generate_credit_reports_for_applicants(applicants: List[Dict[str, Any]], report_date: str) -> Dict[str, Dict[str, Any]]:
    """
    Generate credit reports for a list of applicants.
    
    Args:
        applicants: List of applicant data dictionaries
        report_date: Date for the credit reports
        
    Returns:
        Dictionary mapping applicant names to credit reports
    """
    reports = {}
    
    for applicant in applicants:
        name = f"{applicant['first_name']} {applicant['last_name']}"
        report = generate_credit_report(applicant, report_date)
        reports[name] = report
    
    return reports

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
    
    # Generate credit report
    credit_report = generate_credit_report(sample_applicant, "2023-05-15")
    print("Credit Report:")
    print(json.dumps(credit_report, indent=2))
    
    # Print some key details
    print(f"\nCredit Score: {credit_report['credit_score']['score']}")
    print(f"Credit Bureau: {credit_report['credit_bureau']}")
    print(f"Total Accounts: {credit_report['accounts']['total_accounts']}")
    print(f"Inquiries: {credit_report['inquiries']['total_inquiries']}")