# Mortgage Lending Assistant

A sophisticated AI-powered system designed to streamline and automate the residential home mortgage lending process, making it faster, more accurate, and customer-friendly.

## Overview

The Mortgage Lending Assistant addresses the challenges in traditional mortgage lending processes which are typically complex, time-consuming, and prone to human error. This system provides:

- Automated document processing and analysis
- Intelligent underwriting decision support
- Regulatory compliance verification
- Customer-friendly explanations and guidance

The solution is especially applicable for:
- First-time homebuyers
- Refinancing existing properties
- Primary residence purchases
- Secondary/vacation home financing

## Architecture

The system is built on a multi-agent architecture with specialized components:

- **Document Analysis Agent**: Processes and extracts information from mortgage application documents
- **Underwriting Agent**: Evaluates loan applications based on financial criteria
- **Compliance Agent**: Ensures applications meet regulatory requirements
- **Customer Service Agent**: Handles customer inquiries and generates explanations
- **Orchestrator Agent**: Coordinates workflow between all specialized agents

## Technology Stack

- **Backend**: Python, FastAPI
- **AI & ML**: Azure OpenAI Service, Azure Document Intelligence
- **Data Storage**: Azure Cosmos DB, Azure Blob Storage
- **Integration**: Microsoft Copilot Studio
- **Deployment**: Azure App Service, AWS

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Azure subscription with access to:
  - Azure OpenAI Service
  - Azure Document Intelligence
  - Azure Cosmos DB
  - Azure Blob Storage
- Microsoft Copilot Studio environment

### Environment Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd mortgage-lending-assistant
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on the provided template with your Azure credentials and configuration settings

### Running Locally

1. Start the FastAPI server:
   ```
   uvicorn main:app --reload
   ```

2. Access the API documentation at `http://localhost:8000/docs`

### Deployment

#### AWS Deployment

1. Ensure your `requirements.txt` is up-to-date:
   ```
   pip freeze > requirements.txt
   ```

2. Configure CORS in your `main.py` file:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=[
           "https://copilotstudio.microsoft.com",
           "https://ispring.azurewebsites.net"
           # Add any additional domains that will access your API
       ],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

3. Follow AWS deployment guidelines for FastAPI applications

#### Azure Deployment

The system includes integration with Azure App Service for web deployment.

## API Endpoints

### Core API Endpoints

- `POST /api/applications/submit`: Submit a new mortgage application
- `GET /api/applications/{application_id}/status`: Check application status
- `POST /api/applications/{application_id}/documents/upload`: Upload documents
- `POST /api/loan/recommendations`: Get loan type recommendations
- `POST /api/applications/{application_id}/issues/resolve`: Resolve application issues
- `POST /api/loan/eligibility`: Calculate loan eligibility

### Copilot Studio Integration

- `POST /copilot/process-input`: Process conversational input from Copilot Studio
- `GET /copilot/test-connection`: Test endpoint for Copilot Studio integration
- `POST /copilot/submit-application`: Submit application via Copilot Studio
- `GET /copilot/application-status/{application_id}`: Check status via Copilot Studio

## Security Considerations

- All API endpoints are secured with token-based authentication
- PII (Personally Identifiable Information) detection and protection
- Rate limiting to prevent abuse
- Input validation and sanitization
- CORS configuration to restrict access to trusted domains

## Contributors

[Surajit Chatterjee]

## Contact

For support or inquiries, please contact [surajit.chatterjee@in.ibm.com]