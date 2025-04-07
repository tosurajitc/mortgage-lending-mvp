from ...agents.document_agent import DocumentAnalysisAgent
from src.utils.logging_utils import get_logger
import uuid
from datetime import datetime, timezone

class DocumentActions:
    def __init__(self):
        self.document_agent = DocumentAnalysisAgent()
        self.logger = get_logger("document_actions")
    
    async def validate_document(self, document_type, document_content):
        """Validate a document before submission"""
        return await self.document_agent.validate_document(document_type, document_content)
    
    async def explain_document_requirements(self, document_type):
        """Explain the requirements for a specific document type"""
        return await self.document_agent.get_document_requirements(document_type)
    
    async def upload_document(self, 
        application_id,  # Changed from applicationId 
        document_type,   # Changed from documentType
        document_year=None,
        document_description=None,
        document_format="PDF",
        document_content=""
    ):
        try:
            self.logger.info(f"Processing document upload for application {application_id}: {document_type}")
            
            # Validate the application ID
            application = await self._get_application(application_id)
            if not application:
                return {
                    "error": f"Application {application_id} not found",
                    "message": "Could not find the specified application"
                }
            
            # Validate document type
            if not self._is_valid_document_type(document_type):
                return {
                    "error": "Invalid document type",
                    "message": f"Document type '{document_type}' is not recognized"
                }
            
            # Check if document content is provided
            if not document_content:
                return {
                    "error": "Missing document content",
                    "message": "No document content was provided"
                }
            
            # Create document metadata
            full_document_metadata = {
                "document_type": document_type,
                "document_year": document_year,
                "document_description": document_description,
                "document_format": document_format,
                "upload_timestamp": self._get_current_timestamp()
            }
            
            # Save document content
            document_id = await self._save_document_content(
                application_id, 
                document_type, 
                document_content
            )
            
            # Update application with document reference
            await self._update_application_documents(
                application_id, 
                document_id, 
                full_document_metadata
            )
            
            # Check if this resolves a missing document requirement
            is_required = await self._is_required_document(application_id, document_type)
            
            # Get next steps based on application status
            next_steps = await self._get_document_next_steps(application_id, document_type, is_required)
            
            # Return success response
            return {
                "document_id": document_id,
                "message": f"{document_type} uploaded successfully",
                "next_steps": next_steps,
                "requires_review": True
            }
            
        except Exception as e:
            self.logger.error(f"Error uploading document: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "message": "An error occurred while processing the document"
            }
    
    # Helper methods with mock implementations for MVP
    async def _get_application(self, application_id):
        """Mock implementation to retrieve application"""
        # For MVP/hackathon, just pretend we found the application
        return {"id": application_id, "status": "PROCESSING"}

    def _is_valid_document_type(self, document_type):
        """Check if document type is valid"""
        valid_types = [
            "INCOME_VERIFICATION", "CREDIT_REPORT", "PROPERTY_APPRAISAL",
            "BANK_STATEMENT", "ID_VERIFICATION", "TAX_RETURN", "OTHER",
            # Include original types for backward compatibility
            "W2Form", "PayStub", "BankStatement", "TaxReturn", 
            "CreditReport", "DriverLicense", "PropertyAppraisal"
        ]
        return document_type in valid_types

    async def _save_document_content(self, application_id, document_type, document_content):
        """Save document content to storage (mock implementation)"""
        # For MVP/hackathon, generate a document ID without actually storing
        return f"DOC-{uuid.uuid4().hex[:8].upper()}"

    async def _update_application_documents(self, application_id, document_id, document_metadata):
        """Update application record with document reference (mock implementation)"""
        # For MVP/hackathon, just pretend we updated the application
        return True

    async def _is_required_document(self, application_id, document_type):
        """Check if document is required (mock implementation)"""
        # For MVP/hackathon, assume all documents are required
        return True

    async def _get_document_next_steps(self, application_id, document_type, is_required):
        """Generate next steps based on document upload"""
        if is_required:
            return [
                "Document will be reviewed within 1-2 business days",
                "Check application status for updates",
                "Submit any remaining required documents"
            ]
        else:
            return [
                "Document will be added to your application",
                "No further action needed for this document"
            ]

    def _get_current_timestamp(self):
        """Get current timestamp in ISO format"""
        return datetime.now(timezone.utc).isoformat()