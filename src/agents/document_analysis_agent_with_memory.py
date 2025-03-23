"""
Document Analysis Agent Module with Enhanced Memory Management
Specializes in processing and analyzing various mortgage-related documents.
"""

from typing import Any, Dict, List, Optional
import asyncio
import uuid

from .base_agent import BaseAgent
from src.semantic_kernel.kernel_setup import get_kernel
from src.autogen.reasoning_agents import get_document_reasoning_agent
from utils.logging_utils import get_logger
from .document_memory_integration import DocumentMemoryManager


class DocumentAnalysisAgent(BaseAgent):
    """
    Agent responsible for analyzing mortgage application documents,
    extracting relevant information, and validating document completeness.
    Enhanced with memory management for contextual understanding.
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
        
        # Initialize document memory manager
        self.memory_manager = DocumentMemoryManager()
        
        self.logger.info("Document analysis agent initialized with memory management")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and analyze mortgage application documents.
        
        Args:
            input_data: Document data to analyze, including:
                - application_id: The ID of the application
                - documents: List of document objects to analyze
                - is_update: Boolean indicating if this is an update to existing docs
                - check_context: Boolean indicating whether to check context for existing analysis
                
        Returns:
            Dict containing analysis results
        """
        documents = input_data.get("documents", [])
        application_id = input_data.get("application_id")
        is_update = input_data.get("is_update", False)
        check_context = input_data.get("check_context", True)
        
        if not documents:
            self.logger.warning(f"No documents provided for application {application_id}")
            return {
                "is_complete": False,
                "missing_documents": self._get_required_document_types(),
                "summary": {"error": "No documents provided"}
            }
        
        self.log_processing_step(f"Processing {len(documents)} documents for application {application_id}")
        
        # Check if we have previous analysis in memory if check_context is enabled
        existing_documents = {}
        if check_context and application_id:
            self.log_processing_step("Checking for existing document analysis in context")
            existing_documents = await self.memory_manager.retrieve_document_analysis(application_id)
            
            if existing_documents:
                self.log_processing_step(f"Found {len(existing_documents)} existing documents in context")
        
        # Process new documents
        document_results = []
        for doc in documents:
            # Ensure document has an ID
            if "document_id" not in doc:
                doc["document_id"] = str(uuid.uuid4())
                
            # Check if we already have analysis for this document
            existing_doc = None
            if is_update and existing_documents:
                # Try to find existing analysis by document ID
                for key, value in existing_documents.items():
                    if value.get("document_id") == doc["document_id"]:
                        existing_doc = value
                        break
            
            # If updating and we have existing analysis, merge with updates
            if is_update and existing_doc and "results" in existing_doc:
                # Process the document to get new analysis
                new_analysis = await self._analyze_document(doc)
                
                # Update the existing analysis in memory
                await self.memory_manager.update_document_analysis(
                    application_id=application_id,
                    document_id=doc["document_id"],
                    updates=new_analysis
                )
                
                # Merge existing and new analysis
                merged_analysis = dict(existing_doc["results"])
                merged_analysis.update(new_analysis)
                document_results.append(merged_analysis)
            else:
                # Process the document from scratch
                analysis_result = await self._analyze_document(doc)
                document_results.append(analysis_result)
                
                # Store the new analysis in memory
                if application_id:
                    await self.memory_manager.store_document_analysis(
                        application_id=application_id,
                        document_id=doc["document_id"],
                        document_type=doc.get("document_type", "UNKNOWN"),
                        analysis_results=analysis_result
                    )
        
        # Consolidate results
        consolidated_results = self._consolidate_results(document_results)
        
        # Check for missing required documents
        missing_documents = self._identify_missing_documents(consolidated_results)
        
        # Check for document relationships and store them
        if application_id and len(document_results) > 1:
            self.log_processing_step("Analyzing document relationships")
            document_relationships = await self._analyze_document_relationships(document_results)
            
            if document_relationships:
                await self.memory_manager.store_document_relationships(
                    application_id=application_id,
                    relationships=document_relationships
                )
        
        # Check for inconsistencies across documents
        inconsistencies = await self._identify_inconsistencies(consolidated_results)
        
        # Generate a summary of the documents
        summary = await self._generate_document_summary(consolidated_results)
        
        # If this is an application we're tracking, store verification records
        if application_id:
            for doc_result in document_results:
                doc_id = doc_result.get("document_id")
                if doc_id:
                    # Store verification record
                    await self.memory_manager.store_document_verification_history(
                        application_id=application_id,
                        document_id=doc_id,
                        verification_record={
                            "verification_type": "automated_analysis",
                            "confidence": doc_result.get("confidence", 0.0),
                            "status": doc_result.get("status", "UNKNOWN"),
                            "has_inconsistencies": doc_id in [inc.get("document_id") for inc in inconsistencies]
                        }
                    )
        
        result = {
            "application_id": application_id,
            "document_results": consolidated_results,
            "is_complete": len(missing_documents) == 0,
            "missing_documents": missing_documents,
            "inconsistencies": inconsistencies,
            "summary": summary,
            "overall_confidence": self._calculate_overall_confidence(document_results)
        }
        
        # If requested, perform a semantic search for similar documents
        if input_data.get("search_query") and application_id:
            query = input_data["search_query"]
            self.log_processing_step(f"Searching for documents matching: {query}")
            
            similar_docs = await self.memory_manager.search_similar_documents(
                application_id=application_id,
                query_text=query,
                limit=input_data.get("search_limit", 5)
            )
            
            result["search_results"] = similar_docs
        
        return result
    
    async def retrieve_document_history(self, application_id: str, document_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve document history for an application.
        
        Args:
            application_id: ID of the application
            document_id: Optional ID of a specific document
            
        Returns:
            Document history information
        """
        try:
            # Retrieve document analysis from memory
            documents = await self.memory_manager.retrieve_document_analysis(
                application_id=application_id,
                document_type=None if document_id else None
            )
            
            # If document_id is specified, filter to that document
            if document_id and documents:
                filtered_docs = {}
                for key, doc in documents.items():
                    if doc.get("document_id") == document_id:
                        filtered_docs[key] = doc
                documents = filtered_docs
            
            # Retrieve verification history
            verifications = {}
            if document_id:
                # Get verification history for specific document
                verification_history = await self.memory_manager.retrieve_document_verification_history(
                    application_id=application_id,
                    document_id=document_id
                )
                if verification_history:
                    verifications[document_id] = verification_history
            else:
                # Get verification history for all documents
                for key, doc in documents.items():
                    doc_id = doc.get("document_id")
                    if doc_id:
                        verification_history = await self.memory_manager.retrieve_document_verification_history(
                            application_id=application_id,
                            document_id=doc_id
                        )
                        if verification_history:
                            verifications[doc_id] = verification_history
            
            # Retrieve document relationships
            relationships = await self.memory_manager.retrieve_document_relationships(
                application_id=application_id,
                document_id=document_id
            )
            
            return {
                "application_id": application_id,
                "documents": documents,
                "verifications": verifications,
                "relationships": relationships
            }
            
        except Exception as e:
            self.logger.error(f"Error retrieving document history: {str(e)}", exc_info=True)
            return {
                "application_id": application_id,
                "error": f"Failed to retrieve document history: {str(e)}"
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
            document_id = document.get("document_id", str(uuid.uuid4()))
            
            self.log_processing_step(f"Analyzing document of type: {document_type}")
            
            # Add document_id to the result for tracking
            result = {
                "document_id": document_id,
                "document_type": document_type
            }
            
            # Handle document based on its type
            if document_type == "INCOME_VERIFICATION":
                analysis = await self._process_income_verification(document)
                result.update(analysis)
                
            elif document_type == "CREDIT_REPORT":
                analysis = await self._process_credit_report(document)
                result.update(analysis)
                
            elif document_type == "PROPERTY_APPRAISAL":
                analysis = await self._process_property_appraisal(document)
                result.update(analysis)
                
            elif document_type == "BANK_STATEMENT":
                analysis = await self._process_bank_statement(document)
                result.update(analysis)
                
            elif document_type == "ID_VERIFICATION":
                analysis = await self._process_id_verification(document)
                result.update(analysis)
                
            else:
                # For unknown document types, use generic processing
                analysis = await self._process_generic_document(document)
                result.update(analysis)
                
            return result
                
        except Exception as e:
            self.logger.error(f"Error analyzing document: {str(e)}", exc_info=True)
            return {
                "document_id": document.get("document_id", str(uuid.uuid4())),
                "document_type": document.get("document_type"),
                "status": "ERROR",
                "error_message": str(e),
                "confidence": 0.0
            }
    
    async def _analyze_document_relationships(self, document_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze relationships between documents.
        
        Args:
            document_results: List of document analysis results
            
        Returns:
            List of document relationship objects
        """
        relationships = []
        
        try:
            # Use reasoning agent to identify relationships
            reasoning_result = await self.reasoning_agent.identify_document_relationships(
                document_results=document_results
            )
            
            if reasoning_result and "relationships" in reasoning_result:
                relationships = reasoning_result["relationships"]
                
                # Ensure relationships have proper format
                for relationship in relationships:
                    if "type" not in relationship:
                        relationship["type"] = "related"
                    if "confidence" not in relationship:
                        relationship["confidence"] = 0.7
                
        except Exception as e:
            self.logger.error(f"Error analyzing document relationships: {str(e)}", exc_info=True)
        
        return relationships
    
    # The remaining methods would stay the same as in your original implementation
    # I'll include a few key methods here that might be affected by memory integration
    
    async def _process_income_verification(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Process income verification documents (W-2s, pay stubs, etc.)."""
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
    
    def _consolidate_results(self, document_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Consolidate results from multiple documents into a unified structure."""
        consolidated = {}
        
        for result in document_results:
            doc_type = result.get("document_type")
            if doc_type:
                consolidated[doc_type] = result
        
        return consolidated
    
    def _identify_missing_documents(self, consolidated_results: Dict[str, Any]) -> List[str]:
        """Identify any required documents that are missing."""
        required_documents = self._get_required_document_types()
        
        # Check which required documents are missing
        missing = [doc_type for doc_type in required_documents 
                  if doc_type not in consolidated_results]
        
        return missing


    def _get_required_document_types(self) -> List[str]:
        """Get the list of required document types for a mortgage application."""
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
                    
                    # Store inconsistencies in memory if applicable
                    application_id = next(
                        (doc.get("application_id") for doc in consolidated_results.values() if "application_id" in doc),
                        None
                    )
                    
                    if application_id:
                        context_id = f"document_inconsistencies_{application_id}"
                        inconsistency_data = {
                            "application_id": application_id,
                            "timestamp": self._get_timestamp(),
                            "inconsistencies": inconsistencies
                        }
                        
                        # Store in memory for future reference
                        self.memory_manager.memory_manager.store_context(
                            context_id=context_id,
                            context_data=inconsistency_data,
                            context_type="document_inconsistencies"
                        )
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
                
                # Store the summary in memory if we have an application_id
                application_id = next(
                    (doc.get("application_id") for doc in consolidated_results.values() if "application_id" in doc),
                    None
                )
                
                if application_id:
                    summary["application_id"] = application_id
                    summary["timestamp"] = self._get_timestamp()
                    
                    # Store in memory
                    context_id = f"document_summary_{application_id}"
                    self.memory_manager.memory_manager.store_context(
                        context_id=context_id,
                        context_data=summary,
                        context_type="document_summary"
                    )
            
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
    
    async def retrieve_document_memory(self, 
                                     application_id: str, 
                                     query_text: Optional[str] = None,
                                     memory_type: str = "all") -> Dict[str, Any]:
        """
        Retrieve document-related memory for an application.
        
        Args:
            application_id: ID of the application
            query_text: Optional text to search for semantically similar documents
            memory_type: Type of memory to retrieve ("analysis", "summary", "inconsistencies", "all")
            
        Returns:
            Dict containing requested memory data
        """
        result = {
            "application_id": application_id,
            "timestamp": self._get_timestamp(),
            "memory_type": memory_type
        }
        
        try:
            # Retrieve document analysis if requested
            if memory_type in ["analysis", "all"]:
                document_analysis = await self.memory_manager.retrieve_document_analysis(application_id)
                result["document_analysis"] = document_analysis
            
            # Retrieve document summary if requested
            if memory_type in ["summary", "all"]:
                context_id = f"document_summary_{application_id}"
                summary = self.memory_manager.memory_manager.retrieve_context(context_id)
                if summary:
                    result["document_summary"] = summary
            
            # Retrieve document inconsistencies if requested
            if memory_type in ["inconsistencies", "all"]:
                context_id = f"document_inconsistencies_{application_id}"
                inconsistencies = self.memory_manager.memory_manager.retrieve_context(context_id)
                if inconsistencies:
                    result["document_inconsistencies"] = inconsistencies
            
            # Retrieve document relationships if requested
            if memory_type in ["relationships", "all"]:
                relationships = await self.memory_manager.retrieve_document_relationships(application_id)
                if relationships:
                    result["document_relationships"] = relationships
            
            # Perform semantic search if query text is provided
            if query_text:
                similar_docs = await self.memory_manager.search_similar_documents(
                    application_id=application_id,
                    query_text=query_text,
                    limit=5
                )
                result["search_results"] = similar_docs
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error retrieving document memory: {str(e)}", exc_info=True)
            return {
                "application_id": application_id,
                "error": f"Failed to retrieve document memory: {str(e)}"
            }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    # Adding a method to integrate semantic memory functionality
    async def store_document_context(self, application_id: str, context_data: Dict[str, Any]) -> bool:
        """
        Store contextual information about documents for future reference.
        
        Args:
            application_id: ID of the application
            context_data: Additional context about the documents
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create a context ID for this document context
            context_id = f"document_context_{application_id}"
            
            # Retrieve existing context if it exists
            existing_context = self.memory_manager.memory_manager.retrieve_context(context_id) or {}
            
            # Update with new context data
            existing_context.update({
                "application_id": application_id,
                "updated_at": self._get_timestamp(),
                **context_data
            })
            
            # Store the updated context
            self.memory_manager.memory_manager.store_context(
                context_id=context_id,
                context_data=existing_context,
                context_type="document_context"
            )
            
            self.logger.info(f"Stored document context for application {application_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing document context: {str(e)}", exc_info=True)
            return False
    
    async def retrieve_semantic_memories(self, 
                                       application_id: str, 
                                       query_text: str, 
                                       limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve semantically similar document memories.
        
        Args:
            application_id: ID of the application
            query_text: Query text to search for
            limit: Maximum number of results to return
            
        Returns:
            List of semantically similar document memories
        """
        try:
            # This is a direct interface to the memory manager's search functionality
            return await self.memory_manager.search_similar_documents(
                application_id=application_id,
                query_text=query_text,
                limit=limit
            )
            
        except Exception as e:
            self.logger.error(f"Error retrieving semantic memories: {str(e)}", exc_info=True)
            return []    