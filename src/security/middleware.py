"""
Security Middleware Module
Integrates security features into the FastAPI application middleware.
"""

import os
import json
import time
import logging
from typing import Dict, Any, Callable, List, Union, Optional
from fastapi import Request, Response, FastAPI, HTTPException, status, Depends
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.security import APIKeyHeader
from starlette.responses import JSONResponse
from starlette.types import ASGIApp
import jwt
from datetime import datetime, timedelta

# Import custom security modules
from security.validation import validate_input, ValidationError
from security.pii_detector import detect_and_mask_pii, is_sensitive_request, redact_pii_for_logging
from security.jailbreak_prevention import PromptSecurityFilter, create_safe_prompt_context

# Set up logging
logger = logging.getLogger("security.middleware")

# Load environment variables
API_KEY_NAME = os.getenv("API_KEY_NAME", "X-API-Key")
API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key")  # Should be properly secured in production
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
RATE_LIMIT_REQUESTS_PER_MINUTE = int(os.environ.get("RATE_LIMIT_REQUESTS_PER_MINUTE", "100"))
MAX_REQUEST_BODY_SIZE = int(os.environ.get("MAX_REQUEST_BODY_SIZE", "10485760"))  # 10MB
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")

# API Key security scheme
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Initialize security filter
security_filter = PromptSecurityFilter()

# ========================================================================
# Validation Middleware
# ========================================================================

class ValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for validating incoming requests."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Validate request before processing.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            Response from the next handler or validation error
        """
        try:
            # Check request body size
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > MAX_REQUEST_BODY_SIZE:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": "Request body too large"}
                )
                
            # Only validate POST and PUT requests with JSON content
            if request.method in ["POST", "PUT"] and \
               request.headers.get("content-type", "").startswith("application/json"):
                
                # Parse request body
                body = await request.json()
                
                # Get endpoint path to determine validation schema
                path = request.url.path
                
                # Apply route-specific validation
                await self._validate_route_specific_input(path, body)
                
            # Proceed with the request
            response = await call_next(request)
            return response
            
        except ValidationError as e:
            # Return validation error response
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "detail": str(e),
                    "field": e.field,
                    "details": e.details
                }
            )
        except ValueError as e:
            # Handle JSON parsing errors
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": f"Invalid JSON format: {str(e)}"}
            )
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Error in validation middleware: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error during request validation"}
            )
    
    async def _validate_route_specific_input(self, path: str, body: Dict[str, Any]) -> bool:
        """
        Apply route-specific input validation.
        
        Args:
            path: The request path
            body: The request body
            
        Returns:
            True if valid, raises ValidationError otherwise
        """
        # Map endpoints to validation functions
        validation_map = {
            "/api/applications/submit": self._validate_application_submission,
            "/api/applications/{application_id}/status": self._validate_status_check,
            "/api/applications/{application_id}/documents/upload": self._validate_document_upload,
            "/api/loan/recommendations": self._validate_loan_recommendation,
            "/api/applications/{application_id}/issues/resolve": self._validate_issue_resolution,
            "/api/loan/eligibility": self._validate_loan_eligibility,
            "/copilot/process-input": self._validate_copilot_input
        }
        
        # Find matching validation function
        for route_pattern, validator in validation_map.items():
            # Simple pattern matching (could be improved with regex)
            if self._match_route_pattern(path, route_pattern):
                return await validator(body)
        
        # If no specific validation defined, pass through
        return True
    
    def _match_route_pattern(self, path: str, pattern: str) -> bool:
        """
        Match a path against a route pattern with parameters.
        
        Args:
            path: The actual request path
            pattern: The route pattern with parameters
            
        Returns:
            True if the path matches the pattern
        """
        # Convert pattern to parts and normalize
        pattern_parts = pattern.strip('/').split('/')
        path_parts = path.strip('/').split('/')
        
        # Different number of parts means no match
        if len(pattern_parts) != len(path_parts):
            return False
        
        # Check each part
        for pattern_part, path_part in zip(pattern_parts, path_parts):
            # Parameter part (e.g., {application_id}) matches anything
            if pattern_part.startswith('{') and pattern_part.endswith('}'):
                continue
            # Literal part must match exactly
            elif pattern_part != path_part:
                return False
        
        return True
    
    async def _validate_application_submission(self, body: Dict[str, Any]) -> bool:
        """Validate mortgage application submission."""
        required_fields = ["applicantName", "applicantEmail", "applicantPhone", 
                          "propertyType", "propertyValue", "loanAmount"]
        
        for field in required_fields:
            if field not in body:
                raise ValidationError(f"Missing required field: {field}", field)
        
        # Validate email format
        from security.validation import validate_email
        validate_email(body["applicantEmail"], "applicantEmail")
        
        # Validate phone format
        from security.validation import validate_phone
        validate_phone(body["applicantPhone"], "applicantPhone")
        
        return True
    
    async def _validate_status_check(self, body: Dict[str, Any]) -> bool:
        """Validate status check request."""
        if "applicationId" not in body:
            raise ValidationError("Missing required field: applicationId", "applicationId")
        
        return True
    
    async def _validate_document_upload(self, body: Dict[str, Any]) -> bool:
        """Validate document upload request."""
        required_fields = ["documentType", "documentContent"]
        
        for field in required_fields:
            if field not in body:
                raise ValidationError(f"Missing required field: {field}", field)
        
        return True
    
    async def _validate_loan_recommendation(self, body: Dict[str, Any]) -> bool:
        """Validate loan recommendation request."""
        required_fields = ["annualIncome", "creditScoreRange", "downPaymentPercentage", "propertyType"]
        
        for field in required_fields:
            if field not in body:
                raise ValidationError(f"Missing required field: {field}", field)
        
        return True
    
    async def _validate_issue_resolution(self, body: Dict[str, Any]) -> bool:
        """Validate issue resolution request."""
        required_fields = ["issueType", "issueDescription"]
        
        for field in required_fields:
            if field not in body:
                raise ValidationError(f"Missing required field: {field}", field)
        
        return True
    
    async def _validate_loan_eligibility(self, body: Dict[str, Any]) -> bool:
        """Validate loan eligibility request."""
        required_fields = ["annualIncome", "monthlyDebts", "creditScoreRange", "employmentStatus"]
        
        for field in required_fields:
            if field not in body:
                raise ValidationError(f"Missing required field: {field}", field)
        
        return True
    
    async def _validate_copilot_input(self, body: Dict[str, Any]) -> bool:
        """Validate Copilot input request."""
        if "userInput" not in body:
            raise ValidationError("Missing required field: userInput", "userInput")
        
        return True

# ========================================================================
# PII Protection Middleware
# ========================================================================

class PIIProtectionMiddleware(BaseHTTPMiddleware):
    """Middleware for protecting PII in requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request/response to protect PII.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            Response with PII protected
        """
        # Copy request for potential logging
        try:
            # Only process POST and PUT requests with JSON content
            if request.method in ["POST", "PUT"] and \
               request.headers.get("content-type", "").startswith("application/json"):
                
                # Create a copy of the request to use for the next call
                request_body = await request.json()
                
                # Check if this request contains sensitive data
                if is_sensitive_request(request_body):
                    # Log redacted version for security monitoring
                    redacted_body = redact_pii_for_logging(request_body)
                    logger.info(f"Processing sensitive request: {json.dumps(redacted_body)}")
                    
                    # Create a new request object with the same data
                    # (we don't modify the original request)
                
                # Process the request normally
                response = await call_next(request)
                
                # Check if response contains sensitive data
                if response.headers.get("content-type", "").startswith("application/json"):
                    # Get response body
                    response_body = await self._get_response_body(response)
                    
                    # Mask PII in response body
                    if response_body:
                        masked_body = detect_and_mask_pii(response_body)
                        
                        # Create new response with masked body
                        return self._create_new_response(response, masked_body)
                
                return response
            else:
                # Process non-JSON requests normally
                return await call_next(request)
                
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Error in PII protection middleware: {str(e)}", exc_info=True)
            
            # Continue with the request to avoid breaking functionality
            return await call_next(request)
    
    async def _get_response_body(self, response: Response) -> Optional[Dict[str, Any]]:
        """
        Extract and parse JSON body from response.
        
        Args:
            response: The response to extract from
            
        Returns:
            Parsed JSON body or None if not JSON
        """
        if not response.body:
            return None
            
        try:
            # Decode the response body
            body_str = response.body.decode("utf-8")
            
            # Parse as JSON
            return json.loads(body_str)
        except:
            # Not JSON or other error
            return None
    
    def _create_new_response(self, original_response: Response, new_body: Dict[str, Any]) -> Response:
        """
        Create a new response with the same headers but a new body.
        
        Args:
            original_response: The original response
            new_body: The new body to use
            
        Returns:
            New response with the replaced body
        """
        # Create JSON string from the new body
        new_body_str = json.dumps(new_body)
        
        # Create new response with same status and headers
        new_response = Response(
            content=new_body_str,
            status_code=original_response.status_code,
            headers=dict(original_response.headers),
            media_type="application/json"
        )
        
        return new_response

# ========================================================================
# Jailbreak Prevention Middleware
# ========================================================================

class JailbreakPreventionMiddleware(BaseHTTPMiddleware):
    """Middleware for preventing jailbreak attempts in AI prompts."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Check requests for jailbreak attempts.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            Response with jailbreak protection
        """
        try:
            # Only check specific endpoints that interact with AI
            path = request.url.path
            if (path.startswith("/copilot/") or path.startswith("/api/conversation/")) and \
               request.method == "POST" and \
               request.headers.get("content-type", "").startswith("application/json"):
                
                # Parse request body
                body = await request.json()
                
                # Extract user input
                user_input = None
                if "userInput" in body:
                    user_input = body["userInput"]
                elif "prompt" in body:
                    user_input = body["prompt"]
                elif "text" in body:
                    user_input = body["text"]
                elif "message" in body:
                    user_input = body["message"]
                
                # If we found user input, check for jailbreak attempts
                if user_input:
                    # Check for jailbreak attempt using the security filter
                    user_id = request.headers.get("X-User-ID")
                    security_result = security_filter.process_prompt(user_input, user_id)
                    
                    if not security_result["is_allowed"]:
                        # Return a security violation response
                        return JSONResponse(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            content={
                                "detail": "Security policy violation",
                                "message": security_result["security_advice"],
                                "risk_score": security_result["risk_score"]
                            }
                        )
                    
                    if security_result.get("was_sanitized", False):
                        # Create a new request body with the sanitized prompt
                        new_body = body.copy()
                        
                        if "userInput" in new_body:
                            new_body["userInput"] = security_result["prompt"]
                        elif "prompt" in new_body:
                            new_body["prompt"] = security_result["prompt"]
                        elif "text" in new_body:
                            new_body["text"] = security_result["prompt"]
                        elif "message" in new_body:
                            new_body["message"] = security_result["prompt"]
                        
                        # Add a flag to indicate the sanitization
                        new_body["_security_sanitized"] = True
                        
                        # Log the sanitization
                        logger.warning(f"Sanitized potential jailbreak attempt with score {security_result['risk_score']}")
                        
                        # Continue with the sanitized request
                        request._body = json.dumps(new_body).encode("utf-8")
            
            # Proceed with the request
            return await call_next(request)
            
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Error in jailbreak prevention middleware: {str(e)}", exc_info=True)
            
            # Continue with the request to avoid breaking functionality
            return await call_next(request)

# ========================================================================
# Rate Limiting Middleware
# ========================================================================

class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests."""
    
    def __init__(self, app: ASGIApp):
        """Initialize the middleware."""
        super().__init__(app)
        self.rate_limits = {}  # IP/client_id -> [timestamp1, timestamp2, ...]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Apply rate limiting to requests.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            Response or rate limit exceeded error
        """
        # Get client identifier (IP or API key or user ID)
        client_id = self._get_client_id(request)
        
        # Check if rate limit exceeded
        if self._is_rate_limited(client_id):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": "60 seconds"
                },
                headers={"Retry-After": "60"}
            )
        
        # Record this request
        self._record_request(client_id)
        
        # Proceed with the request
        return await call_next(request)
    
    def _get_client_id(self, request: Request) -> str:
        """
        Get client identifier from request.
        
        Args:
            request: The incoming request
            
        Returns:
            String identifier for the client
        """
        # Try to get from API key or auth token first
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                # Extract user ID from JWT
                token = auth_header.replace("Bearer ", "")
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                if "sub" in payload:
                    return f"user:{payload['sub']}"
            except:
                pass
        
        # Fall back to client IP
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"
    
    def _is_rate_limited(self, client_id: str) -> bool:
        """
        Check if client has exceeded rate limit.
        
        Args:
            client_id: Client identifier
            
        Returns:
            True if rate limited, False otherwise
        """
        # Get client's recent requests
        now = time.time()
        minute_ago = now - 60
        
        if client_id not in self.rate_limits:
            return False
        
        # Filter to requests in the last minute
        recent_requests = [t for t in self.rate_limits[client_id] if t > minute_ago]
        self.rate_limits[client_id] = recent_requests
        
        # Check if too many requests
        return len(recent_requests) >= RATE_LIMIT_REQUESTS_PER_MINUTE
    
    def _record_request(self, client_id: str):
        """
        Record a request for rate limiting.
        
        Args:
            client_id: Client identifier
        """
        now = time.time()
        
        if client_id not in self.rate_limits:
            self.rate_limits[client_id] = []
            
        self.rate_limits[client_id].append(now)

# ========================================================================
# Authentication Middleware
# ========================================================================

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for authentication."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Authenticate requests.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            Response or authentication error
        """
        # Skip authentication for public endpoints
        path = request.url.path
        if self._is_public_endpoint(path):
            return await call_next(request)
        
        # Check API key first (for service-to-service)
        api_key = request.headers.get(API_KEY_NAME)
        if api_key and api_key == API_KEY:
            # Valid API key
            return await call_next(request)
        
        # Check JWT token (for user authentication)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            
            try:
                # Validate JWT token
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                
                # Check if token is expired
                if "exp" in payload and payload["exp"] < time.time():
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "Token has expired"}
                    )
                
                # Valid token, proceed
                return await call_next(request)
                
            except jwt.JWTError:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid authentication token"}
                )
        
        # No valid authentication provided
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Authentication required"}
        )
    
    def _is_public_endpoint(self, path: str) -> bool:
        """
        Check if an endpoint is public (no auth required).
        
        Args:
            path: The request path
            
        Returns:
            True if public, False otherwise
        """
        public_patterns = [
            "/health",
            "/docs",
            "/openapi.json",
            "/auth/login",
            "/auth/register"
        ]
        
        for pattern in public_patterns:
            if path.startswith(pattern):
                return True
        
        return False

# ========================================================================
# CORS Middleware Function
# ========================================================================

def configure_cors(app: FastAPI):
    """
    Configure CORS for the application.
    
    Args:
        app: FastAPI application
    """
    from fastapi.middleware.cors import CORSMiddleware
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ========================================================================
# Security Header Middleware
# ========================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers to responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add security headers to responses.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            Response with security headers
        """
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response

# ========================================================================
# Application Setup Functions
# ========================================================================

def configure_security_middleware(app: FastAPI):
    """
    Configure all security middleware for the application.
    
    Args:
        app: FastAPI application
    """
    # Configure CORS
    configure_cors(app)
    
    # Add security middleware in the correct order (inside-out processing)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(AuthenticationMiddleware)
    app.add_middleware(RateLimitingMiddleware)
    app.add_middleware(JailbreakPreventionMiddleware)
    app.add_middleware(PIIProtectionMiddleware)
    app.add_middleware(ValidationMiddleware)
    
    # Log middleware configuration
    logger.info("Security middleware configured")

# ========================================================================
# Authentication Utilities
# ========================================================================

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time
        
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def get_current_user(token: str = Depends(api_key_header)) -> Dict[str, Any]:
    """
    Get current user from token.
    
    Args:
        token: JWT token
        
    Returns:
        User data from token
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# ========================================================================
# Error Handling Functions
# ========================================================================

def configure_exception_handlers(app: FastAPI):
    """
    Configure global exception handlers.
    
    Args:
        app: FastAPI application
    """
    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": str(exc),
                "field": exc.field,
                "details": exc.details
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers,
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        # Log the error
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        
        # Return a generic error response in production
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"}
        )