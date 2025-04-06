"""
API Middleware for Mortgage Lending Assistant

This module provides middleware components for the FastAPI application,
including validation, PII protection, and jailbreak prevention.
"""

import json
import logging
from typing import Callable, Dict, Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# Import security components
from src.security.validation import validate_input, ValidationError
from src.security.pii_detector import detect_and_mask_pii, is_sensitive_request
from src.security.jailbreak_prevention import PromptSecurityFilter

# Set up logging
logger = logging.getLogger(__name__)

# Initialize security filter
security_filter = PromptSecurityFilter()

# Max request body size (10MB)
MAX_REQUEST_BODY_SIZE = 10 * 1024 * 1024


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
                    status_code=413,
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
                agent_name = None
                if "document" in path:
                    agent_name = "document_analysis"
                elif "underwriting" in path:
                    agent_name = "underwriting"
                elif "compliance" in path:
                    agent_name = "compliance"
                elif "customer" in path:
                    agent_name = "customer_service"
                else:
                    agent_name = "orchestrator"
                
                # Validate input
                validate_input(body, agent_name)
                
            # Proceed with the request
            response = await call_next(request)
            return response
            
        except ValidationError as e:
            # Return validation error response
            return JSONResponse(
                status_code=422,
                content={
                    "detail": str(e),
                    "field": e.field if hasattr(e, "field") else None,
                    "details": e.details if hasattr(e, "details") else {}
                }
            )
        except ValueError as e:
            # Handle JSON parsing errors
            return JSONResponse(
                status_code=400,
                content={"detail": f"Invalid JSON format: {str(e)}"}
            )
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Error in validation middleware: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error during request validation"}
            )


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
        try:
            # Process the request normally first
            response = await call_next(request)
            
            # Check if response contains sensitive data (JSON)
            if response.headers.get("content-type", "").startswith("application/json"):
                response_body = await self._get_response_body(response)
                
                if response_body:
                    # Mask PII in response body
                    masked_body = detect_and_mask_pii(response_body)
                    
                    # Create new response with masked body
                    return self._create_new_response(response, masked_body)
            
            return response
                
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Error in PII protection middleware: {str(e)}", exc_info=True)
            
            # Continue with the request to avoid breaking functionality
            return await call_next(request)
    
    async def _get_response_body(self, response: Response) -> Dict[str, Any]:
        """
        Extract and parse JSON body from response.
        
        Args:
            response: The response to extract from
            
        Returns:
            Parsed JSON body or None if not JSON
        """
        try:
            # Get raw response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            # Store the body for creating a new response later
            response.body = body
            
            # Decode and parse JSON
            text = body.decode("utf-8")
            return json.loads(text)
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
        
        # Create new response
        response = Response(
            content=new_body_str.encode("utf-8"),
            status_code=original_response.status_code,
            headers=dict(original_response.headers),
            media_type="application/json"
        )
        
        return response


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
                elif "inquiry_text" in body:
                    user_input = body["inquiry_text"]
                
                # If we found user input, check for jailbreak attempts
                if user_input:
                    # Check for jailbreak attempt using the security filter
                    user_id = request.headers.get("X-User-ID")
                    security_result = security_filter.process_prompt(user_input, user_id)
                    
                    if not security_result["is_allowed"]:
                        # Return a security violation response
                        return JSONResponse(
                            status_code=400,
                            content={
                                "detail": "Security policy violation",
                                "message": security_result.get("security_advice", 
                                          "Your request was flagged by our security system"),
                                "risk_score": security_result.get("risk_score", 0.8)
                            }
                        )
            
            # Proceed with the request
            return await call_next(request)
            
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Error in jailbreak prevention middleware: {str(e)}", exc_info=True)
            
            # Continue with the request to avoid breaking functionality
            return await call_next(request)


def configure_middleware(app):
    """
    Configure all middleware for the application.
    
    Args:
        app: FastAPI application
    """
    # Add middleware in reverse order (last added = first executed)
    app.add_middleware(ValidationMiddleware)
    app.add_middleware(PIIProtectionMiddleware)
    app.add_middleware(JailbreakPreventionMiddleware)
    
    logger.info("API middleware configured")