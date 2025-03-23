
import random
import uuid
import json
from datetime import datetime, timedelta

class MockDataGenerator:
    """Generates mock data for testing"""
    
    def generate_applicant(self):
        """Generate a mock applicant"""
        first_names = ["John", "Jane", "Michael", "Emily", "David", "Sarah"]
        last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis"]
        
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        
        return {
            "first_name": first_name,
            "last_name": last_name,
            "email": f"{first_name.lower()}.{last_name.lower()}@example.com",
            "phone": f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            "ssn": f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}",
            "dob": (datetime.now() - timedelta(days=random.randint(365*25, 365*60))).strftime("%Y-%m-%d"),
            "income": random.randint(50000, 150000),
            "employment": {
                "employer": f"{random.choice(['ABC', 'XYZ', 'Acme', 'Global'])} Corporation",
                "position": random.choice(["Manager", "Engineer", "Analyst", "Developer"]),
                "years": random.randint(1, 15)
            },
            "credit_score": random.randint(650, 850)
        }
    
    def generate_loan(self):
        """Generate mock loan details"""
        loan_types = ["Conventional", "FHA", "VA", "USDA"]
        loan_purposes = ["Purchase", "Refinance"]
        
        return {
            "type": random.choice(loan_types),
            "purpose": random.choice(loan_purposes),
            "amount": random.randint(200000, 800000),
            "down_payment": random.randint(20000, 200000),
            "term": random.choice([15, 30]),
            "interest_rate": round(random.uniform(3.0, 7.0), 2)
        }
    
    def generate_property(self):
        """Generate mock property information"""
        property_types = ["Single Family", "Condominium", "Townhouse", "Multi-Family"]
        states = ["CA", "NY", "TX", "FL", "IL"]
        
        return {
            "address": f"{random.randint(100, 999)} {random.choice(['Main', 'Oak', 'Maple', 'Pine'])} St",
            "city": random.choice(["Los Angeles", "New York", "Chicago", "Houston", "Miami"]),
            "state": random.choice(states),
            "zip": f"{random.randint(10000, 99999)}",
            "type": random.choice(property_types),
            "value": random.randint(250000, 1000000),
            "year_built": random.randint(1950, 2020)
        }
    
    def generate_document(self, document_type):
        """Generate mock document content"""
        # In a real implementation, this would generate actual document content
        # For testing, we'll just return a description of what would be in the document
        
        if document_type == "W2":
            return {
                "employer": f"{random.choice(['ABC', 'XYZ', 'Acme', 'Global'])} Corporation",
                "tax_year": datetime.now().year - 1,
                "wages": random.randint(50000, 150000),
                "federal_tax": random.randint(5000, 30000),
                "state_tax": random.randint(2000, 15000),
                "social_security": random.randint(3000, 9000),
                "medicare": random.randint(700, 2500)
            }
        elif document_type == "Paystub":
            return {
                "employer": f"{random.choice(['ABC', 'XYZ', 'Acme', 'Global'])} Corporation",
                "pay_period": f"{(datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}",
                "gross_pay": random.randint(2000, 8000),
                "net_pay": random.randint(1500, 6000),
                "ytd_earnings": random.randint(10000, 100000)
            }
        elif document_type == "Bank Statement":
            return {
                "bank_name": f"{random.choice(['First', 'United', 'National', 'Capital'])} Bank",
                "account_number": f"****{random.randint(1000, 9999)}",
                "statement_period": f"{(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}",
                "starting_balance": random.randint(5000, 50000),
                "ending_balance": random.randint(5000, 50000),
                "transactions": [
                    {"date": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d"),
                     "description": random.choice(["Deposit", "Withdrawal", "Payment", "Transfer"]),
                     "amount": random.randint(100, 5000)}
                    for _ in range(5)
                ]
            }
        else:
            return {
                "type": document_type,
                "content": f"Mock content for {document_type}",
                "date": datetime.now().strftime("%Y-%m-%d")
            }