"""
Mortgage Application Generator

This module integrates all the generators to create complete mortgage applications
with associated documents for testing the mortgage lending assistant.
"""

import os
import json
import random
import datetime
import uuid
from typing import Dict, Any, List, Optional

# Import generators
from .applicant_generator import generate_applicant, generate_applicant_set
from .property_generator import generate_property, generate_property_set
from .loan_generator import generate_loan_details
from .document_generator import generate_document_set_for_application

def generate_mortgage_application(applicant_data: Optional[Dict[str, Any]] = None,
                                 property_data: Optional[Dict[str, Any]] = None,
                                 custom_scenario: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a complete mortgage application.
    
    Args:
        applicant_data: Optional applicant data (generated if not provided)
        property_data: Optional property data (generated if not provided)
        custom_scenario: Optional scenario type to generate specific cases
            Options: 'excellent', 'good', 'fair', 'poor', 'jumbo', 'fha', 'va'
        
    Returns:
        Dictionary with complete application data
    """
    # Generate applicant if not provided
    if applicant_data is None:
        # Adjust profile type based on scenario
        profile_type = "good"  # Default
        if custom_scenario:
            if custom_scenario in ['excellent', 'jumbo']:
                profile_type = "excellent"
            elif custom_scenario == 'good':
                profile_type = "good"
            elif custom_scenario in ['fair', 'fha']:
                profile_type = "fair"
            elif custom_scenario in ['poor', 'va']:
                profile_type = "poor"
        
        # Determine if we need a co-applicant
        with_coapplicant = random.random() < 0.6  # 60% chance
        
        # Generate applicant
        applicant_data = generate_applicant(
            profile_type=profile_type,
            age_range=(25, 65),
            with_coapplicant=with_coapplicant
        )
    
    # Generate property if not provided
    if property_data is None:
        # Adjust property type based on scenario
        property_type = None  # Random selection
        if custom_scenario:
            if custom_scenario == 'jumbo':
                # Higher value property for jumbo loan
                property_data = generate_property("Single Family Home")
                # Inflate the property value for jumbo loan
                property_data["estimated_value"] = random.randint(800000, 1500000)
            else:
                property_data = generate_property(property_type)
        else:
            property_data = generate_property(property_type)
    
    # Generate loan details
    loan_data = generate_loan_details(property_data["estimated_value"], applicant_data)
    
    # Create application ID
    application_id = str(uuid.uuid4())
    
    # Create application status (most will be SUBMITTED for testing)
    application_status = "SUBMITTED"
    
    # Determine submission date (within last 30 days)
    days_ago = random.randint(1, 30)
    submission_date = (datetime.datetime.now() - datetime.timedelta(days=days_ago)).strftime("%Y-%m-%d")
    
    # Create application
    application = {
        "application_id": application_id,
        "status": application_status,
        "submission_date": submission_date,
        "primary_applicant": applicant_data["primary_applicant"],
        "property_info": property_data,
        "loan_details": loan_data
    }
    
    # Add co-applicant if present
    if "co_applicant" in applicant_data:
        application["co_applicant"] = applicant_data["co_applicant"]
    
    return application

def generate_application_scenarios(count: int = 10, output_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Generate a diverse set of mortgage application scenarios.
    
    Args:
        count: Number of scenarios to generate
        output_dir: Directory to save scenarios (optional)
        
    Returns:
        List of generated applications
    """
    # Define scenario distribution
    scenario_types = [
        "excellent",  # Excellent credit, high income, strong application
        "good",       # Good credit, stable income, solid application
        "fair",       # Fair credit, average income, some issues
        "poor",       # Poor credit, lower income, multiple issues
        "jumbo",      # High-value property requiring jumbo loan
        "fha",        # FHA loan scenario
        "va"          # VA loan scenario
    ]
    
    # Weights for scenarios (more common scenarios have higher weight)
    weights = [0.15, 0.3, 0.2, 0.1, 0.1, 0.1, 0.05]
    
    # Generate applications
    applications = []
    
    for i in range(count):
        # Select scenario type
        scenario = random.choices(scenario_types, weights=weights, k=1)[0]
        
        # Generate application for this scenario
        application = generate_mortgage_application(custom_scenario=scenario)
        
        # Ensure scenario type is captured for reference
        application["scenario_type"] = scenario
        
        applications.append(application)
        
        # Save to file if output directory specified
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            file_path = os.path.join(output_dir, f"application_{application['application_id']}.json")
            
            with open(file_path, 'w') as f:
                json.dump(application, f, indent=2)
    
    return applications

def generate_complete_application_package(application: Dict[str, Any], 
                                         output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a complete mortgage application package including all documents.
    
    Args:
        application: Application data
        output_dir: Directory to save documents (optional)
        
    Returns:
        Dictionary with application and documents
    """
    # Generate all required documents
    documents = generate_document_set_for_application(application, output_dir)
    
    # Create complete package
    package = {
        "application": application,
        "documents": documents
    }
    
    # Save complete package if output directory specified
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, f"complete_package_{application['application_id']}.json")
        
        with open(file_path, 'w') as f:
            json.dump(package, f, indent=2)
    
    return package

def generate_test_dataset(num_applications: int = 10, output_dir: str = "mock_data/dataset") -> None:
    """
    Generate a complete test dataset with applications and documents.
    
    Args:
        num_applications: Number of applications to generate
        output_dir: Directory to save the dataset
    """
    # Create base directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create applications directory
    applications_dir = os.path.join(output_dir, "applications")
    os.makedirs(applications_dir, exist_ok=True)
    
    # Create documents directory
    documents_dir = os.path.join(output_dir, "documents")
    os.makedirs(documents_dir, exist_ok=True)
    
    # Generate applications
    applications = generate_application_scenarios(num_applications)
    
    # Generate documents for each application
    for application in applications:
        # Save application
        app_id = application["application_id"]
        app_file = os.path.join(applications_dir, f"{app_id}.json")
        
        with open(app_file, 'w') as f:
            json.dump(application, f, indent=2)
        
        # Generate documents
        app_docs_dir = os.path.join(documents_dir, app_id)
        generate_document_set_for_application(application, app_docs_dir)
        
        print(f"Generated application {app_id} with documents")
    
    print(f"Generated test dataset with {num_applications} applications in {output_dir}")

if __name__ == "__main__":
    # Generate a test dataset
    generate_test_dataset(5, "mock_data/sample_data")