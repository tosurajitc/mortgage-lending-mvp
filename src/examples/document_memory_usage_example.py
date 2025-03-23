"""
Example demonstrating how to use the enhanced memory capabilities
of the Document Analysis Agent in a mortgage lending workflow.
"""

import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional

from src.agents.document_analysis_agent_with_memory import DocumentAnalysisAgent
from src.utils.logging_utils import get_logger

logger = get_logger("document_memory_example")

async def process_initial_documents(application_id: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process initial documents for a mortgage application.
    
    Args:
        application_id: ID of the mortgage application
        documents: List of documents to process
        
    Returns:
        Analysis results
    """
    logger.info(f"Processing initial documents for application {application_id}")
    
    # Initialize document agent with memory capabilities
    document_agent = DocumentAnalysisAgent()
    
    # Process the documents
    result = await document_agent.process({
        "application_id": application_id,
        "documents": documents,
        "is_update": False,
        "check_context": True
    })
    
    logger.info(f"Documents processed for application {application_id}")
    
    # Store additional context about the application
    await document_agent.store_document_context(
        application_id=application_id,
        context_data={
            "application_type": "Conventional",
            "loan_amount": 320000,
            "property_type": "Single Family",
            "processing_status": "Initial Review"
        }
    )
    
    return result

async def process_additional_document(application_id: str, document: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an additional document for an existing application.
    
    Args:
        application_id: ID of the mortgage application
        document: Document to process
        
    Returns:
        Updated analysis results
    """
    logger.info(f"Processing additional document for application {application_id}")
    
    # Initialize document agent with memory capabilities
    document_agent = DocumentAnalysisAgent()
    
    # Process the single document, using memory to provide context
    result = await document_agent.process({
        "application_id": application_id,
        "documents": [document],
        "is_update": True,
        "check_context": True
    })
    
    # Update application context
    await document_agent.store_document_context(
        application_id=application_id,
        context_data={
            "processing_status": "Documentation Updated",
            "last_document_type": document.get("document_type")
        }
    )
    
    return result

async def verify_document_consistency(application_id: str) -> Dict[str, Any]:
    """
    Verify consistency across all documents for an application.
    
    Args:
        application_id: ID of the mortgage application
        
    Returns:
        Consistency verification results
    """
    logger.info(f"Verifying document consistency for application {application_id}")
    
    # Initialize document agent with memory capabilities
    document_agent = DocumentAnalysisAgent()
    
    # Retrieve document memory
    memory = await document_agent.retrieve_document_memory(
        application_id=application_id,
        memory_type="all"
    )
    
    # Check if we have inconsistencies in memory
    inconsistencies = memory.get("document_inconsistencies", {}).get("inconsistencies", [])
    
    if inconsistencies:
        logger.warning(f"Found {len(inconsistencies)} inconsistencies in application {application_id}")
        # We could take action here based on the inconsistencies
        
    # Return the document memory retrieval results
    return memory

async def search_for_similar_documents(application_id: str, query: str) -> List[Dict[str, Any]]:
    """
    Search for semantically similar document content across the application.
    
    Args:
        application_id: ID of the mortgage application
        query: Search query text
        
    Returns:
        List of similar document results
    """
    logger.info(f"Searching for documents matching '{query}' in application {application_id}")
    
    # Initialize document agent with memory capabilities
    document_agent = DocumentAnalysisAgent()
    
    # Perform semantic search
    similar_docs = await document_agent.retrieve_semantic_memories(
        application_id=application_id,
        query_text=query,
        limit=5
    )
    
    logger.info(f"Found {len(similar_docs)} matching documents")
    return similar_docs

async def generate_document_history_report(application_id: str) -> Dict[str, Any]:
    """
    Generate a comprehensive report of document history for an application.
    
    Args:
        application_id: ID of the mortgage application
        
    Returns:
        Report of document history
    """
    logger.info(f"Generating document history report for application {application_id}")
    
    # Initialize document agent with memory capabilities
    document_agent = DocumentAnalysisAgent()
    
    # Retrieve document history
    history = await document_agent.retrieve_document_history(
        application_id=application_id
    )
    
    # Generate report
    documents = history.get("documents", {})
    verifications = history.get("verifications", {})
    relationships = history.get("relationships", [])
    
    report = {
        "application_id": application_id,
        "timestamp": document_agent._get_timestamp(),
        "document_count": len(documents),
        "document_types": list(set(doc.get("document_type") for doc in documents.values())),
        "verification_history": {
            doc_id: len(records) for doc_id, records in verifications.items()
        },
        "relationship_count": len(relationships),
        "document_timeline": [
            {
                "document_id": doc.get("document_id"),
                "document_type": doc.get("document_type"),
                "timestamp": doc.get("timestamp"),
                "status": doc.get("results", {}).get("status")
            }
            for doc in sorted(documents.values(), key=lambda x: x.get("timestamp", ""))
        ]
    }
    
    logger.info(f"Generated document history report for application {application_id}")
    return report

# Example usage in a workflow
async def example_workflow():
    """Example workflow demonstrating the use of document memory capabilities."""
    # Generate a unique application ID
    application_id = f"APP-{uuid.uuid4()}"
    
    # Sample documents (in a real scenario, these would contain actual document content)
    initial_documents = [
        {
            "document_id": f"DOC-{uuid.uuid4()}",
            "document_type": "INCOME_VERIFICATION",
            "content": "Sample W-2 form content..."
        },
        {
            "document_id": f"DOC-{uuid.uuid4()}",
            "document_type": "ID_VERIFICATION",
            "content": "Sample driver's license content..."
        }
    ]
    
    # Step 1: Process initial documents
    initial_results = await process_initial_documents(application_id, initial_documents)
    print(f"Initial processing complete. Missing documents: {initial_results['missing_documents']}")
    
    # Step 2: Process an additional document
    additional_document = {
        "document_id": f"DOC-{uuid.uuid4()}",
        "document_type": "CREDIT_REPORT",
        "content": "Sample credit report content..."
    }
    
    updated_results = await process_additional_document(application_id, additional_document)
    print(f"Additional document processed. Missing documents: {updated_results['missing_documents']}")
    
    # Step 3: Verify document consistency
    consistency_results = await verify_document_consistency(application_id)
    if "document_inconsistencies" in consistency_results:
        inconsistencies = consistency_results["document_inconsistencies"].get("inconsistencies", [])
        print(f"Found {len(inconsistencies)} inconsistencies in the documents")
    
    # Step 4: Search for specific information in the documents
    search_results = await search_for_similar_documents(application_id, "credit score")
    print(f"Found {len(search_results)} documents matching 'credit score'")
    
    # Step 5: Generate a document history report
    history_report = await generate_document_history_report(application_id)
    print(f"Document history report generated with {history_report['document_count']} documents")
    
    return {
        "application_id": application_id,
        "initial_results": initial_results,
        "updated_results": updated_results,
        "consistency_results": consistency_results,
        "search_results": search_results,
        "history_report": history_report
    }

# Run the example workflow if executed directly
if __name__ == "__main__":
    result = asyncio.run(example_workflow())
    print(json.dumps(result, indent=2))