
from ...agents.document_agent import DocumentAnalysisAgent

class DocumentActions:
    def __init__(self):
        self.document_agent = DocumentAnalysisAgent()
    
    async def validate_document(self, document_type, document_content):
        """Validate a document before submission"""
        return await self.document_agent.validate_document(document_type, document_content)
    
    async def explain_document_requirements(self, document_type):
        """Explain the requirements for a specific document type"""
        return await self.document_agent.get_document_requirements(document_type)
    

    async def upload_document(self, 
        applicationId,  # Added to match Copilot Studio input
        documentType, 
        documentDescription, 
        documentMetadata  # This can incorporate additional details
    ):
        # Extract additional details from documentMetadata if provided
        document_year = documentMetadata.get('year') if documentMetadata else None
        document_format = documentMetadata.get('format') if documentMetadata else None
        document_content = documentMetadata.get('content') if documentMetadata else None

        try:
            self.logger.info(f"Processing document upload for application {applicationId}: {documentType}")
            
            # Validate the application ID
            application = await self._get_application(applicationId)
            if not application:
                return {
                    "error": f"Application {applicationId} not found",
                    "message": "Could not find the specified application"
                }
            
            # Validate document type
            if not self._is_valid_document_type(documentType):
                return {
                    "error": "Invalid document type",
                    "message": f"Document type '{documentType}' is not recognized"
                }
            
            # Check if document content is provided
            if not document_content:
                return {
                    "error": "Missing document content",
                    "message": "No document content was provided"
                }
            
            # Create document metadata
            full_document_metadata = {
                "document_type": documentType,
                "document_year": document_year,
                "document_description": documentDescription,
                "document_format": document_format,
                "upload_timestamp": self._get_current_timestamp()
            }
            
            # Save document content
            document_id = await self._save_document_content(
                applicationId, 
                documentType, 
                document_content
            )
            
            # Update application with document reference
            await self._update_application_documents(
                applicationId, 
                document_id, 
                full_document_metadata
            )
            
            # Check if this resolves a missing document requirement
            is_required = await self._is_required_document(applicationId, documentType)
            
            # Get next steps based on application status
            next_steps = await self._get_document_next_steps(applicationId, documentType, is_required)
            
            # Return success response
            return {
                "document_id": document_id,
                "message": f"{documentType} uploaded successfully",
                "next_steps": next_steps,
                "requires_review": True
            }
            
        except Exception as e:
            self.logger.error(f"Error uploading document: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "message": "An error occurred while processing the document"
            }
        
    # Helper methods that would need to be implemented

    async def _get_application(self, application_id):
        """Retrieve application from database"""
        # Implementation would depend on your data access layer
        # This would typically query your database for the application
        # For MVP, you might add a simple mock implementation
        pass

    def _is_valid_document_type(self, document_type):
        """Check if document type is valid"""
        valid_types = [
            "W2Form", "PayStub", "BankStatement", "TaxReturn", 
            "CreditReport", "DriverLicense", "PropertyAppraisal"
        ]
        return document_type in valid_types

    async def _save_document_content(self, application_id, document_type, document_content):
        """Save document content to storage"""
        # Implementation would save to Azure Blob Storage or similar
        # This would decode base64 content and store the document
        # Returns a document ID for reference
        # For MVP, you might add a simple mock implementation
        import uuid
        return f"DOC-{uuid.uuid4().hex[:8].upper()}"

    async def _update_application_documents(self, application_id, document_id, document_metadata):
        """Update application record with document reference"""
        # Implementation would update the application record in your database
        # For MVP, you might add a simple mock implementation
        pass

    async def _is_required_document(self, application_id, document_type):
        """Check if document is a required document for the application"""
        # Implementation would check against application requirements
        # For MVP, you might add a simple mock implementation
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
        from datetime import datetime
        return datetime.utcnow().isoformat()