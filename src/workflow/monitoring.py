"""
Monitoring and logging infrastructure for the mortgage application workflow.

This module provides comprehensive monitoring, logging, and observability
for the multi-agent mortgage processing system.
"""

import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
import datetime
import uuid
import json
import time
import threading
from collections import defaultdict, deque


class MetricType(Enum):
    """Types of metrics that can be collected."""
    COUNTER = "counter"    # Cumulative value that only increases
    GAUGE = "gauge"        # Value that can go up or down
    HISTOGRAM = "histogram"  # Distribution of values
    TIMER = "timer"        # Time duration of operations


class AlertSeverity(Enum):
    """Severity levels for alerts."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MonitoringManager:
    """
    Manages monitoring, metrics, and alerting for the workflow system.
    
    This class provides centralized monitoring capabilities, tracking
    performance metrics, system health, and agent activities.
    """
    
    def __init__(self):
        """Initialize the MonitoringManager."""
        self.logger = logging.getLogger(__name__)
        
        # Metrics storage
        self.metrics = {
            "counters": defaultdict(int),
            "gauges": {},
            "histograms": defaultdict(list),
            "timers": defaultdict(list)
        }
        
        # Health checks
        self.health_checks = {}
        
        # Alerts
        self.alerts = []
        self.alert_callbacks = {}
        
        # Event storage
        self.events = deque(maxlen=1000)  # Store last 1000 events
        
        # Create monitoring thread
        self.stop_monitoring = threading.Event()
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
    
    def record_metric(self, 
                    metric_name: str, 
                    value: Union[int, float],
                    metric_type: MetricType,
                    tags: Optional[Dict[str, str]] = None) -> None:
        """
        Record a metric value.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            metric_type: Type of metric
            tags: Optional tags to associate with the metric
        """
        # Add tags to the metric name if provided
        full_name = metric_name
        if tags:
            tag_str = ",".join(f"{k}={v}" for k, v in tags.items())
            full_name = f"{metric_name}[{tag_str}]"
        
        # Record based on metric type
        if metric_type == MetricType.COUNTER:
            self.metrics["counters"][full_name] += value
        elif metric_type == MetricType.GAUGE:
            self.metrics["gauges"][full_name] = value
        elif metric_type == MetricType.HISTOGRAM:
            self.metrics["histograms"][full_name].append(value)
        elif metric_type == MetricType.TIMER:
            self.metrics["timers"][full_name].append(value)
    
    def increment_counter(self, 
                         metric_name: str, 
                         value: int = 1,
                         tags: Optional[Dict[str, str]] = None) -> None:
        """
        Increment a counter metric.
        
        Args:
            metric_name: Name of the counter
            value: Amount to increment by (default: 1)
            tags: Optional tags to associate with the metric
        """
        self.record_metric(
            metric_name=metric_name,
            value=value,
            metric_type=MetricType.COUNTER,
            tags=tags
        )
    
    def set_gauge(self, 
                 metric_name: str, 
                 value: float,
                 tags: Optional[Dict[str, str]] = None) -> None:
        """
        Set a gauge metric value.
        
        Args:
            metric_name: Name of the gauge
            value: Gauge value
            tags: Optional tags to associate with the metric
        """
        self.record_metric(
            metric_name=metric_name,
            value=value,
            metric_type=MetricType.GAUGE,
            tags=tags
        )
    
    def record_histogram(self, 
                        metric_name: str, 
                        value: float,
                        tags: Optional[Dict[str, str]] = None) -> None:
        """
        Record a value for a histogram metric.
        
        Args:
            metric_name: Name of the histogram
            value: Value to record
            tags: Optional tags to associate with the metric
        """
        self.record_metric(
            metric_name=metric_name,
            value=value,
            metric_type=MetricType.HISTOGRAM,
            tags=tags
        )
    
    def record_timer(self, 
                    metric_name: str, 
                    value: float,
                    tags: Optional[Dict[str, str]] = None) -> None:
        """
        Record a timer duration.
        
        Args:
            metric_name: Name of the timer
            value: Duration in seconds
            tags: Optional tags to associate with the metric
        """
        self.record_metric(
            metric_name=metric_name,
            value=value,
            metric_type=MetricType.TIMER,
            tags=tags
        )
    
    def timed_execution(self, metric_name: str, tags: Optional[Dict[str, str]] = None):
        """
        Context manager for timing code execution.
        
        Args:
            metric_name: Name of the timer metric
            tags: Optional tags to associate with the metric
            
        Returns:
            Context manager for timing code execution
        """
        class TimedExecution:
            def __init__(self, manager, name, tags):
                self.manager = manager
                self.name = name
                self.tags = tags
                self.start_time = None
            
            def __enter__(self):
                self.start_time = time.time()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                end_time = time.time()
                duration = end_time - self.start_time
                self.manager.record_timer(self.name, duration, self.tags)
        
        return TimedExecution(self, metric_name, tags)
    
    def register_health_check(self, 
                             name: str, 
                             check_func: callable,
                             interval_seconds: int = 60) -> None:
        """
        Register a health check function.
        
        Args:
            name: Name of the health check
            check_func: Function that returns (is_healthy, details)
            interval_seconds: Check interval in seconds
        """
        self.health_checks[name] = {
            "func": check_func,
            "interval": interval_seconds,
            "last_run": None,
            "status": None,
            "details": None
        }
        
        self.logger.info(f"Registered health check: {name}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get the overall health status of the system.
        
        Returns:
            Dict[str, Any]: Health status information
        """
        # Run any checks that are due
        for name, check in self.health_checks.items():
            self._run_health_check(name)
        
        # Compile results
        checks = {}
        overall_healthy = True
        
        for name, check in self.health_checks.items():
            checks[name] = {
                "healthy": check["status"],
                "details": check["details"],
                "last_checked": check["last_run"]
            }
            
            if check["status"] is False:
                overall_healthy = False
        
        return {
            "healthy": overall_healthy,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "checks": checks
        }
    
    def _run_health_check(self, name: str) -> None:
        """
        Run a specific health check.
        
        Args:
            name: Name of the health check to run
        """
        if name not in self.health_checks:
            return
        
        check = self.health_checks[name]
        
        # Check if it's time to run this check
        now = time.time()
        if check["last_run"] is not None and (now - check["last_run"]) < check["interval"]:
            return
        
        try:
            # Run the check
            is_healthy, details = check["func"]()
            
            # Update status
            check["status"] = is_healthy
            check["details"] = details
            check["last_run"] = now
            
            # If unhealthy, create an alert
            if not is_healthy:
                self.create_alert(
                    name=f"Health check failed: {name}",
                    description=f"Health check '{name}' failed: {details}",
                    severity=AlertSeverity.ERROR,
                    context={"health_check": name}
                )
                
        except Exception as e:
            # Handle errors in the health check itself
            check["status"] = False
            check["details"] = f"Error running health check: {str(e)}"
            check["last_run"] = now
            
            self.logger.exception(f"Error running health check '{name}': {str(e)}")
    
    def create_alert(self, 
                    name: str, 
                    description: str,
                    severity: AlertSeverity,
                    context: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a system alert.
        
        Args:
            name: Alert name/title
            description: Detailed description
            severity: Alert severity
            context: Additional context information
            
        Returns:
            str: Alert ID
        """
        alert_id = str(uuid.uuid4())
        timestamp = datetime.datetime.utcnow().isoformat()
        
        alert = {
            "alert_id": alert_id,
            "name": name,
            "description": description,
            "severity": severity.value,
            "timestamp": timestamp,
            "context": context or {},
            "acknowledged": False
        }
        
        # Add to alerts
        self.alerts.append(alert)
        
        # Log the alert
        log_method = self.logger.info
        if severity == AlertSeverity.WARNING:
            log_method = self.logger.warning
        elif severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL]:
            log_method = self.logger.error
        
        log_method(f"Alert: {name} - {description}")
        
        # Trigger callbacks
        self._trigger_alert_callbacks(alert)
        
        return alert_id
    
    def register_alert_callback(self, 
                              severity: AlertSeverity,
                              callback: callable) -> None:
        """
        Register a callback for alerts of a specific severity.
        
        Args:
            severity: Alert severity to listen for
            callback: Function to call with the alert
        """
        if severity not in self.alert_callbacks:
            self.alert_callbacks[severity] = []
        
        self.alert_callbacks[severity].append(callback)
    
    def _trigger_alert_callbacks(self, alert: Dict[str, Any]) -> None:
        """
        Trigger callbacks for an alert.
        
        Args:
            alert: The alert that was created
        """
        severity = AlertSeverity(alert["severity"])
        
        if severity in self.alert_callbacks:
            for callback in self.alert_callbacks[severity]:
                try:
                    callback(alert)
                except Exception as e:
                    self.logger.error(f"Error in alert callback: {str(e)}")
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: ID of the alert to acknowledge
            
        Returns:
            bool: True if the alert was acknowledged
        """
        for alert in self.alerts:
            if alert["alert_id"] == alert_id:
                alert["acknowledged"] = True
                return True
        
        return False
    
    def get_active_alerts(self, 
                         severity: Optional[AlertSeverity] = None,
                         include_acknowledged: bool = False) -> List[Dict[str, Any]]:
        """
        Get active alerts.
        
        Args:
            severity: Optional severity filter
            include_acknowledged: Whether to include acknowledged alerts
            
        Returns:
            List[Dict[str, Any]]: List of alerts
        """
        filtered_alerts = []
        
        for alert in self.alerts:
            # Filter by acknowledgement
            if not include_acknowledged and alert["acknowledged"]:
                continue
            
            # Filter by severity
            if severity and alert["severity"] != severity.value:
                continue
            
            filtered_alerts.append(alert)
        
        # Sort by timestamp (newest first)
        filtered_alerts.sort(key=lambda a: a["timestamp"], reverse=True)
        
        return filtered_alerts
    
    def record_event(self, 
                    event_type: str, 
                    details: Dict[str, Any],
                    source: str) -> str:
        """
        Record a system event.
        
        Args:
            event_type: Type of event
            details: Event details
            source: Source of the event
            
        Returns:
            str: Event ID
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.datetime.utcnow().isoformat()
        
        event = {
            "event_id": event_id,
            "event_type": event_type,
            "source": source,
            "timestamp": timestamp,
            "details": details
        }
        
        # Add to events deque
        self.events.append(event)
        
        return event_id
    
    def get_events(self, 
                  event_type: Optional[str] = None,
                  source: Optional[str] = None,
                  limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recorded events.
        
        Args:
            event_type: Optional event type filter
            source: Optional source filter
            limit: Maximum number of events to return
            
        Returns:
            List[Dict[str, Any]]: List of events
        """
        filtered_events = []
        
        for event in self.events:
            # Filter by event type
            if event_type and event["event_type"] != event_type:
                continue
            
            # Filter by source
            if source and event["source"] != source:
                continue
            
            filtered_events.append(event)
        
        # Sort by timestamp (newest first)
        filtered_events.sort(key=lambda e: e["timestamp"], reverse=True)
        
        # Apply limit
        return filtered_events[:limit]
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics.
        
        Returns:
            Dict[str, Any]: All metrics
        """
        # For histograms and timers, calculate statistics
        histogram_stats = {}
        for name, values in self.metrics["histograms"].items():
            if values:
                histogram_stats[name] = self._calculate_stats(values)
        
        timer_stats = {}
        for name, values in self.metrics["timers"].items():
            if values:
                timer_stats[name] = self._calculate_stats(values)
        
        return {
            "counters": dict(self.metrics["counters"]),
            "gauges": self.metrics["gauges"],
            "histograms": histogram_stats,
            "timers": timer_stats,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
    
    def _calculate_stats(self, values: List[float]) -> Dict[str, float]:
        """
        Calculate statistics for a list of values.
        
        Args:
            values: List of values
            
        Returns:
            Dict[str, float]: Calculated statistics
        """
        sorted_values = sorted(values)
        count = len(sorted_values)
        
        if count == 0:
            return {
                "count": 0,
                "min": 0,
                "max": 0,
                "mean": 0,
                "median": 0,
                "p95": 0,
                "p99": 0
            }
        
        stats = {
            "count": count,
            "min": min(sorted_values),
            "max": max(sorted_values),
            "mean": sum(sorted_values) / count,
            "median": sorted_values[count // 2]
        }
        
        # Calculate percentiles
        p95_index = int(count * 0.95)
        p99_index = int(count * 0.99)
        
        stats["p95"] = sorted_values[p95_index - 1] if p95_index > 0 else sorted_values[0]
        stats["p99"] = sorted_values[p99_index - 1] if p99_index > 0 else sorted_values[0]
        
        return stats
    
    def _monitoring_loop(self) -> None:
        """Background thread for periodic monitoring tasks."""
        while not self.stop_monitoring.is_set():
            try:
                # Run health checks
                for name in self.health_checks.keys():
                    self._run_health_check(name)
                
                # Sleep for a bit
                time.sleep(1)
                
            except Exception as e:
                self.logger.exception(f"Error in monitoring loop: {str(e)}")
                time.sleep(5)  # Sleep longer on error
    
    def shutdown(self) -> None:
        """Shut down the monitoring system."""
        self.stop_monitoring.set()
        if self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
        
        self.logger.info("Monitoring system shut down")


class PerformanceTracker:
    """
    Tracks and analyzes performance metrics for the workflow system.
    
    This class provides utilities for tracking performance metrics
    and analyzing trends over time.
    """
    
    def __init__(self, monitoring_manager: MonitoringManager):
        """
        Initialize the PerformanceTracker.
        
        Args:
            monitoring_manager: The monitoring manager to use
        """
        self.monitoring = monitoring_manager
        self.logger = logging.getLogger(__name__)
        
        # Performance thresholds
        self.thresholds = {
            "response_time": 5.0,  # seconds
            "processing_time": 30.0,  # seconds
            "error_rate": 0.05  # 5%
        }
    
    def track_agent_execution(self, 
                             agent_type: str,
                             operation: str,
                             duration: float,
                             success: bool,
                             application_id: Optional[str] = None) -> None:
        """
        Track execution performance for an agent operation.
        
        Args:
            agent_type: Type of agent
            operation: Operation being performed
            duration: Duration in seconds
            success: Whether the operation succeeded
            application_id: Optional application ID
        """
        # Create tags
        tags = {
            "agent_type": agent_type,
            "operation": operation,
            "success": str(success).lower()
        }
        
        if application_id:
            tags["application_id"] = application_id
        
        # Record timer
        self.monitoring.record_timer(
            metric_name="agent.execution_time",
            value=duration,
            tags=tags
        )
        
        # Increment operation counter
        self.monitoring.increment_counter(
            metric_name="agent.operations",
            tags=tags
        )
        
        # Increment success/failure counter
        result_metric = "agent.successes" if success else "agent.failures"
        self.monitoring.increment_counter(
            metric_name=result_metric,
            tags=tags
        )
        
        # Check against thresholds
        if duration > self.thresholds["processing_time"]:
            self.monitoring.create_alert(
                name=f"Slow {agent_type} operation",
                description=f"{agent_type} {operation} took {duration:.2f}s to complete",
                severity=AlertSeverity.WARNING,
                context={
                    "agent_type": agent_type,
                    "operation": operation,
                    "duration": duration,
                    "application_id": application_id
                }
            )
    
    def track_workflow_step(self,
                          application_id: str,
                          step_name: str,
                          step_duration: float,
                          success: bool) -> None:
        """
        Track performance for a workflow step.
        
        Args:
            application_id: ID of the application
            step_name: Name of the workflow step
            step_duration: Duration in seconds
            success: Whether the step succeeded
        """
        # Create tags
        tags = {
            "application_id": application_id,
            "step_name": step_name,
            "success": str(success).lower()
        }
        
        # Record timer
        self.monitoring.record_timer(
            metric_name="workflow.step_duration",
            value=step_duration,
            tags=tags
        )
        
        # Increment step counter
        self.monitoring.increment_counter(
            metric_name="workflow.steps",
            tags=tags
        )
        
        # Increment success/failure counter
        result_metric = "workflow.step_successes" if success else "workflow.step_failures"
        self.monitoring.increment_counter(
            metric_name=result_metric,
            tags=tags
        )
    
    def track_application_processing(self,
                                   application_id: str,
                                   total_duration: float,
                                   outcome: str) -> None:
        """
        Track overall application processing.
        
        Args:
            application_id: ID of the application
            total_duration: Total processing duration in seconds
            outcome: Final outcome (approved, declined, etc.)
        """
        # Create tags
        tags = {
            "application_id": application_id,
            "outcome": outcome
        }
        
        # Record timer
        self.monitoring.record_timer(
            metric_name="application.processing_time",
            value=total_duration,
            tags=tags
        )
        
        # Increment application counter
        self.monitoring.increment_counter(
            metric_name="application.processed",
            tags=tags
        )
        
        # Record event
        self.monitoring.record_event(
            event_type="application_processed",
            source="workflow",
            details={
                "application_id": application_id,
                "duration": total_duration,
                "outcome": outcome
            }
        )
    
    def calculate_agent_performance(self, 
                                  agent_type: str,
                                  operation: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate performance metrics for an agent.
        
        Args:
            agent_type: Type of agent
            operation: Optional operation to filter by
            
        Returns:
            Dict[str, Any]: Performance metrics
        """
        metrics = self.monitoring.get_metrics()
        
        # Filter timer stats for this agent
        timer_key_prefix = "agent.execution_time"
        relevant_timers = {}
        
        for name, stats in metrics["timers"].items():
            if timer_key_prefix in name:
                # Parse tags
                tags_str = name.split("[")[1].rstrip("]") if "[" in name else ""
                tags = dict(item.split("=") for item in tags_str.split(",")) if tags_str else {}
                
                if tags.get("agent_type") == agent_type:
                    if operation is None or tags.get("operation") == operation:
                        op = tags.get("operation", "unknown")
                        relevant_timers[op] = stats
        
        # Calculate success rate
        success_counter_prefix = "agent.successes"
        failure_counter_prefix = "agent.failures"
        success_counts = {}
        failure_counts = {}
        
        for name, count in metrics["counters"].items():
            if success_counter_prefix in name or failure_counter_prefix in name:
                # Parse tags
                tags_str = name.split("[")[1].rstrip("]") if "[" in name else ""
                tags = dict(item.split("=") for item in tags_str.split(",")) if tags_str else {}
                
                if tags.get("agent_type") == agent_type:
                    if operation is None or tags.get("operation") == operation:
                        op = tags.get("operation", "unknown")
                        
                        if success_counter_prefix in name:
                            success_counts[op] = count
                        elif failure_counter_prefix in name:
                            failure_counts[op] = count
        
        # Calculate success rates
        success_rates = {}
        for op in set(list(success_counts.keys()) + list(failure_counts.keys())):
            successes = success_counts.get(op, 0)
            failures = failure_counts.get(op, 0)
            total = successes + failures
            
            if total > 0:
                success_rates[op] = successes / total
            else:
                success_rates[op] = 0.0
        
        return {
            "agent_type": agent_type,
            "operation": operation,
            "execution_times": relevant_timers,
            "success_rates": success_rates
        }
    
    def analyze_performance_trends(self) -> Dict[str, Any]:
        """
        Analyze performance trends over time.
        
        Returns:
            Dict[str, Any]: Performance trend analysis
        """
        # In a real implementation, this would analyze metrics over time
        # For the MVP, we'll return a simple structure
        
        return {
            "message": "Performance trend analysis not implemented in MVP",
            "timestamp": datetime.datetime.utcnow().isoformat()
        }


# Factory function to create a monitoring system
def create_monitoring_system() -> Tuple[MonitoringManager, PerformanceTracker]:
    """
    Create a monitoring system.
    
    Returns:
        Tuple[MonitoringManager, PerformanceTracker]: Monitoring components
    """
    monitoring = MonitoringManager()
    tracker = PerformanceTracker(monitoring)
    
    # Register some basic health checks
    monitoring.register_health_check(
        name="system_resources",
        check_func=lambda: _check_system_resources(),
        interval_seconds=60
    )
    
    return monitoring, tracker


def _check_system_resources() -> Tuple[bool, str]:
    """
    Check system resources (memory, CPU).
    This is a simplified implementation for the MVP.
    
    Returns:
        Tuple[bool, str]: (is_healthy, details)
    """
    # In a production system, this would check actual resource usage
    # For MVP, we'll just return healthy
    return True, "System resources are healthy"


class WorkflowMonitoring:
    """
    Specialized monitoring for workflow operations.
    
    This class provides workflow-specific monitoring utilities built
    on top of the general monitoring system.
    """
    
    def __init__(self, 
                 monitoring_manager: MonitoringManager,
                 performance_tracker: PerformanceTracker):
        """
        Initialize the WorkflowMonitoring.
        
        Args:
            monitoring_manager: The monitoring manager to use
            performance_tracker: The performance tracker to use
        """
        self.monitoring = monitoring_manager
        self.tracker = performance_tracker
        self.logger = logging.getLogger(__name__)
        
        # Track active applications
        self.active_applications = {}
        
        # Track step timing
        self.step_timing = {}
    
    def start_application_tracking(self, application_id: str) -> None:
        """
        Start tracking a new application.
        
        Args:
            application_id: The ID of the application
        """
        self.active_applications[application_id] = {
            "start_time": time.time(),
            "current_step": "initiated",
            "steps_completed": [],
            "step_start_time": time.time()
        }
        
        # Increment active applications gauge
        self.monitoring.set_gauge(
            metric_name="workflow.active_applications",
            value=len(self.active_applications)
        )
        
        # Log event
        self.monitoring.record_event(
            event_type="application_started",
            source="workflow",
            details={"application_id": application_id}
        )
    
    def track_step_change(self, 
                        application_id: str, 
                        new_step: str) -> None:
        """
        Track a change in application step.
        
        Args:
            application_id: The ID of the application
            new_step: The new step name
        """
        if application_id not in self.active_applications:
            # Start tracking if not already
            self.start_application_tracking(application_id)
            return
        
        app_tracking = self.active_applications[application_id]
        current_time = time.time()
        previous_step = app_tracking["current_step"]
        step_duration = current_time - app_tracking["step_start_time"]
        
        # Track the completed step
        self.tracker.track_workflow_step(
            application_id=application_id,
            step_name=previous_step,
            step_duration=step_duration,
            success=True  # We assume success since we're moving to the next step
        )
        
        # Update step timing stats
        step_key = previous_step
        if step_key not in self.step_timing:
            self.step_timing[step_key] = []
        
        self.step_timing[step_key].append(step_duration)
        
        # Update tracking info
        app_tracking["current_step"] = new_step
        app_tracking["steps_completed"].append({
            "step": previous_step,
            "duration": step_duration
        })
        app_tracking["step_start_time"] = current_time
        
        # Log event
        self.monitoring.record_event(
            event_type="step_change",
            source="workflow",
            details={
                "application_id": application_id,
                "previous_step": previous_step,
                "new_step": new_step,
                "step_duration": step_duration
            }
        )
    
    def complete_application(self, 
                          application_id: str, 
                          outcome: str) -> None:
        """
        Mark an application as complete.
        
        Args:
            application_id: The ID of the application
            outcome: The final outcome (approved, declined, etc.)
        """
        if application_id not in self.active_applications:
            self.logger.warning(f"Attempting to complete untracked application: {application_id}")
            return
        
        app_tracking = self.active_applications[application_id]
        current_time = time.time()
        total_duration = current_time - app_tracking["start_time"]
        
        # Track final step
        final_step = app_tracking["current_step"]
        step_duration = current_time - app_tracking["step_start_time"]
        
        self.tracker.track_workflow_step(
            application_id=application_id,
            step_name=final_step,
            step_duration=step_duration,
            success=True
        )
        
        # Track overall application processing
        self.tracker.track_application_processing(
            application_id=application_id,
            total_duration=total_duration,
            outcome=outcome
        )
        
        # Remove from active applications
        del self.active_applications[application_id]
        
        # Update active applications gauge
        self.monitoring.set_gauge(
            metric_name="workflow.active_applications",
            value=len(self.active_applications)
        )
        
        # Log event
        self.monitoring.record_event(
            event_type="application_completed",
            source="workflow",
            details={
                "application_id": application_id,
                "outcome": outcome,
                "total_duration": total_duration,
                "steps": app_tracking["steps_completed"] + [{
                    "step": final_step,
                    "duration": step_duration
                }]
            }
        )
    
    def get_step_statistics(self) -> Dict[str, Dict[str, float]]:
        """
        Get statistics on step durations.
        
        Returns:
            Dict[str, Dict[str, float]]: Statistics by step
        """
        statistics = {}
        
        for step, durations in self.step_timing.items():
            if durations:
                count = len(durations)
                statistics[step] = {
                    "count": count,
                    "avg_duration": sum(durations) / count,
                    "min_duration": min(durations),
                    "max_duration": max(durations)
                }
                
                # Calculate percentiles
                sorted_durations = sorted(durations)
                p50_idx = int(count * 0.5)
                p95_idx = int(count * 0.95)
                
                statistics[step]["p50_duration"] = sorted_durations[p50_idx - 1] if p50_idx > 0 else sorted_durations[0]
                statistics[step]["p95_duration"] = sorted_durations[p95_idx - 1] if p95_idx > 0 else sorted_durations[0]
        
        return statistics
    
    def get_active_applications_summary(self) -> Dict[str, Any]:
        """
        Get a summary of active applications.
        
        Returns:
            Dict[str, Any]: Summary information
        """
        current_time = time.time()
        
        # Count applications by current step
        step_counts = {}
        for app_id, tracking in self.active_applications.items():
            step = tracking["current_step"]
            if step not in step_counts:
                step_counts[step] = 0
            step_counts[step] += 1
        
        # Calculate age statistics
        ages = []
        for tracking in self.active_applications.values():
            age = current_time - tracking["start_time"]
            ages.append(age)
        
        age_stats = {
            "count": len(ages),
            "avg_age": sum(ages) / len(ages) if ages else 0,
            "min_age": min(ages) if ages else 0,
            "max_age": max(ages) if ages else 0
        }
        
        return {
            "total_active": len(self.active_applications),
            "by_step": step_counts,
            "age_statistics": age_stats,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }