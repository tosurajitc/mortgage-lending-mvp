# Application configuration
APP_ENV=development  # development, testing, production
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
PORT=8000

# Azure OpenAI Service
AZURE_OPENAI_API_KEY=5kB2wiDU0lB29j3qXJkekOherOEDiH0D76TMUC0vEX1IuXSB03dvJQQJ99BCACYeBjFXJ3w3AAABACOGPtcd
AZURE_OPENAI_ENDPOINT=https://surajit-openai.openai.azure.com/
AZURE_OPENAI_API_VERSION=2023-12-01-preview
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Azure Document Intelligence
AZURE_DOCUMENT_INTELLIGENCE_KEY=8362ioYsQarAdgEl5DhTFcPGDdwee1sxEoIzGH1QaatnzJDOBfj0JQQJ99BCACYeBjFXJ3w3AAALACOGIR1c
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://mvp-document-intelligence.cognitiveservices.azure.com/

# Azure Cosmos DB
COSMOS_URI=https://surajit-cosmosdb.documents.azure.com:443/
COSMOS_KEY=CnL0s6Pgwof0ecRoxZO1VF4O5QPCNSYCY48VMm9Qz2INUoTYm9E87REZX5bgZ0vDKl3GRySaEW0VACDbbo3xIA==
COSMOS_DATABASE=MortgageLendingDB
COSMOS_CONTAINER_APPLICATIONS=Applications
COSMOS_CONTAINER_DOCUMENTS=Documents
COSMOS_CONTAINER_AUDIT=AuditLog

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=mortgagelendingmvp;AccountKey=wbjt8hdx5wTyDlrKqY0i7n00YJ/ssSNWgqiuzp4MTSNAhhA1Y5zhm0xf6p1qjzfiOSanD31VXlY1+AStLGh5VQ==;EndpointSuffix=core.windows.net
AZURE_STORAGE_ACCOUNT=mortgagelendingmvp
AZURE_STORAGE_KEY=wbjt8hdx5wTyDlrKqY0i7n00YJ/ssSNWgqiuzp4MTSNAhhA1Y5zhm0xf6p1qjzfiOSanD31VXlY1+AStLGh5VQ==
AZURE_STORAGE_CONTAINER=mortgage-documents

# Security settings
SECRET_KEY=15bc6b55b44813882cefc28dba6d3cdc24d6a38a1bb0e1b34b342a06ff1f667b
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
PII_DETECTION_THRESHOLD=0.8
ENABLE_JAILBREAK_DETECTION=true
JAILBREAK_THRESHOLD=0.65
RATE_LIMIT_REQUESTS_PER_MINUTE=100
MAX_REQUEST_BODY_SIZE=10485760
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
SECURITY_LEVEL=medium




# Copilot Studio
# Copilot Studio Configuration
COPILOT_STUDIO_TOKEN_ENDPOINT=https://default94e1538a3b464d3fb78c1f1613e4b6.a2.environment.api.powerplatform.com/powervirtualagents/botsbyschema/crf19_mortgageLendingAssistant/directline/token?api-version=2022-03-01-preview
COPILOT_STUDIO_API_KEY=SKntTUITIGEYYhliamGao9jJZGhkY2kI73mCBLp4oL7M71j59Y0YJQQJ99BCAC5T7U2AArohAAABAZBSAYQp.9NrQK5Qj2AmwuIpyvyhOGTygP0RbNGyM4qYupktNx573Uka5z4l8JQQJ99BCAC5T7U2AArohAAABAZBS2pj3
COPILOT_STUDIO_BOT_ID=7b832d0c-a98c-4df1-be62-0b131ad44e3a
COPILOT_STUDIO_TENANT_ID=94e1538a-3b46-4d3f-b78c-1f1613e4b6a2

# Monitoring
ENABLE_TELEMETRY=true
OPENTELEMETRY_ENDPOINT=http://localhost:4317

# Agent Configuration
MAX_REASONING_ITERATIONS=5
CONFIDENCE_THRESHOLD=0.7
DEFAULT_AGENT_TEMPERATURE=0.2

# Workflow settings
DOCUMENT_REQUIRED_TYPES=income_verification,credit_report,property_appraisal
COMPLIANCE_RULES_FILE=compliance_rules.json

# Performance & Security Enhancements
REQUEST_TIMEOUT=30
MAX_CONNECTIONS=100
RATE_LIMIT_REQUESTS_PER_MINUTE=100
MAX_REQUEST_BODY_SIZE=10485760  # 10MB
ALLOWED_ORIGINS=https://your-frontend-domain.com,http://localhost:3000

# Advanced Logging
LOG_FILE_PATH=/var/log/mortgage-lending-mvp/app.log
LOG_MAX_BYTES=10485760  # 10MB
LOG_BACKUP_COUNT=5

# Error Handling
RETRY_ATTEMPTS=3
RETRY_DELAY=2  # seconds

# Existing configurations remain the same

# Security Enhancements
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
MAX_REQUEST_BODY_SIZE=10485760  # 10MB in bytes
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_CONCURRENT_CONNECTIONS=50

# Logging Enhancements
LOG_FILE_PATH=logs/mortgage_lending_mvp.log
LOG_MAX_FILE_SIZE=10485760  # 10MB
LOG_BACKUP_COUNT=5
LOG_ROTATION_INTERVAL=daily

# Performance Configurations
CONNECTION_POOL_MIN_CONNECTIONS=5
CONNECTION_POOL_MAX_CONNECTIONS=20
REQUEST_TIMEOUT=30  # seconds
API_REQUEST_TIMEOUT=10  # seconds for external API calls
RETRY_ATTEMPTS=3
RETRY_DELAY=2  # seconds between retry attempts

# Database Connection Pooling
DB_POOL_MIN_CONNECTIONS=5
DB_POOL_MAX_CONNECTIONS=20
DB_CONNECTION_TIMEOUT=10  # seconds

# External Service Timeouts
AZURE_OPENAI_TIMEOUT=30
DOCUMENT_INTELLIGENCE_TIMEOUT=20