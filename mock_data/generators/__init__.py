"""
Document Generators Package

This package contains specialized generators for different types of mortgage documents.
"""

# Import all generators for easy access
from . import income_document_generator
from . import bank_document_generator
from . import tax_document_generator
from . import credit_document_generator
from . import property_document_generator

# Define the version
__version__ = '0.1.0'