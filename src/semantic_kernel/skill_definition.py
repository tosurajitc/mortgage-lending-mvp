
"""
Defines decorators for Semantic Kernel skills.
"""

from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, cast

T = TypeVar('T')

def sk_function(
    description: str = "",
    name: Optional[str] = None,
    input_description: Optional[str] = None,
    input_default_value: Optional[str] = None,
    input_type: Optional[type] = None,
    output_type: Optional[type] = None,
) -> Callable[[T], T]:
    """
    Decorator for Semantic Kernel functions within a skill.
    
    Args:
        description: Description of what the function does
        name: Optional name of the function, defaults to function name
        input_description: Description of the input
        input_default_value: Default value for the input
        input_type: Type of the input
        output_type: Type of the output
        
    Returns:
        Decorated function
    """
    def decorator(func: T) -> T:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # Store metadata on the function
        wrapper.__sk_function__ = True
        wrapper.__sk_function_name__ = name or func.__name__
        wrapper.__sk_function_description__ = description
        wrapper.__sk_function_input_description__ = input_description
        wrapper.__sk_function_input_default_value__ = input_default_value
        wrapper.__sk_function_input_type__ = input_type
        wrapper.__sk_function_output_type__ = output_type
        
        return cast(T, wrapper)
    return decorator


def sk_function_context_parameter(
    name: str,
    description: str = "",
    default_value: Optional[str] = None,
    type_: Optional[type] = None,
    required: bool = False,
) -> Callable[[T], T]:
    """
    Decorator for parameters to Semantic Kernel functions.
    
    Args:
        name: Parameter name
        description: Description of the parameter
        default_value: Default value for the parameter
        type_: Type of the parameter
        required: Whether the parameter is required
        
    Returns:
        Decorated function
    """
    def decorator(func: T) -> T:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # Store parameter metadata on the function
        if not hasattr(wrapper, "__sk_function_parameters__"):
            wrapper.__sk_function_parameters__ = []
            
        wrapper.__sk_function_parameters__.append({
            "name": name,
            "description": description,
            "default_value": default_value,
            "type": type_,
            "required": required
        })
        
        return cast(T, wrapper)
    return decorator