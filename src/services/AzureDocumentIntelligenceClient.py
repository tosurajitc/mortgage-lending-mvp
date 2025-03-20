"""
Azure Document Intelligence Client
Provides integration with Azure Document Intelligence for extracting information from documents.
"""

import os
import asyncio
from typing import Any, Dict, List, Optional, Union
import json
import base64
import requests
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient

from ..utils.config import get_config
from ..utils.logging_utils import get_logger

logger = get_logger("services.document_intelligence")


class AzureDocumentIntelligenceClient:
    """
    Client for Azure Document Intelligence service.
    Provides methods to extract text, form data, and specific document information.
    """
    
    def __init__(self):
        self.logger = get_logger("azure_document_intelligence")
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the Azure Document Intelligence client."""
        config = get_config()
        
        # Get Azure Document Intelligence credentials
        endpoint = os.environ.get("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT") or \
                  config.get("document_intelligence", {}).get("endpoint")
        api_key = os.environ.get("AZURE_DOCUMENT_INTELLIGENCE_KEY") or \
                 config.get("document_intelligence", {}).get("api_key")
        
        if not endpoint or not api_key:
            self.logger.warning("Azure Document Intelligence credentials not found")
            self.client = None
            return
        
        try:
            # Create Azure Document Intelligence client
            self.endpoint = endpoint
            self.api_key = api_key
            self.credential = AzureKeyCredential(api_key)
            self.client = DocumentAnalysisClient(endpoint, self.credential)
            self.logger.info("Azure Document Intelligence client initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing Azure Document Intelligence client: {str(e)}")
            self.client = None
    
    async def extract_text(self, document_content: Union[str, bytes]) -> str:
        """
        Extract text from a document using Azure Document Intelligence.
        
        Args:
            document_content: Document content as string (file path) or bytes
            
        Returns:
            Extracted text as a string
        """
        if not self.client:
            self.logger.error("Azure Document Intelligence client not initialized")
            return "Azure Document Intelligence client not available"
        
        try:
            # Convert string document_content to bytes if it's a file path
            if isinstance(document_content, str) and os.path.isfile(document_content):
                with open(document_content, "rb") as f:
                    document_content = f.read()
            elif isinstance(document_content, str) and document_content.startswith("data:"):
                # Handle base64 encoded document
                _, encoded = document_content.split(",", 1)
                document_content = base64.b64decode(encoded)
            
            # Run this in a separate thread to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: self.client.begin_analyze_document("prebuilt-read", document_content).result()
            )
            
            # Extract text from result
            extracted_text = ""
            for page in result.pages:
                for line in page.lines:
                    extracted_text += line.content + "\n"
            
            return extracted_text
            
        except Exception as e:
            self.logger.error(f"Error extracting text from document: {str(e)}")
            return f"Error extracting text: {str(e)}"
    
    async def extract_form_data(self, document_content: Union[str, bytes]) -> Dict[str, Any]:
        """
        Extract form data from a document using Azure Document Intelligence.
        
        Args:
            document_content: Document content as string (file path) or bytes
            
        Returns:
            Dict containing extracted form fields and values
        """
        if not self.client:
            self.logger.error("Azure Document Intelligence client not initialized")
            return {"error": "Azure Document Intelligence client not available"}
        
        try:
            # Convert string document_content to bytes if it's a file path
            if isinstance(document_content, str) and os.path.isfile(document_content):
                with open(document_content, "rb") as f:
                    document_content = f.read()
            elif isinstance(document_content, str) and document_content.startswith("data:"):
                # Handle base64 encoded document
                _, encoded = document_content.split(",", 1)
                document_content = base64.b64decode(encoded)
            
            # Run this in a separate thread to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: self.client.begin_analyze_document("prebuilt-document", document_content).result()
            )
            
            # Extract key-value pairs from form
            extracted_data = {}
            
            # Get key-value pairs
            for kv_pair in result.key_value_pairs:
                if kv_pair.key and kv_pair.value:
                    key = kv_pair.key.content
                    value = kv_pair.value.content
                    extracted_data[key] = value
            
            # Get tables
            tables = []
            for table in result.tables:
                table_data = {
                    "row_count": table.row_count,
                    "column_count": table.column_count,
                    "cells": []
                }
                
                for cell in table.cells:
                    table_data["cells"].append({
                        "row_index": cell.row_index,
                        "column_index": cell.column_index,
                        "content": cell.content,
                        "is_header": cell.kind == "columnHeader" or cell.kind == "rowHeader"
                    })
                
                tables.append(table_data)
            
            if tables:
                extracted_data["tables"] = tables
            
            return extracted_data
            
        except Exception as e:
            self.logger.error(f"Error extracting form data from document: {str(e)}")
            return {"error": f"Error extracting form data: {str(e)}"}
    
    async def analyze_document(self, document_type: str, document_content: Union[str, bytes]) -> Dict[str, Any]:
        """
        Analyze a document using the appropriate prebuilt model based on type.
        
        Args:
            document_type: Type of document (e.g., "invoice", "receipt", "idDocument")
            document_content: Document content as string (file path) or bytes
            
        Returns:
            Dict containing analyzed document data
        """
        if not self.client:
            self.logger.error("Azure Document Intelligence client not initialized")
            return {"error": "Azure Document Intelligence client not available"}
        
        # Map document types to Azure Document Intelligence prebuilt models
        model_map = {
            "INCOME_VERIFICATION": "prebuilt-document",  # Use general document model for W2, pay stubs
            "CREDIT_REPORT": "prebuilt-document",
            "PROPERTY_APPRAISAL": "prebuilt-document",
            "BANK_STATEMENT": "prebuilt-document",
            "ID_VERIFICATION": "prebuilt-idDocument",
            "INVOICE": "prebuilt-invoice",
            "RECEIPT": "prebuilt-receipt",
            "TAX_DOCUMENT": "prebuilt-tax.us.w2",  # Specific model for W2 forms
            "DEFAULT": "prebuilt-document"
        }
        
        # Get the appropriate model
        model = model_map.get(document_type.upper(), model_map["DEFAULT"])
        
        try:
            # Convert string document_content to bytes if it's a file path
            if isinstance(document_content, str) and os.path.isfile(document_content):
                with open(document_content, "rb") as f:
                    document_content = f.read()
            elif isinstance(document_content, str) and document_content.startswith("data:"):
                # Handle base64 encoded document
                _, encoded = document_content.split(",", 1)
                document_content = base64.b64decode(encoded)
            
            # Run this in a separate thread to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: self.client.begin_analyze_document(model, document_content).result()
            )
            
            # Process result based on document type
            if document_type.upper() == "ID_VERIFICATION":
                return self._process_id_document(result)
            elif document_type.upper() == "INVOICE":
                return self._process_invoice(result)
            elif document_type.upper() == "RECEIPT":
                return self._process_receipt(result)
            elif document_type.upper() == "TAX_DOCUMENT":
                return self._process_tax_document(result)
            else:
                # Default processing for general documents
                return self._process_general_document(result)
            
        except Exception as e:
            self.logger.error(f"Error analyzing document: {str(e)}")
            return {"error": f"Error analyzing document: {str(e)}"}
    
    def _process_id_document(self, result: Any) -> Dict[str, Any]:
        """
        Process ID document analysis result.
        
        Args:
            result: Azure Document Intelligence result for ID document
            
        Returns:
            Dict containing processed ID document data
        """
        processed_data = {
            "document_type": "ID_VERIFICATION",
            "fields": {}
        }
        
        try:
            # Extract identity document fields
            for document in result.documents:
                for name, field in document.fields.items():
                    processed_data["fields"][name] = field.content if hasattr(field, "content") else str(field.value)
            
            # Standardize output
            standardized = {
                "full_name": processed_data["fields"].get("FirstName", "") + " " + processed_data["fields"].get("LastName", ""),
                "date_of_birth": processed_data["fields"].get("DateOfBirth", ""),
                "document_number": processed_data["fields"].get("DocumentNumber", ""),
                "expiration_date": processed_data["fields"].get("DateOfExpiration", ""),
                "document_type": processed_data["fields"].get("DocumentType", ""),
                "country": processed_data["fields"].get("CountryRegion", ""),
                "address": processed_data["fields"].get("Address", ""),
                "confidence": 0.9  # Placeholder for confidence score
            }
            
            return standardized
            
        except Exception as e:
            self.logger.error(f"Error processing ID document: {str(e)}")
            return {
                "document_type": "ID_VERIFICATION",
                "error": f"Error processing ID document: {str(e)}",
                "raw_fields": processed_data.get("fields", {})
            }
    
    def _process_invoice(self, result: Any) -> Dict[str, Any]:
        """Process invoice analysis result."""
        # Implementation for invoice processing
        return {"document_type": "INVOICE", "message": "Invoice processing not fully implemented"}
    
    def _process_receipt(self, result: Any) -> Dict[str, Any]:
        """Process receipt analysis result."""
        # Implementation for receipt processing
        return {"document_type": "RECEIPT", "message": "Receipt processing not fully implemented"}
    
    def _process_tax_document(self, result: Any) -> Dict[str, Any]:
        """Process tax document analysis result."""
        # Implementation for tax document processing
        return {"document_type": "TAX_DOCUMENT", "message": "Tax document processing not fully implemented"}
    
    def _process_general_document(self, result: Any) -> Dict[str, Any]:
        """
        Process general document analysis result.
        
        Args:
            result: Azure Document Intelligence result for general document
            
        Returns:
            Dict containing processed document data
        """
        processed_data = {
            "document_type": "GENERAL",
            "key_value_pairs": {},
            "tables": [],
            "text": ""
        }
        
        try:
            # Extract key-value pairs
            for kv_pair in result.key_value_pairs:
                if kv_pair.key and kv_pair.value:
                    key = kv_pair.key.content
                    value = kv_pair.value.content
                    processed_data["key_value_pairs"][key] = value
            
            # Extract tables
            for table in result.tables:
                table_data = {
                    "row_count": table.row_count,
                    "column_count": table.column_count,
                    "cells": []
                }
                
                for cell in table.cells:
                    table_data["cells"].append({
                        "row_index": cell.row_index,
                        "column_index": cell.column_index,
                        "content": cell.content,
                        "is_header": cell.kind == "columnHeader" or cell.kind == "rowHeader"
                    })
                
                processed_data["tables"].append(table_data)
            
            # Extract text
            for page in result.pages:
                for line in page.lines:
                    processed_data["text"] += line.content + "\n"
            
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Error processing general document: {str(e)}")
            return {
                "document_type": "GENERAL",
                "error": f"Error processing general document: {str(e)}"
            }