
"""
comprehensive metrics tracking for workflows and agents
monitoring dashboards and performance reports
    alerting and bottleneck detection capabilities
"""

import logging
import json
import time
from typing import Dict, List, Any, Optional, Tuple, Set, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics
import threading
import copy

logger = logging.getLogger(__name__)

class MetricType:
    """Constants for different types of metrics."""
    WORKFLOW_DURATION = "workflow_duration"
    STEP_DURATION = "step_duration"
    AGENT_RESPONSE_TIME = "agent_response_time"
    ERROR_RATE = "error_rate"
    DECISION_CONFIDENCE = "decision_confidence"
    MESSAGE_COUNT = "message_count"
    RETRY_COUNT = "retry_count"
    SUCCESSFUL_COMPLETION = "successful_completion"
    RESOURCE_UTILIZATION = "resource_utilization"
    FEEDBACK_SCORE = "feedback_score"


class CollaborationMetrics:
    """
    Tracks and analyzes metrics for agent collaboration.
    """
    
    def __init__(self, history_size: int = 1000):
        """
        Initialize the metrics system.
        
        Args:
            history_size (int): Maximum number of metric points to store
        """
        self.metrics = defaultdict(lambda: defaultdict(lambda: deque(maxlen=history_size)))
        self.active_timers = {}
        self.workflow_stats = defaultdict(dict)
        self.agent_stats = defaultdict(lambda: defaultdict(list))
        self.alert_thresholds = {}
        self.alert_callbacks = {}
        
        # Performance indicators
        self.kpis = {
            "avg_workflow_duration": 0.0,
            "success_rate": 1.0,
            "error_rate": 0.0,
            "agent_availability": 1.0,
            "decision_confidence_avg": 0.0
        }
        
        # Add a lock for thread safety
        self.lock = threading.RLock()
    
    def start_timer(self, metric_type: str, metric_name: str) -> str:
        """
        Start a timer for duration metrics.
        
        Args:
            metric_type (str): Type of metric
            metric_name (str): Name of the metric
            
        Returns:
            str: Timer ID
        """
        timer_id = f"{metric_type}_{metric_name}_{time.time()}"
        
        with self.lock:
            self.active_timers[timer_id] = {
                "start_time": time.time(),
                "metric_type": metric_type,
                "metric_name": metric_name
            }
        
        return timer_id
    
    def stop_timer(self, timer_id: str) -> Optional[float]:
        """
        Stop a timer and record the duration.
        
        Args:
            timer_id (str): Timer ID from start_timer
            
        Returns:
            Optional[float]: Duration in seconds or None if timer not found
        """
        with self.lock:
            if timer_id not in self.active_timers:
                logger.warning(f"Timer {timer_id} not found")
                return None
            
            timer_info = self.active_timers[timer_id]
            duration = time.time() - timer_info["start_time"]
            
            # Record the duration metric
            self.record_metric(
                metric_type=timer_info["metric_type"],
                metric_name=timer_info["metric_name"],
                value=duration
            )
            
            # Remove the timer
            del self.active_timers[timer_id]
            
            return duration
    
    def record_metric(self, metric_type: str, metric_name: str, value: Any) -> None:
        """
        Record a metric value.
        
        Args:
            metric_type (str): Type of metric
            metric_name (str): Name of the metric
            value (Any): Value to record
        """
        timestamp = datetime.utcnow().isoformat()
        
        with self.lock:
            self.metrics[metric_type][metric_name].append({
                "timestamp": timestamp,
                "value": value
            })
            
            # Check for alerts
            self._check_alert_threshold(metric_type, metric_name, value)
            
            # Update KPIs
            self._update_kpis(metric_type, metric_name, value)
    
    def record_workflow_completed(self, 
                               workflow_id: str, 
                               success: bool,
                               duration: float,
                               metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Record completion of a workflow.
        
        Args:
            workflow_id (str): ID of the workflow
            success (bool): Whether the workflow completed successfully
            duration (float): Duration in seconds
            metadata (Dict[str, Any], optional): Additional metadata
        """
        with self.lock:
            self.workflow_stats[workflow_id] = {
                "success": success,
                "duration": duration,
                "completion_time": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            # Record success metric
            self.record_metric(
                metric_type=MetricType.SUCCESSFUL_COMPLETION,
                metric_name="workflow",
                value=1 if success else 0
            )
            
            # Record duration metric
            self.record_metric(
                metric_type=MetricType.WORKFLOW_DURATION,
                metric_name=workflow_id,
                value=duration
            )
    
    def record_agent_activity(self, 
                           agent_id: str, 
                           activity_type: str,
                           duration: float,
                           success: bool,
                           metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Record an agent activity.
        
        Args:
            agent_id (str): ID of the agent
            activity_type (str): Type of activity
            duration (float): Duration in seconds
            success (bool): Whether the activity was successful
            metadata (Dict[str, Any], optional): Additional metadata
        """
        with self.lock:
            entry = {
                "activity_type": activity_type,
                "duration": duration,
                "success": success,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            self.agent_stats[agent_id]["activities"].append(entry)
            
            # Update activity counts
            activity_counts = self.agent_stats[agent_id].get("activity_counts", {})
            activity_counts[activity_type] = activity_counts.get(activity_type, 0) + 1
            self.agent_stats[agent_id]["activity_counts"] = activity_counts
            
            # Update success rate
            activities = self.agent_stats[agent_id]["activities"]
            success_count = sum(1 for a in activities if a["success"])
            self.agent_stats[agent_id]["success_rate"] = success_count / len(activities) if activities else 1.0
            
            # Record response time metric
            self.record_metric(
                metric_type=MetricType.AGENT_RESPONSE_TIME,
                metric_name=agent_id,
                value=duration
            )
    
    def set_alert_threshold(self, 
                          metric_type: str, 
                          metric_name: str, 
                          min_value: Optional[float] = None,
                          max_value: Optional[float] = None,
                          callback: Optional[Callable[[str, str, float, str], None]] = None) -> None:
        """
        Set an alert threshold for a metric.
        
        Args:
            metric_type (str): Type of metric
            metric_name (str): Name of the metric
            min_value (float, optional): Minimum acceptable value
            max_value (float, optional): Maximum acceptable value
            callback (Callable, optional): Function to call when threshold is exceeded
        """
        threshold_id = f"{metric_type}_{metric_name}"
        
        with self.lock:
            self.alert_thresholds[threshold_id] = {
                "metric_type": metric_type,
                "metric_name": metric_name,
                "min_value": min_value,
                "max_value": max_value
            }
            
            if callback:
                self.alert_callbacks[threshold_id] = callback
    
    def _check_alert_threshold(self, metric_type: str, metric_name: str, value: float) -> None:
        """
        Check if a metric value exceeds alert thresholds.
        
        Args:
            metric_type (str): Type of metric
            metric_name (str): Name of the metric
            value (float): Metric value
        """
        threshold_id = f"{metric_type}_{metric_name}"
        
        if threshold_id not in self.alert_thresholds:
            return
        
        threshold = self.alert_thresholds[threshold_id]
        min_value = threshold.get("min_value")
        max_value = threshold.get("max_value")
        alert_triggered = False
        alert_type = ""
        
        if min_value is not None and value < min_value:
            alert_triggered = True
            alert_type = "below_minimum"
        elif max_value is not None and value > max_value:
            alert_triggered = True
            alert_type = "above_maximum"
        
        if alert_triggered:
            logger.warning(
                f"Alert: {metric_type} {metric_name} value {value} {alert_type}"
            )
            
            # Call the callback if registered
            if threshold_id in self.alert_callbacks:
                try:
                    self.alert_callbacks[threshold_id](metric_type, metric_name, value, alert_type)
                except Exception as e:
                    logger.error(f"Error in alert callback: {str(e)}")
    
    def _update_kpis(self, metric_type: str, metric_name: str, value: float) -> None:
        """
        Update KPIs based on new metric values.
        
        Args:
            metric_type (str): Type of metric
            metric_name (str): Name of the metric
            value (float): Metric value
        """
        # Update specific KPIs based on metric type
        if metric_type == MetricType.WORKFLOW_DURATION:
            # Calculate rolling average workflow duration
            all_durations = []
            for name, values in self.metrics[MetricType.WORKFLOW_DURATION].items():
                all_durations.extend([v["value"] for v in values])
            
            if all_durations:
                self.kpis["avg_workflow_duration"] = sum(all_durations) / len(all_durations)
        
        elif metric_type == MetricType.SUCCESSFUL_COMPLETION:
            # Calculate success rate
            success_values = list(self.metrics[MetricType.SUCCESSFUL_COMPLETION]["workflow"])
            if success_values:
                success_count = sum(1 for v in success_values if v["value"] == 1)
                self.kpis["success_rate"] = success_count / len(success_values)
                self.kpis["error_rate"] = 1.0 - self.kpis["success_rate"]
        
        elif metric_type == MetricType.AGENT_RESPONSE_TIME:
            # Not directly used for KPIs, but could affect agent availability
            pass
        
        elif metric_type == MetricType.DECISION_CONFIDENCE:
            # Calculate average decision confidence
            confidence_values = []
            for name, values in self.metrics[MetricType.DECISION_CONFIDENCE].items():
                confidence_values.extend([v["value"] for v in values])
            
            if confidence_values:
                self.kpis["decision_confidence_avg"] = sum(confidence_values) / len(confidence_values)
    
    def get_metric_statistics(self, metric_type: str, metric_name: str) -> Dict[str, float]:
        """
        Get statistics for a specific metric.
        
        Args:
            metric_type (str): Type of metric
            metric_name (str): Name of the metric
            
        Returns:
            Dict[str, float]: Statistics (min, max, avg, median)
        """
        with self.lock:
            if metric_type not in self.metrics or metric_name not in self.metrics[metric_type]:
                return {
                    "min": 0.0,
                    "max": 0.0,
                    "avg": 0.0,
                    "median": 0.0,
                    "count": 0
                }
            
            values = [entry["value"] for entry in self.metrics[metric_type][metric_name]]
            
            if not values:
                return {
                    "min": 0.0,
                    "max": 0.0,
                    "avg": 0.0,
                    "median": 0.0,
                    "count": 0
                }
            
            return {
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "median": statistics.median(values),
                "count": len(values)
            }
    
    def get_agent_performance(self, agent_id: str) -> Dict[str, Any]:
        """
        Get performance metrics for a specific agent.
        
        Args:
            agent_id (str): ID of the agent
            
        Returns:
            Dict[str, Any]: Agent performance metrics
        """
        with self.lock:
            if agent_id not in self.agent_stats:
                return {
                    "agent_id": agent_id,
                    "success_rate": 0.0,
                    "avg_response_time": 0.0,
                    "activity_count": 0,
                    "active": False
                }
            
            # Calculate average response time
            activities = self.agent_stats[agent_id].get("activities", [])
            durations = [a["duration"] for a in activities]
            avg_response_time = sum(durations) / len(durations) if durations else 0.0
            
            return {
                "agent_id": agent_id,
                "success_rate": self.agent_stats[agent_id].get("success_rate", 0.0),
                "avg_response_time": avg_response_time,
                "activity_count": len(activities),
                "activity_types": self.agent_stats[agent_id].get("activity_counts", {}),
                "active": bool(activities and (datetime.utcnow() - datetime.fromisoformat(activities[-1]["timestamp"])) < timedelta(minutes=10))
            }
    
    def get_workflow_statistics(self, time_period: str = "all") -> Dict[str, Any]:
        """
        Get statistics about workflows.
        
        Args:
            time_period (str): Time period to analyze (all, day, week, month)
            
        Returns:
            Dict[str, Any]: Workflow statistics
        """
        with self.lock:
            # Filter workflows by time period
            cutoff_time = None
            now = datetime.utcnow()
            
            if time_period == "day":
                cutoff_time = now - timedelta(days=1)
            elif time_period == "week":
                cutoff_time = now - timedelta(weeks=1)
            elif time_period == "month":
                cutoff_time = now - timedelta(days=30)
            
            filtered_workflows = {}
            for workflow_id, stats in self.workflow_stats.items():
                if cutoff_time and datetime.fromisoformat(stats["completion_time"]) < cutoff_time:
                    continue
                filtered_workflows[workflow_id] = stats
            
            if not filtered_workflows:
                return {
                    "total_count": 0,
                    "success_count": 0,
                    "error_count": 0,
                    "success_rate": 0.0,
                    "avg_duration": 0.0,
                    "time_period": time_period
                }
            
            # Calculate statistics
            total_count = len(filtered_workflows)
            success_count = sum(1 for w in filtered_workflows.values() if w["success"])
            success_rate = success_count / total_count if total_count > 0 else 0.0
            
            durations = [w["duration"] for w in filtered_workflows.values()]
            avg_duration = sum(durations) / len(durations) if durations else 0.0
            
            return {
                "total_count": total_count,
                "success_count": success_count,
                "error_count": total_count - success_count,
                "success_rate": success_rate,
                "avg_duration": avg_duration,
                "time_period": time_period
            }
    
    def get_kpis(self) -> Dict[str, float]:
        """
        Get key performance indicators.
        
        Returns:
            Dict[str, float]: KPIs
        """
        with self.lock:
            return copy.deepcopy(self.kpis)


class CollaborationMonitor:
    """
    Monitors agent collaboration and provides alerts and dashboards.
    """
    
    def __init__(self, collaboration_manager=None):
        """
        Initialize the collaboration monitor.
        
        Args:
            collaboration_manager: Optional reference to the collaboration manager
        """
        self.collaboration_manager = collaboration_manager
        self.metrics = CollaborationMetrics()
        self.monitored_workflows = {}
        self.monitored_agents = set()
        self.dashboard_data = {}
        self.last_update = time.time()
        self.update_interval = 60  # seconds
    
    def set_collaboration_manager(self, collaboration_manager) -> None:
        """
        Set the collaboration manager for this monitor.
        
        Args:
            collaboration_manager: Reference to the collaboration manager
        """
        self.collaboration_manager = collaboration_manager
    
    def register_workflow(self, workflow_id: str) -> None:
        """
        Register a workflow to be monitored.
        
        Args:
            workflow_id (str): ID of the workflow
        """
        self.monitored_workflows[workflow_id] = {
            "start_time": time.time(),
            "steps_completed": 0,
            "steps_failed": 0,
            "current_step": None,
            "status": "running"
        }
        
        # Start workflow duration timer
        self.metrics.start_timer(MetricType.WORKFLOW_DURATION, workflow_id)
    
    def register_agent(self, agent_id: str) -> None:
        """
        Register an agent to be monitored.
        
        Args:
            agent_id (str): ID of the agent
        """
        self.monitored_agents.add(agent_id)
    
    def update_workflow_status(self, 
                            workflow_id: str, 
                            status: str, 
                            current_step: Optional[str] = None,
                            step_completed: bool = False,
                            step_failed: bool = False) -> None:
        """
        Update the status of a monitored workflow.
        
        Args:
            workflow_id (str): ID of the workflow
            status (str): New status
            current_step (str, optional): Current step name
            step_completed (bool): Whether a step was completed
            step_failed (bool): Whether a step failed
        """
        if workflow_id not in self.monitored_workflows:
            logger.warning(f"Workflow {workflow_id} not registered for monitoring")
            return
        
        workflow = self.monitored_workflows[workflow_id]
        workflow["status"] = status
        
        if current_step:
            workflow["current_step"] = current_step
        
        if step_completed:
            workflow["steps_completed"] += 1
        
        if step_failed:
            workflow["steps_failed"] += 1
        
        # If workflow is complete, record metrics
        if status in ["completed", "failed", "aborted"]:
            timer_id = f"{MetricType.WORKFLOW_DURATION}_{workflow_id}_{workflow['start_time']}"
            duration = self.metrics.stop_timer(timer_id)
            
            self.metrics.record_workflow_completed(
                workflow_id=workflow_id,
                success=(status == "completed"),
                duration=duration or (time.time() - workflow["start_time"]),
                metadata={
                    "steps_completed": workflow["steps_completed"],
                    "steps_failed": workflow["steps_failed"]
                }
            )
    
    def record_agent_step(self, 
                       agent_id: str, 
                       step_name: str, 
                       success: bool,
                       duration: float,
                       metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Record an agent completing a workflow step.
        
        Args:
            agent_id (str): ID of the agent
            step_name (str): Name of the step
            success (bool): Whether the step was successful
            duration (float): Duration in seconds
            metadata (Dict[str, Any], optional): Additional metadata
        """
        if agent_id not in self.monitored_agents:
            self.register_agent(agent_id)
        
        self.metrics.record_agent_activity(
            agent_id=agent_id,
            activity_type=f"step_{step_name}",
            duration=duration,
            success=success,
            metadata=metadata
        )
        
        # Record step duration metric
        self.metrics.record_metric(
            metric_type=MetricType.STEP_DURATION,
            metric_name=step_name,
            value=duration
        )
    
    def record_message_exchange(self, 
                              sender: str, 
                              recipient: str, 
                              message_type: str,
                              response_time: Optional[float] = None) -> None:
        """
        Record a message exchange between agents.
        
        Args:
            sender (str): ID of the sending agent
            recipient (str): ID of the receiving agent
            message_type (str): Type of message
            response_time (float, optional): Response time in seconds
        """
        # Record message count
        self.metrics.record_metric(
            metric_type=MetricType.MESSAGE_COUNT,
            metric_name=f"{sender}_to_{recipient}",
            value=1
        )
        
        # Record response time if provided
        if response_time is not None:
            self.metrics.record_metric(
                metric_type=MetricType.AGENT_RESPONSE_TIME,
                metric_name=recipient,
                value=response_time
            )
    
    def update_dashboard(self) -> Dict[str, Any]:
        """
        Update the dashboard data with current metrics.
        
        Returns:
            Dict[str, Any]: Dashboard data
        """
        current_time = time.time()
        
        # Only update at specified interval
        if current_time - self.last_update < self.update_interval:
            return self.dashboard_data
        
        self.last_update = current_time
        
        # Compile dashboard data
        self.dashboard_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "kpis": self.metrics.get_kpis(),
            "active_workflows": {
                wid: info for wid, info in self.monitored_workflows.items()
                if info["status"] in ["running", "waiting_for_event", "step_in_progress", "awaiting_confirmation"]
            },
            "agent_performance": {
                agent_id: self.metrics.get_agent_performance(agent_id)
                for agent_id in self.monitored_agents
            },
            "workflow_statistics": {
                "day": self.metrics.get_workflow_statistics("day"),
                "week": self.metrics.get_workflow_statistics("week"),
                "month": self.metrics.get_workflow_statistics("month"),
                "all": self.metrics.get_workflow_statistics("all")
            },
            "message_statistics": self._get_message_statistics(),
            "step_statistics": self._get_step_statistics(),
            "recent_errors": self._get_recent_errors()
        }
        
        return self.dashboard_data
    
    def _get_message_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about agent message exchanges.
        
        Returns:
            Dict[str, Any]: Message statistics
        """
        message_stats = {}
        
        # Calculate total messages between each agent pair
        for metric_name in self.metrics.metrics.get(MetricType.MESSAGE_COUNT, {}):
            stats = self.metrics.get_metric_statistics(MetricType.MESSAGE_COUNT, metric_name)
            if stats["count"] > 0:
                message_stats[metric_name] = stats["count"]
        
        # Calculate total messages per agent
        agent_messages = defaultdict(int)
        for metric_name, count in message_stats.items():
            if "_to_" in metric_name:
                sender, recipient = metric_name.split("_to_")
                agent_messages[sender] += count
                agent_messages[recipient] += count
        
        return {
            "total_messages": sum(message_stats.values()),
            "agent_pair_messages": message_stats,
            "agent_messages": dict(agent_messages)
        }
    
    def _get_step_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about workflow steps.
        
        Returns:
            Dict[str, Any]: Step statistics
        """
        step_stats = {}
        
        # Get statistics for each step
        for metric_name in self.metrics.metrics.get(MetricType.STEP_DURATION, {}):
            stats = self.metrics.get_metric_statistics(MetricType.STEP_DURATION, metric_name)
            step_stats[metric_name] = {
                "avg_duration": stats["avg"],
                "min_duration": stats["min"],
                "max_duration": stats["max"],
                "count": stats["count"]
            }
        
        return step_stats
    
    def _get_recent_errors(self) -> List[Dict[str, Any]]:
        """
        Get recent errors from workflows.
        
        Returns:
            List[Dict[str, Any]]: Recent errors
        """
        errors = []
        
        # Check for failed workflows
        for workflow_id, info in self.monitored_workflows.items():
            if info["status"] == "failed":
                errors.append({
                    "type": "workflow_failure",
                    "workflow_id": workflow_id,
                    "step": info.get("current_step"),
                    "timestamp": time.time() - (time.time() - info["start_time"])
                })
        
        # Return most recent errors first
        errors.sort(key=lambda e: e["timestamp"], reverse=True)
        return errors[:10]  # Limit to 10 most recent
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get the current dashboard data.
        
        Returns:
            Dict[str, Any]: Dashboard data
        """
        return self.update_dashboard()
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive performance report.
        
        Returns:
            Dict[str, Any]: Performance report
        """
        # Get the latest dashboard data
        dashboard = self.update_dashboard()
        
        # Compare with historical KPIs if available
        kpi_trends = {}
        for kpi, value in dashboard["kpis"].items():
            kpi_trends[kpi] = {
                "current": value,
                "trend": "stable"  # Default trend
            }
        
        # Detailed workflow analysis
        workflow_stats = self.metrics.get_workflow_statistics("all")
        
        # Agent performance ranking
        agent_performance = []
        for agent_id, perf in dashboard["agent_performance"].items():
            agent_performance.append({
                "agent_id": agent_id,
                "success_rate": perf["success_rate"],
                "avg_response_time": perf["avg_response_time"],
                "activity_count": perf["activity_count"]
            })
        
        # Sort by success rate (descending)
        agent_performance.sort(key=lambda a: a["success_rate"], reverse=True)
        
        # Calculate bottlenecks
        bottlenecks = []
        step_stats = dashboard["step_statistics"]
        for step_name, stats in step_stats.items():
            if stats["avg_duration"] > 5.0:  # Arbitrary threshold
                bottlenecks.append({
                    "step_name": step_name,
                    "avg_duration": stats["avg_duration"],
                    "count": stats["count"]
                })
        
        # Sort by average duration (descending)
        bottlenecks.sort(key=lambda b: b["avg_duration"], reverse=True)
        
        return {
            "generation_time": datetime.utcnow().isoformat(),
            "kpi_trends": kpi_trends,
            "workflow_statistics": workflow_stats,
            "agent_performance_ranking": agent_performance,
            "bottlenecks": bottlenecks,
            "error_rate": dashboard["kpis"]["error_rate"],
            "recommendations": self._generate_recommendations(dashboard)
        }
    
    def _generate_recommendations(self, dashboard: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations based on dashboard data.
        
        Args:
            dashboard (Dict[str, Any]): Dashboard data
            
        Returns:
            List[str]: Recommendations
        """
        recommendations = []
        
        # Check for high error rate
        if dashboard["kpis"]["error_rate"] > 0.1:
            recommendations.append(
                "Error rate is above 10%. Consider reviewing error handling in workflows."
            )
        
        # Check for slow workflows
        if dashboard["kpis"]["avg_workflow_duration"] > 60:
            recommendations.append(
                "Average workflow duration is high. Identify bottlenecks in workflow steps."
            )
        
        # Check for agent performance issues
        for agent_id, perf in dashboard["agent_performance"].items():
            if perf["success_rate"] < 0.8:
                recommendations.append(
                    f"Agent {agent_id} has a low success rate ({perf['success_rate']:.2f}). "
                    "Consider reviewing its implementation or providing additional training."
                )
        
        # Check for step performance issues
        for step_name, stats in dashboard["step_statistics"].items():
            if stats["avg_duration"] > 10.0:
                recommendations.append(
                    f"Step {step_name} has a high average duration ({stats['avg_duration']:.2f}s). "
                    "Consider optimizing this step."
                )
        
        return recommendations


def create_default_metrics() -> CollaborationMetrics:
    """
    Create a metrics instance with default alert thresholds.
    
    Returns:
        CollaborationMetrics: Metrics instance
    """
    metrics = CollaborationMetrics()
    
    # Set default alert thresholds
    metrics.set_alert_threshold(
        metric_type=MetricType.WORKFLOW_DURATION,
        metric_name="workflow",
        max_value=300.0  # Alert if workflow takes more than 5 minutes
    )
    
    metrics.set_alert_threshold(
        metric_type=MetricType.STEP_DURATION,
        metric_name="any",
        max_value=60.0  # Alert if any step takes more than 1 minute
    )
    
    metrics.set_alert_threshold(
        metric_type=MetricType.AGENT_RESPONSE_TIME,
        metric_name="any",
        max_value=30.0  # Alert if any agent takes more than 30 seconds to respond
    )
    
    metrics.set_alert_threshold(
        metric_type=MetricType.ERROR_RATE,
        metric_name="workflow",
        max_value=0.2  # Alert if error rate exceeds 20%
    )
    
    metrics.set_alert_threshold(
        metric_type=MetricType.DECISION_CONFIDENCE,
        metric_name="any",
        min_value=0.7  # Alert if decision confidence falls below 70%
    )
    
    return metrics


def create_collaboration_monitor(collaboration_manager=None) -> CollaborationMonitor:
    """
    Create a collaboration monitor with default metrics.
    
    Args:
        collaboration_manager: Optional reference to the collaboration manager
        
    Returns:
        CollaborationMonitor: Monitor instance
    """
    monitor = CollaborationMonitor(collaboration_manager)
    
    # Use default metrics
    monitor.metrics = create_default_metrics()
    
    return monitor