"""
Document Analysis Agent Module (Enhanced)
Specializes in processing and analyzing various mortgage-related documents.
Added integration with DocumentAnalyzerPlugin for enhanced document analysis.
"""

from typing import Any, Dict, List, Optional
import asyncio
import json
import logging

from .base_agent import BaseAgent
from src.semantic_kernel.kernel_setup import get_kernel
from src.autogen.reasoning_agents import get_document_reasoning_agent
from src.utils.logging_utils import get_logger
from src.semantic_kernel.plugins.document_plugin import DocumentAnalyzerPlugin


class DocumentAnalysisAgent(BaseAgent):
    """
    Agent responsible for analyzing mortgage application documents,
    extracting relevant information, and validating document completeness.
    Enhanced with DocumentAnalyzerPlugin for improved document analysis.
    """
    
    def __init__(self, agent_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Document Analysis Agent.
        
        Args:
            agent_config: Configuration for the agent
        """
        super().__init__("document_analysis", agent_config)
        
        # Initialize Semantic Kernel
        self.kernel = get_kernel()
        
        # Register DocumentAnalyzerPlugin
        self._register_document_analyzer()
        
        # Get document reasoning agent from AutoGen
        self.reasoning_agent = get_document_reasoning_agent()
        
        self.logger.info("Document analysis agent initialized with enhanced analysis capabilities")
    
    def _register_document_analyzer(self):
        """
        Register the DocumentAnalyzerPlugin with the semantic kernel.
        """
        try:
            # Create an instance of the DocumentAnalyzerPlugin
            document_analyzer = DocumentAnalyzerPlugin(self.kernel)
            
            # Register the plugin with the kernel
            self.kernel.add_plugin(document_analyzer, "document_plugin")
            
            self.logger.info("DocumentAnalyzerPlugin registered successfully")
        except Exception as e:
            self.logger.error(f"Error registering DocumentAnalyzerPlugin: {str(e)}")
            # Continue without the plugin to maintain backward compatibility
            self.logger.info("Continuing with default document analysis capabilities")

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and analyze mortgage application documents.
        
        Args:
            input_data: Document data to analyze, including:
                - application_id: The ID of the application
                - documents: List of document objects to analyze
                - is_update: Boolean indicating if this is an update to existing docs
                
        Returns:
            Dict containing analysis results
        """
        documents = input_data.get("documents", [])
        application_id = input_data.get("application_id")
        is_update = input_data.get("is_update", False)
        
        if not documents:
            self.logger.warning(f"No documents provided for application {application_id}")
            return {
                "is_complete": False,
                "missing_documents": self._get_required_document_types(),
                "summary": {"error": "No documents provided"}
            }
        
        self.log_processing_step(f"Processing {len(documents)} documents for application {application_id}")
        
        # Process each document in parallel
        document_results = await asyncio.gather(
            *[self._analyze_document_enhanced(doc) for doc in documents]
        )
        
        # Consolidate results
        consolidated_results = self._consolidate_results(document_results)
        
        # Check for missing required documents
        missing_documents = self._identify_missing_documents(consolidated_results)
        
        # Check for inconsistencies across documents
        inconsistencies = await self._identify_inconsistencies_enhanced(consolidated_results, document_results)
        
        # Generate a summary of the documents
        summary = await self._generate_document_summary_enhanced(consolidated_results)
        
        # Use enhanced fraud detection if available
        fraud_indicators = await self._detect_fraud_indicators_enhanced(consolidated_results, document_results)
        
        return {
            "application_id": application_id,
            "document_results": consolidated_results,
            "is_complete": len(missing_documents) == 0,
            "missing_documents": missing_documents,
            "inconsistencies": inconsistencies,
            "summary": summary,
            "fraud_indicators": fraud_indicators if fraud_indicators else [],
            "overall_confidence": self._calculate_overall_confidence(document_results)
        }
    
    async def validate_document(self, document_type: str, document_content: Any) -> Dict[str, Any]:
        """
        Validate a document before processing.
        Enhanced with DocumentAnalyzerPlugin for improved validation.
        
        Args:
            document_type: Type of document to validate
            document_content: Content of the document
            
        Returns:
            Dict with validation results
        """
        try:
            # Try enhanced validation if document plugin is available
            if "document_plugin" in self.kernel.plugins:
                try:
                    document_plugin = self.kernel.plugins.get("document_plugin")
                    
                    # Prepare document data for validation
                    document = {
                        "document_type": document_type,
                        "content": document_content
                    }
                    
                    # Extract data based on document type
                    if document_type.upper() == "W2_FORM":
                        extracted_result = await document_plugin.extract_w2_information.invoke_async(
                            document_text=str(document_content)
                        )
                        extracted_data = json.loads(extracted_result.result)
                    elif document_type.upper() == "PAY_STUB":
                        extracted_result = await document_plugin.extract_pay_stub_information.invoke_async(
                            document_text=str(document_content)
                        )
                        extracted_data = json.loads(extracted_result.result)
                    elif document_type.upper() == "BANK_STATEMENT":
                        extracted_result = await document_plugin.extract_bank_statement_information.invoke_async(
                            document_text=str(document_content)
                        )
                        extracted_data = json.loads(extracted_result.result)
                    else:
                        # For other document types, use generic extraction
                        extracted_data = {"document_type": document_type}
                    
                    # Validate document completeness
                    validation_result = await document_plugin.validate_document_completeness.invoke_async(
                        document_type=document_type,
                        extracted_data=json.dumps(extracted_data)
                    )
                    validation_data = json.loads(validation_result.result)
                    
                    # Return enhanced validation result
                    return {
                        "is_valid": validation_data.get("is_valid", False),
                        "document_type": document_type,
                        "confidence": extracted_data.get("verification_score", 0),
                        "issues": validation_data.get("missing_fields", []),
                        "completeness_score": validation_data.get("completeness_score", 0),
                        "enhanced_validation_used": True
                    }
                except Exception as e:
                    self.logger.warning(f"Enhanced validation failed: {str(e)}. Falling back to standard validation.")
                    # Continue with standard validation if enhanced validation fails
            
            # Fall back to standard validation
            document = {
                "document_type": document_type,
                "content": document_content
            }
            
            # Call existing _analyze_document method
            analysis_result = await self._analyze_document(document)
            
            # Prepare validation response
            return {
                "is_valid": analysis_result.get("status", "") == "PROCESSED",
                "document_type": document_type,
                "confidence": analysis_result.get("confidence", 0),
                "issues": analysis_result.get("error_message", [])
            }
        
        except Exception as e:
            self.logger.error(f"Error validating document: {str(e)}", exc_info=True)
            return {
                "is_valid": False,
                "document_type": document_type,
                "error": str(e)
            }

    async def get_document_requirements(self, document_type: str) -> Dict[str, Any]:
        """
        Provide detailed requirements for a specific document type.
        Enhanced with DocumentAnalyzerPlugin for more detailed requirements.
        
        Args:
            document_type: Type of document to get requirements for
            
        Returns:
            Dict with document requirements and guidance
        """
        # Try enhanced document requirements if document plugin is available
        if "document_plugin" in self.kernel.plugins:
            try:
                # Use DocumentAnalyzerPlugin to provide enhanced requirements
                document_plugin = self.kernel.plugins.get("document_plugin")
                
                # Get document requirements
                # Note: DocumentAnalyzerPlugin doesn't have a specific method for this,
                # but we can use the validate_document_completeness method to infer requirements
                
                # Create a minimal document structure to analyze
                minimal_data = {
                    "document_type": document_type,
                    "verification_score": 0
                }
                
                # Validate the minimal document to get missing fields
                validation_result = await document_plugin.validate_document_completeness.invoke_async(
                    document_type=document_type,
                    extracted_data=json.dumps(minimal_data)
                )
                
                validation_data = json.loads(validation_result.result)
                
                # Extract requirements from missing fields
                required_fields = []
                for field in validation_data.get("missing_fields", []):
                    # Clean up the field name (remove "Missing " prefix)
                    if field.startswith("Missing "):
                        required_fields.append(field[8:])
                    else:
                        required_fields.append(field)
                
                # Return enhanced requirements
                return {
                    "document_type": document_type,
                    "name": self._get_document_display_name(document_type),
                    "description": f"Required document for mortgage application: {document_type}",
                    "required_fields": required_fields,
                    "acceptance_criteria": [
                        "Document must be complete and legible",
                        "All required fields must be present",
                        "Document must be recent (typically within last 60 days)"
                    ],
                    "enhanced_requirements_used": True
                }
            except Exception as e:
                self.logger.warning(f"Enhanced document requirements failed: {str(e)}. Falling back to standard requirements.")
                # Continue with standard requirements if enhanced requirements fail
        
        # Mapping of document types to their specific requirements (standard fallback)
        document_requirements = {
            "W2_FORM": {
                "name": "W-2 Form",
                "description": "Wage and Tax Statement",
                "required_fields": [
                    "Employer's name and address",
                    "Employee's full name and address",
                    "Employee's Social Security Number",
                    "Total wages earned",
                    "Federal income tax withheld",
                    "State and local income tax withheld"
                ],
                "acceptance_criteria": [
                    "Must be from the most recent tax year",
                    "Must show complete employment information",
                    "Must be signed or have employer's official stamp"
                ],
                "recommended_format": ["PDF", "High-resolution image"],
                "maximum_file_size": "5MB"
            },
            "PAY_STUB": {
                "name": "Pay Stub",
                "description": "Recent proof of income",
                "required_fields": [
                    "Employee name",
                    "Employer name",
                    "Pay period",
                    "Gross earnings",
                    "Net earnings",
                    "Year-to-date earnings"
                ],
                "acceptance_criteria": [
                    "Must be from within the last 30 days",
                    "Must show complete pay breakdown",
                    "Must include employer contact information"
                ],
                "recommended_format": ["PDF", "High-resolution image"],
                "maximum_file_size": "3MB"
            },
            "BANK_STATEMENT": {
                "name": "Bank Statement",
                "description": "Proof of financial assets and income",
                "required_fields": [
                    "Bank name and account information",
                    "Account holder's name",
                    "Statement period",
                    "Starting and ending balance",
                    "Transaction history"
                ],
                "acceptance_criteria": [
                    "Must be from within the last 3 months",
                    "Must show full account number (last 4 digits visible)",
                    "Must include bank logo or official letterhead"
                ],
                "recommended_format": ["PDF", "High-resolution image"],
                "maximum_file_size": "5MB"
            },
            # Add more document types as needed
        }
        
        # Normalize document type input
        normalized_type = document_type.upper().replace(" ", "_")
        
        # Check if document type exists in requirements
        if normalized_type not in document_requirements:
            return {
                "error": f"No requirements found for document type: {document_type}",
                "available_types": list(document_requirements.keys())
            }
        
        # Return standard requirements
        requirements = document_requirements[normalized_type]
        
        return {
            "document_type": normalized_type,
            "name": requirements["name"],
            "description": requirements["description"],
            "required_fields": requirements["required_fields"],
            "acceptance_criteria": requirements["acceptance_criteria"],
            "recommended_format": requirements.get("recommended_format", ["PDF"]),
            "maximum_file_size": requirements.get("maximum_file_size", "5MB")
        }
    
    async def _analyze_document_enhanced(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single document with enhanced capabilities.
        Falls back to standard analysis if enhanced analysis fails.
        
        Args:
            document: Document data object with type, content, etc.
            
        Returns:
            Dict with analysis results for the document
        """
        try:
            document_type = document.get("document_type", "").upper()
            self.log_processing_step(f"Analyzing document of type: {document_type}")
            
            # Try enhanced analysis if document plugin is available
            if "document_plugin" in self.kernel.plugins:
                try:
                    document_plugin = self.kernel.plugins.get("document_plugin")
                    
                    # Extract data based on document type
                    if document_type == "W2_FORM" or document_type == "INCOME_VERIFICATION":
                        extracted_result = await document_plugin.extract_w2_information.invoke_async(
                            document_text=str(document.get("content", ""))
                        )
                        extracted_data = json.loads(extracted_result.result)
                        
                        # Map extracted fields to standard format
                        result = {
                            "document_type": document_type,
                            "income_amount": extracted_data.get("income", {}).get("wages"),
                            "employer_name": extracted_data.get("employer", {}).get("name"),
                            "employment_duration": "Not specified",  # W-2 doesn't specify duration
                            "document_date": extracted_data.get("tax_year"),
                            "confidence": extracted_data.get("verification_score", 0.85),
                            "status": "PROCESSED",
                            "enhanced_analysis_used": True
                        }
                        
                        return result
                        
                    elif document_type == "PAY_STUB":
                        extracted_result = await document_plugin.extract_pay_stub_information.invoke_async(
                            document_text=str(document.get("content", ""))
                        )
                        extracted_data = json.loads(extracted_result.result)
                        
                        # Map extracted fields to standard format
                        result = {
                            "document_type": document_type,
                            "income_amount": extracted_data.get("income", {}).get("gross_pay"),
                            "employer_name": extracted_data.get("employer", {}).get("name"),
                            "employee_name": extracted_data.get("employee", {}).get("name"),
                            "pay_period": extracted_data.get("pay_period", {}).get("period"),
                            "ytd_gross": extracted_data.get("income", {}).get("ytd_gross"),
                            "confidence": extracted_data.get("verification_score", 0.85),
                            "status": "PROCESSED",
                            "enhanced_analysis_used": True
                        }
                        
                        return result
                        
                    elif document_type == "BANK_STATEMENT":
                        extracted_result = await document_plugin.extract_bank_statement_information.invoke_async(
                            document_text=str(document.get("content", ""))
                        )
                        extracted_data = json.loads(extracted_result.result)
                        
                        # Map extracted fields to standard format
                        result = {
                            "document_type": document_type,
                            "account_balance": extracted_data.get("balances", {}).get("ending"),
                            "account_number": extracted_data.get("account", {}).get("number"),
                            "account_holder": extracted_data.get("account", {}).get("holder"),
                            "bank_name": extracted_data.get("bank", {}).get("name"),
                            "statement_period": extracted_data.get("statement_period"),
                            "transactions": {
                                "deposits": extracted_data.get("transactions", {}).get("deposits"),
                                "withdrawals": extracted_data.get("transactions", {}).get("withdrawals")
                            },
                            "confidence": extracted_data.get("verification_score", 0.85),
                            "status": "PROCESSED",
                            "enhanced_analysis_used": True
                        }
                        
                        return result
                        
                    elif document_type == "CREDIT_REPORT":
                        # No specific method for credit reports, use standard analysis
                        pass
                        
                    elif document_type == "PROPERTY_APPRAISAL":
                        # No specific method for property appraisals, use standard analysis
                        pass
                        
                    elif document_type == "ID_VERIFICATION":
                        # No specific method for ID verification, use standard analysis
                        pass
                
                except Exception as e:
                    self.logger.warning(f"Enhanced document analysis failed for {document_type}: {str(e)}. Falling back to standard analysis.")
                    # Continue with standard analysis if enhanced analysis fails
            
            # Fall back to standard analysis method
            return await self._analyze_document(document)
                
        except Exception as e:
            self.logger.error(f"Error analyzing document: {str(e)}", exc_info=True)
            return {
                "document_type": document.get("document_type"),
                "status": "ERROR",
                "error_message": str(e),
                "confidence": 0.0
            }
    
    async def _identify_inconsistencies_enhanced(self, consolidated_results: Dict[str, Any],
                                               document_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify inconsistencies across documents with enhanced capabilities.
        
        Args:
            consolidated_results: Consolidated document results
            document_results: Raw document results
            
        Returns:
            List of identified inconsistencies
        """
        inconsistencies = []
        
        # Use document plugin if available
        if "document_plugin" in self.kernel.plugins and len(consolidated_results) > 1:
            try:
                document_plugin = self.kernel.plugins.get("document_plugin")
                
                # Prepare documents data for the plugin
                documents_data = []
                for doc_type, doc_result in consolidated_results.items():
                    # Include only documents with enhanced analysis
                    if doc_result.get("enhanced_analysis_used", False):
                        documents_data.append(doc_result)
                
                # Only use enhanced consistency check if we have at least 2 enhanced documents
                if len(documents_data) >= 2:
                    # Verify document consistency
                    consistency_result = await document_plugin.verify_document_consistency.invoke_async(
                        documents_data=json.dumps(documents_data)
                    )
                    
                    consistency_data = json.loads(consistency_result.result)
                    
                    # Extract inconsistencies
                    if not consistency_data.get("is_consistent", True):
                        inconsistencies = consistency_data.get("inconsistencies", [])
                        
                        # Return enhanced inconsistencies
                        return inconsistencies
            except Exception as e:
                self.logger.warning(f"Enhanced inconsistency detection failed: {str(e)}. Falling back to standard detection.")
                # Continue with standard inconsistency detection if enhanced detection fails
        
        # Use reasoning agent to identify inconsistencies (standard approach)
        if len(consolidated_results) > 1:
            try:
                reasoning_result = await self.reasoning_agent.identify_document_inconsistencies(
                    document_results=consolidated_results
                )
                
                if reasoning_result and "inconsistencies" in reasoning_result:
                    inconsistencies = reasoning_result["inconsistencies"]
            except Exception as e:
                self.logger.error(f"Error identifying inconsistencies: {str(e)}", exc_info=True)
                # Return empty list if there's an error, don't fail the whole process
        
        return inconsistencies
    
    async def _generate_document_summary_enhanced(self, consolidated_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary of all analyzed documents with enhanced capabilities.
        
        Args:
            consolidated_results: Consolidated document results
            
        Returns:
            Dict with summarized document information
        """
        try:
            # Check if we have any enhanced documents
            has_enhanced_docs = any(doc.get("enhanced_analysis_used", False) 
                                   for doc in consolidated_results.values())
            
            # Use document plugin for human-readable summary if available
            if "document_plugin" in self.kernel.plugins and has_enhanced_docs:
                try:
                    document_plugin = self.kernel.plugins.get("document_plugin")
                    
                    # Generate summary for each document type that used enhanced analysis
                    narrative_summaries = []
                    
                    for doc_type, doc_result in consolidated_results.items():
                        if doc_result.get("enhanced_analysis_used", False):
                            # Generate human-readable summary
                            summary_result = await document_plugin.summarize_document_for_review.invoke_async(
                                document_type=doc_type,
                                extracted_data=json.dumps(doc_result)
                            )
                            
                            narrative_summaries.append(summary_result.result)
                    
                    if narrative_summaries:
                        # Extract key information as before
                        summary = {}
                        
                        # Income information
                        if "INCOME_VERIFICATION" in consolidated_results or "W2_FORM" in consolidated_results:
                            income_doc = consolidated_results.get("INCOME_VERIFICATION", consolidated_results.get("W2_FORM", {}))
                            summary["income"] = {
                                "annual_income": income_doc.get("income_amount"),
                                "employer": income_doc.get("employer_name"),
                                "employment_duration": income_doc.get("employment_duration")
                            }
                        
                        # Credit information
                        if "CREDIT_REPORT" in consolidated_results:
                            credit_doc = consolidated_results["CREDIT_REPORT"]
                            summary["credit"] = {
                                "score": credit_doc.get("credit_score"),
                                "total_debt": sum(debt.get("amount", 0) for debt in credit_doc.get("outstanding_debts", []))
                            }
                        
                        # Property information
                        if "PROPERTY_APPRAISAL" in consolidated_results:
                            property_doc = consolidated_results["PROPERTY_APPRAISAL"]
                            summary["property"] = {
                                "value": property_doc.get("property_value"),
                                "address": property_doc.get("property_address"),
                                "type": property_doc.get("property_type")
                            }
                        
                        # Banking information
                        if "BANK_STATEMENT" in consolidated_results:
                            bank_doc = consolidated_results["BANK_STATEMENT"]
                            summary["banking"] = {
                                "balance": bank_doc.get("account_balance"),
                                "period": bank_doc.get("statement_period")
                            }
                        
                        # Applicant information
                        if "ID_VERIFICATION" in consolidated_results:
                            id_doc = consolidated_results["ID_VERIFICATION"]
                            summary["applicant"] = {
                                "name": id_doc.get("full_name"),
                                "dob": id_doc.get("date_of_birth")
                            }
                        
                        # Add enhanced narrative summary
                        summary["narrative"] = "\n\n".join(narrative_summaries)
                        summary["enhanced_summary_used"] = True
                        
                        return summary
                except Exception as e:
                    self.logger.warning(f"Enhanced document summary failed: {str(e)}. Falling back to standard summary.")
                    # Continue with standard summary if enhanced summary fails
            
            # Fall back to standard summary approach
            # Extract key information from each document type
            summary = {}
            
            # Income information
            if "INCOME_VERIFICATION" in consolidated_results:
                income_doc = consolidated_results["INCOME_VERIFICATION"]
                summary["income"] = {
                    "annual_income": income_doc.get("income_amount"),
                    "employer": income_doc.get("employer_name"),
                    "employment_duration": income_doc.get("employment_duration")
                }
            
            # Credit information
            if "CREDIT_REPORT" in consolidated_results:
                credit_doc = consolidated_results["CREDIT_REPORT"]
                summary["credit"] = {
                    "score": credit_doc.get("credit_score"),
                    "total_debt": sum(debt.get("amount", 0) for debt in credit_doc.get("outstanding_debts", []))
                }
            
            # Property information
            if "PROPERTY_APPRAISAL" in consolidated_results:
                property_doc = consolidated_results["PROPERTY_APPRAISAL"]
                summary["property"] = {
                    "value": property_doc.get("property_value"),
                    "address": property_doc.get("property_address"),
                    "type": property_doc.get("property_type")
                }
            
            # Banking information
            if "BANK_STATEMENT" in consolidated_results:
                bank_doc = consolidated_results["BANK_STATEMENT"]
                summary["banking"] = {
                    "balance": bank_doc.get("account_balance"),
                    "period": bank_doc.get("statement_period")
                }
            
            # Applicant information
            if "ID_VERIFICATION" in consolidated_results:
                id_doc = consolidated_results["ID_VERIFICATION"]
                summary["applicant"] = {
                    "name": id_doc.get("full_name"),
                    "dob": id_doc.get("date_of_birth")
                }
            
            # Use reasoning agent to generate an overall document summary in natural language
            reasoning_result = await self.reasoning_agent.summarize_document_collection(
                document_summary=summary
            )
            
            if reasoning_result and "narrative_summary" in reasoning_result:
                summary["narrative"] = reasoning_result["narrative_summary"]
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating document summary: {str(e)}", exc_info=True)
            return {"error": "Failed to generate document summary"}
    
    async def _detect_fraud_indicators_enhanced(self, consolidated_results: Dict[str, Any],
                                              document_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect potential indicators of fraud in documents with enhanced capabilities.
        
        Args:
            consolidated_results: Consolidated document results
            document_results: Raw document results
            
        Returns:
            List of fraud indicators
        """
        # Use document plugin if available
        if "document_plugin" in self.kernel.plugins:
            try:
                document_plugin = self.kernel.plugins.get("document_plugin")
                
                # Check each document for fraud indicators
                fraud_indicators = []
                
                for doc_type, doc_result in consolidated_results.items():
                    # Only check documents that used enhanced analysis
                    if doc_result.get("enhanced_analysis_used", False):
                        # Detect fraud indicators
                        fraud_result = await document_plugin.detect_fraud_indicators.invoke_async(
                            document_type=doc_type,
                            extracted_data=json.dumps(doc_result)
                        )
                        
                        fraud_data = json.loads(fraud_result.result)
                        
                        # Add fraud indicators if detected
                        if fraud_data.get("fraud_indicators_detected", False):
                            for indicator in fraud_data.get("fraud_indicators", []):
                                fraud_indicators.append({
                                    "document_type": doc_type,
                                    "indicator": indicator,
                                    "risk_level": fraud_data.get("risk_score", 0.5)
                                })
                
                if fraud_indicators:
                    return fraud_indicators
            except Exception as e:
                self.logger.warning(f"Enhanced fraud detection failed: {str(e)}. Falling back to standard detection.")
                # Continue with standard fraud detection if enhanced detection fails
        
        # Fall back to standard approach (which may not include fraud detection)
        return []
    
    def _calculate_overall_confidence(self, document_results: List[Dict[str, Any]]) -> float:
        """
        Calculate overall confidence score across all documents.
        
        Args:
            document_results: List of individual document analysis results
            
        Returns:
            Float representing overall confidence (0-1)
        """
        if not document_results:
            return 0.0
        
        # Calculate weighted average of confidence scores
        total_confidence = sum(result.get("confidence", 0) for result in document_results)
        return total_confidence / len(document_results)
    
    # Helper method to get a human-readable document name
    def _get_document_display_name(self, document_type: str) -> str:
        """Get a human-readable name for a document type."""
        document_names = {
            "W2_FORM": "W-2 Tax Form",
            "PAY_STUB": "Pay Stub",
            "BANK_STATEMENT": "Bank Statement",
            "CREDIT_REPORT": "Credit Report",
            "PROPERTY_APPRAISAL": "Property Appraisal",
            "ID_VERIFICATION": "Identification Document",
            "INCOME_VERIFICATION": "Income Verification Document",
            "TAX_RETURN": "Tax Return",
            "EMPLOYMENT_VERIFICATION": "Employment Verification"
        }
        
        normalized_type = document_type.upper().replace(" ", "_")
        return document_names.get(normalized_type, document_type)
    
    async def _analyze_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single document using the appropriate method based on document type.
        
        Args:
            document: Document data object with type, content, etc.
            
        Returns:
            Dict with analysis results for the document
        """
        try:
            document_type = document.get("document_type", "").upper()
            self.log_processing_step(f"Analyzing document of type: {document_type}")
            
            # Handle document based on its type
            if document_type == "INCOME_VERIFICATION":
                return await self._process_income_verification(document)
                
            elif document_type == "CREDIT_REPORT":
                return await self._process_credit_report(document)
                
            elif document_type == "PROPERTY_APPRAISAL":
                return await self._process_property_appraisal(document)
                
            elif document_type == "BANK_STATEMENT":
                return await self._process_bank_statement(document)
                
            elif document_type == "ID_VERIFICATION":
                return await self._process_id_verification(document)
                
            else:
                # For unknown document types, use generic processing
                return await self._process_generic_document(document)
                
        except Exception as e:
            self.logger.error(f"Error analyzing document: {str(e)}", exc_info=True)
            return {
                "document_type": document.get("document_type"),
                "status": "ERROR",
                "error_message": str(e),
                "confidence": 0.0
            }