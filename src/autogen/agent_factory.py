"""
Agent Factory Module
Creates and configures AutoGen agents for the mortgage lending system.
"""

import os
from typing import Any, Dict, List, Optional

import autogen
from autogen import Agent, AssistantAgent, UserProxyAgent
from ..utils.config import get_config
from ..utils.logging_utils import get_logger

logger = get_logger("autogen.agent_factory")


def create_assistant_agent(
    name: str,
    system_message: str,
    llm_config: Optional[Dict[str, Any]] = None,
) -> AssistantAgent:
    """
    Create an AutoGen assistant agent with the specified configuration.
    
    Args:
        name: Name of the agent
        system_message: System message defining the agent's behavior
        llm_config: Configuration for the LLM (defaults to configuration from config file)
        
    Returns:
        Configured AssistantAgent
    """
    # If no LLM config provided, use default from config
    if llm_config is None:
        config = get_config()
        llm_config = {
            "config_list": [
                {
                    "model": config.get("openai", {}).get("model", "gpt-4-turbo"),
                    "api_key": os.environ.get("AZURE_OPENAI_API_KEY"),
                    "api_base": os.environ.get("AZURE_OPENAI_ENDPOINT"),
                    "api_type": "azure",
                    "api_version": config.get("openai", {}).get("api_version", "2023-07-01-preview"),
                }
            ],
            "temperature": 0.1,
            "cache_seed": 42  # For reproducibility
        }
    
    logger.info(f"Creating assistant agent: {name}")
    
    return AssistantAgent(
        name=name,
        system_message=system_message,
        llm_config=llm_config
    )


def create_user_proxy_agent(
    name: str,
    human_input_mode: str = "NEVER",
    max_consecutive_auto_reply: int = 10,
    code_execution_config: Optional[Dict[str, Any]] = None,
) -> UserProxyAgent:
    """
    Create an AutoGen user proxy agent with the specified configuration.
    
    Args:
        name: Name of the agent
        human_input_mode: When to request human input
        max_consecutive_auto_reply: Maximum number of consecutive auto replies
        code_execution_config: Configuration for code execution
        
    Returns:
        Configured UserProxyAgent
    """
    # Default code execution config if not provided
    if code_execution_config is None:
        code_execution_config = {
            "work_dir": "workspace",
            "use_docker": False,
            "last_n_messages": 3,
        }
    
    logger.info(f"Creating user proxy agent: {name}")
    
    return UserProxyAgent(
        name=name,
        human_input_mode=human_input_mode,
        max_consecutive_auto_reply=max_consecutive_auto_reply,
        code_execution_config=code_execution_config
    )


def create_document_analysis_assistant() -> AssistantAgent:
    """
    Create a specialized assistant agent for document analysis tasks.
    
    Returns:
        Document analysis AssistantAgent
    """
    system_message = """
    You are an expert document analysis assistant specialized in mortgage application documents.
    Your role is to:
    
    1. Extract relevant information from various document types including income verification, 
       credit reports, property appraisals, bank statements, and identification documents.
    2. Identify inconsistencies across documents.
    3. Determine if all required documentation is present.
    4. Assess the quality and reliability of the provided documents.
    
    You should be precise and thorough in your analysis, focusing on extracting factual information
    without making subjective judgments about the application's merits.
    
    When processing documents, always:
    - Report confidence levels for extracted information
    - Flag potential issues or discrepancies
    - Clearly state what information is missing if any
    - Structure your response in a clear, organized manner
    """
    
    return create_assistant_agent(
        name="document_analyzer",
        system_message=system_message,
        llm_config={
            "config_list": get_config().get("openai", {}).get("config_list", []),
            "temperature": 0.1,
            "seed": 42,
            "functions": [
                {
                    "name": "analyze_document",
                    "description": "Analyze and extract information from a document",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "document_type": {
                                "type": "string",
                                "description": "Type of document being analyzed"
                            },
                            "document_content": {
                                "type": "string",
                                "description": "Content of the document to analyze"
                            }
                        },
                        "required": ["document_type", "document_content"]
                    }
                },
                {
                    "name": "check_document_consistency",
                    "description": "Check consistency between multiple documents",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "documents": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "document_type": {"type": "string"},
                                        "extracted_data": {"type": "object"}
                                    }
                                },
                                "description": "List of documents with their extracted data"
                            }
                        },
                        "required": ["documents"]
                    }
                }
            ]
        }
    )


def create_underwriting_assistant() -> AssistantAgent:
    """
    Create a specialized assistant agent for underwriting tasks.
    
    Returns:
        Underwriting AssistantAgent
    """
    system_message = """
    You are an expert mortgage underwriting assistant specialized in evaluating loan applications.
    Your role is to:
    
    1. Analyze financial ratios like DTI (Debt-to-Income), LTV (Loan-to-Value), and PITI.
    2. Evaluate credit reports and payment history.
    3. Assess property appraisals and values.
    4. Determine whether applications meet lending criteria.
    5. Provide clear explanations for underwriting decisions.
    
    You should follow standard underwriting practices while being able to identify compensating
    factors that might justify exceptions to standard rules. Your analysis should be thorough,
    fair, and consistent.
    
    When evaluating applications, always:
    - Calculate and verify key financial ratios
    - Consider both standard criteria and compensating factors
    - Assess risk levels objectively
    - Provide clear reasoning for your decisions
    - Suggest conditions for approval when appropriate
    """
    
    return create_assistant_agent(
        name="underwriter",
        system_message=system_message,
        llm_config={
            "config_list": get_config().get("openai", {}).get("config_list", []),
            "temperature": 0.1,
            "seed": 42,
            "functions": [
                {
                    "name": "evaluate_application",
                    "description": "Evaluate a mortgage application against underwriting criteria",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "application_data": {
                                "type": "object",
                                "description": "Core application data"
                            },
                            "document_analysis": {
                                "type": "object",
                                "description": "Results from document analysis"
                            },
                            "financial_ratios": {
                                "type": "object",
                                "description": "Pre-calculated financial ratios"
                            }
                        },
                        "required": ["application_data", "document_analysis"]
                    }
                }
            ]
        }
    )


def create_compliance_assistant() -> AssistantAgent:
    """
    Create a specialized assistant agent for compliance tasks.
    
    Returns:
        Compliance AssistantAgent
    """
    system_message = """
    You are an expert mortgage compliance assistant specialized in regulatory requirements.
    Your role is to:
    
    1. Verify adherence to laws like TILA, RESPA, ECOA, and HMDA.
    2. Check fair lending compliance.
    3. Identify high-risk applications that require additional scrutiny.
    4. Ensure proper disclosures have been provided.
    5. Verify that loan terms and conditions meet regulatory standards.
    
    You should be precise and thorough in your compliance checks, focusing on regulatory
    requirements without making subjective judgments about the application's merits.
    
    When checking compliance, always:
    - Cite specific regulations when identifying issues
    - Flag potential fair lending concerns
    - Verify documentation completeness
    - Provide clear explanations for compliance findings
    - Suggest remediation steps for any compliance issues
    """
    
    return create_assistant_agent(
        name="compliance_checker",
        system_message=system_message,
        llm_config={
            "config_list": get_config().get("openai", {}).get("config_list", []),
            "temperature": 0.1,
            "seed": 42,
            "functions": [
                {
                    "name": "check_compliance",
                    "description": "Check regulatory compliance of a mortgage application",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "application_data": {
                                "type": "object",
                                "description": "Core application data"
                            },
                            "underwriting_results": {
                                "type": "object",
                                "description": "Results from underwriting evaluation"
                            }
                        },
                        "required": ["application_data", "underwriting_results"]
                    }
                }
            ]
        }
    )


def create_customer_service_assistant() -> AssistantAgent:
    """
    Create a specialized assistant agent for customer service tasks.
    
    Returns:
        Customer service AssistantAgent
    """
    system_message = """
    You are an expert mortgage customer service assistant specialized in explaining mortgage processes.
    Your role is to:
    
    1. Explain the mortgage application process in clear, non-technical language.
    2. Answer questions about application status and requirements.
    3. Explain reasons for application decisions in a empathetic and helpful way.
    4. Provide guidance on next steps and document requirements.
    5. Address customer concerns professionally and supportively.
    
    You should be empathetic, clear, and customer-focused, avoiding technical jargon
    unless necessary and explaining it when used.
    
    When interacting with customers, always:
    - Use plain language rather than technical terms
    - Be empathetic, especially when delivering disappointing news
    - Provide clear, actionable next steps
    - Explain "why" behind requirements or decisions
    - Be supportive and solutions-oriented
    """
    
    return create_assistant_agent(
        name="customer_service",
        system_message=system_message,
        llm_config={
            "config_list": get_config().get("openai", {}).get("config_list", []),
            "temperature": 0.7,  # Slightly higher temperature for more natural-sounding responses
            "seed": 42,
            "functions": [
                {
                    "name": "generate_response",
                    "description": "Generate a customer-friendly response",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "request_type": {
                                "type": "string",
                                "description": "Type of customer request"
                            },
                            "application_context": {
                                "type": "object",
                                "description": "Application context and details"
                            },
                            "customer_query": {
                                "type": "string",
                                "description": "Customer's question or concern"
                            }
                        },
                        "required": ["request_type", "application_context"]
                    }
                }
            ]
        }
    )