#!/usr/bin/env python
"""
Security Integration Test Runner

This script runs the security integration tests for the Mortgage Lending Assistant.
It focuses on testing various security components including PII detection,
input validation, jailbreak prevention, and middleware integration.
"""

import os
import sys
import unittest
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("security_tests")

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

def run_security_tests():
    """Run the security integration tests."""
    logger.info("=" * 80)
    logger.info("RUNNING SECURITY INTEGRATION TESTS")
    logger.info("=" * 80)
    
    # Import test modules
    try:
        from tests.integration.test_security_integration import SecurityIntegrationTests, MortgageSpecificSecurityTests
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Please ensure you're running this script from the project root directory")
        return False
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases to the suite
    test_suite.addTest(unittest.makeSuite(SecurityIntegrationTests))
    test_suite.addTest(unittest.makeSuite(MortgageSpecificSecurityTests))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Report results
    logger.info("=" * 80)
    if result.wasSuccessful():
        logger.info("All security integration tests PASSED!")
        return True
    else:
        logger.error(f"Security integration tests FAILED: {len(result.failures)} failures, {len(result.errors)} errors")
        return False

if __name__ == "__main__":
    success = run_security_tests()
    sys.exit(0 if success else 1)