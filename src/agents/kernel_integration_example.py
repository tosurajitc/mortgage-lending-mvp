"""
Example demonstrating how to integrate existing agents with Semantic Kernel.

This module provides examples of integrating the existing BaseAgent structure
with Semantic Kernel capabilities through the AgentKernelConnector.
"""

import json
from typing import Dict, Any, Optional

from src.agents.base_agent import BaseAgent
from src.agents.kernel_connector import AgentKernelConnector
from src.utils.logging_utils import get_logger

class KernelEnabledAgent(BaseAgent):
    """
    Example of an agent that uses Semantic Kernel capabilities.
    
    This class demonstrates how to extend the existing BaseAgent
    to incorporate Semantic Kernel functionality.
    """
    
    def __init__(self, agent_name: str, agent_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the kernel-enabled agent.
        
        Args:
            agent_name: Unique identifier for the agent
            agent_config: Configuration dictionary for the agent
        """
        super().__init__(agent_name, agent_config)
        self.kernel_connector = AgentKernelConnector()
        self.log_processing_step(f"Initialized kernel connector")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data using Semantic Kernel capabilities.
        
        Args:
            input_data: The data to be processed
            
        Returns:
            Processing results
        """
        # Example of how to use Semantic Kernel in the process method
        self.log_processing_step("Starting Semantic Kernel analysis")
        
        try:
            # Use connector to run document analysis if document data is provided
            if "document_text" in input_data and "document_type" in input_data:
                document_text = input_data["document_text"]
                document_type = input_data["document_type"]
                
                # Example of executing a document analysis function
                if document_type == "W2_FORM":
                    self.log_processing_step("Analyzing W-2 document")
                    w2_result = self.kernel_connector.execute_plugin_function(
                        "document",
                        "extract_w2_information",
                        {"document_text": document_text}
                    )
                    w2_data = json.loads(w2_result)
                    self.log_processing_step("W-2 analysis complete")
                    
                    # Store the extracted data in context
                    if "application_id" in input_data:
                        self.kernel_connector.store_context(
                            f"document_{input_data['application_id']}",
                            {"w2_data": w2_data},
                            "document_analysis"
                        )
                    
                    return {
                        "status": "success",
                        "document_analysis": w2_data,
                        "message": "Document analysis completed successfully"
                    }
                
                elif document_type == "PAY_STUB":
                    self.log_processing_step("Analyzing pay stub document")
                    paystub_result = self.kernel_connector.execute_plugin_function(
                        "document",
                        "extract_pay_stub_information",
                        {"document_text": document_text}
                    )
                    paystub_data = json.loads(paystub_result)
                    self.log_processing_step("Pay stub analysis complete")
                    
                    # Store the extracted data in context
                    if "application_id" in input_data:
                        self.kernel_connector.store_context(
                            f"document_{input_data['application_id']}",
                            {"paystub_data": paystub_data},
                            "document_analysis"
                        )
                    
                    return {
                        "status": "success",
                        "document_analysis": paystub_data,
                        "message": "Document analysis completed successfully"
                    }
                
                elif document_type == "BANK_STATEMENT":
                    self.log_processing_step("Analyzing bank statement document")
                    bank_result = self.kernel_connector.execute_plugin_function(
                        "document",
                        "extract_bank_statement_information",
                        {"document_text": document_text}
                    )
                    bank_data = json.loads(bank_result)
                    self.log_processing_step("Bank statement analysis complete")
                    
                    # Store the extracted data in context
                    if "application_id" in input_data:
                        self.kernel_connector.store_context(
                            f"document_{input_data['application_id']}",
                            {"bank_statement_data": bank_data},
                            "document_analysis"
                        )
                    
                    return {
                        "status": "success",
                        "document_analysis": bank_data,
                        "message": "Document analysis completed successfully"
                    }
                
                else:
                    return {
                        "status": "error",
                        "message": f"Unsupported document type: {document_type}"
                    }
                
            # Example of executing a compliance check if application data is provided
            elif "application_data" in input_data:
                self.log_processing_step("Performing compliance check")
                application_json = json.dumps(input_data["application_data"])
                
                # Check ability to repay
                atr_result = self.kernel_connector.execute_plugin_function(
                    "compliance",
                    "check_ability_to_repay",
                    {"application_data": application_json}
                )
                atr_data = json.loads(atr_result)
                
                # Check fair lending compliance
                fair_lending_result = self.kernel_connector.execute_plugin_function(
                    "compliance",
                    "check_fair_lending",
                    {"application_data": application_json}
                )
                fair_lending_data = json.loads(fair_lending_result)
                
                # Store the compliance results in memory
                if "application_id" in input_data:
                    self.kernel_connector.store_context(
                        f"compliance_{input_data['application_id']}",
                        {
                            "atr_compliance": atr_data,
                            "fair_lending_compliance": fair_lending_data
                        },
                        "compliance_check"
                    )
                
                self.log_processing_step("Compliance checks complete")
                
                return {
                    "status": "success",
                    "compliance_checks": {
                        "ability_to_repay": atr_data,
                        "fair_lending": fair_lending_data
                    },
                    "message": "Compliance checks completed successfully"
                }
            
            # Example of performing underwriting evaluation
            elif "underwriting_data" in input_data:
                self.log_processing_step("Performing underwriting evaluation")
                underwriting_json = json.dumps(input_data["underwriting_data"])
                
                # Evaluate income and employment
                income_result = self.kernel_connector.execute_plugin_function(
                    "underwriting",
                    "evaluate_income_and_employment",
                    {"application_data": underwriting_json}
                )
                income_data = json.loads(income_result)
                
                # Evaluate credit profile
                credit_result = self.kernel_connector.execute_plugin_function(
                    "underwriting",
                    "evaluate_credit_profile",
                    {"application_data": underwriting_json}
                )
                credit_data = json.loads(credit_result)
                
                # Store the underwriting results in memory
                if "application_id" in input_data:
                    self.kernel_connector.store_context(
                        f"underwriting_{input_data['application_id']}",
                        {
                            "income_evaluation": income_data,
                            "credit_evaluation": credit_data
                        },
                        "underwriting_evaluation"
                    )
                
                self.log_processing_step("Underwriting evaluation complete")
                
                return {
                    "status": "success",
                    "underwriting_evaluation": {
                        "income_and_employment": income_data,
                        "credit_profile": credit_data
                    },
                    "message": "Underwriting evaluation completed successfully"
                }
            
            # Example of using semantic functions with prompts
            elif "query" in input_data and "use_semantic_prompt" in input_data:
                self.log_processing_step("Using semantic prompt function")
                prompt_type = input_data.get("prompt_type", "compliance")
                prompt_function = input_data.get("prompt_function", "regulatory_check")
                
                result = self.kernel_connector.execute_semantic_function(
                    prompt_type,
                    prompt_function,
                    input_data["query"]
                )
                
                self.log_processing_step("Semantic prompt execution complete")
                
                return {
                    "status": "success",
                    "prompt_result": result,
                    "message": f"Executed semantic prompt {prompt_type}.{prompt_function} successfully"
                }
            
            # Default handling if no specific task is identified
            else:
                return {
                    "status": "error",
                    "message": "Unrecognized task type in input data"
                }
                
        except Exception as e:
            self.logger.error(f"Error in Semantic Kernel processing: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Semantic Kernel processing failed: {str(e)}"
            }


# Example of using the kernel-enabled agent with the document agent
class DocumentAnalysisAgent(KernelEnabledAgent):
    """
    Specialized agent for document analysis using Semantic Kernel capabilities.
    """
    
    def __init__(self, agent_config: Optional[Dict[str, Any]] = None):
        """Initialize the document analysis agent."""
        super().__init__("document_analysis", agent_config)
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process document analysis requests."""
        if "document_text" not in input_data or "document_type" not in input_data:
            return {"status": "error", "message": "Missing required document data"}
        
        # Let the parent class handle the actual document processing
        return await super().process(input_data)


# Example of using the kernel-enabled agent with the compliance agent
class ComplianceCheckAgent(KernelEnabledAgent):
    """
    Specialized agent for compliance checking using Semantic Kernel capabilities.
    """
    
    def __init__(self, agent_config: Optional[Dict[str, Any]] = None):
        """Initialize the compliance check agent."""
        super().__init__("compliance_check", agent_config)
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process compliance check requests."""
        if "application_data" not in input_data:
            return {"status": "error", "message": "Missing required application data"}
        
        # Let the parent class handle the actual compliance checking
        return await super().process(input_data)


# Example usage of retrieving context across agents
async def retrieve_application_analysis(application_id: str) -> Dict[str, Any]:
    """
    Example function that retrieves and combines analysis from multiple contexts.
    
    Args:
        application_id: The ID of the application to analyze
        
    Returns:
        Combined analysis data
    """
    connector = AgentKernelConnector()
    
    # Retrieve document analysis
    document_context = connector.retrieve_context(f"document_{application_id}", {})
    
    # Retrieve compliance check results
    compliance_context = connector.retrieve_context(f"compliance_{application_id}", {})
    
    # Retrieve underwriting evaluation
    underwriting_context = connector.retrieve_context(f"underwriting_{application_id}", {})
    
    # Combine all contexts into a comprehensive analysis
    return {
        "application_id": application_id,
        "document_analysis": document_context,
        "compliance_checks": compliance_context,
        "underwriting_evaluation": underwriting_context,
        "analysis_timestamp": datetime.now().isoformat()
    }