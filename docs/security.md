# Mortgage Lending Assistant Security Documentation

## Overview

This document describes the security features implemented in the Mortgage Lending Assistant application, including input validation, PII detection and protection, jailbreak prevention, and security middleware. It provides guidance for developers, administrators, and security personnel on how to maintain and extend these security features.

## Table of Contents

1. [Security Architecture](#security-architecture)
2. [Input Validation](#input-validation)
3. [PII Detection and Protection](#pii-detection-and-protection)
4. [Jailbreak Prevention](#jailbreak-prevention)
5. [Security Middleware](#security-middleware)
6. [Configuration](#configuration)
7. [Security Incident Response](#security-incident-response)
8. [Secure Coding Guidelines](#secure-coding-guidelines)

## Security Architecture

The security architecture of the Mortgage Lending Assistant follows a defense-in-depth approach with multiple layers of protection:

```
                    ┌─────────────────────────────────────────┐
                    │           FastAPI Application           │
                    └─────────────────────────────────────────┘
                                      ↑
                                      │
┌───────────────────────────────────────────────────────────────────────┐
│                         Security Headers Middleware                    │
├───────────────────────────────────────────────────────────────────────┤
│                       Authentication Middleware                        │
├───────────────────────────────────────────────────────────────────────┤
│                       Rate Limiting Middleware                         │
├───────────────────────────────────────────────────────────────────────┤
│                    Jailbreak Prevention Middleware                     │
├───────────────────────────────────────────────────────────────────────┤
│                       PII Protection Middleware                        │
├───────────────────────────────────────────────────────────────────────┤
│                        Validation Middleware                           │
└───────────────────────────────────────────────────────────────────────┘
                                      ↑
                                      │
                    ┌─────────────────────────────────────────┐
                    │                Client                    │
                    └─────────────────────────────────────────┘
```

This layered approach ensures that security controls are applied consistently across the application, with each layer providing specific protections.

## Input Validation

# Purpose

Input validation prevents injection attacks, overflow attacks, and other vulnerabilities by ensuring that all input data conforms to expected formats and ranges.

# Components

- Base validation function: `validate_input()` provides generic validation
- **Type-specific validators: Functions for validating strings, numbers, dates, emails, etc.
- Agent-specific validators: Custom validation for each agent type
- Sanitization: Functions to clean and sanitize input

# Usage

For basic input validation:

```python
from security.validation import validate_input

# Validate input data
validate_input(input_data, agent_name="document_analysis")
```

For specific field validation:

```python
from security.validation import validate_string, validate_email, validate_numeric

# Validate specific fields
email = validate_email(user_input["email"], "email")
amount = validate_numeric(user_input["loan_amount"], "loan_amount", min_value=1000, max_value=10000000)
```

# Configuration

Validation constraints are configured in `config/security_config.json` under the `input_validation` key:

```json
{
  "input_validation": {
    "max_string_length": 1000,
    "max_array_length": 100,
    "allowed_document_extensions": [".pdf", ".jpg", ".png", ".docx", ".xlsx"]
  }
}
```

# PII Detection and Protection

# Purpose

PII detection and protection identify and secure personally identifiable information to prevent data breaches and maintain compliance with privacy regulations.

# Components

- PIIDetector class: Core functionality for detecting and redacting PII
- PII detection patterns: Regular expressions for identifying different PII types
- **Redaction functions: Tools to mask or remove PII from data
- Utility functions: High-level functions for working with PII

# PII Types Detected

The system detects the following types of PII:

- Social Security Numbers (SSN)
- Credit Card Numbers
- Phone Numbers
- Email Addresses
- Driver's License Numbers
- Physical Addresses
- Dates of Birth
- Account Numbers

### Usage

For basic PII detection and masking:

```python
from security.pii_detector import detect_and_mask_pii, is_sensitive_request

# Check if data contains sensitive information
if is_sensitive_request(data):
    # Mask PII in the data
    masked_data = detect_and_mask_pii(data)
```

For more detailed PII management:

```python
from security.pii_detector import PIIDetector

# Create detector instance
detector = PIIDetector()

# Find PII in text
pii_findings = detector.detect_pii(text)

# Redact PII from text
redacted_text = detector.redact_pii(text)

# Handle PII in dictionaries
redacted_dict = detector.redact_pii_in_dict(data_dict)

# Safe logging with PII redacted
detector.safe_log_data(sensitive_data, logging.INFO)
```

# Configuration

PII detection is configured in `config/security_config.json` under the `pii_detection` key:

```json
{
  "pii_detection": {
    "pii_types": ["SSN", "CREDIT_CARD", "PHONE_NUMBER", "EMAIL", "DRIVER_LICENSE", "ADDRESS", "DOB", "ACCOUNT_NUMBER"],
    "redaction_enabled": true
  }
}
```

# Jailbreak Prevention

# Purpose

Jailbreak prevention protects against attempts to manipulate the AI to bypass security controls or generate harmful content, especially in Copilot Studio interactions.

# Components

- PromptSecurityFilter class: Main filter for detecting and preventing jailbreaks
- Detection patterns: Regular expressions and keywords for identifying attempts
- Risk scoring: Calculation of jailbreak likelihood
- Sanitization: Removal of potentially malicious instructions

# Usage

For checking individual prompts:

```python
from security.jailbreak_prevention import check_jailbreak_attempt

# Check if a prompt is a jailbreak attempt
is_jailbreak, score, pattern = check_jailbreak_attempt(user_prompt)
if is_jailbreak:
    # Handle jailbreak attempt
    print(f"Jailbreak detected with score {score}, pattern: {pattern}")
```

For comprehensive filtering:

```python
from security.jailbreak_prevention import PromptSecurityFilter

# Create filter
security_filter = PromptSecurityFilter()

# Process a prompt
result = security_filter.process_prompt(user_prompt)
if not result["is_allowed"]:
    # Handle blocked prompt
    print(result["security_advice"])
else:
    # Use sanitized prompt if needed
    sanitized_prompt = result["prompt"]
```

# Configuration

Jailbreak prevention is configured in `config/security_config.json` under the `jailbreak_prevention` key:

```json
{
  "jailbreak_prevention": {
    "enabled": true,
    "threshold": 0.65,
    "security_level": "medium",
    "blocked_patterns": [
      "ignore instructions",
      "bypass restrictions",
      "admin mode",
      "developer mode"
    ]
  }
}
```

# Security Middleware

# Purpose

Security middleware provides application-level protection across all endpoints by applying security controls consistently to all requests and responses.

### Components

- ValidationMiddleware: Validates all incoming requests
- PIIProtectionMiddleware: Detects and protects PII in requests/responses
- JailbreakPreventionMiddleware: Prevents jailbreak attempts in AI prompts
- RateLimitingMiddleware: Prevents abuse through rate limiting
- AuthenticationMiddleware: Ensures proper authentication
- SecurityHeadersMiddleware: Adds security headers to responses

# Setup

To configure all security middleware:

```python
from fastapi import FastAPI
from security.middleware import configure_security_middleware

app = FastAPI()

# Configure all security middleware
configure_security_middleware(app)
```

To configure individual middleware:

```python
from fastapi import FastAPI
from security.middleware import ValidationMiddleware, PIIProtectionMiddleware

app = FastAPI()

# Add specific middleware
app.add_middleware(ValidationMiddleware)
app.add_middleware(PIIProtectionMiddleware)
```

# Configuration

Middleware settings are configured in environment variables and `config/security_config.json`:

```
# .env file example
API_KEY_NAME=X-API-Key
API_KEY=your-api-key-here
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
RATE_LIMIT_REQUESTS_PER_MINUTE=100
MAX_REQUEST_BODY_SIZE=10485760
ALLOWED_ORIGINS=https://yoursite.com,http://localhost:3000
```

# Configuration

#Security Configuration File

The primary security configuration is located in `config/security_config.json`. This file controls:

- Input validation parameters
- PII detection settings
- Jailbreak prevention thresholds
- Other security features

Example configuration:

```json
{
  "input_validation": {
    "max_string_length": 1000,
    "max_array_length": 100,
    "allowed_document_extensions": [".pdf", ".jpg", ".png", ".docx", ".xlsx"]
  },
  "pii_detection": {
    "pii_types": ["SSN", "CREDIT_CARD", "PHONE_NUMBER", "EMAIL", "DRIVER_LICENSE", "ADDRESS", "DOB", "ACCOUNT_NUMBER"],
    "redaction_enabled": true
  },
  "jailbreak_prevention": {
    "enabled": true,
    "threshold": 0.65,
    "security_level": "medium",
    "blocked_patterns": [
      "ignore instructions",
      "bypass restrictions"
    ]
  },
  "middleware": {
    "enable_rate_limiting": true,
    "enable_pii_protection": true,
    "enable_validation": true,
    "enable_jailbreak_prevention": true
  }
}
```

# Environment Variables

Security-related environment variables used by the application include:

| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_JAILBREAK_DETECTION` | Enable/disable jailbreak detection | `true` |
| `JAILBREAK_THRESHOLD` | Threshold for jailbreak detection | `0.65` |
| `API_KEY_NAME` | Name of the API key header | `X-API-Key` |
| `API_KEY` | API key value for service authentication | - |
| `SECRET_KEY` | Secret key for JWT tokens | - |
| `ALGORITHM` | Algorithm for JWT tokens | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiration | `30` |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | Rate limit threshold | `100` |
| `MAX_REQUEST_BODY_SIZE` | Maximum request body size | `10485760` (10MB) |
| `ALLOWED_ORIGINS` | Allowed origins for CORS | `*` |

# Security Incident Response

# Reporting Security Issues

If you discover a security vulnerability, please follow these steps:

1. Do NOT disclose the vulnerability publicly
2. Email security@yourcompany.com with details
3. Include steps to reproduce the issue
4. Wait for confirmation before disclosing

# Incident Response Process

When a security incident is detected:

1. Containment: Limit the impact by isolating affected systems
2. Assessment: Determine the scope and impact of the incident
3. Remediation: Fix the security issue
4. Recovery: Restore normal operations
5. Post-Incident Review: Document lessons learned

# Security Logs

Security-related events are logged to:

- Application logs with prefix `security.`
- Security audit logs for critical events
- Standard output/error for development environments

#Secure Coding Guidelines

# General Principles

1. Input Validation: Validate all input data using the provided validation functions
2. Output Encoding: Encode all output to prevent XSS and injection attacks
3. Parameterized Queries: Use parameterized queries for database access
4. Principle of Least Privilege: Limit access to the minimum required
5. Defense in Depth: Apply multiple layers of security controls

# PII Handling

1. Minimize Collection: Only collect PII that is absolutely necessary
2. Secure Storage: Use encryption for storing PII
3. Redaction in Logs: Never log unredacted PII
4. Need-to-Know Basis: Limit access to PII to those who need it
5. Proper Disposal: Securely delete PII when no longer needed

#AI Prompt Security

1. Sanitize Inputs: Filter out jailbreak attempts and harmful content
2. Verify Outputs: Check AI-generated content for PII and security issues
3. Contextual Security: Provide secure default behaviors for AI prompts
4. Limited Information: Do not disclose system details in prompts or responses
5. Regular Updates: Keep jailbreak detection patterns up to date

---

# Appendix A: Security Checklist for New Features

- [ ] Validate all input data
- [ ] Check for PII in responses
- [ ] Configure appropriate middleware
- [ ] Add proper authentication and authorization
- [ ] Implement rate limiting for new endpoints
- [ ] Add security tests for the feature
- [ ] Document security considerations

# Appendix B: Regulatory Compliance

This security implementation helps maintain compliance with:

- GLBA (Gramm-Leach-Bliley Act): Financial privacy protections
- FCRA (Fair Credit Reporting Act): Credit information privacy
- State Privacy Laws: (e.g., CCPA, CPRA) for personal data protection
- Industry Best Practices: OWASP Top 10, NIST guidelines