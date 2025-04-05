

import os
import json
import logging
import logging.config
from pathlib import Path

def setup_logging(
    config_path=None,
    default_level=logging.INFO,
    env_key='LOG_CFG'
):
    """
    Set up logging configuration for the application.
    
    Args:
        config_path (str, optional): Path to the logging config file.
        default_level (int, optional): Default logging level if config fails.
        env_key (str, optional): Environment variable to check for config path.
    """

    # Add environment variable for log level
    log_level = os.getenv('LOG_LEVEL', default_level)
    try:
        default_level = getattr(logging, log_level.upper())
    except AttributeError:
        default_level = logging.INFO

        
    # Create logs directory if it doesn't exist
    Path('logs').mkdir(exist_ok=True)
    
    # Get config path from environment variable if provided
    env_path = os.getenv(env_key, None)
    if env_path:
        config_path = env_path
    
    # Default to project config directory if not provided
    if not config_path:
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / 'config' / 'logging_config.json'
    
    # Set up configuration from file if it exists
    if os.path.exists(config_path):
        with open(config_path, 'rt') as f:
            config = json.load(f)
        
        # Update Application Insights connection string from environment
        app_insights_conn_str = os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')
        if app_insights_conn_str and 'handlers' in config and 'application_insights' in config['handlers']:
            config['handlers']['application_insights']['connection_string'] = app_insights_conn_str
        
        # Create log directory if it doesn't exist (for any file handlers)
        for handler in config.get('handlers', {}).values():
            if 'filename' in handler:
                log_dir = os.path.dirname(handler['filename'])
                if log_dir:
                    os.makedirs(log_dir, exist_ok=True)
        
        logging.config.dictConfig(config)
    else:
        # Basic configuration if file not found
        logging.basicConfig(
            level=default_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logging.warning(f"Logging config file not found at {config_path}. Using basic configuration.")
def get_logger(name):
    """
    Get a logger with the specified name.
    
    Args:
        name (str): Name of the logger
        
    Returns:
        logging.Logger: Logger with the specified name
    """
    return logging.getLogger(name)


def get_audit_logger():
    """
    Get a logger for security audit events.
    
    Returns:
        logging.Logger: Logger configured for security auditing
    """
    return logging.getLogger('src.security.audit')

def log_agent_action(agent_name, action, details=None, status="success"):
    """
    Log an action performed by an agent.
    
    Args:
        agent_name (str): Name of the agent
        action (str): The action performed
        details (dict, optional): Additional details about the action
        status (str, optional): Status of the action (success/failure)
    """
    logger = logging.getLogger(f'src.agents.{agent_name}')
    
    log_data = {
        "agent": agent_name,
        "action": action,
        "status": status
    }
    
    if details:
        log_data["details"] = details
    
    if status == "success":
        logger.info(f"{agent_name} - {action}", extra=log_data)
    else:
        logger.error(f"{agent_name} - {action} - FAILED", extra=log_data)

def log_security_event(event_type, details, severity="INFO"):
    """
    Log a security-related event.
    
    Args:
        event_type (str): Type of security event (e.g., "AccessDenied", "PII_Detected")
        details (dict): Details about the security event
        severity (str, optional): Severity level (INFO, WARNING, ERROR)
    """
    security_logger = logging.getLogger('src.security')
    
    log_data = {
        "event_type": event_type,
        "details": details
    }
    
    if severity == "WARNING":
        security_logger.warning(f"Security event: {event_type}", extra=log_data)
    elif severity == "ERROR":
        security_logger.error(f"Security event: {event_type}", extra=log_data)
    else:
        security_logger.info(f"Security event: {event_type}", extra=log_data)

def log_workflow_step(workflow_id, step_name, status="started", details=None):
    """
    Log a workflow step event.
    
    Args:
        workflow_id (str): ID of the workflow
        step_name (str): Name of the step
        status (str, optional): Status of the step (started/completed/failed)
        details (dict, optional): Additional details about the step
    """
    workflow_logger = logging.getLogger('src.workflow')
    
    log_data = {
        "workflow_id": workflow_id,
        "step": step_name,
        "status": status
    }
    
    if details:
        log_data["details"] = details
    
    if status == "failed":
        workflow_logger.error(f"Workflow {workflow_id} - {step_name} - {status}", extra=log_data)
    else:
        workflow_logger.info(f"Workflow {workflow_id} - {step_name} - {status}", extra=log_data)