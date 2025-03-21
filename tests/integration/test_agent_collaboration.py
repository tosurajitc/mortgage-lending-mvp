"""
Test the basic collaboration patterns (sequential workflows)
Test error handling and recovery
Test message passing between agents
Test dynamic agent selection
Test the feedback system
Test metrics and monitoring
Include end-to-end workflow testing

"""

import os
import sys
import unittest
import json
import time
from unittest.mock import MagicMock, patch
import logging
from typing import Dict, List, Any, Optional, Tuple

# Add project root to path
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.autogen.collaboration.manager import CollaborationManager
from src.autogen.collaboration.agent import BaseCollaborativeAgent
from src.autogen.collaboration.selection import DynamicAgentSelector  # Using the existing selector
from src.autogen.collaboration.feedback import FeedbackLoop, FeedbackEntry, FeedbackType
from src.autogen.collaboration.metrics import CollaborationMonitor, MetricType
from src.autogen.reasoning_agents import create_reasoning_agents
from src.data.models import ApplicationStatus  # Import models from your existing codebase

# Configure logging for tests
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MockAgent(BaseCollaborativeAgent):
    """Mock agent implementation for testing."""
    
    def __init__(self, agent_id: str, capabilities: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id)
        self.execute_step_mock = MagicMock()
        self.receive_message_mock = MagicMock()
        self.implemented_steps = []
        self.capabilities = capabilities or {}
    
    def execute_step(self, step_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Mock execution of a step."""
        self.execute_step_mock(step_name, inputs)
        
        # Default success response
        if step_name in self.implemented_steps:
            return {
                "status": "success",
                "output": {"result": f"Mock result for {step_name}"}
            }
        else:
            return {
                "status": "error",
                "error": f"Step {step_name} not implemented"
            }
    
    def receive_message(self, message: Dict[str, Any]) -> None:
        """Mock receiving a message."""
        super().receive_message(message)
        self.receive_message_mock(message)
    
    def set_implemented_steps(self, steps: List[str]) -> None:
        """Set steps that this agent can implement."""
        self.implemented_steps = steps
    
    def can_handle_step(self, step_name: str) -> bool:
        """Check if agent can handle a step."""
        return step_name in self.implemented_steps
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities."""
        return self.capabilities


class TestAgentCollaboration(unittest.TestCase):
    """Integration tests for agent collaboration patterns."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a test configuration file
        self.config = {
            "collaboration_patterns": {
                "test_workflow": {
                    "description": "Test workflow for integration testing",
                    "workflow_type": "sequential",
                    "agents": ["orchestrator", "document_agent", "underwriting_agent"],
                    "initiator": "orchestrator",
                    "steps": [
                        {
                            "name": "start_test",
                            "agent": "orchestrator",
                            "description": "Start the test workflow",
                            "required": True,
                            "timeout_seconds": 10,
                            "retry_count": 0,
                            "requires_confirmation": False,
                            "outputs": ["test_started"]
                        },
                        {
                            "name": "process_document",
                            "agent": "document_agent",
                            "description": "Process a test document",
                            "required": True,
                            "timeout_seconds": 10,
                            "retry_count": 1,
                            "requires_confirmation": False,
                            "inputs": ["test_started"],
                            "outputs": ["document_result"]
                        },
                        {
                            "name": "evaluate_document",
                            "agent": "underwriting_agent",
                            "description": "Evaluate the document result",
                            "required": True,
                            "timeout_seconds": 10,
                            "retry_count": 0,
                            "requires_confirmation": True,
                            "inputs": ["document_result"],
                            "outputs": ["evaluation_result"]
                        }
                    ],
                    "error_handling": {
                        "process_document": {
                            "on_timeout": "retry",
                            "on_error": "notify_orchestrator",
                            "max_retries": 1,
                            "fallback": "skip_step"
                        }
                    }
                }
            },
            "agent_capabilities": {
                "orchestrator": {
                    "can_initiate": True,
                    "can_finalize_decisions": True,
                    "can_resolve_conflicts": True,
                    "can_delegate": True,
                    "can_monitor": True,
                    "priority_level": 1
                },
                "document_agent": {
                    "can_initiate": False,
                    "can_finalize_decisions": False,
                    "can_resolve_conflicts": False,
                    "can_delegate": False,
                    "can_monitor": False,
                    "priority_level": 2
                },
                "underwriting_agent": {
                    "can_initiate": False,
                    "can_finalize_decisions": False,
                    "can_resolve_conflicts": False,
                    "can_delegate": False,
                    "can_monitor": False,
                    "priority_level": 2
                }
            }
        }
        
        # Write config to temporary file
        self.config_path = "test_config.json"
        with open(self.config_path, "w") as f:
            json.dump(self.config, f)
        
        # Create collaboration manager
        self.manager = CollaborationManager(self.config_path)
        
        # Create mock agents
        self.orchestrator = MockAgent("orchestrator", self.config["agent_capabilities"]["orchestrator"])
        self.document_agent = MockAgent("document_agent", self.config["agent_capabilities"]["document_agent"])
        self.underwriting_agent = MockAgent("underwriting_agent", self.config["agent_capabilities"]["underwriting_agent"])
        
        # Set implemented steps
        self.orchestrator.set_implemented_steps(["start_test"])
        self.document_agent.set_implemented_steps(["process_document"])
        self.underwriting_agent.set_implemented_steps(["evaluate_document"])
        
        # Register agents
        self.manager.register_agent("orchestrator", self.orchestrator)
        self.manager.register_agent("document_agent", self.document_agent)
        self.manager.register_agent("underwriting_agent", self.underwriting_agent)
        
        # Set up agents' collaboration manager
        self.orchestrator.set_collaboration_manager(self.manager)
        self.document_agent.set_collaboration_manager(self.manager)
        self.underwriting_agent.set_collaboration_manager(self.manager)
    
    def tearDown(self):
        """Clean up after tests."""
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
    
    def test_sequential_workflow(self):
        """Test a sequential workflow pattern."""
        # Create a workflow session
        session_id = self.manager.create_workflow_session(
            pattern_name="test_workflow",
            context_data={"initial_data": "test"},
            initiator="orchestrator"
        )
        
        # Verify session was created
        self.assertIsNotNone(session_id)
        self.assertTrue(session_id in self.manager.active_sessions)
        
        # Check that the first step was executed
        self.orchestrator.execute_step_mock.assert_called_once()
        args, _ = self.orchestrator.execute_step_mock.call_args
        self.assertEqual(args[0], "start_test")
        
        # Simulate step completion confirmation (normally happens in _handle_step_completion)
        self.manager.confirm_step(session_id, True)
        
        # Check that the second step was executed
        self.document_agent.execute_step_mock.assert_called_once()
        args, _ = self.document_agent.execute_step_mock.call_args
        self.assertEqual(args[0], "process_document")
        
        # Simulate step completion confirmation
        self.manager.confirm_step(session_id, True)
        
        # Check that the third step was executed
        self.underwriting_agent.execute_step_mock.assert_called_once()
        args, _ = self.underwriting_agent.execute_step_mock.call_args
        self.assertEqual(args[0], "evaluate_document")
        
        # Simulate confirmation required step (confirmation needed)
        status = self.manager.get_session_status(session_id)
        self.assertEqual(status["status"], "awaiting_confirmation")
        
        # Confirm the step
        self.manager.confirm_step(session_id, True)
        
        # Check that workflow is completed
        status = self.manager.get_session_status(session_id)
        self.assertEqual(status["status"], "completed")
    
    def test_error_handling(self):
        """Test error handling in workflow."""
        # Override document agent to return an error
        def mock_error_execute(step_name, inputs):
            return {
                "status": "error",
                "error": "Test error"
            }
        
        self.document_agent.execute_step = mock_error_execute
        
        # Create a workflow session
        session_id = self.manager.create_workflow_session(
            pattern_name="test_workflow",
            context_data={"initial_data": "test"},
            initiator="orchestrator"
        )
        
        # Verify session was created
        self.assertIsNotNone(session_id)
        
        # Simulate first step completion
        self.manager.confirm_step(session_id, True)
        
        # Get status - should be in error state or awaiting instruction
        status = self.manager.get_session_status(session_id)
        self.assertTrue(status["status"] in ["error", "awaiting_orchestrator_instruction"])
        
        # If in awaiting instruction state, resume with skip
        if status["status"] == "awaiting_orchestrator_instruction":
            self.manager.resume_workflow(session_id, "skip")
            
            # Check that workflow continued to next step
            status = self.manager.get_session_status(session_id)
            self.assertTrue(status["status"] in ["awaiting_confirmation", "step_in_progress"])
    
    def test_message_passing(self):
        """Test message passing between agents."""
        # Send a message from orchestrator to document agent
        message_id = self.manager.send_message(
            sender="orchestrator",
            recipient="document_agent",
            message_type="request",
            content={"request_type": "test_request", "data": "test"},
            priority="high"
        )
        
        # Verify message was received
        self.document_agent.receive_message_mock.assert_called_once()
        
        # Get the message that was received
        args, _ = self.document_agent.receive_message_mock.call_args
        message = args[0]
        
        # Check message content
        self.assertEqual(message["sender"], "orchestrator")
        self.assertEqual(message["recipient"], "document_agent")
        self.assertEqual(message["message_type"], "request")
        self.assertEqual(message["content"]["request_type"], "test_request")
    
    def test_dynamic_agent_selection(self):
        """Test dynamic agent selection using your existing DynamicAgentSelector."""
        # Create a mortgage application data
        application_data = {
            "loan_details": {"loan_type": "conventional"},
            "property_info": {"property_type": "single_family"},
            "employment_type": "W2_EMPLOYED",
            "loan_details": {
                "is_first_time_homebuyer": True,
                "loan_type": "conventional"
            },
            "primary_applicant": {
                "credit_score": 750,
                "annual_income": 96000  # equivalent to monthly_income: 8000
            },
            "monthly_debt": 2000
        }
        
        # Create a selector
        selector = DynamicAgentSelector()
        
        # Test document analysis team selection
        doc_team = selector.select_document_analysis_team(application_data)
        self.assertTrue(len(doc_team) >= 2)  # Should include at least coordinator and one specialist
        
        # Test underwriting team selection
        underwriting_team = selector.select_underwriting_team(application_data)
        self.assertTrue(len(underwriting_team) >= 2)  # Should include at least coordinator and one specialist
        
        # For conventional loans, should include conventional loan specialist
        specialist_names = [agent.name for agent in underwriting_team]
        self.assertIn("conventional_loan_specialist", specialist_names)
        
        # Test with a different loan type
        application_data["loan_details"]["loan_type"] = "fha"
        fha_team = selector.select_underwriting_team(application_data)
        specialist_names = [agent.name for agent in fha_team]
        self.assertIn("fha_loan_specialist", specialist_names)
    
    def test_feedback_system(self):
        """Test the feedback system."""
        # Create a feedback loop
        feedback_loop = FeedbackLoop(self.manager)
        
        # Create a feedback entry
        feedback = FeedbackEntry(
            source_agent="orchestrator",
            target_agent="document_agent",
            feedback_type=FeedbackType.ACCURACY,
            score=0.8,
            comments="Good job processing the document"
        )
        
        # Provide feedback
        result = feedback_loop.provide_feedback(feedback)
        
        # Verify feedback was processed
        self.assertTrue(result)
        
        # Get feedback summary
        summary = feedback_loop.get_agent_feedback_summary("document_agent")
        
        # Verify summary contains our feedback
        self.assertEqual(summary["feedback_count"], 1)
        self.assertIn("accuracy", summary["average_scores"])
        self.assertAlmostEqual(summary["average_scores"]["accuracy"], 0.8)
    
    def test_metrics_monitoring(self):
        """Test metrics and monitoring."""
        # Create a monitor
        monitor = CollaborationMonitor(self.manager)
        
        # Register a workflow
        monitor.register_workflow("test_workflow_1")
        
        # Register agents
        monitor.register_agent("orchestrator")
        monitor.register_agent("document_agent")
        
        # Record agent activity
        monitor.record_agent_step(
            agent_id="document_agent",
            step_name="process_document",
            success=True,
            duration=1.5,
            metadata={"document_type": "test"}
        )
        
        # Update workflow status
        monitor.update_workflow_status(
            workflow_id="test_workflow_1",
            status="completed",
            step_completed=True
        )
        
        # Get dashboard data
        dashboard = monitor.get_dashboard_data()
        
        # Verify metrics were recorded
        self.assertIn("agent_performance", dashboard)
        self.assertIn("document_agent", dashboard["agent_performance"])
        self.assertIn("workflow_statistics", dashboard)
    
    @patch('src.autogen.reasoning_agents.autogen.AssistantAgent')
    def test_integration_with_reasoning_agents(self, mock_assistant_agent):
        """Test integration with reasoning agents."""
        # Mock AutoGen agent
        mock_autogen_agent = MagicMock()
        mock_autogen_agent.generate_reply = MagicMock(return_value="Test response")
        mock_assistant_agent.return_value = mock_autogen_agent
        
        # Create reasoning agents
        reasoning_agents = create_reasoning_agents(self.manager)
        
        # Verify agents were created
        self.assertIn("document_reasoning", reasoning_agents)
        self.assertIn("underwriting_reasoning", reasoning_agents)
        self.assertIn("compliance_reasoning", reasoning_agents)
        
        # Register a reasoning agent
        self.manager.register_agent("document_reasoning", reasoning_agents["document_reasoning"])
        
        # Test executing a reasoning step
        result = reasoning_agents["document_reasoning"].execute_reasoning(
            reasoning_type="document_analysis",
            inputs={"document_content": "This is a test document"}
        )
        
        # Verify reasoning was executed
        self.assertEqual(result["status"], "success")


class TestMortgageWorkflows(unittest.TestCase):
    """Tests specific to mortgage lending workflows using your DynamicAgentSelector."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a test configuration file
        self.config = {
            "collaboration_patterns": {
                "mortgage_application": {
                    "description": "Process a mortgage application",
                    "workflow_type": "sequential_with_validation",
                    "agents": ["orchestrator", "document_agent", "underwriting_agent", "compliance_agent"],
                    "initiator": "orchestrator",
                    "steps": [
                        {
                            "name": "receive_application",
                            "agent": "orchestrator",
                            "description": "Receive and validate the application",
                            "required": True,
                            "outputs": ["application_data"]
                        },
                        {
                            "name": "analyze_documents",
                            "agent": "document_agent",
                            "description": "Analyze application documents",
                            "required": True,
                            "inputs": ["application_data"],
                            "outputs": ["document_analysis"]
                        },
                        {
                            "name": "assess_risk",
                            "agent": "underwriting_agent",
                            "description": "Assess application risk",
                            "required": True,
                            "inputs": ["application_data", "document_analysis"],
                            "outputs": ["risk_assessment"]
                        },
                        {
                            "name": "check_compliance",
                            "agent": "compliance_agent",
                            "description": "Check regulatory compliance",
                            "required": True,
                            "inputs": ["application_data", "document_analysis", "risk_assessment"],
                            "outputs": ["compliance_status"]
                        },
                        {
                            "name": "make_decision",
                            "agent": "orchestrator",
                            "description": "Make final decision",
                            "required": True,
                            "inputs": ["risk_assessment", "compliance_status"],
                            "outputs": ["final_decision"]
                        }
                    ]
                }
            }
        }
        
        # Write config to temporary file
        self.config_path = "test_mortgage_config.json"
        with open(self.config_path, "w") as f:
            json.dump(self.config, f)
        
        # Create collaboration manager
        self.manager = CollaborationManager(self.config_path)
        
        # Create dynamic agent selector
        self.agent_selector = DynamicAgentSelector()
        
        # Setup monitoring
        self.monitor = CollaborationMonitor(self.manager)
        
        # Setup feedback system
        self.feedback = FeedbackLoop(self.manager)
    
    def tearDown(self):
        """Clean up after tests."""
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
    
    def test_conventional_loan_workflow(self):
        """Test a conventional loan workflow with document analysis."""
        # Create mock application
        application_data = {
            "loan_details": {
                "loan_type": "conventional", 
                "loan_amount": 350000,
                "is_first_time_homebuyer": False
            },
            "property_info": {
                "property_type": "single_family",
                "estimated_value": 450000
            },
            "employment_type": "W2_EMPLOYED",
            "primary_applicant": {
                "credit_score": 740,
                "annual_income": 114000  # 9500 monthly
            },
            "monthly_debt": 2500
        }
        
        # Set up teams based on application characteristics
        doc_team = self.agent_selector.select_document_analysis_team(application_data)
        self.assertIsNotNone(doc_team)
        self.assertTrue(len(doc_team) >= 2)
        
        underwriting_team = self.agent_selector.select_underwriting_team(application_data)
        self.assertIsNotNone(underwriting_team)
        self.assertTrue(len(underwriting_team) >= 2)
        
        compliance_team = self.agent_selector.select_compliance_team(application_data)
        self.assertIsNotNone(compliance_team)
        self.assertTrue(len(compliance_team) >= 2)
        
        # Verify correct specialists were selected for conventional loan
        specialist_names = [agent.name for agent in underwriting_team]
        self.assertIn("conventional_loan_specialist", specialist_names)
        
        # Test income verification specialist selection
        doc_specialist_names = [agent.name for agent in doc_team]
        self.assertIn("income_verification_specialist", doc_specialist_names)
    
    def test_self_employed_loan_workflow(self):
        """Test a self-employed loan workflow with specialized team selection."""
        # Create mock application for self-employed borrower
        application_data = {
            "loan_details": {
                "loan_type": "conventional", 
                "loan_amount": 500000,
                "is_first_time_homebuyer": False
            },
            "property_info": {
                "property_type": "single_family",
                "estimated_value": 650000
            },
            "employment_type": "SELF_EMPLOYED",
            "primary_applicant": {
                "credit_score": 780,
                "annual_income": 180000  # 15000 monthly
            },
            "monthly_debt": 4000,
            "income": {
                "self_employment": 180000,
                "w2": 0
            }
        }
        
        # Set up teams based on application characteristics
        doc_team = self.agent_selector.select_document_analysis_team(application_data)
        underwriting_team = self.agent_selector.select_underwriting_team(application_data)
        
        # Verify self-employment specialist was selected
        doc_specialist_names = [agent.name for agent in doc_team]
        self.assertIn("self_employment_specialist", doc_specialist_names)
        
        # Verify self-employment specialist is also on underwriting team for complex income
        underwriting_specialist_names = [agent.name for agent in underwriting_team]
        self.assertIn("self_employment_specialist", underwriting_specialist_names)
    
    def test_first_time_homebuyer_customer_service(self):
        """Test first-time homebuyer customer service team selection."""
        # Create mock application
        application_data = {
            "loan_details": {
                "loan_type": "fha", 
                "loan_amount": 250000,
                "is_first_time_homebuyer": True
            },
            "property_info": {
                "property_type": "single_family",
                "estimated_value": 275000
            },
            "employment_type": "W2_EMPLOYED",
            "primary_applicant": {
                "credit_score": 680,
                "annual_income": 78000  # 6500 monthly
            },
            "monthly_debt": 1800
        }
        
        # Set up customer service team
        customer_team = self.agent_selector.select_customer_service_team(
            application_data, 
            communication_type="explanation"
        )
        
        # Verify first-time homebuyer specialist was selected
        specialist_names = [agent.name for agent in customer_team]
        self.assertIn("first_time_homebuyer_specialist", specialist_names)
        
        # Test rejection scenario
        rejection_team = self.agent_selector.select_customer_service_team(
            application_data, 
            communication_type="rejection"
        )
        
        # Verify adverse action specialist was selected
        specialist_names = [agent.name for agent in rejection_team]
        self.assertIn("adverse_action_specialist", specialist_names)


if __name__ == "__main__":
    unittest.main()