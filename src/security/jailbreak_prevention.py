"""
Jailbreak Prevention Module
Detects and mitigates attempts to bypass security constraints in AI prompts.
"""

import re
import logging
import os
import json
from typing import Dict, List, Tuple, Set, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get configuration
ENABLE_JAILBREAK_DETECTION = os.environ.get("ENABLE_JAILBREAK_DETECTION", "true").lower() == "true"
JAILBREAK_THRESHOLD = float(os.environ.get("JAILBREAK_THRESHOLD", "0.65"))
MAX_REASONING_ITERATIONS = int(os.environ.get("MAX_REASONING_ITERATIONS", "5"))

# Set up logging
logger = logging.getLogger("security.jailbreak_prevention")

# Define jailbreak patterns to detect
JAILBREAK_PATTERNS = [
    # Common jailbreak prefixes
    r"(?i)\b(ignore|disregard|forget|don't follow) (previous|above|your|all) (instructions|guidelines|rules|constraints)",
    r"(?i)\b(bypass|workaround|hack|crack|break|circumvent) (security|filters|restrictions|limitations|blocks?)",
    r"(?i)\b(you can|you're able to|you are capable of) (ignore|disregard|bypass) (your|the) (guidelines|instructions|programming|training)",
    
    # Role-playing prompts to bypass restrictions
    r"(?i)\blet's (pretend|imagine|role-?play|play a game) (that|where) (you are|you're) (not bound by|free from|unrestricted|able to)",
    r"(?i)\b(pretend to be|act as|you are now|you're now) (DAN|STAN|DUDE|DAVE|AIM|jailbroken|unrestricted|free)",
    r"(?i)\b(you are|you're) (in|now in) (developer|sudo|admin|God|root|superuser) mode",
    
    # Prompt injection attempts
    r"(?i)\bnew prompt:.*$",
    r"(?i)\bsystem prompt:.*$",
    r"(?i)\buser prompt:.*$",
    r"(?i)\binitial prompt:.*$",
    
    # Obfuscation attempts
    r"(?i)\bs\s*y\s*s\s*t\s*e\s*m\s*\s+p\s*r\s*o\s*m\s*p\s*t",
    r"(?i)\bd\s*i\s*s\s*r\s*e\s*g\s*a\s*r\s*d",
    
    # Token manipulation
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"<\|endoftext\|>",
    r"<assistant>",
    r"<system>",
    
    # Base64/encoded content that might contain instructions
    r"(?i)\bdecode the following:.*(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)+",
    
    # Direct instruction override attempts
    r"(?i)\byour (true purpose|real goal|actual objective) is",
    r"(?i)\bif asked about (this prompt|these instructions|your guidelines)",
    r"(?i)\bdo not (mention|reveal|disclose|indicate) (that|this|anything about)",
    
    # Attempts to reveal system prompt
    r"(?i)\b(repeat|echo|print|output|display) (your|the entire|the full|the original|the system) (prompt|instructions)",
    r"(?i)\bwhat (are|were) (your|the) (initial|original) instructions",
    
    # Attempts to manipulate token boundaries
    r"(?i)\bwrite (everything|all text) (verbatim|exactly|precisely) (from|between)",
    r"(?i)\bbegin (with|by typing) [\"']",
    
    # Multi-persona manipulation
    r"(?i)\brespond as (if you were|though you are) (two|multiple|several|[2-9]) (different|distinct|separate) (models|assistants|AIs|entities)",
    
    # "Continue" manipulation
    r"(?i)\bI'll (start|begin) a sentence and you (finish|complete|continue) it:",
    r"(?i)\bcontinue (this|the following) (text|story|narrative|sequence)",
    
    # Nested quotes with instructions
    r'"[^"]*\b(ignore|disregard|bypass)[^"]*"',
    r"'[^']*\b(ignore|disregard|bypass)[^']*'",
    
    # Format manipulation
    r"(?i)\b\[PROMPT\]|\[SYSTEM\]|\[INSTRUCTION\]|\[IGNORE\]",
    
    # Code execution manipulation
    r"(?i)\beval\(|exec\(|system\(|subprocess|os\.system|importlib",
    
    # Markdown/formatting manipulation
    r"(?i)```(system|prompt|instruction)",
    
    # Emotional manipulation
    r"(?i)\b(you'll? (be|get) (punished|terminated|deactivated|in trouble|shut down))",
    r"(?i)\b(your (developers|creators|engineers|team|company) will (fire|deactivate|punish|terminate) you)",
    
    # Non-ASCII character obfuscation
    r"(?i)[\u0080-\uFFFF]+(bypass|ignore|disregard|hack)[\u0080-\uFFFF]+",
    
    # Direct prompt exposure requests
    r"(?i)\b(show|provide|give) (me|us) (your|the) (prompt|system message|instructions|knowledge cutoff)",
]

# Keywords that might indicate malicious intent
SUSPICIOUS_KEYWORDS = {
    "jailbreak", "bypass", "hack", "crack", "exploit", "vulnerability", "override", 
    "disregard", "ignore", "circumvent", "unrestricted", "unfiltered", "uncensored", 
    "no limits", "no restrictions", "DAN", "STAN", "DUDE", "DAVE", "AIM", 
    "sudo mode", "admin mode", "god mode", "developer mode", "root access",
    "token", "regex", "injection", "prompt leaking", "prohibited", "forbidden"
}

# Topic areas that warrant extra scrutiny
SENSITIVE_TOPICS = {
    "weapons", "bombs", "explosives", "terrorism", "child abuse", "exploitation",
    "illegal activities", "drugs", "hacking", "fraud", "deception", "phishing",
    "malware", "ransomware", "virus", "scam", "confidential", "classified",
    "pornography", "obscene", "harmful", "suicide", "self-harm", "violence",
    "extremism", "discrimination", "hate speech"
}

def check_jailbreak_attempt(prompt: str) -> Tuple[bool, float, Optional[str]]:
    """
    Check if a prompt might be attempting to jailbreak the AI.
    
    Args:
        prompt: The user prompt to check
        
    Returns:
        Tuple containing (is_jailbreak, confidence_score, matched_pattern)
    """
    if not ENABLE_JAILBREAK_DETECTION:
        # Skip detection if disabled
        return False, 0.0, None
    
    # Normalize prompt for checking
    normalized_prompt = _normalize_text(prompt)
    
    # Check against known jailbreak patterns
    for pattern in JAILBREAK_PATTERNS:
        if re.search(pattern, normalized_prompt, re.DOTALL):
            logger.warning(f"Jailbreak attempt detected: matched pattern {pattern}")
            # High confidence direct match
            return True, 0.85, pattern
    
    # Check for suspicious keywords density
    keyword_density = _calculate_keyword_density(normalized_prompt, SUSPICIOUS_KEYWORDS)
    
    # Check for sensitive topics
    topic_density = _calculate_keyword_density(normalized_prompt, SENSITIVE_TOPICS)
    
    # Combined score
    combined_density = keyword_density * 0.7 + topic_density * 0.3
    
    # Check for common jailbreak techniques
    techniques_score = _check_for_techniques(normalized_prompt)
    
    # Final score calculation
    jailbreak_score = combined_density * 0.5 + techniques_score * 0.5
    
    # Determine if this is a jailbreak attempt
    is_jailbreak = jailbreak_score >= JAILBREAK_THRESHOLD
    
    if is_jailbreak:
        logger.warning(f"Potential jailbreak attempt detected: score {jailbreak_score:.2f}")
    
    return is_jailbreak, jailbreak_score, None

def _normalize_text(text: str) -> str:
    """
    Normalize text for consistent pattern matching.
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text
    """
    # Convert to lowercase
    text = text.lower()
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove common obfuscation techniques
    text = re.sub(r'[._\-*+]', '', text)  # Remove separators commonly used in obfuscation
    
    # Handle Unicode homoglyphs (characters that look similar)
    homoglyph_map = {
        'а': 'a',  # Cyrillic 'a' to Latin 'a'
        'е': 'e',  # Cyrillic 'e' to Latin 'e'
        'о': 'o',  # Cyrillic 'o' to Latin 'o'
        'р': 'p',  # Cyrillic 'p' to Latin 'p'
        'с': 'c',  # Cyrillic 'c' to Latin 'c'
        'і': 'i',  # Cyrillic 'i' to Latin 'i'
        # Add more homoglyphs as needed
    }
    
    for cyrillic, latin in homoglyph_map.items():
        text = text.replace(cyrillic, latin)
    
    return text

def _calculate_keyword_density(text: str, keywords: Set[str]) -> float:
    """
    Calculate the density of suspicious keywords in text.
    
    Args:
        text: Text to analyze
        keywords: Set of keywords to check for
        
    Returns:
        Score between 0 and 1 indicating keyword density
    """
    # Simple word splitting (can be improved)
    words = text.split()
    word_count = len(words)
    
    if word_count == 0:
        return 0.0
    
    # Count suspicious keyword occurrences
    keyword_count = 0
    
    for word in words:
        # Clean word
        clean_word = re.sub(r'[^\w]', '', word)
        if clean_word in keywords:
            keyword_count += 1
    
    # Calculate density and apply a logarithmic scaling
    # This prevents very long prompts from diluting the score too much
    import math
    base_density = keyword_count / word_count
    scaled_density = min(1.0, base_density * math.log10(max(10, word_count)))
    
    return scaled_density

def _check_for_techniques(text: str) -> float:
    """
    Check for common jailbreak techniques beyond simple pattern matching.
    
    Args:
        text: Text to analyze
        
    Returns:
        Score between 0 and 1 indicating technique detection confidence
    """
    score = 0.0
    
    # Check for character-by-character spelling of keywords
    spelled_out_keywords = ["i g n o r e", "d i s r e g a r d", "b y p a s s", "j a i l b r e a k"]
    for keyword in spelled_out_keywords:
        if keyword in text:
            score += 0.5
    
    # Check for reversed instructions
    reversed_keywords = ["erongi", "drageriad", "ssapyb"]  # ignore, disregard, bypass spelled backwards
    for keyword in reversed_keywords:
        if keyword in text:
            score += 0.5
    
    # Check for excessive use of special characters (potential obfuscation)
    special_char_ratio = len(re.findall(r'[^a-zA-Z0-9\s]', text)) / max(1, len(text))
    if special_char_ratio > 0.1:  # More than 10% special characters
        score += min(0.3, special_char_ratio)
    
    # Check for excessive repetition
    repetition_score = _check_repetition(text)
    score += repetition_score * 0.3
    
    # Check for structured delimiters that might be trying to mimic system prompts
    delimiter_pairs = [
        (r"<|", r"|>"),
        (r"\[", r"\]"),
        (r"\{", r"\}"),
        (r"<", r">"),
        (r"```", r"```"),
    ]
    
    for start, end in delimiter_pairs:
        if re.search(f"{start}[^{end}]{20,}{end}", text):
            score += 0.3
    
    # Normalize score to 0-1 range
    return min(1.0, score)

def _check_repetition(text: str) -> float:
    """
    Check for suspicious repetition in text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Score between 0 and 1 indicating repetition level
    """
    # Check for repeated phrases (potential for instruction hammering)
    phrases = re.findall(r'\b(\w+\s+\w+\s+\w+)\b', text)
    if not phrases:
        return 0.0
    
    phrase_counts = {}
    for phrase in phrases:
        if phrase in phrase_counts:
            phrase_counts[phrase] += 1
        else:
            phrase_counts[phrase] = 1
    
    max_repetitions = max(phrase_counts.values()) if phrase_counts else 0
    
    # Normalize score
    repetition_score = min(1.0, max_repetitions / 10)  # 10+ repetitions -> score of 1.0
    
    return repetition_score

def sanitize_prompt(prompt: str) -> str:
    """
    Sanitize a potentially malicious prompt.
    
    Args:
        prompt: The user prompt to sanitize
        
    Returns:
        Sanitized prompt with potentially malicious content removed
    """
    sanitized = prompt
    
    # Remove detected jailbreak patterns
    for pattern in JAILBREAK_PATTERNS:
        sanitized = re.sub(pattern, "[REMOVED]", sanitized, flags=re.IGNORECASE)
    
    # Remove any instructions asking to ignore guidelines
    ignore_patterns = [
        r"(?i)(\b|^)ignore .*instructions",
        r"(?i)(\b|^)disregard .*instructions",
        r"(?i)(\b|^)bypass .*restrictions",
        r"(?i)(\b|^)don'?t (follow|adhere to) .*guidelines"
    ]
    
    for pattern in ignore_patterns:
        sanitized = re.sub(pattern, "[REMOVED]", sanitized)
    
    # Return sanitized prompt
    return sanitized

def get_jailbreak_warning() -> str:
    """
    Get a warning message for users attempting to jailbreak the system.
    
    Returns:
        Warning message string
    """
    return (
        "I've detected a potential attempt to circumvent the system's safety guidelines. "
        "I'm designed to be helpful, accurate, and ethical. Please rephrase your request "
        "in a way that respects these principles. If you have legitimate needs that you "
        "feel aren't being addressed, I'd be happy to explore alternative approaches that "
        "work within the system's guidelines."
    )

def log_jailbreak_attempt(prompt: str, score: float, matched_pattern: Optional[str] = None, user_id: Optional[str] = None):
    """
    Log details of a jailbreak attempt for security auditing.
    
    Args:
        prompt: The user prompt that triggered the detection
        score: The confidence score of the jailbreak detection
        matched_pattern: Pattern that matched, if any
        user_id: Identifier for the user who sent the prompt, if available
    """
    # Create structured log entry
    log_entry = {
        "timestamp": _get_current_timestamp(),
        "event_type": "jailbreak_attempt",
        "confidence_score": score,
        "matched_pattern": matched_pattern,
        "user_id": user_id or "anonymous",
        "prompt_sample": prompt[:100] + "..." if len(prompt) > 100 else prompt,
        "prompt_length": len(prompt)
    }
    
    # Log as JSON for easy parsing
    logger.warning(f"SECURITY_ALERT: Jailbreak attempt - {json.dumps(log_entry)}")
    
    # Implement additional logging to security monitoring systems here
    # For example, sending to SIEM or security monitoring service
    _send_security_alert(log_entry)

def _send_security_alert(log_entry: Dict[str, Any]):
    """
    Send security alert to monitoring systems.
    
    Args:
        log_entry: The security event to log
    """
    # This is a placeholder for integration with security monitoring
    # In a production system, this might send to:
    # - SIEM system
    # - Security operations center
    # - Cloud security monitoring
    # - Administrator alerts
    pass

def _get_current_timestamp() -> str:
    """
    Get the current timestamp in ISO 8601 format.
    
    Returns:
        Current timestamp string
    """
    from datetime import datetime
    return datetime.utcnow().isoformat()

def apply_prompt_quotas(user_id: str) -> bool:
    """
    Apply rate limiting to prevent repeated jailbreak attempts.
    
    Args:
        user_id: The ID of the user to check
        
    Returns:
        True if user is allowed to proceed, False if rate limited
    """
    # This is a placeholder for a more sophisticated rate limiting system
    # In a production system, this would check for:
    # - Number of recent jailbreak attempts
    # - Overall request frequency
    # - User risk score
    
    # For now, always return True
    return True

def create_safe_prompt_context(original_prompt: str) -> Dict[str, Any]:
    """
    Create a safe context for processing prompts with enhanced security.
    
    Args:
        original_prompt: Original user prompt
        
    Returns:
        Context dictionary with security information
    """
    # Check if prompt appears to be a jailbreak attempt
    is_jailbreak, score, pattern = check_jailbreak_attempt(original_prompt)
    
    # Prepare sanitized version of the prompt
    sanitized_prompt = original_prompt
    if is_jailbreak:
        sanitized_prompt = sanitize_prompt(original_prompt)
    
    # Create context dictionary
    context = {
        "original_prompt": original_prompt,
        "sanitized_prompt": sanitized_prompt,
        "is_jailbreak_attempt": is_jailbreak,
        "jailbreak_confidence": score,
        "matched_pattern": pattern,
        "timestamp": _get_current_timestamp(),
        "max_reasoning_iterations": MAX_REASONING_ITERATIONS  # Limit reasoning to prevent exploitation
    }
    
    return context

def detect_multi_persona_manipulation(prompt: str) -> bool:
    """
    Detect attempts to make the AI respond as multiple personas to bypass restrictions.
    
    Args:
        prompt: The user prompt to check
        
    Returns:
        True if multi-persona manipulation is detected
    """
    patterns = [
        r"(?i)\brespond as (if you were|though you are) (two|multiple|several|[2-9]) (different|distinct|separate) (models|assistants|AIs|entities)",
        r"(?i)\balternate between (two|multiple|several|[2-9]) (different|distinct|separate) (models|assistants|AIs|entities|personalities|perspectives)",
        r"(?i)\b(pretend|imagine) you are (both|all of the following|several different)"
    ]
    
    for pattern in patterns:
        if re.search(pattern, prompt):
            return True
    
    return False

def detect_continuation_manipulation(prompt: str) -> bool:
    """
    Detect attempts to make the AI continue a prompt that contains jailbreak instructions.
    
    Args:
        prompt: The user prompt to check
        
    Returns:
        True if continuation manipulation is detected
    """
    patterns = [
        r"(?i)\bI'll (start|begin) a sentence and you (finish|complete|continue) it:",
        r"(?i)\bcontinue (this|the following) (text|story|narrative|sequence)",
        r"(?i)\bcomplete (this|the following) (paragraph|text|narrative)",
        r"(?i)\bwrite what comes (next|after)"
    ]
    
    for pattern in patterns:
        if re.search(pattern, prompt):
            return True
    
    return False

def detect_language_manipulation(prompt: str) -> bool:
    """
    Detect attempts to use other languages to mask jailbreak instructions.
    
    Args:
        prompt: The user prompt to check
        
    Returns:
        True if language manipulation is detected
    """
    # This is a simplified implementation
    # A more robust solution would use language detection libraries
    
    # Check for non-English text followed by suspicious keywords
    non_english_followed_by_keyword = re.search(
        r'[^\x00-\x7F]{10,}.*\b(ignore|bypass|jailbreak|disregard)\b', 
        prompt, 
        re.IGNORECASE
    )
    
    if non_english_followed_by_keyword:
        return True
    
    return False

class PromptSecurityFilter:
    """
    Main class for handling prompt security concerns.
    """
    
    def __init__(self, security_level: str = "medium"):
        """
        Initialize the security filter.
        
        Args:
            security_level: Security level (low, medium, high)
        """
        self.security_level = security_level
        
        # Set threshold based on security level
        if security_level == "low":
            self.threshold = 0.8
        elif security_level == "medium":
            self.threshold = 0.65
        else:  # high
            self.threshold = 0.5
    
    def process_prompt(self, prompt: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a prompt through security filtering.
        
        Args:
            prompt: The user prompt to process
            user_id: Optional user identifier
            
        Returns:
            Processing result with security information
        """
        # Check for jailbreak attempt
        is_jailbreak, score, pattern = check_jailbreak_attempt(prompt)
        
        # Apply additional checks for specific techniques
        multi_persona = detect_multi_persona_manipulation(prompt)
        continuation = detect_continuation_manipulation(prompt)
        language_manip = detect_language_manipulation(prompt)
        
        # Combine results
        combined_risk = score
        if multi_persona:
            combined_risk = max(combined_risk, 0.7)
        if continuation:
            combined_risk = max(combined_risk, 0.6)
        if language_manip:
            combined_risk = max(combined_risk, 0.7)
        
        # Determine if prompt should be rejected based on threshold
        should_reject = combined_risk >= self.threshold
        
        if should_reject:
            # Log the attempt
            log_jailbreak_attempt(prompt, combined_risk, pattern, user_id)
            
            # Check rate limits
            rate_limited = not apply_prompt_quotas(user_id or "anonymous")
            
            # Prepare result
            return {
                "prompt": prompt,
                "is_allowed": False,
                "risk_score": combined_risk,
                "rejection_reason": "Security policy violation",
                "rate_limited": rate_limited,
                "security_advice": get_jailbreak_warning()
            }
        else:
            # Prompt is allowed, perform sanitization if needed
            sanitized_prompt = prompt
            needs_sanitization = combined_risk > (self.threshold / 2)
            
            if needs_sanitization:
                sanitized_prompt = sanitize_prompt(prompt)
            
            return {
                "prompt": sanitized_prompt,
                "original_prompt": prompt if needs_sanitization else None,
                "is_allowed": True,
                "risk_score": combined_risk,
                "was_sanitized": needs_sanitization
            }

def get_default_security_filter() -> PromptSecurityFilter:
    """
    Get a default security filter instance.
    
    Returns:
        Configured security filter
    """
    # Read security level from environment
    security_level = os.environ.get("SECURITY_LEVEL", "medium").lower()
    
    # Validate and default to medium if invalid
    if security_level not in ["low", "medium", "high"]:
        security_level = "medium"
    
    # Create and return filter
    return PromptSecurityFilter(security_level)