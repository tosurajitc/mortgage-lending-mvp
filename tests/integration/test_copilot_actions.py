# tests/integration/test_copilot_actions.py
import pytest
import asyncio
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Add mock implementations for testing
class MockOrchestratorAgent:
    def __init__(self):
        self.applications = {}
    
    async def process_new_application(self, applicant_data, loan_details, property_info):
        """Process a new mortgage application"""
        application_id = str(uuid.uuid4())
        
        # Store application data
        self.applications[application_id] = {
            "applicant": applicant_data,
            "loan": loan_details,
            "property": property_info,
            "status": "submitted",
            "submission_date": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        
        return {
            "application_id": application_id,
            "status": "submitted",
            "submission_date": self.applications[application_id]["submission_date"]
        }
    
    async def get_application_status(self, application_id):
        """Get the status of an application"""
        if application_id not in self.applications:
            return {"error": "Application not found"}
        
        app = self.applications[application_id]
        
        return {
            "application_id": application_id,
            "status": app["status"],
            "submission_date": app["submission_date"],
            "last_updated": app["last_updated"],
            "next_steps": ["We are reviewing your application"]
        }

class MockDocumentAnalysisAgent:
    def __init__(self):
        self.document_requirements = {
            "W2": {
                "description": "Annual wage and tax statement from your employer",
                "requirements": [
                    "Must be from the past 2 years",
                    "Must show full tax year information"
                ]
            },
            "Paystub": {
                "description": "Recent pay statement from your employer",
                "requirements": [
                    "Must be from within the last 30 days",
                    "Must show year-to-date earnings"
                ]
            }
        }
    
    async def validate_document(self, document_type, document_content):
        """Validate a document"""
        return {
            "is_valid": True,
            "issues": [],
            "document_type": document_type
        }
    
    async def get_document_requirements(self, document_type):
        """Get requirements for a document type"""
        if document_type not in self.document_requirements:
            return {
                "error": f"Unknown document type: {document_type}",
                "available_types": list(self.document_requirements.keys())
            }
        
        requirements = self.document_requirements[document_type]
        
        return {
            "document_type": document_type,
            "description": requirements["description"],
            "requirements": requirements["requirements"]
        }

# Mock application actions
class ApplicationActions:
    def __init__(self):
        self.orchestrator = MockOrchestratorAgent()
    
    async def submit_application(self, applicant_data, loan_details, property_info):
        """Submit a new mortgage application"""
        return await self.orchestrator.process_new_application(
            applicant_data, loan_details, property_info
        )
    
    async def check_application_status(self, application_id):
        """Check the status of an existing application"""
        return await self.orchestrator.get_application_status(application_id)

# Mock document actions
class DocumentActions:
    def __init__(self):
        self.document_agent = MockDocumentAnalysisAgent()
    
    async def validate_document(self, document_type, document_content):
        """Validate a document before submission"""
        return await self.document_agent.validate_document(document_type, document_content)
    
    async def explain_document_requirements(self, document_type):
        """Explain the requirements for a specific document type"""
        return await self.document_agent.get_document_requirements(document_type)

# Mock data generator
class MockDataGenerator:
    """Generates mock data for testing"""
    
    def generate_applicant(self):
        """Generate a mock applicant"""
        return {
            "first_name": "John",
            "last_name": "Smith",
            "email": "john.smith@example.com",
            "phone": "555-123-4567",
            "ssn": "123-45-6789",
            "dob": "1980-01-01",
            "income": 85000,
            "employment": {
                "employer": "ABC Corporation",
                "position": "Engineer",
                "years": 5
            },
            "credit_score": 720
        }
    
    def generate_loan(self):
        """Generate mock loan details"""
        return {
            "type": "Conventional",
            "purpose": "Purchase",
            "amount": 350000,
            "down_payment": 70000,
            "term": 30,
            "interest_rate": 5.25
        }
    
    def generate_property(self):
        """Generate mock property information"""
        return {
            "address": "123 Main St",
            "city": "New York",
            "state": "NY",
            "zip": "10001",
            "type": "Single Family",
            "value": 450000,
            "year_built": 1995
        }
    
    def generate_document(self, document_type):
        """Generate mock document content"""
        if document_type == "W2":
            return {
                "employer": "ABC Corporation",
                "tax_year": 2023,
                "wages": 85000,
                "federal_tax": 15000
            }
        elif document_type == "Paystub":
            return {
                "employer": "ABC Corporation",
                "pay_period": "2024-03-01 to 2024-03-15",
                "gross_pay": 3500,
                "net_pay": 2500,
                "ytd_earnings": 21000
            }
        else:
            return {
                "type": document_type,
                "content": f"Mock content for {document_type}"
            }

class TestCopilotActions:
    """Test suite for Copilot Studio actions"""
    
    @classmethod
    def setup_class(cls):
        """Set up test fixtures"""
        cls.app_actions = ApplicationActions()
        cls.doc_actions = DocumentActions()
        cls.mock_data = MockDataGenerator()
        
        # Create directory for test outputs
        os.makedirs("tests/outputs", exist_ok=True)
    
    def test_submit_application(self):
        """Test submitting a new mortgage application"""
        # Generate mock application data
        applicant_data = self.mock_data.generate_applicant()
        loan_details = self.mock_data.generate_loan()
        property_info = self.mock_data.generate_property()
        
        # Call the action
        result = asyncio.run(self.app_actions.submit_application(
            applicant_data, loan_details, property_info
        ))
        
        # Save result for inspection
        with open("tests/outputs/submit_application_result.json", "w") as f:
            json.dump(result, f, indent=2)
        
        # Assertions
        assert result is not None
        assert "application_id" in result
        assert "status" in result
        assert result["status"] == "submitted"
    
    def test_check_application_status(self):
        """Test checking an application status"""
        # First submit an application to get an ID
        applicant_data = self.mock_data.generate_applicant()
        loan_details = self.mock_data.generate_loan()
        property_info = self.mock_data.generate_property()
        
        submit_result = asyncio.run(self.app_actions.submit_application(
            applicant_data, loan_details, property_info
        ))
        
        application_id = submit_result["application_id"]
        
        # Check status
        result = asyncio.run(self.app_actions.check_application_status(application_id))
        
        # Save result for inspection
        with open("tests/outputs/check_status_result.json", "w") as f:
            json.dump(result, f, indent=2)
        
        # Assertions
        assert result is not None
        assert "application_id" in result
        assert result["application_id"] == application_id
        assert "status" in result
    
    def test_validate_document(self):
        """Test document validation"""
        # Generate mock document
        document_type = "W2"
        document_content = self.mock_data.generate_document(document_type)
        
        # Validate document
        result = asyncio.run(self.doc_actions.validate_document(document_type, document_content))
        
        # Save result for inspection
        with open("tests/outputs/validate_document_result.json", "w") as f:
            json.dump(result, f, indent=2)
        
        # Assertions
        assert result is not None
        assert "is_valid" in result
        assert "issues" in result
    
    def test_explain_document_requirements(self):
        """Test explaining document requirements"""
        document_type = "W2"
        
        # Get explanation
        result = asyncio.run(self.doc_actions.explain_document_requirements(document_type))
        
        # Save result for inspection
        with open("tests/outputs/document_requirements_result.json", "w") as f:
            json.dump(result, f, indent=2)
        
        # Assertions
        assert result is not None
        assert "document_type" in result
        assert document_type == result["document_type"]
        assert "requirements" in result