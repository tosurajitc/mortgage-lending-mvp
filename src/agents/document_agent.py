"""
Document Analysis Agent Module
Specializes in processing and analyzing various mortgage-related documents.
"""

from typing import Any, Dict, List, Optional
import asyncio

from .base_agent import BaseAgent
from src.semantic_kernel.kernel_setup import get_kernel
from src.autogen.reasoning_agents import get_document_reasoning_agent
from utils.logging_utils import get_logger


class DocumentAnalysisAgent(BaseAgent):
    """
    Agent responsible for analyzing mortgage application documents,
    extracting relevant information, and validating document completeness.
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
        
        # Get document reasoning agent from AutoGen
        self.reasoning_agent = get_document_reasoning_agent()
        
        self.logger.info("Document analysis agent initialized")
    
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
            *[self._analyze_document(doc) for doc in documents]
        )
        
        # Consolidate results
        consolidated_results = self._consolidate_results(document_results)
        
        # Check for missing required documents
        missing_documents = self._identify_missing_documents(consolidated_results)
        
        # Check for inconsistencies across documents
        inconsistencies = await self._identify_inconsistencies(consolidated_results)
        
        # Generate a summary of the documents
        summary = await self._generate_document_summary(consolidated_results)
        
        return {
            "application_id": application_id,
            "document_results": consolidated_results,
            "is_complete": len(missing_documents) == 0,
            "missing_documents": missing_documents,
            "inconsistencies": inconsistencies,
            "summary": summary,
            "overall_confidence": self._calculate_overall_confidence(document_results)
        }
    
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
    
    async def _process_income_verification(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process income verification documents (W-2s, pay stubs, etc.).
        
        Args:
            document: Income document data
            
        Returns:
            Dict with extracted income information
        """
        # Use Semantic Kernel plugin for income verification processing
        income_plugin = self.kernel.plugins.get("document_plugin")
        
        # Process document content through plugin
        extracted_data = await income_plugin.extract_income_data.invoke_async(document.get("content", ""))
        
        # Use reasoning agent for validation and complex extraction
        reasoning_result = await self.reasoning_agent.reason_about_income_document(
            document_content=document.get("content", ""),
            initial_extraction=extracted_data.result
        )
        
        # Combine semantic kernel and reasoning agent results
        combined_result = {
            "document_type": "INCOME_VERIFICATION",
            "income_amount": reasoning_result.get("income_amount"),
            "employer_name": reasoning_result.get("employer_name"),
            "employment_duration": reasoning_result.get("employment_duration"),
            "document_date": reasoning_result.get("document_date"),
            "confidence": reasoning_result.get("confidence", 0.85),
            "status": "PROCESSED"
        }
        
        return combined_result
    
    async def _process_credit_report(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process credit report documents.
        
        Args:
            document: Credit report document data
            
        Returns:
            Dict with extracted credit information
        """
        credit_plugin = self.kernel.plugins.get("document_plugin")
        
        # Process document content through plugin
        extracted_data = await credit_plugin.extract_credit_data.invoke_async(document.get("content", ""))
        
        # Use reasoning agent for validation and complex extraction
        reasoning_result = await self.reasoning_agent.reason_about_credit_document(
            document_content=document.get("content", ""),
            initial_extraction=extracted_data.result
        )
        
        # Combine results
        return {
            "document_type": "CREDIT_REPORT",
            "credit_score": reasoning_result.get("credit_score"),
            "outstanding_debts": reasoning_result.get("outstanding_debts", []),
            "payment_history": reasoning_result.get("payment_history", {}),
            "report_date": reasoning_result.get("report_date"),
            "confidence": reasoning_result.get("confidence", 0.85),
            "status": "PROCESSED"
        }
    
    async def _process_property_appraisal(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process property appraisal documents.
        
        Args:
            document: Property appraisal document data
            
        Returns:
            Dict with extracted property information
        """
        property_plugin = self.kernel.plugins.get("document_plugin")
        
        # Process document content through plugin
        extracted_data = await property_plugin.extract_property_data.invoke_async(document.get("content", ""))
        
        # Use reasoning agent for validation and complex extraction
        reasoning_result = await self.reasoning_agent.reason_about_property_document(
            document_content=document.get("content", ""),
            initial_extraction=extracted_data.result
        )
        
        # Combine results
        return {
            "document_type": "PROPERTY_APPRAISAL",
            "property_value": reasoning_result.get("property_value"),
            "property_address": reasoning_result.get("property_address"),
            "property_type": reasoning_result.get("property_type"),
            "appraisal_date": reasoning_result.get("appraisal_date"),
            "confidence": reasoning_result.get("confidence", 0.85),
            "status": "PROCESSED"
        }
    
    async def _process_bank_statement(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process bank statement documents.
        
        Args:
            document: Bank statement document data
            
        Returns:
            Dict with extracted banking information
        """
        bank_plugin = self.kernel.plugins.get("document_plugin")
        
        # Process document content through plugin
        extracted_data = await bank_plugin.extract_bank_data.invoke_async(document.get("content", ""))
        
        # Use reasoning agent for validation and complex extraction
        reasoning_result = await self.reasoning_agent.reason_about_bank_document(
            document_content=document.get("content", ""),
            initial_extraction=extracted_data.result
        )
        
        # Combine results
        return {
            "document_type": "BANK_STATEMENT",
            "account_balance": reasoning_result.get("account_balance"),
            "account_number": reasoning_result.get("account_number"),
            "transactions": reasoning_result.get("transactions", []),
            "statement_period": reasoning_result.get("statement_period", {}),
            "confidence": reasoning_result.get("confidence", 0.85),
            "status": "PROCESSED"
        }
    
    async def _process_id_verification(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process ID verification documents.
        
        Args:
            document: ID verification document data
            
        Returns:
            Dict with extracted identity information
        """
        id_plugin = self.kernel.plugins.get("document_plugin")
        
        # Process document content through plugin
        extracted_data = await id_plugin.extract_id_data.invoke_async(document.get("content", ""))
        
        # Use reasoning agent for validation and complex extraction
        reasoning_result = await self.reasoning_agent.reason_about_id_document(
            document_content=document.get("content", ""),
            initial_extraction=extracted_data.result
        )
        
        # Combine results
        return {
            "document_type": "ID_VERIFICATION",
            "full_name": reasoning_result.get("full_name"),
            "date_of_birth": reasoning_result.get("date_of_birth"),
            "id_number": reasoning_result.get("id_number"),
            "id_type": reasoning_result.get("id_type"),
            "expiration_date": reasoning_result.get("expiration_date"),
            "confidence": reasoning_result.get("confidence", 0.85),
            "status": "PROCESSED"
        }
    
    async def _process_generic_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process generic documents that don't fit specific categories.
        
        Args:
            document: Generic document data
            
        Returns:
            Dict with extracted text and basic analysis
        """
        # Use default document processing
        generic_plugin = self.kernel.plugins.get("document_plugin")
        
        # Extract text and basic entities
        extracted_text = await generic_plugin.extract_text.invoke_async(document.get("content", ""))
        
        return {
            "document_type": document.get("document_type", "UNKNOWN"),
            "extracted_text": extracted_text.result,
            "confidence": 0.7,  # Default lower confidence for generic documents
            "status": "PROCESSED"
        }
    
    def _consolidate_results(self, document_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Consolidate results from multiple documents into a unified structure.
        
        Args:
            document_results: List of individual document analysis results
            
        Returns:
            Dict with consolidated results by document type
        """
        consolidated = {}
        
        for result in document_results:
            doc_type = result.get("document_type")
            if doc_type:
                consolidated[doc_type] = result
        
        return consolidated
    
    def _identify_missing_documents(self, consolidated_results: Dict[str, Any]) -> List[str]:
        """
        Identify any required documents that are missing.
        
        Args:
            consolidated_results: Consolidated document results
            
        Returns:
            List of missing document types
        """
        required_documents = self._get_required_document_types()
        
        # Check which required documents are missing
        missing = [doc_type for doc_type in required_documents 
                  if doc_type not in consolidated_results]
        
        return missing
    
    def _get_required_document_types(self) -> List[str]:
        """
        Get the list of required document types for a mortgage application.
        
        Returns:
            List of required document type strings
        """
        # This could be configurable based on loan type
        return [
            "INCOME_VERIFICATION",
            "CREDIT_REPORT",
            "PROPERTY_APPRAISAL",
            "ID_VERIFICATION"
        ]
    
    async def _identify_inconsistencies(self, consolidated_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify inconsistencies across documents.
        
        Args:
            consolidated_results: Consolidated document results
            
        Returns:
            List of identified inconsistencies
        """
        inconsistencies = []
        
        # Use reasoning agent to identify inconsistencies
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
    
    async def _generate_document_summary(self, consolidated_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary of all analyzed documents.
        
        Args:
            consolidated_results: Consolidated document results
            
        Returns:
            Dict with summarized document information
        """
        try:
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