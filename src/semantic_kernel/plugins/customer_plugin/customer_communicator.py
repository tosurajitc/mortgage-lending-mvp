"""
Semantic Kernel plugin for customer communication.

This plugin provides functions for generating responses to customer inquiries,
creating status updates, and explaining mortgage concepts.
"""

import json
from typing import Dict, List, Any, Optional

import semantic_kernel as sk

from src.utils.logging_utils import get_logger

logger = get_logger("semantic_kernel.plugins.customer")

class CustomerCommunicatorPlugin:
    """
    Plugin for generating customer communications.
    
    Provides functions for creating personalized responses to customer inquiries,
    generating status updates, and explaining mortgage concepts in clear language.
    """
    
    def __init__(self, kernel: Optional[sk.Kernel] = None):
        """
        Initialize the customer communicator plugin.
        
        Args:
            kernel: Optional Semantic Kernel instance
        """
        self.kernel = kernel
        self.logger = logger
        
        # Common mortgage terms and concepts for explanations
        self.mortgage_concepts = {
            "apr": "Annual Percentage Rate - The yearly cost of a mortgage including interest and fees",
            "piti": "Principal, Interest, Taxes, Insurance - The four components of a mortgage payment",
            "escrow": "An account where funds are held for taxes and insurance payments",
            "ltv": "Loan-to-Value ratio - The ratio of the loan amount to the appraised property value",
            "dti": "Debt-to-Income ratio - The percentage of monthly income that goes toward debt payments",
            "pmi": "Private Mortgage Insurance - Insurance required for conventional loans with less than 20% down payment",
            "amortization": "The process of paying off a loan through regular payments of principal and interest",
            "rate_lock": "A commitment by a lender to hold a certain interest rate for a specified period",
            "points": "Fees paid to reduce the interest rate on a mortgage",
            "underwriting": "The process of evaluating a loan application to determine lending risk",
            "closing_costs": "Fees paid at the closing of a real estate transaction",
            "pre_approval": "A preliminary evaluation of a borrower's ability to qualify for a loan",
            "pre_qualification": "An estimate of how much a borrower might be eligible to borrow",
            "refinance": "The process of replacing an existing mortgage with a new one, often to secure a lower rate",
            "heloc": "Home Equity Line of Credit - A line of credit secured by home equity",
            "arm": "Adjustable Rate Mortgage - A mortgage with an interest rate that changes periodically",
            "fixed_rate": "A mortgage with an interest rate that remains the same for the entire term",
            "jumbo_loan": "A mortgage that exceeds the conforming loan limits set by Fannie Mae and Freddie Mac",
            "fha_loan": "A mortgage insured by the Federal Housing Administration",
            "va_loan": "A mortgage guaranteed by the Department of Veterans Affairs"
        }
    
    @sk_function(
        description="Generate a personalized response to a customer inquiry",
        name="respondToInquiry"
    )
    @sk_function_context_parameter(
        name="customer_name",
        description="Name of the customer"
    )
    @sk_function_context_parameter(
        name="inquiry_text",
        description="Text of the customer's inquiry"
    )
    @sk_function_context_parameter(
        name="application_data",
        description="JSON string containing the relevant application data (optional)"
    )
    def respond_to_inquiry(self, context: sk.SKContext) -> str:
        """
        Generate a personalized response to a customer inquiry.
        
        Args:
            context: Semantic Kernel context with customer information and inquiry
            
        Returns:
            Personalized response text
        """
        customer_name = context["customer_name"]
        inquiry_text = context["inquiry_text"]
        application_data = json.loads(context.get("application_data", "{}"))
        
        # Log the inquiry
        self.logger.info(f"Generating response for {customer_name}'s inquiry: {inquiry_text[:50]}...")
        
        # Parse the inquiry to determine the type
        inquiry_type = self._categorize_inquiry(inquiry_text)
        
        # Generate an appropriate response based on the inquiry type
        if inquiry_type == "status_update":
            return self._generate_status_update(customer_name, application_data)
        elif inquiry_type == "document_question":
            return self._generate_document_response(customer_name, inquiry_text, application_data)
        elif inquiry_type == "timeline_question":
            return self._generate_timeline_response(customer_name, inquiry_text, application_data)
        elif inquiry_type == "term_explanation":
            term = self._extract_mortgage_term(inquiry_text)
            return self._explain_mortgage_term(customer_name, term)
        elif inquiry_type == "rate_question":
            return self._generate_rate_response(customer_name, inquiry_text, application_data)
        else:
            # General response for other types of inquiries
            return self._generate_general_response(customer_name, inquiry_text, application_data)
    
    @sk_function(
        description="Generate a loan application status update",
        name="generateStatusUpdate"
    )
    @sk_function_context_parameter(
        name="customer_name",
        description="Name of the customer"
    )
    @sk_function_context_parameter(
        name="application_data",
        description="JSON string containing the application data"
    )
    def generate_status_update(self, context: sk.SKContext) -> str:
        """
        Generate a status update for a loan application.
        
        Args:
            context: Semantic Kernel context with customer and application data
            
        Returns:
            Status update text
        """
        customer_name = context["customer_name"]
        application_data = json.loads(context["application_data"])
        
        return self._generate_status_update(customer_name, application_data)
    
    @sk_function(
        description="Explain a mortgage term or concept in simple language",
        name="explainMortgageTerm"
    )
    @sk_function_context_parameter(
        name="term",
        description="The mortgage term or concept to explain"
    )
    @sk_function_context_parameter(
        name="customer_name",
        description="Name of the customer (optional)"
    )
    def explain_mortgage_term(self, context: sk.SKContext) -> str:
        """
        Explain a mortgage term or concept in simple language.
        
        Args:
            context: Semantic Kernel context with the term to explain
            
        Returns:
            Clear explanation of the mortgage term
        """
        term = context["term"].lower()
        customer_name = context.get("customer_name", "")
        
        return self._explain_mortgage_term(customer_name, term)
    
    @sk_function(
        description="Generate a customized loan application checklist",
        name="generateApplicationChecklist"
    )
    @sk_function_context_parameter(
        name="customer_name",
        description="Name of the customer"
    )
    @sk_function_context_parameter(
        name="loan_type",
        description="Type of mortgage loan (e.g., Conventional, FHA, VA)"
    )
    @sk_function_context_parameter(
        name="loan_purpose",
        description="Purpose of the loan (e.g., Purchase, Refinance)"
    )
    def generate_application_checklist(self, context: sk.SKContext) -> str:
        """
        Generate a customized checklist for a loan application.
        
        Args:
            context: Semantic Kernel context with customer and loan information
            
        Returns:
            Customized application checklist
        """
        customer_name = context["customer_name"]
        loan_type = context["loan_type"]
        loan_purpose = context["loan_purpose"]
        
        # Base checklist items for all loan types
        checklist = [
            "Government-issued ID (driver's license, passport, etc.)",
            "Social Security number",
            "Proof of income (pay stubs for the last 30 days)",
            "W-2 forms for the past two years",
            "Federal tax returns for the past two years",
            "Bank statements for the past two months",
            "Proof of other assets (retirement accounts, investments)",
            "List of current debts (credit cards, loans, etc.)",
            "Contact information for employers (past two years)"
        ]
        
        # Add loan type specific items
        if loan_type.lower() == "conventional":
            if loan_purpose.lower() == "purchase":
                checklist.extend([
                    "Proof of down payment funds",
                    "Purchase agreement or contract",
                    "Contact information for real estate agent"
                ])
            elif loan_purpose.lower() == "refinance":
                checklist.extend([
                    "Current mortgage statement",
                    "Homeowners insurance policy",
                    "Property tax statements"
                ])
        elif loan_type.lower() == "fha":
            checklist.extend([
                "FHA case number (if already assigned)",
                "Proof of down payment funds (minimum 3.5%)",
                "Gift letter (if using gift funds for down payment)"
            ])
        elif loan_type.lower() == "va":
            checklist.extend([
                "Certificate of Eligibility (COE)",
                "DD-214 for veterans",
                "Statement of Service for active duty"
            ])
        
        # Format the checklist
        header = f"# Mortgage Application Checklist for {customer_name}\n\n"
        header += f"Loan Type: {loan_type}\n"
        header += f"Purpose: {loan_purpose}\n\n"
        header += "Please provide the following documents to complete your application:\n\n"
        
        formatted_checklist = header
        for i, item in enumerate(checklist, 1):
            formatted_checklist += f"{i}. {item}\n"
        
        formatted_checklist += "\nNote: Additional documents may be requested during the underwriting process. All documents should be recent (within 60 days of submission)."
        
        return formatted_checklist
    
    @sk_function(
        description="Notify customer about missing or incomplete documents",
        name="notifyMissingDocuments"
    )
    @sk_function_context_parameter(
        name="customer_name",
        description="Name of the customer"
    )
    @sk_function_context_parameter(
        name="missing_documents",
        description="JSON array of missing document descriptions"
    )
    @sk_function_context_parameter(
        name="deadline_days",
        description="Number of days to submit the documents"
    )
    def notify_missing_documents(self, context: sk.SKContext) -> str:
        """
        Generate a notification about missing or incomplete documents.
        
        Args:
            context: Semantic Kernel context with customer and missing document information
            
        Returns:
            Notification message about missing documents
        """
        customer_name = context["customer_name"]
        missing_documents = json.loads(context["missing_documents"])
        deadline_days = int(context["deadline_days"])
        
        # Generate a personalized notification
        greeting = f"Dear {customer_name},\n\n"
        
        introduction = "Thank you for your mortgage application. To continue processing your application, " 
        introduction += "we need the following document(s) that are either missing or incomplete:\n\n"
        
        document_list = ""
        for i, doc in enumerate(missing_documents, 1):
            document_list += f"{i}. {doc}\n"
        
        deadline_text = f"\nPlease provide these documents within the next {deadline_days} business days "
        deadline_text += "to avoid delays in processing your application. You can submit them through our secure portal or by contacting your loan officer directly.\n\n"
        
        closing = "If you have any questions or need assistance with these documents, please don't hesitate to contact us.\n\n"
        closing += "Thank you for your prompt attention to this matter.\n\n"
        closing += "Sincerely,\nYour Mortgage Team"
        
        return greeting + introduction + document_list + deadline_text + closing
    
    @sk_function(
        description="Explain a specific step in the mortgage process",
        name="explainMortgageStep"
    )
    @sk_function_context_parameter(
        name="step_name",
        description="Name of the mortgage process step to explain"
    )
    @sk_function_context_parameter(
        name="customer_name",
        description="Name of the customer (optional)"
    )
    def explain_mortgage_step(self, context: sk.SKContext) -> str:
        """
        Explain a specific step in the mortgage process.
        
        Args:
            context: Semantic Kernel context with the step to explain
            
        Returns:
            Clear explanation of the mortgage process step
        """
        step_name = context["step_name"].lower()
        customer_name = context.get("customer_name", "")
        
        # Define explanations for common mortgage process steps
        step_explanations = {
            "pre-qualification": (
                "Pre-qualification is the initial step where a lender provides an estimate of how much you might be able to borrow. "
                "It's based on information you provide about your income, assets, and debts. "
                "Pre-qualification is usually quick and doesn't involve a detailed look at your financial history."
            ),
            "pre-approval": (
                "Pre-approval is a more thorough evaluation of your finances. "
                "The lender will verify your income, assets, and credit history. "
                "Pre-approval gives you a specific loan amount and shows sellers you're a serious buyer. "
                "It typically involves completing a mortgage application and providing financial documentation."
            ),
            "application": (
                "The application step involves completing a full mortgage application with a lender. "
                "You'll provide detailed information about your finances, employment history, and the property. "
                "This is where you'll specify the loan type, term, and other preferences. "
                "After submission, the lender will provide a Loan Estimate within three business days."
            ),
            "processing": (
                "Processing begins after your application is submitted. "
                "A loan processor reviews your application and supporting documents, "
                "orders necessary reports (credit, title, appraisal), and prepares your file for underwriting. "
                "They may request additional documentation to complete your file."
            ),
            "underwriting": (
                "Underwriting is where a lender's underwriter evaluates your application to determine lending risk. "
                "They assess your credit history, income stability, debt levels, and the property's value. "
                "The underwriter makes the final decision on whether to approve your loan, "
                "and may issue conditional approval pending specific requirements."
            ),
            "conditional approval": (
                "Conditional approval means your loan is approved provided certain conditions are met. "
                "These conditions might include additional documentation, explanation of credit issues, "
                "or property-related requirements. "
                "Your loan officer will guide you through satisfying these conditions."
            ),
            "closing disclosure": (
                "The Closing Disclosure is a five-page form that provides the final details of your mortgage loan. "
                "It includes the loan terms, projected monthly payments, and closing costs. "
                "By law, you must receive this document at least three business days before closing, "
                "giving you time to review the final terms of your loan."
            ),
            "closing": (
                "Closing (or settlement) is the final step in the mortgage process. "
                "You'll sign the final loan documents, pay closing costs, and the property officially becomes yours. "
                "Typically, all parties meet with a closing agent to complete the necessary paperwork. "
                "After closing, the loan is funded and ownership of the property is transferred."
            ),
            "rate lock": (
                "A rate lock is a lender's commitment to hold a specific interest rate for a set period, "
                "typically 30, 45, or 60 days. "
                "This protects you from rate increases during the loan processing period. "
                "Some rate locks may have fees or require float-down options for rate decreases."
            ),
            "appraisal": (
                "An appraisal is an independent evaluation of a property's value. "
                "A licensed appraiser inspects the property and compares it to similar properties that recently sold. "
                "Lenders require appraisals to ensure the property is worth at least the loan amount. "
                "The appraisal fee is typically paid by the borrower as part of closing costs."
            )
        }
        
        # Generate an explanation for the requested step
        if step_name in step_explanations:
            explanation = step_explanations[step_name]
            
            if customer_name:
                return f"Hi {customer_name},\n\n{explanation}\n\nIs there anything specific about this step you'd like to know more about?"
            else:
                return explanation
        else:
            # If the step isn't found, provide a general response
            if customer_name:
                return f"Hi {customer_name},\n\nI don't have specific information about the '{context['step_name']}' step. Would you like me to explain a different part of the mortgage process, or can I help with something else?"
            else:
                return f"I don't have specific information about the '{context['step_name']}' step. Would you like me to explain a different part of the mortgage process, or can I help with something else?"
    
    # Helper methods
    def _categorize_inquiry(self, inquiry_text: str) -> str:
        """Categorize the type of customer inquiry."""
        inquiry_lower = inquiry_text.lower()
        
        # Check for status update requests
        if any(phrase in inquiry_lower for phrase in [
            "status", "update", "progress", "where is", "how is", "what's happening"
        ]):
            return "status_update"
        
        # Check for document questions
        if any(phrase in inquiry_lower for phrase in [
            "document", "paperwork", "upload", "submit", "send", "form", "proof", "statement"
        ]):
            return "document_question"
        
        # Check for timeline questions
        if any(phrase in inquiry_lower for phrase in [
            "how long", "when will", "timeline", "time frame", "schedule", "next step", "process"
        ]):
            return "timeline_question"
        
        # Check for term explanation requests
        if any(phrase in inquiry_lower for phrase in [
            "what is", "what does", "explain", "mean", "definition", "understand"
        ]):
            return "term_explanation"
        
        # Check for rate questions
        if any(phrase in inquiry_lower for phrase in [
            "rate", "interest", "apr", "percentage", "points", "lock"
        ]):
            return "rate_question"
        
        # Default to general inquiry
        return "general_inquiry"
    
    def _extract_mortgage_term(self, inquiry_text: str) -> str:
        """Extract the mortgage term being asked about."""
        inquiry_lower = inquiry_text.lower()
        
        # Check for specific terms in the inquiry
        for term in self.mortgage_concepts.keys():
            if term in inquiry_lower or term.replace("_", " ") in inquiry_lower:
                return term
        
        # Check for phrases like "what is X" or "explain X"
        explanation_patterns = [
            r"what\s+(?:is|are)\s+(?:the|a|an)?\s+([a-z\s]+)",
            r"explain\s+(?:the|a|an)?\s+([a-z\s]+)",
            r"meaning\s+of\s+([a-z\s]+)",
            r"define\s+([a-z\s]+)"
        ]
        
        for pattern in explanation_patterns:
            matches = re.search(pattern, inquiry_lower)
            if matches:
                term = matches.group(1).strip()
                # Check if extracted term is close to any known term
                for known_term in self.mortgage_concepts.keys():
                    if known_term in term or known_term.replace("_", " ") in term:
                        return known_term
        
        # Default to a general term if nothing specific is found
        return "general"
    
    def _explain_mortgage_term(self, customer_name: str, term: str) -> str:
        """Generate an explanation for a mortgage term."""
        # Get the explanation for the term
        if term in self.mortgage_concepts:
            explanation = self.mortgage_concepts[term]
        else:
            # For terms not in our dictionary, provide a general response
            explanation = "I don't have a specific definition for that term in my database. I'd recommend asking your loan officer for clarification."
        
        # Format the response
        if customer_name:
            greeting = f"Hi {customer_name},\n\n"
        else:
            greeting = ""
        
        if term != "general":
            term_formatted = term.replace("_", " ").upper()
            response = f"{greeting}{term_formatted}: {explanation}\n\nIs there anything else you'd like to know?"
        else:
            response = f"{greeting}I'm not sure which mortgage term you're asking about. Could you please specify the term you'd like me to explain?"
        
        return response
    
    def _generate_status_update(self, customer_name: str, application_data: Dict[str, Any]) -> str:
        """Generate a status update for a loan application."""
        # Extract status information from application data
        application_id = application_data.get("application_id", "your application")
        current_status = application_data.get("status", "under review")
        submission_date = application_data.get("submission_date", "recently")
        
        # Extract next steps information if available
        next_steps = application_data.get("next_steps", [])
        pending_items = application_data.get("pending_items", [])
        
        # Format the status update
        greeting = f"Hi {customer_name},\n\n"
        
        status_info = f"Your mortgage application ({application_id}) submitted on {submission_date} is currently {current_status}. "
        
        if current_status.lower() == "approved":
            status_info += "Congratulations! Your loan officer will be in touch soon to discuss the next steps in the closing process."
        elif current_status.lower() == "denied":
            status_info += "We regret to inform you that your application was not approved. Your loan officer will contact you to discuss the reasons and potential options."
        elif current_status.lower() == "conditionally approved":
            status_info += "Your application has been conditionally approved. This means we need some additional information before giving final approval."
        else:
            status_info += "Our team is actively working on your application."
        
        next_steps_text = ""
        if next_steps:
            next_steps_text += "\n\nNext steps in your application process:\n"
            for i, step in enumerate(next_steps, 1):
                next_steps_text += f"{i}. {step}\n"
        
        pending_items_text = ""
        if pending_items:
            pending_items_text += "\nWe're currently waiting for the following items:\n"
            for i, item in enumerate(pending_items, 1):
                pending_items_text += f"{i}. {item}\n"
            pending_items_text += "\nProviding these items promptly will help avoid delays in processing your application."
        
        closing = "\nIf you have any questions or need assistance, please don't hesitate to contact your loan officer."
        
        return greeting + status_info + next_steps_text + pending_items_text + closing
    
    def _generate_document_response(self, customer_name: str, inquiry_text: str, application_data: Dict[str, Any]) -> str:
        """Generate a response to a document-related inquiry."""
        # Extract document information from application data
        required_documents = application_data.get("required_documents", [])
        submitted_documents = application_data.get("submitted_documents", [])
        pending_documents = application_data.get("pending_documents", [])
        
        # Format the response
        greeting = f"Hi {customer_name},\n\n"
        
        # Try to determine the specific document question
        inquiry_lower = inquiry_text.lower()
        
        if "submit" in inquiry_lower or "upload" in inquiry_lower or "send" in inquiry_lower:
            response = "You can submit documents through our secure online portal, by email to your loan officer, or in person at any of our branch locations. "
            response += "For the online portal, you'll need your application ID and the password you created when you applied."
        elif "required" in inquiry_lower or "need" in inquiry_lower or "what" in inquiry_lower:
            if required_documents:
                response = "For your mortgage application, we need the following documents:\n\n"
                for i, doc in enumerate(required_documents, 1):
                    response += f"{i}. {doc}\n"
            else:
                response = "Your loan officer will provide you with a specific list of required documents based on your loan type and circumstances. "
                response += "Common documents include proof of income, tax returns, bank statements, and identification."
        elif "received" in inquiry_lower or "got" in inquiry_lower:
            if submitted_documents:
                response = "We have received the following documents from you:\n\n"
                for i, doc in enumerate(submitted_documents, 1):
                    response += f"{i}. {doc}\n"
                
                if pending_documents:
                    response += "\nWe're still waiting for:\n\n"
                    for i, doc in enumerate(pending_documents, 1):
                        response += f"{i}. {doc}\n"
            else:
                response = "I don't see any documents recorded as received in your file. "
                response += "If you've recently submitted documents, they may still be processing."
        else:
            # General document response
            response = "For document questions, I recommend contacting your loan officer directly. "
            response += "They can provide the most up-to-date information about your specific document requirements and submission status."
        
        closing = "\n\nIs there anything else I can help with regarding your documents?"
        
        return greeting + response + closing
    
    def _generate_timeline_response(self, customer_name: str, inquiry_text: str, application_data: Dict[str, Any]) -> str:
        """Generate a response to a timeline-related inquiry."""
        # Extract timeline information from application data
        current_stage = application_data.get("current_stage", "processing")
        submission_date = application_data.get("submission_date", "recently")
        estimated_completion = application_data.get("estimated_completion", "")
        
        # Format the response
        greeting = f"Hi {customer_name},\n\n"
        
        # Generate timeline information based on current stage
        stage_timelines = {
            "application": "The application stage typically takes 1-3 days.",
            "processing": "The processing stage typically takes 1-2 weeks.",
            "underwriting": "The underwriting stage typically takes 1-2 weeks.",
            "conditional approval": "Addressing conditions typically takes 1-2 weeks, depending on how quickly you can provide the requested information.",
            "clear to close": "Once clear to close is issued, closing can happen within a few days to a week.",
            "closing scheduled": "Your closing is scheduled! Your loan officer will confirm the exact date and time.",
            "closed": "Congratulations! Your loan has been closed and funded."
        }
        
        inquiry_lower = inquiry_text.lower()
        
        if "how long" in inquiry_lower or "timeline" in inquiry_lower or "time frame" in inquiry_lower:
            response = f"Your application was submitted on {submission_date} and is currently in the {current_stage} stage. "
            
            if current_stage.lower() in stage_timelines:
                response += stage_timelines[current_stage.lower()] + " "
            
            if estimated_completion:
                response += f"Based on current processing times, we estimate completion by {estimated_completion}."
            else:
                response += "The total mortgage process typically takes 30-45 days from application to closing, but this can vary based on complexity and current volume."
        elif "next step" in inquiry_lower:
            # Map current stage to next stage
            stage_progression = {
                "application": "processing",
                "processing": "underwriting",
                "underwriting": "conditional approval",
                "conditional approval": "clear to close",
                "clear to close": "closing scheduled",
                "closing scheduled": "closing"
            }
            
            next_stage = stage_progression.get(current_stage.lower(), "")
            
            if next_stage:
                response = f"You're currently in the {current_stage} stage. The next step will be {next_stage}. "
                if next_stage.lower() in stage_timelines:
                    response += stage_timelines[next_stage.lower()]
            else:
                response = f"You're currently in the {current_stage} stage. Your loan officer can provide you with specific information about what to expect next."
        else:
            # General timeline response
            response = f"Your application is currently in the {current_stage} stage. "
            response += "The mortgage process typically includes application, processing, underwriting, conditional approval, clear to close, and closing. "
            response += "The total timeline is usually 30-45 days, but can vary based on your specific circumstances and current processing volumes."
        
        closing = "\n\nIf you need a more specific timeline, please contact your loan officer directly."
        
        return greeting + response + closing
    
    def _generate_rate_response(self, customer_name: str, inquiry_text: str, application_data: Dict[str, Any]) -> str:
        """Generate a response to an interest rate inquiry."""
        # Extract rate information from application data
        interest_rate = application_data.get("interest_rate", "")
        apr = application_data.get("apr", "")
        rate_lock = application_data.get("rate_lock", {})
        rate_lock_date = rate_lock.get("date", "")
        rate_lock_expiration = rate_lock.get("expiration", "")
        rate_lock_status = rate_lock.get("status", "")
        
        # Format the response
        greeting = f"Hi {customer_name},\n\n"
        
        inquiry_lower = inquiry_text.lower()
        
        if "my rate" in inquiry_lower or "interest rate" in inquiry_lower:
            if interest_rate:
                response = f"Your current interest rate is {interest_rate}%. "
                if apr:
                    response += f"The Annual Percentage Rate (APR) is {apr}%. "
                    
                if rate_lock_status:
                    if rate_lock_status.lower() == "locked":
                        response += f"Your rate is locked until {rate_lock_expiration}."
                    else:
                        response += "Your rate is currently floating (not locked)."
            else:
                response = "I don't see specific rate information in your application records. Please contact your loan officer for the most current rate information."
        elif "lock" in inquiry_lower:
            if rate_lock_status:
                if rate_lock_status.lower() == "locked":
                    response = f"Your rate is currently locked at {interest_rate}%. "
                    response += f"The rate lock was secured on {rate_lock_date} and expires on {rate_lock_expiration}."
                else:
                    response = "Your rate is not currently locked. Please contact your loan officer if you'd like to discuss locking your rate."
            else:
                response = "I don't see rate lock information in your application records. Please contact your loan officer to discuss rate lock options."
        elif "points" in inquiry_lower:
            points = application_data.get("points", "")
            if points:
                response = f"Your loan includes {points} points. Each point costs 1% of your loan amount and reduces your interest rate by approximately 0.25%."
            else:
                response = "I don't see information about points in your application records. Please contact your loan officer for details about points and how they"