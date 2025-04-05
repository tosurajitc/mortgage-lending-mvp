from azure.storage.blob import BlobServiceClient
import os

class DocumentStorageService:
    def __init__(self, connection_string, container_name):
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.blob_service_client.get_container_client(container_name)

    def upload_document(self, file_path, blob_name):
        """
        Upload a document to Azure Blob Storage
        
        :param file_path: Local path of the document
        :param blob_name: Name to give the blob in storage
        :return: URL of the uploaded blob
        """
        try:
            with open(file_path, "rb") as data:
                blob_client = self.container_client.upload_blob(name=blob_name, data=data)
            return blob_client.url
        except Exception as e:
            print(f"Error uploading document: {e}")
            return None

    def download_document(self, blob_name, local_path):
        """
        Download a document from Azure Blob Storage
        
        :param blob_name: Name of the blob in storage
        :param local_path: Local path to save the document
        :return: Boolean indicating success
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            with open(local_path, "wb") as download_file:
                download_file.write(blob_client.download_blob().readall())
            return True
        except Exception as e:
            print(f"Error downloading document: {e}")
            return False

    def list_documents(self):
        """
        List all documents in the container
        
        :return: List of blob names
        """
        try:
            return [blob.name for blob in self.container_client.list_blobs()]
        except Exception as e:
            print(f"Error listing documents: {e}")
            return []