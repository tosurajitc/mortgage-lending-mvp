"""
Decision Tracker Module
Tracks and records decisions made by agents during the mortgage process.
"""

from typing import Any, Dict, List, Optional
import asyncio
from datetime import datetime
import json

from ..data.cosmos_manager import CosmosManager
from ..utils.logging_utils import get_logger

logger = get_logger("workflow.decision_tracker")


class DecisionTracker:
    """
    Tracks decisions made by agents during the mortgage application process.
    Records decision types, outcomes, factors, and explanations for audit and review.
    """
    
    def __init__(self):
        self.logger = get_logger("decision_tracker")
        self.cosmos_manager = CosmosManager()
        
    async def record_decision(self, application_id: str, decision_type: str, 
                             decision: bool, factors: Dict[str, Any], 
                             agent: Optional[str] = None, 
                             explanation: Optional[str] = None) -> Dict[str, Any]:
        """
        Record a decision made during the application process.
        
        Args:
            application_id: Unique identifier for the application
            decision_type: Type of decision (e.g., underwriting, compliance)
            decision: Boolean decision outcome (True for approval, False for rejection)
            factors: Dictionary of factors that influenced the decision
            agent: Optional identifier of the agent making the decision
            explanation: Optional explanation for the decision
            
        Returns:
            Dict containing the recorded decision
        """
        self.logger.info(f"Recording {decision_type} decision for application {application_id}")
        
        # Create decision record
        now = datetime.utcnow().isoformat()
        decision_record = {
            "id": f"{application_id}_{decision_type}_{now}",
            "application_id": application_id,
            "decision_type": decision_type,
            "decision": decision,
            "factors": factors,
            "agent": agent,
            "explanation": explanation,
            "timestamp": now
        }
        
        # Store in database
        try:
            await self.cosmos_manager.create_item("decisions", decision_record)
            return decision_record
            
        except Exception as e:
            self.logger.error(f"Error recording decision: {str(e)}")
            return decision_record
    
    async def get_decisions(self, application_id: str, decision_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get decisions for an application, optionally filtered by type.
        
        Args:
            application_id: Unique identifier for the application
            decision_type: Optional type of decision to filter by
            
        Returns:
            List of decision records
        """
        try:
            query = f"SELECT * FROM c WHERE c.application_id = '{application_id}'"
            
            if decision_type:
                query += f" AND c.decision_type = '{decision_type}'"
                
            query += " ORDER BY c.timestamp DESC"
            
            result = await self.cosmos_manager.query_items("decisions", query)
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting decisions: {str(e)}")
            return []
    
    async def get_latest_decision(self, application_id: str, decision_type: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent decision of a specific type for an application.
        
        Args:
            application_id: Unique identifier for the application
            decision_type: Type of decision to retrieve
            
        Returns:
            Dict containing the most recent decision or None if not found
        """
        decisions = await self.get_decisions(application_id, decision_type)
        
        if decisions:
            # Decisions are already sorted by timestamp descending
            return decisions[0]
        
        return None
    
    async def get_decision_audit_trail(self, application_id: str) -> Dict[str, Any]:
        """
        Get a comprehensive audit trail of all decisions for an application.
        
        Args:
            application_id: Unique identifier for the application
            
        Returns:
            Dict containing decision audit information
        """
        decisions = await self.get_decisions(application_id)
        
        # Group decisions by type
        decision_groups = {}
        for decision in decisions:
            decision_type = decision.get("decision_type")
            if decision_type not in decision_groups:
                decision_groups[decision_type] = []
            
            decision_groups[decision_type].append(decision)
        
        # Get final decisions by type
        final_decisions = {}
        for decision_type, group in decision_groups.items():
            if group:
                # Most recent decision of each type
                final_decisions[decision_type] = group[0]
        
        # Compile audit trail
        audit_trail = {
            "application_id": application_id,
            "decision_count": len(decisions),
            "decision_types": list(decision_groups.keys()),
            "final_decisions": final_decisions,
            "all_decisions": decisions,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return audit_trail
    
    async def analyze_decision_factors(self, application_id: str) -> Dict[str, Any]:
        """
        Analyze the factors that influenced decisions for an application.
        
        Args:
            application_id: Unique identifier for the application
            
        Returns:
            Dict containing analysis of decision factors
        """
        decisions = await self.get_decisions(application_id)
        
        # Extract all factors from decisions
        all_factors = {}
        for decision in decisions:
            decision_type = decision.get("decision_type")
            decision_factors = decision.get("factors", {})
            
            if decision_type not in all_factors:
                all_factors[decision_type] = {}
            
            # Merge factors from this decision
            for factor_key, factor_value in decision_factors.items():
                if factor_key not in all_factors[decision_type]:
                    all_factors[decision_type][factor_key] = []
                
                all_factors[decision_type][factor_key].append({
                    "value": factor_value,
                    "timestamp": decision.get("timestamp"),
                    "decision": decision.get("decision")
                })
        
        # Analyze frequency and impact of factors
        factor_analysis = {}
        for decision_type, factors in all_factors.items():
            factor_analysis[decision_type] = {}
            
            for factor_key, factor_history in factors.items():
                # Count occurrences of this factor
                occurrences = len(factor_history)
                
                # Count how often this factor is present in approvals vs rejections
                approvals = sum(1 for item in factor_history if item.get("decision") is True)
                rejections = sum(1 for item in factor_history if item.get("decision") is False)
                
                # Calculate impact score (percentage difference)
                impact_score = 0
                if occurrences > 0:
                    impact_score = (approvals - rejections) / occurrences
                
                factor_analysis[decision_type][factor_key] = {
                    "occurrences": occurrences,
                    "approvals": approvals,
                    "rejections": rejections,
                    "impact_score": impact_score,
                    "history": factor_history
                }
        
        return {
            "application_id": application_id,
            "factor_analysis": factor_analysis,
            "generated_at": datetime.utcnow().isoformat()
        }