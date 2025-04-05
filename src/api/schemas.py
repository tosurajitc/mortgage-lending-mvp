# schemas.py - Revised approach to avoid syntax errors

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, List, Any, Union
from datetime import datetime
from enum import Enum

# Base response class
class BaseResponse(BaseModel):
    success: bool = True
    message: str = "Operation completed successfully"
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

# Document type enum
class DocumentType(str, Enum):
    """Enum for document types - can be used for validation"""
    INCOME_VERIFICATION = "INCOME_VERIFICATION"
    CREDIT_REPORT = "CREDIT_REPORT"
    PROPERTY_APPRAISAL = "PROPERTY_APPRAISAL"
    BANK_STATEMENT = "BANK_STATEMENT"
    ID_VERIFICATION = "ID_VERIFICATION"
    TAX_RETURN = "TAX_RETURN"
    OTHER = "OTHER"

# Keep all your existing schemas unchanged
class UploadDocumentsSchema(BaseModel):
    applicationId: str
    documentType: str
    documentDescription: Optional[str] = None
    documentMetadata: Optional[Dict[str, str]] = None

class LoanTypeRecommendationSchema(BaseModel):
    annualIncome: float
    creditScoreRange: str
    downPaymentPercentage: float
    propertyType: str
    propertyValue: float

class LoanEligibilityCalculationsSchema(BaseModel):
    annualIncome: float
    creditScoreRange: str
    monthlyDebts: float
    employmentStatus: str
    propertyValue: float
    desiredLoanAmount: float

class ResolveMortgageIssuesSchema(BaseModel):
    applicationId: str
    issueType: str
    issueDescription: str
    supportingDocuments: Optional[List[str]] = None  # Assuming base64 encoded or file paths

class SubmitMortgageApplicationSchema(BaseModel):
    applicantName: str
    applicantEmail: str
    applicantPhone: str
    applicantAddress: str
    applicantSSN: str
    propertyType: str
    propertyAddress: str
    propertyValue: float
    loanAmount: float
    employmentStatus: str
    employmentType: str
    employmentLength: str
    annualIncome: float
    creditScoreRange: str
    existingMortgages: Optional[float] = None

class CheckApplicationStatusSchema(BaseModel):
    applicationId: str
    applicantName: str

# Add new schemas that are compatible with Copilot Studio - instead of extending
class CopilotUploadDocumentSchema(BaseModel):
    applicationId: str
    documentType: str  # Can use as string for compatibility
    documentYear: Optional[str] = None
    documentDescription: Optional[str] = None
    documentFormat: str = "PDF"
    documentContent: Optional[str] = None  # For base64 encoded content

class CopilotLoanRecommendationSchema(BaseModel):
    annualIncome: float
    creditScoreRange: str
    downPaymentPercentage: float
    propertyType: str
    propertyValue: Optional[float] = None
    homeOwnershipPlans: Optional[str] = None
    militaryService: Optional[bool] = False
    propertyLocation: Optional[str] = None
    financialPriority: Optional[str] = None

class CopilotLoanEligibilitySchema(BaseModel):
    annualIncome: float
    monthlyDebts: float
    creditScoreRange: str
    employmentStatus: str
    propertyValue: Optional[float] = None
    downPaymentAmount: Optional[float] = None
    loanTermYears: int = 30
    propertyType: str = "SINGLE_FAMILY"
    propertyLocation: Optional[str] = None
    desiredLoanAmount: Optional[float] = None

class CopilotIssueResolutionSchema(BaseModel):
    applicationId: str
    issueType: str
    issueDescription: str
    contactPreference: str = "EMAIL"
    urgencyLevel: str = "MEDIUM"
    supportingDocuments: Optional[List[str]] = None

# Response models for Copilot Studio
class ApplicationStatusResponse(BaseModel):
    applicationId: str
    applicationStatus: str
    currentStage: str
    pendingItems: List[str] = []
    estimatedCompletion: str
    lastUpdated: str
    statusExplanation: str

class DocumentUploadResponse(BaseModel):
    applicationId: str
    uploadStatus: str
    documentType: str
    message: str
    nextSteps: List[str] = []

class LoanRecommendationResponse(BaseModel):
    recommendedLoanTypes: List[Dict[str, Any]]
    primaryRecommendation: str
    explanation: str
    eligibility: Dict[str, Any] = {}
    nextSteps: List[str] = []

class LoanEligibilityResponse(BaseModel):
    eligibilityStatus: str
    maximumLoanAmount: float
    estimatedMonthlyPayment: float
    eligibilityFactors: Dict[str, Any] = {}
    recommendedActions: List[str] = []
    affordabilityAnalysis: Dict[str, Any] = {}

class IssueResolutionResponse(BaseModel):
    applicationId: str
    caseNumber: str
    resolutionSteps: List[str]
    estimatedResolutionTime: str
    message: str

class CopilotUserInputRequest(BaseModel):
    userInput: str
    sessionId: Optional[str] = None
    context: Optional[Dict[str, Any]] = {}

class CopilotUserInputResponse(BaseModel):
    response: str
    context: Dict[str, Any] = {}
    nextActions: List[str] = []
    requiredInfo: List[str] = []
    sessionId: str
    error: Optional[str] = None