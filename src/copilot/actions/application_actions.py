# src/copilot/actions/application_actions.py
from ...agents.orchestrator import OrchestratorAgent
from datetime import datetime
import logging
import uuid
from fastapi import HTTPException
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Outputs to console
        logging.FileHandler('application.log')  # Outputs to a file
    ]
)

class ApplicationActions:
    def __init__(self):
        self.orchestrator = OrchestratorAgent()
        self.logger = logging.getLogger(__name__)
    

    async def submit_application(self, 
            applicantName, 
            applicantEmail, 
            applicantPhone, 
            applicantAddress, 
            applicantSSN, 
            propertyType, 
            propertyAddress, 
            propertyValue, 
            loanAmount, 
            employmentStatus, 
            employmentType, 
            employmentLength, 
            annualIncome, 
            creditScoreRange, 
            existingMortgages=None
        ):
        try:
            # Comprehensive input validation
            required_params = [
                applicantName, applicantEmail, applicantPhone, 
                applicantAddress, applicantSSN, propertyType, 
                propertyAddress, propertyValue, loanAmount, 
                employmentStatus, employmentType, employmentLength, 
                annualIncome, creditScoreRange
            ]
            
            if any(param is None or param == '' for param in required_params):
                logger.warning("Missing required parameters")
                return {
                    "status": "ERROR",
                    "message": "All parameters are required. Please provide complete information."
                }

            # Restructure data to match existing method
            applicant_data = {
                "name": applicantName,
                "email": applicantEmail,
                "phone": applicantPhone,
                "address": applicantAddress,
                "ssn": applicantSSN,
                "income": annualIncome,
                "credit_score_range": creditScoreRange,
                "employment": {
                    "status": employmentStatus,
                    "type": employmentType,
                    "length": employmentLength
                }
            }
            
            property_info = {
                "type": propertyType,
                "address": propertyAddress,
                "value": propertyValue
            }
            
            loan_details = {
                "amount": loanAmount,
                "existing_mortgages": existingMortgages
            }
            
            # Initialize empty documents list
            documents = []
            
            # Create a unique application ID
            application_id = f"APP-{datetime.now().strftime('%Y%m%d')}-{applicantName.split()[-1].upper()}"
            
            # Prepare input data for orchestrator
            input_data = {
                "action": "process_application",
                "application_id": application_id,
                "application_data": {
                    "applicant": applicant_data,
                    "loan": loan_details,
                    "property": property_info
                },
                "documents": documents
            }
            
            # Log the input data for tracking
            logger.info(f"Submitting application: {application_id}")
            logger.info(f"Application input data: {input_data}")
            
            # Process the application
            try:
                result = await self.orchestrator.process(input_data)
                
                # Additional logging for successful submission
                logger.info(f"Application {application_id} processed successfully")
                
                return {
                    "applicationId": result.get('application_id', str(uuid.uuid4())),
                    "applicationStatus": result.get('status', 'INITIATED'),
                    "nextSteps": result.get('next_steps', []),
                    "requiredDocuments": result.get('missing_documents', []),
                    "estimatedReviewTime": result.get('estimated_review_time', '1-2 business days')
                }
            
            except Exception as process_error:
                # Log any errors during processing
                logger.error(f"Error processing application {application_id}: {str(process_error)}")
                
                return {
                    "applicationId": application_id,
                    "applicationStatus": "ERROR",
                    "nextSteps": [],
                    "requiredDocuments": [],
                    "estimatedReviewTime": "Unable to determine"
                }
        
        except Exception as general_error:
            # Catch-all for any other unexpected errors
            logger.error(f"Unexpected error in application submission: {str(general_error)}")
            
            return {
                    "applicationId": str(uuid.uuid4()),
                    "applicationStatus": "ERROR",
                    "nextSteps": [],
                    "requiredDocuments": [],
                    "estimatedReviewTime": "Unable to determine"
                    }
        
        
    async def check_application_status(self, application_id, extra_context=None):
        """Check the status of an existing application"""
        return await self.orchestrator.get_application_status(application_id, extra_context)
    
    async def provide_additional_documents(self, application_id, document_type, document_content):
        """Add additional documents to an existing application"""
        return await self.orchestrator.add_document(
            application_id, document_type, document_content
        )
    
    async def recommend_loan_types(self, annual_income, credit_score_range, down_payment_percentage, 
                            property_type, homeownership_plans, military_service, 
                            property_location, financial_priority):
        """
        Recommend appropriate loan types based on applicant criteria.
        
        Args:
            annual_income: Annual income of the applicant
            credit_score_range: Credit score range of the applicant
            down_payment_percentage: Percentage of down payment available
            property_type: Type of property (SingleFamily, Condo, etc.)
            homeownership_plans: How long the applicant plans to own the home
            military_service: Military service status of the applicant
            property_location: Location type (Urban, Suburban, Rural)
            financial_priority: Applicant's top financial priority for the loan
            
        Returns:
            Dict containing recommended loan types and explanations
        """
        try:
            self.logger.info("Processing loan type recommendation request")
            
            # Convert credit score range to numeric estimate for calculations
            credit_score = self._estimate_credit_score(credit_score_range)
            
            # Initialize recommendations list
            recommended_loan_types = []
            eligibility = {}
            
            # Check VA loan eligibility
            va_eligible = self._check_va_eligibility(military_service)
            eligibility["VA"] = va_eligible
            
            # Check USDA loan eligibility
            usda_eligible = self._check_usda_eligibility(property_location, annual_income)
            eligibility["USDA"] = usda_eligible
            
            # Check FHA eligibility
            fha_eligible = credit_score >= 580 and annual_income > 0
            eligibility["FHA"] = fha_eligible
            
            # Check conventional loan eligibility
            conventional_eligible = credit_score >= 620
            eligibility["Conventional"] = conventional_eligible
            
            # Check jumbo loan eligibility (simplified)
            jumbo_eligible = credit_score >= 700 and annual_income >= 100000
            eligibility["Jumbo"] = jumbo_eligible
            
            # Determine recommendations based on eligibility and preferences
            
            # VA Loan recommendation
            if va_eligible:
                recommended_loan_types.append({
                    "loan_type": "VA Loan",
                    "benefits": [
                        "No down payment required",
                        "No private mortgage insurance",
                        "Competitive interest rates",
                        "Limited closing costs"
                    ],
                    "requirements": [
                        "Certificate of Eligibility (COE)",
                        "Sufficient income and credit for loan amount",
                        "Property must be primary residence"
                    ],
                    "match_score": self._calculate_match_score(
                        down_payment_percentage < 10,  # Good for low down payments
                        financial_priority == "LowestUpfrontCosts",
                        homeownership_plans == "LongTerm"
                    )
                })
            
            # USDA Loan recommendation
            if usda_eligible:
                recommended_loan_types.append({
                    "loan_type": "USDA Loan",
                    "benefits": [
                        "No down payment required",
                        "Lower mortgage insurance costs",
                        "Lower than market interest rates",
                        "Can finance closing costs"
                    ],
                    "requirements": [
                        "Property in eligible rural area",
                        "Income below 115% of area median",
                        "Property must be primary residence"
                    ],
                    "match_score": self._calculate_match_score(
                        down_payment_percentage < 10,  # Good for low down payments
                        property_location == "Rural",
                        financial_priority == "LowestMonthlyPayment"
                    )
                })
            
            # FHA Loan recommendation
            if fha_eligible:
                recommended_loan_types.append({
                    "loan_type": "FHA Loan",
                    "benefits": [
                        "Down payment as low as 3.5%",
                        "More flexible credit requirements",
                        "May allow higher debt-to-income ratios",
                        "Available for various property types"
                    ],
                    "requirements": [
                        "Minimum credit score of 580 for 3.5% down",
                        "Property must meet FHA standards",
                        "Mortgage insurance required"
                    ],
                    "match_score": self._calculate_match_score(
                        down_payment_percentage < 10,  # Good for low down payments
                        credit_score < 680,  # Better for lower credit scores
                        financial_priority == "LowestDownPayment"
                    )
                })
            
            # Conventional 97 Loan recommendation (for low down payment)
            if conventional_eligible and down_payment_percentage < 5:
                recommended_loan_types.append({
                    "loan_type": "Conventional 97",
                    "benefits": [
                        "Down payment as low as 3%",
                        "Private mortgage insurance is cancellable",
                        "More flexible property requirements",
                        "May have lower mortgage insurance than FHA"
                    ],
                    "requirements": [
                        "Minimum credit score of 620",
                        "First-time homebuyers preferred",
                        "Private mortgage insurance required",
                        "Maximum loan limits apply"
                    ],
                    "match_score": self._calculate_match_score(
                        down_payment_percentage < 5,  # Good for low down payments
                        homeownership_plans == "FirstTime",
                        credit_score >= 680  # Better for higher credit scores
                    )
                })
            
            # Standard Conventional Loan recommendation
            if conventional_eligible and down_payment_percentage >= 5:
                recommended_loan_types.append({
                    "loan_type": "Conventional Loan",
                    "benefits": [
                        "Flexible terms (15, 20, or 30 years)",
                        "No upfront mortgage insurance fee",
                        "PMI removable when equity reaches 20%",
                        "Lower mortgage insurance costs with higher down payment"
                    ],
                    "requirements": [
                        "Minimum credit score of 620",
                        "Down payment of at least 5%",
                        "PMI required if down payment under 20%"
                    ],
                    "match_score": self._calculate_match_score(
                        down_payment_percentage >= 10,  # Better with higher down payment
                        credit_score >= 700,  # Better for higher credit scores
                        financial_priority == "LowerInterestRate"
                    )
                })
            
            # Jumbo Loan recommendation
            if jumbo_eligible:
                recommended_loan_types.append({
                    "loan_type": "Jumbo Loan",
                    "benefits": [
                        "Allows borrowing above conforming loan limits",
                        "Competitive interest rates",
                        "Options for luxury or high-cost properties",
                        "Various term options available"
                    ],
                    "requirements": [
                        "Higher credit score requirements (usually 700+)",
                        "Larger down payment (often 10-20%)",
                        "More stringent debt-to-income requirements",
                        "Higher cash reserves needed"
                    ],
                    "match_score": self._calculate_match_score(
                        property_type in ["SingleFamily", "Luxury"],
                        credit_score >= 720,
                        annual_income >= 150000
                    )
                })
            
            # Sort recommendations by match score
            recommended_loan_types.sort(key=lambda x: x.get("match_score", 0), reverse=True)
            
            # Get primary recommendation
            primary_recommendation = recommended_loan_types[0]["loan_type"] if recommended_loan_types else "Conventional Loan"
            
            # Generate explanation based on criteria
            explanation = self._generate_recommendation_explanation(
                primary_recommendation,
                credit_score_range,
                down_payment_percentage,
                military_service,
                property_location,
                financial_priority
            )
            
            # Generate next steps
            next_steps = [
                "Complete a full mortgage application for detailed rates and terms",
                f"Gather documentation needed for {primary_recommendation}",
                "Speak with a mortgage specialist to discuss options in detail"
            ]
            
            # Return recommendations with explanation
            return {
                "recommended_loan_types": [loan["loan_type"] for loan in recommended_loan_types],
                "detailed_recommendations": recommended_loan_types,
                "primary_recommendation": primary_recommendation,
                "explanation": explanation,
                "eligibility": eligibility,
                "next_steps": next_steps
            }
            
        except Exception as e:
            self.logger.error(f"Error generating loan recommendations: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "recommended_loan_types": ["Conventional Loan"],  # Fallback recommendation
                "explanation": "Unable to provide personalized recommendations due to an error. Conventional loans are generally available to borrowers with good credit and stable income.",
                "next_steps": ["Speak with a mortgage specialist for personalized advice"]
            }

    # Helper methods
    def _estimate_credit_score(self, credit_score_range):
        """Convert credit score range to a numeric estimate"""
        if credit_score_range == "Excellent (750+)":
            return 750
        elif credit_score_range == "Good (700-749)":
            return 725
        elif credit_score_range == "Fair (650-699)":
            return 675
        elif credit_score_range == "Poor (below 650)":
            return 625
        else:
            return 680  # Default middle estimate

    def _check_va_eligibility(self, military_service):
        """Check if applicant is eligible for VA loan based on military service"""
        return military_service in ["Active", "Veteran", "Reserves", "NationalGuard"]

    def _check_usda_eligibility(self, property_location, annual_income):
        """Check if applicant is eligible for USDA loan based on location and income"""
        # Simplified check - in production would check against USDA eligible areas
        is_rural = property_location == "Rural"
        
        # Simplified income check - in production would check against area median income
        income_eligible = annual_income < 100000
        
        return is_rural and income_eligible

    def _calculate_match_score(self, *factors):
        """Calculate match score based on relevant factors (boolean values)"""
        # Simple scoring: each True factor adds points
        return sum(30 for factor in factors if factor)

    def _generate_recommendation_explanation(self, primary_recommendation, credit_score_range, 
                                        down_payment_percentage, military_service,
                                        property_location, financial_priority):
        """Generate personalized explanation for loan recommendations"""
        explanation = f"Based on your information, a {primary_recommendation} appears to be your best option. "
        
        # Add credit score context
        if credit_score_range == "Excellent (750+)":
            explanation += "Your excellent credit score qualifies you for the best loan terms available. "
        elif credit_score_range == "Good (700-749)":
            explanation += "Your good credit score gives you access to most loan types with competitive rates. "
        elif credit_score_range == "Fair (650-699)":
            explanation += "With your fair credit score, you still have several loan options, though rates may be slightly higher. "
        else:
            explanation += "Your credit score may limit some options, but programs like FHA loans are designed to help. "
        
        # Add down payment context
        if down_payment_percentage < 3.5:
            explanation += "With your limited down payment, VA or USDA loans could be ideal if you're eligible, otherwise FHA or Conventional 97 are worth exploring. "
        elif down_payment_percentage < 10:
            explanation += "Your down payment is enough for FHA loans and some conventional loans, which offer good flexibility. "
        elif down_payment_percentage < 20:
            explanation += "Your substantial down payment opens up conventional loans, though you'll still have mortgage insurance until reaching 20%. "
        else:
            explanation += "Your 20%+ down payment allows you to avoid mortgage insurance with conventional loans, saving on monthly payments. "
        
        # Add military service context
        if self._check_va_eligibility(military_service):
            explanation += "As someone eligible for VA benefits, a VA loan offers exceptional terms with no down payment required. "
        
        # Add location context
        if property_location == "Rural" and annual_income < 100000:
            explanation += "The rural location of your property might qualify you for a USDA loan with favorable terms. "
        
        # Add priority context
        if financial_priority == "LowestMonthlyPayment":
            explanation += "Since you're focused on the lowest monthly payment, a 30-year term would be most appropriate. "
        elif financial_priority == "LowestDownPayment":
            explanation += "Since minimizing your down payment is important, focus on loan types that require 3-3.5% down. "
        elif financial_priority == "LowestTotalCost":
            explanation += "To achieve the lowest total cost, consider a 15-year term if affordable, as you'll pay significantly less interest. "
        
        return explanation
    
    async def resolve_issue(self, application_id, issue_type, issue_description, contact_preference, urgency_level):
        """
        Handle resolution of issues for mortgage applications.
        
        Args:
            application_id: ID of the application
            issue_type: Type of issue (DocumentRejection, ApplicationDelay, etc.)
            issue_description: User description of the issue
            contact_preference: Preferred contact method (Email, Phone, etc.)
            urgency_level: Urgency level of the issue (High, Medium, Low)
            
        Returns:
            Dict containing case information and resolution steps
        """
        try:
            self.logger.info(f"Processing issue resolution for application {application_id}: {issue_type}")
            
            # Validate the application ID
            application = await self._get_application(application_id)
            if not application:
                return {
                    "error": f"Application {application_id} not found",
                    "message": "Could not find the specified application",
                    "resolution_steps": ["Verify your application ID and try again"]
                }
            
            # Generate a case number for tracking
            case_number = f"CASE-{application_id[:4]}-{self._generate_case_id()}"
            
            # Record the issue in the system
            await self._record_application_issue(
                application_id=application_id,
                case_number=case_number,
                issue_type=issue_type,
                issue_description=issue_description,
                contact_preference=contact_preference,
                urgency_level=urgency_level,
                status="OPEN"
            )
            
            # Get resolution steps based on issue type
            resolution_steps = self._get_resolution_steps(issue_type)
            
            # Get estimated resolution time based on issue type and urgency
            resolution_time = self._get_resolution_time(issue_type, urgency_level)
            
            # Set appropriate message based on contact preference
            message = self._get_contact_message(contact_preference, resolution_time)
            
            # If high urgency, trigger immediate notification to mortgage team
            if urgency_level == "High":
                await self._send_urgent_notification(
                    application_id=application_id,
                    case_number=case_number,
                    issue_type=issue_type,
                    issue_description=issue_description
                )
            
            # Return the response
            return {
                "case_number": case_number,
                "resolution_steps": resolution_steps,
                "estimated_resolution_time": resolution_time,
                "message": message
            }
            
        except Exception as e:
            self.logger.error(f"Error resolving application issue: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "message": "An error occurred while processing your issue",
                "resolution_steps": ["Please contact customer support directly"],
                "estimated_resolution_time": "Unknown due to error"
            }

    # Helper methods
    def _generate_case_id(self):
        """Generate a unique case ID"""
        import random
        import string
        import datetime
        
        # Get current date as MMDD format
        date_str = datetime.datetime.now().strftime("%m%d")
        
        # Generate 4 random characters
        random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        
        return f"{date_str}-{random_chars}"

    async def _record_application_issue(self, application_id, case_number, issue_type, 
                                    issue_description, contact_preference, urgency_level, status):
        """Record issue details in database"""
        # Implementation would depend on your data storage mechanism
        # For MVP, you might implement a simple in-memory storage or mock
        
        # Example implementation using cosmos_manager:
        from src.data.cosmos_manager import CosmosDBManager
        
        cosmos = CosmosDBManager()
        
        issue_data = {
            "id": case_number,
            "application_id": application_id,
            "issue_type": issue_type,
            "issue_description": issue_description,
            "contact_preference": contact_preference,
            "urgency_level": urgency_level,
            "status": status,
            "created_at": self._get_current_timestamp(),
            "updated_at": self._get_current_timestamp()
        }
        
        try:
            await cosmos.create_item("AuditLog", issue_data)
            return True
        except Exception as e:
            self.logger.error(f"Error recording application issue: {str(e)}", exc_info=True)
            return False

    def _get_resolution_steps(self, issue_type):
        """Get resolution steps based on issue type"""
        steps_map = {
            "DocumentRejection": [
                "Our team will review the document rejection reason",
                "You'll receive specific guidance on document requirements",
                "Submit a new document following the guidelines provided",
                "Check your application status for updates"
            ],
            "ApplicationDelay": [
                "Our team will identify the cause of the delay",
                "You'll be notified of any additional information needed",
                "We'll expedite processing once all requirements are met",
                "Check your application status for updates"
            ],
            "UnderwritingIssue": [
                "An underwriter will review your application in detail",
                "We'll contact you regarding any specific concerns",
                "You may need to provide additional documentation",
                "A mortgage specialist will guide you through any required steps"
            ],
            "TechnicalProblem": [
                "Our technical team will investigate the issue",
                "We'll notify you once the problem is resolved",
                "If necessary, we'll provide alternative submission methods",
                "Check your application status for updates"
            ]
        }
        
        # Return steps for the specific issue type, or generic steps if not found
        return steps_map.get(issue_type, [
            "A mortgage specialist will review your issue",
            "We'll contact you via your preferred method",
            "You may be asked to provide additional information",
            "Check your application status for updates"
        ])

    def _get_resolution_time(self, issue_type, urgency_level):
        """Get estimated resolution time based on issue type and urgency"""
        if urgency_level == "High":
            return "1-2 business days"
        
        time_map = {
            "DocumentRejection": "2-3 business days",
            "ApplicationDelay": "3-5 business days",
            "UnderwritingIssue": "3-5 business days",
            "TechnicalProblem": "1-2 business days"
        }
        
        return time_map.get(issue_type, "3-5 business days")

    def _get_contact_message(self, contact_preference, resolution_time):
        """Get appropriate message based on contact preference"""
        if contact_preference == "Email":
            return f"We'll email you with updates within {resolution_time}"
        elif contact_preference == "Phone":
            return f"A specialist will call you within {resolution_time}"
        elif contact_preference == "Text":
            return f"You'll receive text updates within {resolution_time}"
        else:
            return f"We'll contact you via your preferred method within {resolution_time}"

    async def _send_urgent_notification(self, application_id, case_number, issue_type, issue_description):
        """Send urgent notification to mortgage team"""
        # Implementation would depend on your notification system
        # For MVP, you might implement a simple logging mechanism
        
        self.logger.warning(
            f"URGENT ISSUE: Application {application_id}, Case {case_number}, "
            f"Type: {issue_type}, Description: {issue_description}"
        )
        
        # In a real implementation, this might send an email or Teams notification
        # to the mortgage team
        
        return True

    def _get_current_timestamp(self):
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat()

    async def _get_application(self, application_id):
        """Retrieve application from database"""
        # Implementation would depend on your data access layer
        # This would typically query your database for the application
        # For MVP, you might add a simple mock implementation
        return {"id": application_id, "status": "PROCESSING"}
    
    async def calculate_loan_eligibility(self, annual_income, monthly_debts, credit_score_range, 
                               employment_status, down_payment_amount, loan_term_years, 
                               property_type, property_location):
        """
        Calculate loan eligibility and maximum loan amount based on financial information.
        
        Args:
            annual_income: Annual income of the applicant
            monthly_debts: Monthly debt payments of the applicant
            credit_score_range: Credit score range of the applicant
            employment_status: Employment status (Employed, SelfEmployed, etc.)
            down_payment_amount: Down payment amount available
            loan_term_years: Desired loan term in years
            property_type: Type of property (SingleFamily, Condo, etc.)
            property_location: Location/market of the property
            
        Returns:
            Dict containing eligibility information and maximum loan amount
        """
        try:
            self.logger.info("Processing loan eligibility calculation")
            
            # Convert credit score range to numeric value
            credit_score = self._estimate_credit_score(credit_score_range)
            
            # Calculate monthly income
            monthly_income = annual_income / 12
            
            # Calculate maximum DTI (Debt-to-Income) ratio based on credit score
            max_dti = self._get_max_dti(credit_score)
            
            # Calculate front-end ratio limit (housing expense to income)
            max_frontend_ratio = self._get_max_frontend_ratio(credit_score)
            
            # Calculate current DTI without new mortgage
            current_dti = monthly_debts / monthly_income if monthly_income > 0 else 1
            
            # Calculate available monthly payment based on maximum back-end DTI
            available_monthly_payment = (monthly_income * max_dti) - monthly_debts
            
            # Calculate maximum loan amount based on available payment
            interest_rate = self._estimate_interest_rate(credit_score_range, loan_term_years)
            max_loan_amount = self._calculate_max_loan_amount(
                available_monthly_payment, 
                interest_rate, 
                loan_term_years
            )
            
            # Calculate maximum loan amount based on down payment (assuming 80% LTV for simplicity)
            # For a more sophisticated calculation, you would vary LTV based on credit score and loan type
            min_ltv = self._get_min_ltv(credit_score, property_type)
            max_loan_from_down_payment = (down_payment_amount / (1 - min_ltv)) - down_payment_amount
            
            # The maximum loan amount is the lower of the two calculations
            final_max_loan = min(max_loan_amount, max_loan_from_down_payment)
            
            # Calculate total purchase price (loan + down payment)
            total_purchase_price = final_max_loan + down_payment_amount
            
            # Calculate estimated monthly payment
            estimated_monthly_payment = self._calculate_monthly_payment(
                final_max_loan,
                interest_rate,
                loan_term_years
            )
            
            # Add estimated property taxes and insurance
            estimated_tax_rate = self._get_estimated_tax_rate(property_location)
            estimated_insurance_rate = self._get_estimated_insurance_rate(property_type, property_location)
            
            estimated_tax_payment = (total_purchase_price * estimated_tax_rate) / 12
            estimated_insurance_payment = (total_purchase_price * estimated_insurance_rate) / 12
            
            # Calculate total monthly housing payment including taxes and insurance
            total_monthly_housing = estimated_monthly_payment + estimated_tax_payment + estimated_insurance_payment
            
            # Calculate front-end ratio to determine if within limits
            frontend_ratio = total_monthly_housing / monthly_income if monthly_income > 0 else 1
            
            # Determine if loan is affordable based on front-end ratio
            affordable_by_frontend = frontend_ratio <= max_frontend_ratio
            
            # Determine eligibility factors
            eligibility_factors = {
                "credit_score": {
                    "value": credit_score,
                    "minimum_required": 620,
                    "meets_requirement": credit_score >= 620
                },
                "dti_ratio": {
                    "value": current_dti + (total_monthly_housing / monthly_income if monthly_income > 0 else 0),
                    "maximum_allowed": max_dti,
                    "meets_requirement": (current_dti + (total_monthly_housing / monthly_income if monthly_income > 0 else 0)) <= max_dti
                },
                "frontend_ratio": {
                    "value": frontend_ratio,
                    "maximum_allowed": max_frontend_ratio,
                    "meets_requirement": affordable_by_frontend
                },
                "employment": {
                    "status": employment_status,
                    "meets_requirement": employment_status in ["Employed", "SelfEmployed"]
                }
            }
            
            # Determine overall eligibility
            overall_eligible = (
                credit_score >= 620 and
                affordable_by_frontend and
                (current_dti + (total_monthly_housing / monthly_income if monthly_income > 0 else 0)) <= max_dti and
                employment_status in ["Employed", "SelfEmployed"]
            )
            
            # Generate affordability analysis
            affordability_analysis = {
                "monthly_income": monthly_income,
                "monthly_debts": monthly_debts,
                "available_for_housing": available_monthly_payment,
                "estimated_principal_interest": estimated_monthly_payment,
                "estimated_taxes": estimated_tax_payment,
                "estimated_insurance": estimated_insurance_payment,
                "total_monthly_housing": total_monthly_housing,
                "front_end_ratio": frontend_ratio,
                "back_end_ratio": (monthly_debts + total_monthly_housing) / monthly_income if monthly_income > 0 else 1
            }
            
            # Generate recommended actions based on eligibility
            recommended_actions = self._get_recommended_actions(
                overall_eligible,
                eligibility_factors,
                down_payment_amount,
                total_purchase_price
            )
            
            # Return complete eligibility information
            return {
                "eligibility_status": "ELIGIBLE" if overall_eligible else "NOT_ELIGIBLE",
                "maximum_loan_amount": round(final_max_loan, 2),
                "total_purchase_price": round(total_purchase_price, 2),
                "down_payment_amount": down_payment_amount,
                "down_payment_percentage": round((down_payment_amount / total_purchase_price) * 100 if total_purchase_price > 0 else 0, 2),
                "estimated_monthly_payment": round(estimated_monthly_payment, 2),
                "estimated_total_monthly_payment": round(total_monthly_housing, 2),
                "interest_rate": interest_rate,
                "eligibility_factors": eligibility_factors,
                "affordability_analysis": affordability_analysis,
                "recommended_actions": recommended_actions
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating loan eligibility: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "eligibility_status": "ERROR",
                "message": "An error occurred while calculating loan eligibility",
                "recommended_actions": [
                    "Try again with different values",
                    "Contact a mortgage specialist for personalized assistance"
                ]
            }

    # Additional helper methods for loan eligibility calculation
    def _get_max_dti(self, credit_score):
        """Get maximum allowable DTI ratio based on credit score"""
        if credit_score >= 740:
            return 0.45  # 45%
        elif credit_score >= 700:
            return 0.43  # 43%
        elif credit_score >= 660:
            return 0.41  # 41%
        elif credit_score >= 620:
            return 0.38  # 38%
        else:
            return 0.36  # 36%

    def _get_max_frontend_ratio(self, credit_score):
        """Get maximum allowable front-end ratio based on credit score"""
        if credit_score >= 740:
            return 0.32  # 32%
        elif credit_score >= 700:
            return 0.30  # 30%
        elif credit_score >= 660:
            return 0.29  # 29%
        elif credit_score >= 620:
            return 0.28  # 28%
        else:
            return 0.25  # 25%

    def _get_min_ltv(self, credit_score, property_type):
        """Get minimum required loan-to-value ratio based on credit score and property type"""
        base_ltv = 0.8  # 80% LTV (20% down) as default
        
        # Adjust based on credit score
        if credit_score >= 740:
            base_ltv = 0.95  # 5% down
        elif credit_score >= 700:
            base_ltv = 0.9  # 10% down
        elif credit_score >= 660:
            base_ltv = 0.85  # 15% down
        
        # Adjust based on property type
        if property_type == "Condo":
            base_ltv -= 0.05  # Require 5% more down for condos
        elif property_type == "MultiFamily":
            base_ltv -= 0.1  # Require 10% more down for multi-family
        
        return max(0.6, min(0.95, base_ltv))  # Keep between 60% and 95%

    def _estimate_interest_rate(self, credit_score_range, loan_term_years):
        """Estimate interest rate based on credit score and loan term"""
        # Base rates - would normally come from current market rates
        base_rate_30yr = 0.055  # 5.5% for 30-year
        base_rate_15yr = 0.045  # 4.5% for 15-year
        
        # Adjust for loan term
        if loan_term_years <= 15:
            base_rate = base_rate_15yr
        else:
            base_rate = base_rate_30yr
        
        # Adjust for credit score
        if credit_score_range == "Excellent (750+)":
            return base_rate - 0.005  # -0.5%
        elif credit_score_range == "Good (700-749)":
            return base_rate  # No adjustment
        elif credit_score_range == "Fair (650-699)":
            return base_rate + 0.005  # +0.5%
        elif credit_score_range == "Poor (below 650)":
            return base_rate + 0.015  # +1.5%
        else:
            return base_rate

    def _calculate_max_loan_amount(self, monthly_payment, annual_interest_rate, loan_term_years):
        """Calculate maximum loan amount based on monthly payment"""
        # Convert annual rate to monthly
        monthly_rate = annual_interest_rate / 12
        
        # Calculate number of payments
        num_payments = loan_term_years * 12
        
        # Use present value of annuity formula
        if monthly_rate > 0:
            loan_amount = monthly_payment * ((1 - (1 + monthly_rate) ** -num_payments) / monthly_rate)
        else:
            loan_amount = monthly_payment * num_payments
        
        return loan_amount

    def _calculate_monthly_payment(self, loan_amount, annual_interest_rate, loan_term_years):
        """Calculate monthly payment for a loan"""
        # Convert annual rate to monthly
        monthly_rate = annual_interest_rate / 12
        
        # Calculate number of payments
        num_payments = loan_term_years * 12
        
        # Use standard mortgage payment formula
        if monthly_rate > 0:
            payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
        else:
            payment = loan_amount / num_payments
        
        return payment

    def _get_estimated_tax_rate(self, property_location):
        """Get estimated annual property tax rate based on location"""
        # These rates would typically come from a database or service
        location_rates = {
            "New York": 0.0186,     # 1.86%
            "California": 0.0077,   # 0.77%
            "Texas": 0.0181,        # 1.81%
            "Florida": 0.0098,      # 0.98%
            "Illinois": 0.0227,     # 2.27%
            "Pennsylvania": 0.0158, # 1.58%
            "Ohio": 0.0157,         # 1.57%
            "Michigan": 0.0158,     # 1.58%
            "Georgia": 0.0092,      # 0.92%
            "North Carolina": 0.0084, # 0.84%
        }
        
        return location_rates.get(property_location, 0.0125)  # Default to 1.25%

    def _get_estimated_insurance_rate(self, property_type, property_location):
        """Get estimated annual insurance rate based on property type and location"""
        # Base rate varies by property type
        if property_type == "SingleFamily":
            base_rate = 0.0035  # 0.35%
        elif property_type == "Condo":
            base_rate = 0.0025  # 0.25% (lower for condos)
        elif property_type == "MultiFamily":
            base_rate = 0.0045  # 0.45% (higher for multi-family)
        else:
            base_rate = 0.0035  # Default
        
        # Adjust for high-risk locations
        high_risk_locations = ["Florida", "Louisiana", "Texas Gulf Coast"]
        if property_location in high_risk_locations:
            base_rate *= 1.5  # 50% increase for high-risk locations
        
        return base_rate

    def _get_recommended_actions(self, overall_eligible, eligibility_factors, down_payment, total_purchase):
        """Generate recommended actions based on eligibility factors"""
        actions = []
        
        if overall_eligible:
            actions.append("Complete a full mortgage application to proceed")
            actions.append("Gather required documentation for verification")
            
            # Check if more down payment would be beneficial
            down_payment_percentage = (down_payment / total_purchase) * 100 if total_purchase > 0 else 0
            if down_payment_percentage < 20:
                actions.append("Consider increasing down payment to 20% to avoid mortgage insurance")
            
        else:
            # Check individual factors and provide specific recommendations
            if not eligibility_factors["credit_score"]["meets_requirement"]:
                actions.append("Work on improving your credit score before applying")
                actions.append("Check credit report for errors and address outstanding issues")
            
            if not eligibility_factors["dti_ratio"]["meets_requirement"]:
                actions.append("Reduce existing debt to improve debt-to-income ratio")
                actions.append("Consider a lower loan amount to reduce monthly payment")
            
            if not eligibility_factors["frontend_ratio"]["meets_requirement"]:
                actions.append("Look for properties with lower purchase prices")
                actions.append("Increase down payment to reduce loan amount and monthly payment")
            
            if not eligibility_factors["employment"]["meets_requirement"]:
                actions.append("Establish stable employment history before applying")
            
            # Generic recommendations
            actions.append("Speak with a mortgage specialist for personalized advice")
        
        return actions