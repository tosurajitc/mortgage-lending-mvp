"""
Document Memory Integration Module

Provides memory management capabilities for document analysis agents,
allowing storage and retrieval of document analysis context across sessions.
"""

import json
from typing import Dict, List, Any, Optional

from src.semantic_kernel.memory_manager import MemoryManager
from src.utils.logging_utils import get_logger

logger = get_logger("document_memory")

class DocumentMemoryManager:
    """
    Manages memory operations for document analysis.
    
    This class provides specialized memory operations for document processing,
    enabling semantic search, contextual history, and related functionality.
    """
    
    def __init__(self):
        """Initialize the document memory manager."""
        self.memory_manager = MemoryManager()
        self.logger = logger
        
    async def store_document_analysis(self, 
                                    application_id: str, 
                                    document_id: str, 
                                    document_type: str,
                                    analysis_results: Dict[str, Any]) -> str:
        """
        Store document analysis results in memory for future reference.
        
        Args:
            application_id: ID of the mortgage application
            document_id: Unique ID of the analyzed document
            document_type: Type of document (e.g., INCOME_VERIFICATION)
            analysis_results: Results of document analysis
            
        Returns:
            The memory key where the results are stored
        """
        context_id = f"document_analysis_{application_id}"
        memory_key = f"{document_type}_{document_id}"
        
        # Create document analysis context if it doesn't exist
        context = self.memory_manager.retrieve_context(context_id)
        if context is None:
            context = {
                "application_id": application_id,
                "documents": {}
            }
        
        # Add document analysis to context
        if "documents" not in context:
            context["documents"] = {}
            
        context["documents"][memory_key] = {
            "document_type": document_type,
            "document_id": document_id,
            "timestamp": self._get_timestamp(),
            "results": analysis_results
        }
        
        # Store document text for semantic search
        document_text = self._extract_document_text(analysis_results)
        if document_text:
            semantic_key = await self._store_in_semantic_memory(
                application_id=application_id,
                document_id=document_id,
                document_type=document_type,
                document_text=document_text,
                analysis_highlights=self._extract_highlights(analysis_results)
            )
            context["documents"][memory_key]["semantic_key"] = semantic_key
        
        # Update the context in memory
        self.memory_manager.store_context(context_id, context, "document_analysis")
        
        self.logger.info(f"Stored document analysis for {document_type} in application {application_id}")
        return memory_key
        
    async def retrieve_document_analysis(self, 
                                      application_id: str, 
                                      document_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve document analysis results for an application.
        
        Args:
            application_id: ID of the mortgage application
            document_type: Optional filter for specific document type
            
        Returns:
            Dictionary of document analysis results
        """
        context_id = f"document_analysis_{application_id}"
        context = self.memory_manager.retrieve_context(context_id)
        
        if context is None or "documents" not in context:
            return {}
            
        # If document type is specified, filter results
        if document_type:
            filtered_documents = {}
            for key, doc in context["documents"].items():
                if doc.get("document_type") == document_type:
                    filtered_documents[key] = doc
            return filtered_documents
        
        return context["documents"]
        
    async def search_similar_documents(self, 
                                     application_id: str, 
                                     query_text: str, 
                                     limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for semantically similar documents.
        
        Args:
            application_id: ID of the mortgage application
            query_text: Text to search for
            limit: Maximum number of results to return
            
        Returns:
            List of similar document results
        """
        collection_name = f"documents_{application_id}"
        
        try:
            # Retrieve similar documents from semantic memory
            similar_docs = await self.memory_manager.retrieve_similar_memories(
                collection_name=collection_name,
                query=query_text,
                limit=limit
            )
            
            # Map memory results to document results
            results = []
            for doc in similar_docs:
                doc_id = doc.get("metadata", {}).get("document_id")
                doc_type = doc.get("metadata", {}).get("document_type")
                
                # Retrieve full document analysis if available
                if doc_id and doc_type:
                    doc_analysis = await self.retrieve_document_analysis(
                        application_id=application_id,
                        document_type=doc_type
                    )
                    
                    doc_key = next((k for k, v in doc_analysis.items() 
                                 if v.get("document_id") == doc_id), None)
                    
                    if doc_key:
                        results.append({
                            "document_id": doc_id,
                            "document_type": doc_type,
                            "relevance_score": doc.get("relevance", 0),
                            "analysis": doc_analysis[doc_key].get("results", {}),
                            "highlights": doc.get("metadata", {}).get("highlights", [])
                        })
                    else:
                        # If full analysis not found, return basic info
                        results.append({
                            "document_id": doc_id,
                            "document_type": doc_type,
                            "relevance_score": doc.get("relevance", 0),
                            "text": doc.get("text", ""),
                            "highlights": doc.get("metadata", {}).get("highlights", [])
                        })
                        
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching similar documents: {str(e)}", exc_info=True)
            return []
            
    async def update_document_analysis(self,
                                    application_id: str,
                                    document_id: str,
                                    updates: Dict[str, Any]) -> bool:
        """
        Update existing document analysis with new information.
        
        Args:
            application_id: ID of the mortgage application
            document_id: ID of the document to update
            updates: New information to add to the analysis
            
        Returns:
            True if successful, False otherwise
        """
        context_id = f"document_analysis_{application_id}"
        context = self.memory_manager.retrieve_context(context_id)
        
        if context is None or "documents" not in context:
            return False
            
        # Find the document to update
        for key, doc in context["documents"].items():
            if doc.get("document_id") == document_id:
                # Update the results
                if "results" in doc:
                    doc["results"].update(updates)
                else:
                    doc["results"] = updates
                    
                # Update timestamp
                doc["updated_at"] = self._get_timestamp()
                
                # Store updated context
                self.memory_manager.store_context(context_id, context, "document_analysis")
                return True
                
        return False
        
    async def store_document_relationships(self,
                                        application_id: str,
                                        relationships: List[Dict[str, Any]]) -> bool:
        """
        Store relationships between documents.
        
        Args:
            application_id: ID of the mortgage application
            relationships: List of document relationship objects
            
        Returns:
            True if successful, False otherwise
        """
        context_id = f"document_relationships_{application_id}"
        
        try:
            # Create or retrieve relationships context
            context = self.memory_manager.retrieve_context(context_id) or {
                "application_id": application_id,
                "relationships": []
            }
            
            # Add new relationships
            if "relationships" not in context:
                context["relationships"] = []
                
            context["relationships"].extend(relationships)
            
            # Store updated context
            self.memory_manager.store_context(context_id, context, "document_relationships")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing document relationships: {str(e)}", exc_info=True)
            return False
            
    async def retrieve_document_relationships(self,
                                          application_id: str,
                                          document_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relationships between documents.
        
        Args:
            application_id: ID of the mortgage application
            document_id: Optional filter for relationships involving a specific document
            
        Returns:
            List of document relationship objects
        """
        context_id = f"document_relationships_{application_id}"
        context = self.memory_manager.retrieve_context(context_id)
        
        if context is None or "relationships" not in context:
            return []
            
        # If document_id is specified, filter for relationships involving that document
        if document_id:
            return [
                rel for rel in context["relationships"]
                if rel.get("source_id") == document_id or rel.get("target_id") == document_id
            ]
            
        return context["relationships"]
        
    async def store_document_verification_history(self,
                                              application_id: str,
                                              document_id: str,
                                              verification_record: Dict[str, Any]) -> bool:
        """
        Store verification history for a document.
        
        Args:
            application_id: ID of the mortgage application
            document_id: ID of the document
            verification_record: Verification information
            
        Returns:
            True if successful, False otherwise
        """
        context_id = f"document_verification_{application_id}"
        
        try:
            # Create or retrieve verification context
            context = self.memory_manager.retrieve_context(context_id) or {
                "application_id": application_id,
                "verification_history": {}
            }
            
            # Ensure verification_history exists
            if "verification_history" not in context:
                context["verification_history"] = {}
                
            # Add timestamp to verification record
            verification_record["timestamp"] = self._get_timestamp()
            
            # Add document verification history
            if document_id not in context["verification_history"]:
                context["verification_history"][document_id] = []
                
            context["verification_history"][document_id].append(verification_record)
            
            # Store updated context
            self.memory_manager.store_context(context_id, context, "document_verification")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing document verification: {str(e)}", exc_info=True)
            return False
    
    async def _store_in_semantic_memory(self,
                                     application_id: str,
                                     document_id: str,
                                     document_type: str,
                                     document_text: str,
                                     analysis_highlights: List[str]) -> str:
        """
        Store document text in semantic memory for similarity search.
        
        Args:
            application_id: ID of the mortgage application
            document_id: ID of the document
            document_type: Type of document
            document_text: Text content of the document
            analysis_highlights: Key highlights from the analysis
            
        Returns:
            Key of the stored memory
        """
        collection_name = f"documents_{application_id}"
        
        # Create metadata to store with the text
        metadata = {
            "document_id": document_id,
            "document_type": document_type,
            "application_id": application_id,
            "highlights": analysis_highlights
        }
        
        # Store in semantic memory
        memory_key = self.memory_manager.store_semantic_memory(
            collection_name=collection_name,
            text=document_text,
            metadata=metadata
        )
        
        return memory_key
    
    def _extract_document_text(self, analysis_results: Dict[str, Any]) -> str:
        """
        Extract text content from document analysis results.
        
        Args:
            analysis_results: Document analysis results
            
        Returns:
            Extracted text content
        """
        # Try to extract text from various possible locations
        if "extracted_text" in analysis_results:
            return analysis_results["extracted_text"]
            
        # For structured document results, create a text representation
        text_parts = []
        
        # Recursively extract all string values
        def extract_text_values(obj, prefix=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, (dict, list)):
                        extract_text_values(value, f"{prefix}{key}: ")
                    elif value is not None:
                        text_parts.append(f"{prefix}{key}: {value}")
            elif isinstance(obj, list):
                for item in obj:
                    extract_text_values(item, prefix)
                    
        extract_text_values(analysis_results)
        return "\n".join(text_parts)
    
    def _extract_highlights(self, analysis_results: Dict[str, Any]) -> List[str]:
        """
        Extract key highlights from document analysis results.
        
        Args:
            analysis_results: Document analysis results
            
        Returns:
            List of key highlights
        """
        highlights = []
        
        # Extract highlights based on document type
        doc_type = analysis_results.get("document_type", "")
        
        if doc_type == "INCOME_VERIFICATION":
            if "income_amount" in analysis_results:
                highlights.append(f"Income: {analysis_results['income_amount']}")
            if "employer_name" in analysis_results:
                highlights.append(f"Employer: {analysis_results['employer_name']}")
        
        elif doc_type == "CREDIT_REPORT":
            if "credit_score" in analysis_results:
                highlights.append(f"Credit Score: {analysis_results['credit_score']}")
        
        elif doc_type == "PROPERTY_APPRAISAL":
            if "property_value" in analysis_results:
                highlights.append(f"Property Value: {analysis_results['property_value']}")
            if "property_address" in analysis_results:
                highlights.append(f"Address: {analysis_results['property_address']}")
        
        elif doc_type == "BANK_STATEMENT":
            if "account_balance" in analysis_results:
                highlights.append(f"Balance: {analysis_results['account_balance']}")
        
        # If no specific highlights were found, use generic extraction
        if not highlights:
            # Check for confidence score
            if "confidence" in analysis_results:
                highlights.append(f"Confidence: {analysis_results['confidence']}")
                
            # Take the first few key-value pairs as highlights
            count = 0
            for key, value in analysis_results.items():
                if key not in ("document_type", "status", "confidence") and count < 3:
                    if isinstance(value, (str, int, float, bool)):
                        highlights.append(f"{key}: {value}")
                        count += 1
        
        return highlights
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    async def retrieve_document_verification_history(self,
                                                application_id: str,
                                                document_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve verification history for a document.
        
        Args:
            application_id: ID of the mortgage application
            document_id: ID of the document
            
        Returns:
            List of verification records
        """
        context_id = f"document_verification_{application_id}"
        context = self.memory_manager.retrieve_context(context_id)
        
        if context is None or "verification_history" not in context:
            return []
            
        # Return verification history for the specified document
        return context["verification_history"].get(document_id, [])