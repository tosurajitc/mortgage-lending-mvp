"""
Bank Document Generator

This module generates mock bank-related documents for mortgage applications:
- Bank statements 

These are simplified representations with the key data that would be extracted
by the document processing agent.
"""

import random
import datetime
import uuid
from typing import Dict, Any, List, Optional

def generate_bank_statement(applicant_data: Dict[str, Any], statement_date: str, days: int = 30) -> Dict[str, Any]:
    """
    Generate a mock bank statement for an applicant.
    
    Args:
        applicant_data: Applicant information
        statement_date: End date for the statement
        days: Number of days in the statement period
        
    Returns:
        Dictionary representing a bank statement
    """
    first_name = applicant_data["first_name"]
    last_name = applicant_data["last_name"]
    address = applicant_data["address"]
    annual_income = applicant_data.get("annual_income", 75000)  # Default if not provided
    
    # Calculate monthly income and spending
    monthly_income = annual_income / 12
    monthly_spending = monthly_income * random.uniform(0.5, 0.9)  # 50-90% of income
    
    # Generate account info
    account_type = random.choice(["Checking", "Savings"])
    account_number_last_four = f"{random.randint(1000, 9999)}"
    
    # Generate bank info
    bank_names = [
        "First National Bank", "Citizens Trust", "Metro Credit Union", 
        "Coastal Savings", "United Community Bank", "Summit Financial"
    ]
    bank_name = random.choice(bank_names)
    
    # Calculate statement period
    end_date = datetime.datetime.strptime(statement_date, "%Y-%m-%d")
    start_date = end_date - datetime.timedelta(days=days)
    
    # Format dates for output
    statement_period = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d")
    }
    
    # Generate beginning and ending balances
    # Starting with a reasonable balance based on income
    beginning_balance = round(monthly_income * random.uniform(0.5, 3.0), 2)
    
    # Generate transactions
    transactions = []
    
    # Add regular income deposits
    pay_date_1 = start_date + datetime.timedelta(days=random.randint(1, 15))
    transactions.append({
        "date": pay_date_1.strftime("%Y-%m-%d"),
        "description": f"DIRECT DEPOSIT - {applicant_data.get('employer_name', 'EMPLOYER')}",
        "amount": round(monthly_income / 2, 2),
        "type": "deposit"
    })
    
    # Second paycheck if in the statement period
    pay_date_2 = pay_date_1 + datetime.timedelta(days=15)
    if pay_date_2 < end_date:
        transactions.append({
            "date": pay_date_2.strftime("%Y-%m-%d"),
            "description": f"DIRECT DEPOSIT - {applicant_data.get('employer_name', 'EMPLOYER')}",
            "amount": round(monthly_income / 2, 2),
            "type": "deposit"
        })
    
    # Add some other possible deposits
    if random.random() < 0.3:  # 30% chance
        deposit_date = start_date + datetime.timedelta(days=random.randint(5, days-5))
        transactions.append({
            "date": deposit_date.strftime("%Y-%m-%d"),
            "description": random.choice([
                "TRANSFER FROM SAVINGS", 
                "MOBILE DEPOSIT",
                "ATM DEPOSIT",
                "ZELLE PAYMENT",
                "VENMO TRANSFER"
            ]),
            "amount": round(random.uniform(100, 1000), 2),
            "type": "deposit"
        })
    
    # Add withdrawal transactions
    num_withdrawals = random.randint(15, 30)
    common_merchants = [
        "GROCERY STORE", "GAS STATION", "AMAZON", "NETFLIX", "UTILITY CO",
        "INTERNET SERVICE", "CELL PHONE", "RESTAURANT", "COFFEE SHOP",
        "PHARMACY", "DEPARTMENT STORE", "HOME IMPROVEMENT", "INSURANCE"
    ]
    
    # Generate withdrawal amounts that add up close to monthly_spending
    withdrawal_amounts = []
    remaining_spending = monthly_spending
    
    # First generate major expenses
    rent_mortgage = monthly_income * random.uniform(0.2, 0.4)
    withdrawal_amounts.append(rent_mortgage)
    remaining_spending -= rent_mortgage
    
    # Then distribute the rest
    while remaining_spending > 10:
        if len(withdrawal_amounts) >= num_withdrawals - 1:
            withdrawal_amounts.append(remaining_spending)
            break
            
        amount = min(remaining_spending, random.uniform(10, 200))
        withdrawal_amounts.append(amount)
        remaining_spending -= amount
    
    # Randomize and create transactions
    random.shuffle(withdrawal_amounts)
    
    for i, amount in enumerate(withdrawal_amounts):
        transaction_date = start_date + datetime.timedelta(days=random.randint(1, days-1))
        
        # Format description based on amount
        if amount > monthly_income * 0.2:
            description = "RENT" if random.random() < 0.7 else "MORTGAGE"
        else:
            description = random.choice(common_merchants)
            
        transactions.append({
            "date": transaction_date.strftime("%Y-%m-%d"),
            "description": description,
            "amount": round(amount, 2),
            "type": "withdrawal"
        })
    
    # Sort transactions by date
    transactions.sort(key=lambda x: x["date"])
    
    # Calculate ending balance
    total_deposits = sum(t["amount"] for t in transactions if t["type"] == "deposit")
    total_withdrawals = sum(t["amount"] for t in transactions if t["type"] == "withdrawal")
    ending_balance = beginning_balance + total_deposits - total_withdrawals
    
    # Generate document
    document = {
        "document_type": "Bank Statement",
        "statement_period": statement_period,
        "account_holder": {
            "name": f"{first_name} {last_name}",
            "address": address
        },
        "bank_info": {
            "name": bank_name,
            "address": {
                "street": f"{random.randint(100, 999)} Financial Way",
                "city": random.choice(["New York", "Chicago", "San Francisco", "Dallas", "Boston"]),
                "state": random.choice(["NY", "IL", "CA", "TX", "MA"]),
                "zip_code": f"{random.randint(10000, 99999)}"
            }
        },
        "account_info": {
            "type": account_type,
            "number_last_four": account_number_last_four
        },
        "summary": {
            "beginning_balance": beginning_balance,
            "total_deposits": total_deposits,
            "total_withdrawals": total_withdrawals,
            "ending_balance": ending_balance
        },
        "transactions": transactions,
        "metadata": {
            "document_id": str(uuid.uuid4()),
            "extraction_confidence": random.uniform(0.85, 0.99)
        }
    }
    
    return document

def generate_bank_statements_sequence(applicant_data: Dict[str, Any], end_date: str, num_statements: int = 3) -> List[Dict[str, Any]]:
    """
    Generate a sequence of consecutive bank statements.
    
    Args:
        applicant_data: Applicant information
        end_date: End date for the most recent statement
        num_statements: Number of statements to generate
        
    Returns:
        List of bank statements in reverse chronological order
    """
    statements = []
    current_end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    
    for i in range(num_statements):
        statement_date = current_end_date.strftime("%Y-%m-%d")
        statement = generate_bank_statement(applicant_data, statement_date, 30)
        statements.append(statement)
        
        # Move to previous month
        current_end_date = current_end_date - datetime.timedelta(days=30)
    
    return statements

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
    
    # Generate single bank statement
    statement = generate_bank_statement(sample_applicant, "2023-05-31")
    print("Bank Statement:")
    print(json.dumps(statement, indent=2))
    
    # Generate sequence of statements
    print("\nGenerating sequence of statements...")
    statements = generate_bank_statements_sequence(sample_applicant, "2023-05-31", 3)
    print(f"Generated {len(statements)} statements")