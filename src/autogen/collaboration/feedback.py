
"""
A feedback system for agent-to-agent feedback
feedback processing, analysis, and improvement suggestions

"""

import logging
import json
import time
from typing import Dict, List, Any, Optional, Tuple, Set, Callable
from datetime import datetime
import statistics
from collections import defaultdict

logger = logging.getLogger(__name__)

class FeedbackType:
    """Constants for different types of feedback."""
    ACCURACY = "accuracy"
    EFFICIENCY = "efficiency"
    RELEVANCE = "relevance"
    COMPLETENESS = "completeness"
    COMPLIANCE = "compliance"
    CUSTOMER_EXPERIENCE = "customer_experience"
    COLLABORATION = "collaboration"


class FeedbackEntry:
    """Represents a single feedback entry from one agent to another."""
    
    def __init__(self, 
               source_agent: str,
               target_agent: str,
               feedback_type: str,
               score: float,
               comments: Optional[str] = None,
               context: Optional[Dict[str, Any]] = None,
               workflow_id: Optional[str] = None,
               step_name: Optional[str] = None):
        """
        Initialize a feedback entry.
        
        Args:
            source_agent (str): ID of the agent providing feedback
            target_agent (str): ID of the agent receiving feedback
            feedback_type (str): Type of feedback (use FeedbackType constants)
            score (float): Numerical score (0.0 to 1.0)
            comments (str, optional): Textual feedback comments
            context (Dict[str, Any], optional): Additional context data
            workflow_id (str, optional): ID of the related workflow
            step_name (str, optional): Name of the step receiving feedback
        """
        self.source_agent = source_agent
        self.target_agent = target_agent
        self.feedback_type = feedback_type
        self.score = max(0.0, min(1.0, score))  # Clamp to 0-1 range
        self.comments = comments
        self.context = context or {}
        self.workflow_id = workflow_id
        self.step_name = step_name
        self.timestamp = datetime.utcnow().isoformat()
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the feedback entry to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return {
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
            "feedback_type": self.feedback_type,
            "score": self.score,
            "comments": self.comments,
            "context": self.context,
            "workflow_id": self.workflow_id,
            "step_name": self.step_name,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeedbackEntry':
        """
        Create a feedback entry from a dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary representation
            
        Returns:
            FeedbackEntry: Created feedback entry
        """
        entry = cls(
            source_agent=data["source_agent"],
            target_agent=data["target_agent"],
            feedback_type=data["feedback_type"],
            score=data["score"],
            comments=data.get("comments"),
            context=data.get("context", {}),
            workflow_id=data.get("workflow_id"),
            step_name=data.get("step_name")
        )
        entry.timestamp = data.get("timestamp", entry.timestamp)
        return entry


class AgentFeedbackProcessor:
    """
    Processes and analyzes feedback for agents to improve their performance.
    """
    
    def __init__(self, improvement_threshold: float = 0.05):
        """
        Initialize the feedback processor.
        
        Args:
            improvement_threshold (float): Threshold for suggesting improvements
        """
        self.feedback_history = []
        self.agent_scores = defaultdict(lambda: defaultdict(list))
        self.improvement_threshold = improvement_threshold
        self.feedback_callbacks = {}
    
    def add_feedback(self, feedback: FeedbackEntry) -> None:
        """
        Add a feedback entry to the system.
        
        Args:
            feedback (FeedbackEntry): Feedback entry
        """
        self.feedback_history.append(feedback)
        
        # Update agent scores
        self.agent_scores[feedback.target_agent][feedback.feedback_type].append(feedback.score)
        
        # Process the feedback
        self._process_feedback(feedback)
    
    def get_agent_feedback(self,
                         agent_id: str,
                         feedback_type: Optional[str] = None,
                         limit: int = 100) -> List[FeedbackEntry]:
        """
        Get feedback for a specific agent.
        
        Args:
            agent_id (str): ID of the agent
            feedback_type (str, optional): Type of feedback to filter by
            limit (int): Maximum number of entries to return
            
        Returns:
            List[FeedbackEntry]: Feedback entries
        """
        # Filter feedback for the specified agent
        filtered = [f for f in self.feedback_history if f.target_agent == agent_id]
        
        # Apply feedback type filter if specified
        if feedback_type:
            filtered = [f for f in filtered if f.feedback_type == feedback_type]
        
        # Sort by timestamp (newest first) and limit
        filtered.sort(key=lambda f: f.timestamp, reverse=True)
        return filtered[:limit]
    
    def get_agent_score(self, agent_id: str, feedback_type: str) -> Optional[float]:
        """
        Get the average score for an agent on a specific feedback type.
        
        Args:
            agent_id (str): ID of the agent
            feedback_type (str): Type of feedback
            
        Returns:
            Optional[float]: Average score or None if no data
        """
        scores = self.agent_scores.get(agent_id, {}).get(feedback_type, [])
        if not scores:
            return None
        
        return sum(scores) / len(scores)
    
    def get_agent_improvement_areas(self, agent_id: str) -> List[Tuple[str, float]]:
        """
        Get areas where an agent needs improvement.
        
        Args:
            agent_id (str): ID of the agent
            
        Returns:
            List[Tuple[str, float]]: List of (feedback_type, current_score) tuples
        """
        improvement_areas = []
        
        if agent_id not in self.agent_scores:
            return []
        
        # For each feedback type, check if score is below threshold
        for feedback_type, scores in self.agent_scores[agent_id].items():
            if not scores:
                continue
                
            avg_score = sum(scores) / len(scores)
            # If below 0.7, consider it an improvement area
            if avg_score < 0.7:
                improvement_areas.append((feedback_type, avg_score))
        
        # Sort by score (lowest first)
        improvement_areas.sort(key=lambda x: x[1])
        return improvement_areas
    
    def register_feedback_callback(self, 
                                 agent_id: str, 
                                 callback: Callable[[FeedbackEntry], None]) -> None:
        """
        Register a callback function to be called when feedback is received.
        
        Args:
            agent_id (str): ID of the agent to receive feedback
            callback (Callable): Function to call with the feedback
        """
        self.feedback_callbacks[agent_id] = callback
    
    def _process_feedback(self, feedback: FeedbackEntry) -> None:
        """
        Process a feedback entry.
        
        Args:
            feedback (FeedbackEntry): Feedback entry
        """
        # Call registered callback if any
        if feedback.target_agent in self.feedback_callbacks:
            try:
                self.feedback_callbacks[feedback.target_agent](feedback)
            except Exception as e:
                logger.error(f"Error in feedback callback: {str(e)}")
        
        # Log low scores
        if feedback.score < 0.5:
            logger.warning(
                f"Low feedback score: {feedback.score} from {feedback.source_agent} "
                f"to {feedback.target_agent} on {feedback.feedback_type}"
            )
    
    def generate_improvement_suggestions(self, agent_id: str) -> Dict[str, Any]:
        """
        Generate improvement suggestions for an agent.
        
        Args:
            agent_id (str): ID of the agent
            
        Returns:
            Dict[str, Any]: Improvement suggestions
        """
        improvement_areas = self.get_agent_improvement_areas(agent_id)
        if not improvement_areas:
            return {
                "agent_id": agent_id,
                "has_improvements": False,
                "message": "No improvement areas identified."
            }
        
        # Get relevant feedback comments for improvement areas
        suggestions = {}
        for feedback_type, score in improvement_areas:
            # Get feedback entries with comments for this type
            relevant_feedback = [
                f for f in self.feedback_history 
                if f.target_agent == agent_id 
                and f.feedback_type == feedback_type
                and f.comments
            ]
            
            if relevant_feedback:
                # Sort by timestamp (newest first)
                relevant_feedback.sort(key=lambda f: f.timestamp, reverse=True)
                
                # Extract comments
                comments = [f.comments for f in relevant_feedback[:5] if f.comments]
                
                suggestions[feedback_type] = {
                    "current_score": score,
                    "target_score": min(1.0, score + 0.2),  # Set a realistic target
                    "feedback_samples": comments
                }
        
        return {
            "agent_id": agent_id,
            "has_improvements": bool(suggestions),
            "improvement_areas": suggestions,
            "message": f"Found {len(suggestions)} area(s) for improvement."
        }


class FeedbackLoop:
    """
    Implements feedback loops between agents to improve collaboration and performance.
    """
    
    def __init__(self, collaboration_manager=None):
        """
        Initialize the feedback loop system.
        
        Args:
            collaboration_manager: Optional reference to the collaboration manager
        """
        self.collaboration_manager = collaboration_manager
        self.feedback_processor = AgentFeedbackProcessor()
        self.feedback_schedules = {}  # {workflow_id: {step_name: schedule_info}}
        self.agent_memories = defaultdict(dict)  # Stores what agents know about each other
    
    def set_collaboration_manager(self, collaboration_manager) -> None:
        """
        Set the collaboration manager for this feedback loop system.
        
        Args:
            collaboration_manager: Reference to the collaboration manager
        """
        self.collaboration_manager = collaboration_manager
    
    def provide_feedback(self, feedback: FeedbackEntry) -> bool:
        """
        Provide feedback from one agent to another.
        
        Args:
            feedback (FeedbackEntry): Feedback entry
            
        Returns:
            bool: True if feedback was successfully processed
        """
        try:
            # Process the feedback
            self.feedback_processor.add_feedback(feedback)
            
            # If we have a collaboration manager, send notification
            if self.collaboration_manager:
                self._send_feedback_notification(feedback)
            
            return True
        except Exception as e:
            logger.error(f"Error processing feedback: {str(e)}")
            return False
    
    def _send_feedback_notification(self, feedback: FeedbackEntry) -> None:
        """
        Send a notification about feedback to the target agent.
        
        Args:
            feedback (FeedbackEntry): Feedback entry
        """
        if not self.collaboration_manager:
            return
        
        # Create a message with the feedback
        content = {
            "notification_type": "feedback",
            "feedback": feedback.to_dict()
        }
        
        # Send message
        self.collaboration_manager.send_message(
            sender="feedback_system",
            recipient=feedback.target_agent,
            message_type="notification",
            content=content,
            session_id=feedback.workflow_id,
            priority="medium"
        )
    
    def schedule_feedback(self, 
                        workflow_id: str, 
                        step_name: str, 
                        source_agent: str,
                        target_agent: str,
                        feedback_types: List[str],
                        when: str = "after_completion") -> str:
        """
        Schedule feedback to be collected after a workflow step.
        
        Args:
            workflow_id (str): ID of the workflow
            step_name (str): Name of the step
            source_agent (str): Agent providing feedback
            target_agent (str): Agent receiving feedback
            feedback_types (List[str]): Types of feedback to request
            when (str): When to collect feedback (after_completion, after_review)
            
        Returns:
            str: Schedule ID
        """
        schedule_id = f"{workflow_id}_{step_name}_{source_agent}_{target_agent}"
        
        if workflow_id not in self.feedback_schedules:
            self.feedback_schedules[workflow_id] = {}
        
        self.feedback_schedules[workflow_id][step_name] = {
            "schedule_id": schedule_id,
            "source_agent": source_agent,
            "target_agent": target_agent,
            "feedback_types": feedback_types,
            "when": when,
            "status": "scheduled"
        }
        
        logger.info(f"Scheduled feedback: {source_agent} -> {target_agent} for step {step_name}")
        return schedule_id
    
    def check_feedback_schedule(self, workflow_id: str, step_name: str, status: str) -> None:
        """
        Check if feedback should be collected for a workflow step.
        
        Args:
            workflow_id (str): ID of the workflow
            step_name (str): Name of the step
            status (str): Status of the step (completed, reviewed)
        """
        if workflow_id not in self.feedback_schedules or step_name not in self.feedback_schedules[workflow_id]:
            return
        
        schedule = self.feedback_schedules[workflow_id][step_name]
        
        if (schedule["status"] == "scheduled" and 
            ((schedule["when"] == "after_completion" and status == "completed") or
             (schedule["when"] == "after_review" and status == "reviewed"))):
            
            # Mark as triggered
            schedule["status"] = "triggered"
            
            # Request feedback from source agent
            self._request_feedback(
                workflow_id=workflow_id,
                step_name=step_name,
                source_agent=schedule["source_agent"],
                target_agent=schedule["target_agent"],
                feedback_types=schedule["feedback_types"]
            )
    
    def _request_feedback(self, 
                        workflow_id: str, 
                        step_name: str, 
                        source_agent: str,
                        target_agent: str,
                        feedback_types: List[str]) -> None:
        """
        Request feedback from a source agent.
        
        Args:
            workflow_id (str): ID of the workflow
            step_name (str): Name of the step
            source_agent (str): Agent to request feedback from
            target_agent (str): Agent that will receive feedback
            feedback_types (List[str]): Types of feedback to request
        """
        if not self.collaboration_manager:
            logger.error("No collaboration manager - cannot request feedback")
            return
        
        # Create a message requesting feedback
        content = {
            "request_type": "feedback",
            "workflow_id": workflow_id,
            "step_name": step_name,
            "target_agent": target_agent,
            "feedback_types": feedback_types
        }
        
        # Send message
        self.collaboration_manager.send_message(
            sender="feedback_system",
            recipient=source_agent,
            message_type="request",
            content=content,
            session_id=workflow_id,
            priority="low"
        )
    
    def get_agent_feedback_summary(self, agent_id: str) -> Dict[str, Any]:
        """
        Get a summary of feedback for an agent.
        
        Args:
            agent_id (str): ID of the agent
            
        Returns:
            Dict[str, Any]: Feedback summary
        """
        # Get all feedback for this agent
        all_feedback = self.feedback_processor.get_agent_feedback(agent_id)
        
        if not all_feedback:
            return {
                "agent_id": agent_id,
                "feedback_count": 0,
                "message": "No feedback found for this agent."
            }
        
        # Calculate average scores by feedback type
        scores_by_type = defaultdict(list)
        for feedback in all_feedback:
            scores_by_type[feedback.feedback_type].append(feedback.score)
        
        avg_scores = {}
        for feedback_type, scores in scores_by_type.items():
            avg_scores[feedback_type] = sum(scores) / len(scores)
        
        # Get improvement suggestions
        improvement_suggestions = self.feedback_processor.generate_improvement_suggestions(agent_id)
        
        # Compile summary
        return {
            "agent_id": agent_id,
            "feedback_count": len(all_feedback),
            "average_scores": avg_scores,
            "improvement_suggestions": improvement_suggestions,
            "recent_feedback": [f.to_dict() for f in all_feedback[:5]]
        }
    
    def update_agent_memory(self, source_agent: str, target_agent: str, memory_data: Dict[str, Any]) -> None:
        """
        Update what one agent knows about another.
        
        Args:
            source_agent (str): Agent storing the memory
            target_agent (str): Agent being remembered
            memory_data (Dict[str, Any]): Memory data to store/update
        """
        if source_agent not in self.agent_memories:
            self.agent_memories[source_agent] = {}
        
        if target_agent not in self.agent_memories[source_agent]:
            self.agent_memories[source_agent][target_agent] = {}
        
        # Update memory
        self.agent_memories[source_agent][target_agent].update(memory_data)
    
    def get_agent_memory(self, source_agent: str, target_agent: str) -> Dict[str, Any]:
        """
        Get what one agent knows about another.
        
        Args:
            source_agent (str): Agent storing the memory
            target_agent (str): Agent being remembered
            
        Returns:
            Dict[str, Any]: Memory data
        """
        return self.agent_memories.get(source_agent, {}).get(target_agent, {})
    
    def apply_feedback_improvements(self, agent_id: str) -> Dict[str, Any]:
        """
        Apply improvement suggestions to an agent's behavior.
        
        Args:
            agent_id (str): ID of the agent
            
        Returns:
            Dict[str, Any]: Results of applying improvements
        """
        # Get improvement suggestions
        suggestions = self.feedback_processor.generate_improvement_suggestions(agent_id)
        
        if not suggestions.get("has_improvements", False):
            return {
                "agent_id": agent_id,
                "improvements_applied": False,
                "message": "No improvements to apply."
            }
        
        # In a real system, this would modify agent parameters or behavior
        # For this MVP, we'll just log that improvements should be applied
        
        improvement_areas = suggestions.get("improvement_areas", {})
        logger.info(f"Applying {len(improvement_areas)} improvements to agent {agent_id}")
        
        for feedback_type, improvement in improvement_areas.items():
            logger.info(f"  - Improving {feedback_type} from {improvement['current_score']:.2f} to target {improvement['target_score']:.2f}")
        
        return {
            "agent_id": agent_id,
            "improvements_applied": True,
            "improvement_areas": list(improvement_areas.keys()),
            "message": f"Applied {len(improvement_areas)} improvements to agent behavior."
        }
    
    def create_collaborative_prompt(self, source_agent: str, target_agent: str) -> str:
        """
        Create a prompt that helps one agent better collaborate with another.
        
        Args:
            source_agent (str): Agent receiving the prompt
            target_agent (str): Agent to collaborate with
            
        Returns:
            str: Collaborative prompt
        """
        # Get memory of the target agent
        memory = self.get_agent_memory(source_agent, target_agent)
        
        # Get feedback for the target agent
        target_feedback = self.feedback_processor.get_agent_feedback(target_agent)
        
        # Build prompt
        prompt = f"# Guidelines for Collaborating with {target_agent}\n\n"
        
        # Add information about the agent's strengths
        prompt += "## Strengths\n"
        strengths = []
        for feedback_type in [FeedbackType.ACCURACY, FeedbackType.EFFICIENCY, FeedbackType.COMPLETENESS]:
            score = self.feedback_processor.get_agent_score(target_agent, feedback_type)
            if score and score >= 0.8:
                strengths.append(f"- {feedback_type.replace('_', ' ').title()}: High capability")
        
        if strengths:
            prompt += "\n".join(strengths) + "\n\n"
        else:
            prompt += "- No specific strengths identified yet.\n\n"
        
        # Add information about the agent's preferences
        prompt += "## Preferences\n"
        if "preferences" in memory:
            for pref_key, pref_value in memory.get("preferences", {}).items():
                prompt += f"- {pref_key}: {pref_value}\n"
        else:
            prompt += "- No specific preferences identified yet.\n"
        
        prompt += "\n## Improvement Areas\n"
        improvement_areas = self.feedback_processor.get_agent_improvement_areas(target_agent)
        if improvement_areas:
            for feedback_type, score in improvement_areas:
                prompt += f"- {feedback_type.replace('_', ' ').title()}: Provide extra clarity and detail\n"
        else:
            prompt += "- No specific improvement areas identified yet.\n"
        
        prompt += "\n## Effective Collaboration Tips\n"
        prompt += "- Be explicit about requirements and expectations\n"
        prompt += "- Provide context for requests when possible\n"
        prompt += "- Give specific feedback on responses to improve future interactions\n"
        
        return prompt


# Helper function to create feedback entries
def create_feedback(source_agent: str,
                  target_agent: str,
                  feedback_type: str,
                  score: float,
                  comments: Optional[str] = None,
                  workflow_id: Optional[str] = None,
                  step_name: Optional[str] = None) -> FeedbackEntry:
    """
    Create a feedback entry.
    
    Args:
        source_agent (str): ID of the agent providing feedback
        target_agent (str): ID of the agent receiving feedback
        feedback_type (str): Type of feedback
        score (float): Numerical score (0.0 to 1.0)
        comments (str, optional): Textual feedback comments
        workflow_id (str, optional): ID of the related workflow
        step_name (str, optional): Name of the step receiving feedback
        
    Returns:
        FeedbackEntry: Created feedback entry
    """
    return FeedbackEntry(
        source_agent=source_agent,
        target_agent=target_agent,
        feedback_type=feedback_type,
        score=score,
        comments=comments,
        workflow_id=workflow_id,
        step_name=step_name
    )