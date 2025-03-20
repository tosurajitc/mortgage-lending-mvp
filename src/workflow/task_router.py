"""
Task Router Module
Routes tasks to appropriate agents based on task type, content, and workflow state.
"""

from typing import Any, Dict, List, Optional, Tuple
import asyncio
from datetime import datetime
import json

from ..agents.orchestrator import OrchestratorAgent
from ..agents.document_agent import DocumentAnalysisAgent
from ..agents.underwriting_agent import UnderwritingAgent
from ..agents.compliance_agent import ComplianceAgent
from ..agents.customer_agent import CustomerServiceAgent
from ..autogen.conversation_manager import ConversationManager
from .state_manager import StateManager
from ..utils.logging_utils import get_logger
from ..data.models import ApplicationState

logger = get_logger("workflow.task_router")


class TaskRouter:
    """
    Routes tasks to appropriate agents based on task type and application state.
    Orchestrates the workflow by determining which agent should handle each task.
    """
    
    def __init__(self):
        self.logger = get_logger("task_router")
        self.state_manager = StateManager()
        
        # Initialize agents
        self.orchestrator = OrchestratorAgent()
        self.document_agent = DocumentAnalysisAgent()
        self.underwriting_agent = UnderwritingAgent()  
        self.compliance_agent = ComplianceAgent()
        self.customer_agent = CustomerServiceAgent()
        
        # For complex tasks that require multi-agent collaboration
        self.conversation_manager = ConversationManager()
        
        self.logger.info("Task router initialized")
    
    async def route_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route a task to the appropriate agent based on type and context.
        
        Args:
            task: Task description and data
            
        Returns:
            Dict containing the task result
        """
        task_type = task.get("task_type", "")
        application_id = task.get("application_id")
        
        self.logger.info(f"Routing task: {task_type} for application {application_id}")
        
        # Get current application state
        app_state = None
        if application_id:
            app_state = await self.state_manager.get_application_state(application_id)
        
        # Route based on task type
        if task_type == "process_application":
            return await self._route_process_application_task(task, app_state)
        elif task_type == "analyze_documents":
            return await self._route_document_analysis_task(task, app_state)
        elif task_type == "evaluate_application":
            return await self._route_underwriting_task(task, app_state)
        elif task_type == "check_compliance":
            return await self._route_compliance_task(task, app_state)
        elif task_type == "handle_customer_inquiry":
            return await self._route_customer_inquiry_task(task, app_state)
        elif task_type == "resolve_complex_application":
            return await self._route_complex_application_task(task, app_state)
        elif task_type == "generate_customer_explanation":
            return await self._route_customer_explanation_task(task, app_state)
        else:
            # Default to orchestrator for unknown task types
            self.logger.warning(f"Unknown task type: {task_type}, routing to orchestrator")
            return await self.orchestrator.execute(task)
    
    async def _route_process_application_task(self, task: Dict[str, Any], 
                                             app_state: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Route a process_application task.
        
        Args:
            task: Task details
            app_state: Current application state
            
        Returns:
            Dict containing task result
        """
        # Always route process_application tasks to the orchestrator
        self.logger.info("Routing process_application task to orchestrator")
        
        # Add application state to task if available
        if app_state:
            task["current_state"] = app_state.get("status")
            task["application_context"] = app_state.get("context", {})
        
        # Process the application through the orchestrator
        return await self.orchestrator.execute(task)
    
    async def _route_document_analysis_task(self, task: Dict[str, Any], 
                                           app_state: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Route a document analysis task.
        
        Args:
            task: Task details
            app_state: Current application state
            
        Returns:
            Dict containing task result
        """
        self.logger.info("Routing document analysis task to document agent")
        
        # Route to document analysis agent
        result = await self.document_agent.execute(task)
        
        # Update application state if needed
        application_id = task.get("application_id")
        if application_id and result.get("is_complete") is not None:
            if result.get("is_complete"):
                # All documents are complete and valid
                await self.state_manager.update_application_state(
                    application_id,
                    ApplicationState.DOCUMENTS_PROCESSED,
                    {"document_analysis": result},
                    "Document analysis completed successfully"
                )
            else:
                # Documents are incomplete or invalid
                await self.state_manager.update_application_state(
                    application_id,
                    ApplicationState.DOCUMENTS_SUBMITTED,
                    {"document_analysis": result, "missing_documents": result.get("missing_documents", [])},
                    "Document analysis identified missing or invalid documents"
                )
        
        return result
    
    async def _route_underwriting_task(self, task: Dict[str, Any], 
                                      app_state: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Route an underwriting evaluation task.
        
        Args:
            task: Task details
            app_state: Current application state
            
        Returns:
            Dict containing task result
        """
        self.logger.info("Routing underwriting task to underwriting agent")
        
        # Add application context if available
        if app_state:
            task["application_context"] = app_state.get("context", {})
            
            # Add document analysis results if available in context
            if "document_analysis" in app_state.get("context", {}):
                task["document_analysis"] = app_state["context"]["document_analysis"]
        
        # Route to underwriting agent
        result = await self.underwriting_agent.execute(task)
        
        # Update application state if needed
        application_id = task.get("application_id")
        if application_id:
            # Update state based on underwriting decision
            new_state = ApplicationState.UNDERWRITING_COMPLETED
            
            await self.state_manager.update_application_state(
                application_id,
                new_state,
                {"underwriting_results": result},
                f"Underwriting completed with decision: {result.get('is_approved', False)}"
            )
        
        return result
    
    async def _route_compliance_task(self, task: Dict[str, Any], 
                                    app_state: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Route a compliance check task.
        
        Args:
            task: Task details
            app_state: Current application state
            
        Returns:
            Dict containing task result
        """
        self.logger.info("Routing compliance task to compliance agent")
        
        # Add application context if available
        if app_state:
            task["application_context"] = app_state.get("context", {})
            
            # Add previous results if available
            context = app_state.get("context", {})
            if "document_analysis" in context:
                task["document_analysis"] = context["document_analysis"]
            if "underwriting_results" in context:
                task["underwriting_results"] = context["underwriting_results"]
        
        # Route to compliance agent
        result = await self.compliance_agent.execute(task)
        
        # Update application state if needed
        application_id = task.get("application_id")
        if application_id:
            # Determine new state based on compliance check
            new_state = ApplicationState.COMPLIANCE_CHECKED
            
            # If compliance failed, set appropriate state
            if not result.get("is_compliant", True):
                new_state = ApplicationState.REJECTED_COMPLIANCE
            
            await self.state_manager.update_application_state(
                application_id,
                new_state,
                {"compliance_results": result},
                f"Compliance check completed with result: {result.get('is_compliant', False)}"
            )
        
        return result
    
    async def _route_customer_inquiry_task(self, task: Dict[str, Any], 
                                          app_state: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Route a customer inquiry task.
        
        Args:
            task: Task details
            app_state: Current application state
            
        Returns:
            Dict containing task result
        """
        self.logger.info("Routing customer inquiry task to customer service agent")
        
        # Add application context if available
        if app_state:
            task["application_context"] = app_state.get("context", {})
            task["current_state"] = app_state.get("status")
        
        # Route to customer service agent
        return await self.customer_agent.execute(task)
    
    async def _route_complex_application_task(self, task: Dict[str, Any], 
                                             app_state: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Route a complex application that needs multi-agent collaboration.
        
        Args:
            task: Task details
            app_state: Current application state
            
        Returns:
            Dict containing task result
        """
        self.logger.info("Routing complex application to conversation manager")
        
        # Prepare application data with context
        application_data = task.get("application_data", {})
        
        if app_state:
            # Merge context into application data
            context = app_state.get("context", {})
            for key, value in context.items():
                if key not in application_data:
                    application_data[key] = value
        
        # Process through conversation manager
        result = await self.conversation_manager.process_complex_application(application_data)
        
        # Update application state based on the decision
        application_id = task.get("application_id") or application_data.get("application_id")
        if application_id:
            # Determine new state based on decision
            new_state = ApplicationState.APPROVED if result.get("decision", False) else ApplicationState.REJECTED_UNDERWRITING
            
            await self.state_manager.update_application_state(
                application_id,
                new_state,
                {"complex_decision": result},
                f"Complex application processing completed with decision: {result.get('decision', False)}"
            )
        
        return result
    
    async def _route_customer_explanation_task(self, task: Dict[str, Any], 
                                              app_state: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Route a task to generate a detailed customer explanation.
        
        Args:
            task: Task details
            app_state: Current application state
            
        Returns:
            Dict containing task result
        """
        self.logger.info("Routing customer explanation task to conversation manager")
        
        # Prepare application data with context
        application_data = task.get("application_data", {})
        decision_data = task.get("decision_data", {})
        
        if app_state:
            # Merge context into application data
            context = app_state.get("context", {})
            for key, value in context.items():
                if key not in application_data:
                    application_data[key] = value
        
        # Generate explanation through conversation manager
        result = await self.conversation_manager.generate_customer_explanation(
            application_data, decision_data
        )
        
        # Add explanation to application context
        application_id = task.get("application_id") or application_data.get("application_id")
        if application_id:
            await self.state_manager.add_context_data(
                application_id,
                {"customer_explanation": result.get("explanation", "")},
                "Generated detailed customer explanation"
            )
        
        return result
    
    async def get_suggested_next_tasks(self, application_id: str) -> List[Dict[str, Any]]:
        """
        Get suggested next tasks for an application based on its current state.
        
        Args:
            application_id: Unique identifier for the application
            
        Returns:
            List of suggested task dictionaries
        """
        # Get current application state
        app_state = await self.state_manager.get_application_state(application_id)
        
        if not app_state:
            return []
        
        current_state = app_state.get("status")
        context = app_state.get("context", {})
        
        suggested_tasks = []
        
        # Suggest tasks based on current state
        if current_state == ApplicationState.INITIATED:
            # New application, suggest document analysis
            suggested_tasks.append({
                "task_type": "analyze_documents",
                "application_id": application_id,
                "priority": "high",
                "description": "Analyze submitted documents"
            })
            
        elif current_state == ApplicationState.DOCUMENTS_SUBMITTED:
            # Documents submitted but not processed
            suggested_tasks.append({
                "task_type": "analyze_documents",
                "application_id": application_id,
                "priority": "high",
                "description": "Analyze submitted documents"
            })
            
        elif current_state == ApplicationState.DOCUMENTS_PROCESSED:
            # Documents processed, ready for underwriting
            suggested_tasks.append({
                "task_type": "evaluate_application",
                "application_id": application_id,
                "priority": "high",
                "description": "Evaluate application for underwriting decision"
            })
            
        elif current_state == ApplicationState.UNDERWRITING_COMPLETED:
            # Underwriting completed, ready for compliance check
            suggested_tasks.append({
                "task_type": "check_compliance",
                "application_id": application_id,
                "priority": "high",
                "description": "Check application for regulatory compliance"
            })
            
        elif current_state == ApplicationState.COMPLIANCE_CHECKED:
            # If underwriting approved and compliance passed
            underwriting_results = context.get("underwriting_results", {})
            compliance_results = context.get("compliance_results", {})
            
            if underwriting_results.get("is_approved", False) and compliance_results.get("is_compliant", False):
                # Ready for final approval
                suggested_tasks.append({
                    "task_type": "process_application",
                    "application_id": application_id,
                    "action": "finalize_approval",
                    "priority": "high",
                    "description": "Finalize application approval"
                })
            else:
                # Generate rejection explanation
                suggested_tasks.append({
                    "task_type": "generate_customer_explanation",
                    "application_id": application_id,
                    "priority": "high",
                    "description": "Generate detailed rejection explanation"
                })
        
        # Add generic tasks for any state
        suggested_tasks.append({
            "task_type": "handle_customer_inquiry",
            "application_id": application_id,
            "priority": "medium",
            "description": "Respond to customer inquiries"
        })
        
        return suggested_tasks