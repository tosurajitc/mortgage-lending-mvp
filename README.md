# Mortgage Lending Assistant MVP

An intelligent mortgage lending assistant that uses agentic AI to streamline the mortgage application process.

## Overview

This project implements a multi-agent AI system for mortgage lending that:

- Processes mortgage applications through an intelligent workflow
- Analyzes loan documents using Azure Document Intelligence
- Makes underwriting decisions based on comprehensive data analysis
- Ensures regulatory compliance with mortgage lending rules
- Provides a conversational interface through Copilot Studio

## Features

- **Document Analysis**: Automated extraction of key information from mortgage documents
- **Intelligent Underwriting**: Risk assessment and lending decision support
- **Compliance Checking**: Automated verification of regulatory requirements
- **Multi-Agent Architecture**: Collaborative AI agents for specialized tasks
- **Conversational UI**: Natural language interface for applicants and lenders

## Architecture

The system uses a multi-agent architecture with these key components:

- **Orchestrator Agent**: Coordinates the overall workflow
- **Document Analysis Agent**: Processes and extracts data from documents
- **Underwriting Agent**: Evaluates loan applications
- **Compliance Agent**: Ensures regulatory requirements are met
- **Customer Service Agent**: Handles inquiries and explanations

## Technology Stack

- **Python 3.9+** for core development
- **Azure OpenAI** for AI capabilities
- **Semantic Kernel** for plugin architecture
- **AutoGen** for multi-agent reasoning
- **Azure Document Intelligence** for document analysis
- **Azure Cosmos DB** for data storage
- **Copilot Studio** for conversational interface

## Setup

### Prerequisites

- Python 3.9 or higher
- Azure subscription with access to:
  - Azure OpenAI Service
  - Azure Document Intelligence
  - Azure Cosmos DB
  - Azure Storage
- Copilot Studio subscription

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/mortgage-lending-mvp.git
   cd mortgage-lending-mvp
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   python scripts/setup_env.py
   ```

5. Verify your environment setup:
   ```bash
   python scripts/test_env.py
   ```

## Development

### Project Structure

```
mortgage-lending-mvp/
├── src/                     # Source code
│   ├── agents/              # Agent implementations
│   ├── autogen/             # AutoGen integration
│   ├── semantic_kernel/     # Semantic Kernel plugins
│   ├── copilot/             # Copilot Studio integration
│   ├── data/                # Data models and management
│   ├── security/            # Security components
│   ├── workflow/            # Workflow management
│   ├── utils/               # Utility functions
│   └── api/                 # API layer
├── config/                  # Configuration files
├── tests/                   # Test suite
├── docs/                    # Documentation
├── scripts/                 # Utility scripts
├── deployment/              # Deployment configuration
└── mock_data/               # Test data generators
```

### Running Tests

```bash
pytest
```

### Running the Application

```bash
python src/api/app.py
```

## Usage

### API Endpoints

The system exposes the following API endpoints:

- `POST /api/applications`: Create a new mortgage application
- `POST /api/applications/{id}/documents`: Submit documents for an application
- `GET /api/applications/{id}/status`: Check application status
- `GET /api/applications/{id}`: Get application details

### Copilot Integration

The system integrates with Copilot Studio to provide a conversational interface. See the `docs/copilot_integration.md` file for details on setting up the integration.

## License

[MIT](LICENSE)