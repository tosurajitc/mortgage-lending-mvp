"""
Document Generator

This is the main module that coordinates generation of mock documents for mortgage applications.
It imports specialized generators for different document types and provides a unified interface.

Usage:
    import document_generator as dg
    
    # Generate a complete document set for an applicant
    documents = dg.generate_document_set(applicant_data, property_data, loan_data)
"""

import os
import json
import random
import datetime
import uuid
from typing import Dict, Any, List, Tuple, Optional

# Import specialized document generators
from .generators import (
    income_document_generator,
    bank_document_generator, 
    tax_document_generator,
    credit_document_generator,
    property_document_generator
)

def generate_document_set(
    applicant_data: Dict[str, Any],
    property_data: Optional[Dict[str, Any]] = None,
    loan_data: Optional[Dict[str, Any]] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Generate a complete set of documents for a mortgage application.
    
    Args:
        applicant_data: Applicant information
        property_data: Property information (optional)
        loan_data: Loan information (optional)
        
    Returns:
        Dictionary with lists of documents by category
    """
    # Get current date and prior dates for documents
    current_date = datetime.datetime.now()
    current_year = current_date.year
    
    # Generate dates for various documents
    tax_year = current_year - 1
    statement_date = (current_date - datetime.timedelta(days=random.randint(5, 30))).strftime("%Y-%m-%d")
    pay_date = (current_date - datetime.timedelta(days=random.randint(1, 20))).strftime("%Y-%m-%d")
    credit_report_date = (current_date - datetime.timedelta(days=random.randint(1, 45))).strftime("%Y-%m-%d")
    
    # Generate income documents
    w2_forms = [
        income_document_generator.generate_w2_form(applicant_data, tax_year),
        income_document_generator.generate_w2_form(applicant_data, tax_year - 1)
    ]
    
    pay_stubs = [
        income_document_generator.generate_pay_stub(applicant_data, pay_date),
        income_document_generator.generate_pay_stub(
            applicant_data, 
            (datetime.datetime.strptime(pay_date, "%Y-%m-%d") - datetime.timedelta(days=15)).strftime("%Y-%m-%d")
        )
    ]
    
    # Generate bank documents
    bank_statements = [
        bank_document_generator.generate_bank_statement(applicant_data, statement_date, 30),
        bank_document_generator.generate_bank_statement(
            applicant_data,
            (datetime.datetime.strptime(statement_date, "%Y-%m-%d") - datetime.timedelta(days=30)).strftime("%Y-%m-%d"),
            30
        ),
        bank_document_generator.generate_bank_statement(
            applicant_data,
            (datetime.datetime.strptime(statement_date, "%Y-%m-%d") - datetime.timedelta(days=60)).strftime("%Y-%m-%d"),
            30
        )
    ]
    
    # Generate tax documents
    tax_returns = [
        tax_document_generator.generate_tax_return(applicant_data, tax_year),
        tax_document_generator.generate_tax_return(applicant_data, tax_year - 1)
    ]
    
    # Generate credit document
    credit_report = credit_document_generator.generate_credit_report(applicant_data, credit_report_date)
    
    # Generate property document if property data provided
    property_appraisal = None
    if property_data:
        property_appraisal = property_document_generator.generate_property_appraisal(
            property_data, 
            applicant_data,
            (current_date - datetime.timedelta(days=random.randint(5, 30))).strftime("%Y-%m-%d")
        )
    
    # Combine all documents
    document_set = {
        "income_documents": {
            "w2_forms": w2_forms,
            "pay_stubs": pay_stubs
        },
        "bank_documents": {
            "bank_statements": bank_statements
        },
        "tax_documents": {
            "tax_returns": tax_returns
        },
        "credit_documents": {
            "credit_report": credit_report
        }
    }
    
    # Add property documents if available
    if property_appraisal:
        document_set["property_documents"] = {
            "property_appraisal": property_appraisal
        }
    
    return document_set

def save_document_set(document_set: Dict[str, Any], output_dir: str, applicant_id: str) -> None:
    """
    Save a document set to files.
    
    Args:
        document_set: Document set to save
        output_dir: Directory to save documents in
        applicant_id: ID to use in filenames
    """
    # Create base directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create subdirectories for document types
    for doc_type in document_set.keys():
        type_dir = os.path.join(output_dir, doc_type)
        os.makedirs(type_dir, exist_ok=True)
        
        # Save each document category
        for category, docs in document_set[doc_type].items():
            if isinstance(docs, list):
                # Save list of documents
                for i, doc in enumerate(docs):
                    filename = f"{applicant_id}_{category}_{i+1}.json"
                    with open(os.path.join(type_dir, filename), 'w') as f:
                        json.dump(doc, f, indent=2)
            else:
                # Save single document
                filename = f"{applicant_id}_{category}.json"
                with open(os.path.join(type_dir, filename), 'w') as f:
                    json.dump(docs, f, indent=2)
    
    print(f"Saved document set for applicant {applicant_id} to {output_dir}")

def generate_document_set_for_application(
    application_data: Dict[str, Any], 
    output_dir: str = "mock_data/sample_data/documents"
) -> Dict[str, Any]:
    """
    Generate a complete document set for a mortgage application.
    
    Args:
        application_data: Complete application data including applicant, property, and loan info
        output_dir: Directory to save documents in
        
    Returns:
        Generated document set
    """
    # Extract components from application
    applicant_data = application_data.get("primary_applicant", {})
    property_data = application_data.get("property_info", {})
    loan_data = application_data.get("loan_details", {})
    
    # Add co-applicant if available
    if "co_applicant" in application_data:
        applicant_data["co_applicant"] = application_data["co_applicant"]
    
    # Generate documents
    document_set = generate_document_set(applicant_data, property_data, loan_data)
    
    # Save documents if output directory specified
    if output_dir:
        application_id = application_data.get("application_id", str(uuid.uuid4()))
        save_document_set(document_set, output_dir, application_id)
    
    return document_set

if __name__ == "__main__":
    # Simple test to generate documents for a sample applicant
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
    
    sample_property = {
        "address": {
            "street": "456 Elm St",
            "city": "Somewhere",
            "state": "CA",
            "zip_code": "90211",
            "country": "USA"
        },
        "property_type": "Single Family Home",
        "estimated_value": 450000,
        "year_built": 1995,
        "square_footage": 1800,
        "bedrooms": 3,
        "bathrooms": 2
    }
    
    # Generate document set
    documents = generate_document_set(sample_applicant, sample_property)
    
    # Save to output directory
    output_dir = "mock_data/sample_data/documents"
    os.makedirs(output_dir, exist_ok=True)
    save_document_set(documents, output_dir, "sample_applicant")
    
    print("Generated sample documents.")