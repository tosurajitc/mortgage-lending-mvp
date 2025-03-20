"""
Data models for the Mortgage Lending Assistant.

This module defines the core data structures used throughout the application,
including mortgage applications, documents, and processing results.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import uuid


class ApplicationStatus(str, Enum):
    """Status of a mortgage application."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    DOCUMENT_REVIEW = "document_review"
    UNDERWRITING = "underwriting"
    COMPLIANCE_REVIEW = "compliance_review"
    DECISION_PENDING = "decision_pending"
    APPROVED = "approved"
    DENIED = "denied"
    CANCELLED = "cancelled"


class DocumentType(str, Enum):
    """Types of documents that can be submitted with a mortgage application."""
    W2_FORM = "w2_form"
    PAY_STUB = "pay_stub"
    BANK_STATEMENT = "bank_statement"
    TAX_RETURN = "tax_return"
    CREDIT_REPORT = "credit_report"
    PROPERTY_APPRAISAL = "property_appraisal"
    IDENTITY_DOCUMENT = "identity_document"
    OTHER = "other"


class DecisionOutcome(str, Enum):
    """Possible outcomes for a mortgage application decision."""
    APPROVED = "approved"
    CONDITIONALLY_APPROVED = "conditionally_approved"
    DENIED = "denied"
    NEEDS_MORE_INFO = "needs_more_info"
    MANUAL_REVIEW = "manual_review"


@dataclass
class Address:
    """Physical address information."""
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"


@dataclass
class Applicant:
    """Information about a mortgage applicant."""
    first_name: str
    last_name: str
    email: str
    phone: str
    date_of_birth: str
    ssn_last_four: str
    address: Address
    employment_status: str
    employer_name: Optional[str] = None
    years_at_current_job: Optional[float] = None
    annual_income: Optional[float] = None
    credit_score: Optional[int] = None


@dataclass
class Property:
    """Information about the property being mortgaged."""
    address: Address
    property_type: str
    estimated_value: float
    year_built: Optional[int] = None
    square_footage: Optional[int] = None


@dataclass
class LoanDetails:
    """Details about the requested mortgage loan."""
    loan_amount: float
    loan_term_years: int
    interest_rate: Optional[float] = None
    loan_type: str = "conventional"
    down_payment: Optional[float] = None
    is_first_time_homebuyer: bool = False


@dataclass
class Document:
    """A document associated with a mortgage application."""
    document_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    document_type: DocumentType
    file_name: str
    upload_date: datetime = field(default_factory=datetime.utcnow)
    content_type: str
    file_size: int
    status: str = "pending_review"
    metadata: Dict[str, Any] = field(default_factory=dict)
    extracted_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FinancialAnalysis:
    """Results of financial analysis on a mortgage application."""
    debt_to_income_ratio: Optional[float] = None
    loan_to_value_ratio: Optional[float] = None
    front_end_ratio: Optional[float] = None
    back_end_ratio: Optional[float] = None
    income_stability_score: Optional[float] = None
    affordability_score: Optional[float] = None
    risk_factors: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)


@dataclass
class ComplianceCheck:
    """Results of compliance checks on a mortgage application."""
    passed: bool = False
    regulation_sets_checked: List[str] = field(default_factory=list)
    issues_found: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class Decision:
    """A decision on a mortgage application."""
    outcome: DecisionOutcome
    interest_rate: Optional[float] = None
    loan_amount_approved: Optional[float] = None
    conditions: List[str] = field(default_factory=list)
    denial_reasons: List[str] = field(default_factory=list)
    decision_date: datetime = field(default_factory=datetime.utcnow)
    decision_maker: str = "automated"
    explanation: str = ""
    confidence_score: Optional[float] = None


@dataclass
class MortgageApplication:
    """A complete mortgage application."""
    application_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: ApplicationStatus = ApplicationStatus.DRAFT
    creation_date: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    # Core application data
    primary_applicant: Optional[Applicant] = None
    co_applicant: Optional[Applicant] = None
    property_info: Optional[Property] = None
    loan_details: Optional[LoanDetails] = None
    
    # Processing data
    documents: List[Document] = field(default_factory=list)
    financial_analysis: Optional[FinancialAnalysis] = None
    compliance_check: Optional[ComplianceCheck] = None
    decision: Optional[Decision] = None
    
    # Additional information
    notes: List[Dict[str, Any]] = field(default_factory=list)
    agent_interactions: List[Dict[str, Any]] = field(default_factory=list)
    
    def update_status(self, new_status: ApplicationStatus) -> None:
        """Update the application status and last_updated timestamp."""
        self.status = new_status
        self.last_updated = datetime.utcnow()
        
    def add_document(self, document: Document) -> None:
        """Add a new document to the application."""
        self.documents.append(document)
        self.last_updated = datetime.utcnow()
        
    def add_note(self, author: str, content: str) -> None:
        """Add a note to the application."""
        self.notes.append({
            "author": author,
            "content": content,
            "timestamp": datetime.utcnow()
        })
        self.last_updated = datetime.utcnow()
        
    def record_agent_interaction(self, agent_type: str, action: str, details: Dict[str, Any]) -> None:
        """Record an interaction with an agent."""
        self.agent_interactions.append({
            "agent_type": agent_type,
            "action": action,
            "details": details,
            "timestamp": datetime.utcnow()
        })
        self.last_updated = datetime.utcnow()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the application to a dictionary for storage."""
        # Implementation would convert all nested dataclasses to dictionaries
        # This is a placeholder for the actual implementation
        return {
            "application_id": self.application_id,
            "status": self.status.value,
            "creation_date": self.creation_date.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            # Other fields would be converted here
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MortgageApplication':
        """Create an application from a dictionary."""
        # Implementation would convert dictionary back to nested dataclasses
        # This is a placeholder for the actual implementation
        application = cls(
            application_id=data.get("application_id", str(uuid.uuid4())),
            status=ApplicationStatus(data.get("status", ApplicationStatus.DRAFT.value)),
            creation_date=datetime.fromisoformat(data.get("creation_date", datetime.utcnow().isoformat())),
            last_updated=datetime.fromisoformat(data.get("last_updated", datetime.utcnow().isoformat())),
            # Other fields would be converted here
        )
        return application