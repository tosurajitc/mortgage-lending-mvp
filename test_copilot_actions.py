# scripts/test_copilot_actions.py
import asyncio
import json
import argparse
from src.copilot.actions.application_actions import ApplicationActions
from src.copilot.actions.document_actions import DocumentActions
from src.data.mock_data_generator import MockDataGenerator

import logging
logging.basicConfig(level=logging.DEBUG)

async def test_submit_application():
    """Test submit application action"""
    app_actions = ApplicationActions()
    mock_data = MockDataGenerator()
    
    # Generate mock data
    applicant_data = mock_data.generate_applicant()
    loan_details = mock_data.generate_loan()
    property_info = mock_data.generate_property()
    
    print("Submitting application with data:")
    print(f"Applicant: {json.dumps(applicant_data, indent=2)}")
    print(f"Loan: {json.dumps(loan_details, indent=2)}")
    print(f"Property: {json.dumps(property_info, indent=2)}")
    
    # Call action
    result = await app_actions.submit_application(
    applicant_data,  # existing argument
    loan_details,    # existing argument
    property_info,   # existing argument
    applicantAddress=f"{property_info['address']}, {property_info['city']}, {property_info['state']} {property_info['zip']}",
    applicantSSN=applicant_data['ssn'],
    propertyType=property_info['type'],
    propertyAddress=f"{property_info['address']}, {property_info['city']}, {property_info['state']} {property_info['zip']}",
    propertyValue=property_info['value'],
    loanAmount=loan_details['amount'],
    employmentStatus="EMPLOYED",  # You may need to derive this
    employmentType="FULL_TIME",   # You may need to derive this
    employmentLength=str(applicant_data['employment']['years']),
    annualIncome=applicant_data['income'],
    creditScoreRange=f"{applicant_data['credit_score'] - 50}-{applicant_data['credit_score'] + 50}"
    )
    
    print("\nResult:")
    print(json.dumps(result, indent=2))
    
    return result.get("application_id") if result else None

async def test_check_status(application_id=None):
    """Test check application status action"""
    app_actions = ApplicationActions()
    
    if not application_id:
        # Create a new application first
        application_id = await test_submit_application()
        if not application_id:
            print("Failed to create application for status check")
            return
    
    print(f"\nChecking status for application: {application_id}")
    
    # Call action
    result = await app_actions.check_application_status(application_id)
    
    print("\nResult:")
    print(json.dumps(result, indent=2))

async def test_validate_document(document_type=None):
    """Test document validation action"""
    doc_actions = DocumentActions()
    mock_data = MockDataGenerator()
    
    if not document_type:
        document_type = "W2"  # Default document type
    
    document_content = mock_data.generate_document(document_type)
    
    print(f"\nValidating document of type: {document_type}")
    print(f"Document content (excerpt): {str(document_content)[:100]}...")
    
    # Call action
    result = await doc_actions.validate_document(document_type, document_content)
    
    print("\nResult:")
    print(json.dumps(result, indent=2))

async def test_document_requirements(document_type=None):
    """Test document requirements explanation action"""
    doc_actions = DocumentActions()
    
    if not document_type:
        document_type = "W2"  # Default document type
    
    print(f"\nGetting requirements for document type: {document_type}")
    
    # Call action
    result = await doc_actions.explain_document_requirements(document_type)
    
    print("\nResult:")
    print(json.dumps(result, indent=2))

async def main(args):
    """Main function to run tests"""
    if args.action == "submit":
        await test_submit_application()
    elif args.action == "status":
        await test_check_status(args.application_id)
    elif args.action == "validate":
        await test_validate_document(args.document_type)
    elif args.action == "requirements":
        await test_document_requirements(args.document_type)
    elif args.action == "all":
        app_id = await test_submit_application()
        await test_check_status(app_id)
        await test_validate_document()
        await test_document_requirements()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Copilot Studio actions locally")
    parser.add_argument("action", choices=["submit", "status", "validate", "requirements", "all"],
                       help="Action to test")
    parser.add_argument("--application-id", help="Application ID for status check")
    parser.add_argument("--document-type", help="Document type to validate or explain")
    
    args = parser.parse_args()
    
    asyncio.run(main(args))