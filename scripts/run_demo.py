#!/usr/bin/env python
"""
Mortgage Lending Assistant Demo Script

This script demonstrates the core functionality of the Mortgage Lending Assistant
by processing a sample mortgage application through all agents in the system.
"""

import os
import sys
import json
import asyncio
import logging
import argparse
from datetime import datetime
from pprint import pprint

# Add project root to path to ensure imports work correctly
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("mortgage_demo")

# Import required modules
try:
    from src.agents.orchestrator import OrchestratorAgent
    from src.data.mock_data_generator import MockDataGenerator
    from src.utils.logging_utils import get_logger
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.error("Please ensure you're running this script from the project root directory")
    sys.exit(1)

async def run_demo(full_demo=False):
    """Run the complete mortgage application demo."""
    logger.info("Starting Mortgage Lending Assistant Demo")
    logger.info("=" * 80)
    
    # Initialize components
    mock_data = MockDataGenerator()
    orchestrator = OrchestratorAgent()
    
    # Generate mock data with more variability if full demo is requested
    applicant_data = mock_data.generate_applicant()
    loan_details = mock_data.generate_loan()
    property_info = mock_data.generate_property()
    
    # Customize loan details for different scenarios
    if full_demo:
        # Simulate different loan scenarios
        scenarios = [
            {
                "loan_type": "CONVENTIONAL",
                "amount": 350000,
                "down_payment": 70000,  # 20% down payment
                "credit_score_range": "Good (700-749)"
            },
            {
                "loan_type": "FHA",
                "amount": 250000,
                "down_payment": 35000,  # 14% down payment
                "credit_score_range": "Fair (650-699)"
            },
            {
                "loan_type": "VA",
                "amount": 400000,
                "down_payment": 0,  # No down payment for VA loan
                "credit_score_range": "Excellent (750+)",
                "military_service": "Veteran"
            }
        ]
        
        # Cycle through scenarios
        for scenario in scenarios:
            loan_details.update(scenario)
            
            # Generate unique application ID
            application_id = f"APP-{datetime.now().strftime('%Y%m%d')}-{applicant_data['last_name'].upper()}-{scenario['loan_type']}"
            
            # Display scenario details
            logger.info(f"\n{'='*40} NEW SCENARIO {'='*40}")
            logger.info(f"Loan Type: {scenario['loan_type']}")
            logger.info(f"Application ID: {application_id}")
            logger.info(f"Applicant: {applicant_data['first_name']} {applicant_data['last_name']}")
            logger.info(f"Loan Amount: ${scenario['amount']}")
            logger.info(f"Down Payment: ${scenario['down_payment']}")
            logger.info(f"Credit Score Range: {scenario['credit_score_range']}")
            
            # Generate mock documents for each scenario
            documents = [
                {
                    "document_type": "INCOME_VERIFICATION",
                    "content": mock_data.generate_document("W2")
                },
                {
                    "document_type": "CREDIT_REPORT",
                    "content": {
                        "credit_score": 720,
                        "outstanding_debts": [
                            {"type": "MORTGAGE", "amount": 0},
                            {"type": "AUTO_LOAN", "amount": 15000},
                            {"type": "CREDIT_CARD", "amount": 5000}
                        ]
                    }
                },
                {
                    "document_type": "PROPERTY_APPRAISAL",
                    "content": {
                        "property_value": property_info["value"],
                        "property_address": f"{property_info['address']}, {property_info['city']}, {property_info['state']} {property_info['zip']}",
                        "property_type": property_info["type"]
                    }
                },
                {
                    "document_type": "BANK_STATEMENT",
                    "content": mock_data.generate_document("Bank Statement")
                }
            ]
            
            # Process application
            try:
                result = await orchestrator.process({
                    "action": "process_application",
                    "application_id": application_id,
                    "applicant": applicant_data,
                    "loan_details": loan_details,
                    "property_info": property_info,
                    "documents": documents
                })
                
                # Display detailed results
                logger.info("\nAPPLICATION PROCESSING RESULTS")
                logger.info("-" * 40)
                logger.info(f"Application Status: {result.get('status', 'UNKNOWN')}")
                logger.info(f"Underwriting Approved: {result.get('underwriting_approved', False)}")
                logger.info(f"Compliance Approved: {result.get('compliance_approved', False)}")
                
                # Detailed logging for full demo
                pprint(result)
                
            except Exception as e:
                logger.error(f"Error processing scenario: {str(e)}", exc_info=True)
    
    else:
        # Original single scenario processing
        # (Keep the original single scenario implementation)
        application_id = f"APP-{datetime.now().strftime('%Y%m%d')}-{applicant_data['last_name'].upper()}"
        
        # Process application
        try:
            result = await orchestrator.process({
                "action": "process_application",
                "application_id": application_id,
                "applicant": applicant_data,
                "loan_details": loan_details,
                "property_info": property_info,
                "documents": documents
            })
            
            # Display results similar to the original implementation
            logger.info(f"Application Status: {result.get('status', 'UNKNOWN')}")
            logger.info(f"Underwriting Approved: {result.get('underwriting_approved', False)}")
            logger.info(f"Compliance Approved: {result.get('compliance_approved', False)}")
            
        except Exception as e:
            logger.error(f"Error processing application: {str(e)}", exc_info=True)

def main():
    parser = argparse.ArgumentParser(description="Mortgage Lending Assistant Demo")
    parser.add_argument("--full", action="store_true", help="Run full demo with multiple scenarios")
    args = parser.parse_args()

    # Run the async demo
    asyncio.run(run_demo(full_demo=args.full))

if __name__ == "__main__":
    main()