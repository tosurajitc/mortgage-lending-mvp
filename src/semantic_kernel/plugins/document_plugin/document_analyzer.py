# src/semantic_kernel/plugins/document_plugin/document_analyzer.py

import os
import json
import datetime
from typing import Dict, List, Any, Optional, Tuple
import semantic_kernel as sk
from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter
import re

from utils.logging_utils import get_logger
from data.models import Document, DocumentType

logger = get_logger("semantic_kernel.plugins.document")

class DocumentAnalyzerPlugin:
    """
    Plugin for analyzing mortgage-related documents.
    Provides functions for extracting information, validating documents,
    and summarizing document contents.
    """
    
    def __init__(self, kernel: Optional[sk.Kernel] = None):
        """
        Initialize the document analyzer plugin.
        
        Args:
            kernel: Optional Semantic Kernel instance
        """
        self.kernel = kernel
        self.logger = logger
    
    @sk_function(
        description="Extract key information from a W-2 tax form",
        name="extractW2Information"
    )
    @sk_function_context_parameter(
        name="document_text",
        description="The text content of the W-2 form"
    )
    def extract_w2_information(self, context: sk.SKContext) -> str:
        """
        Extract key information from a W-2 tax form.
        
        Args:
            context: Semantic Kernel context containing document text
            
        Returns:
            JSON string with extracted information
        """
        document_text = context["document_text"]
        
        # Extract employer information
        employer_name = self._extract_with_pattern(document_text, r"(?:Employer's name|employer name)[^\n]*?([A-Z][A-Za-z\s\.,]+)")
        employer_ein = self._extract_with_pattern(document_text, r"(?:Employer identification number|EIN)[^\n]*?(\d{2}-\d{7})")
        
        # Extract employee information
        employee_name = self._extract_with_pattern(document_text, r"(?:Employee's name|employee name)[^\n]*?([A-Z][A-Za-z\s\.,]+)")
        employee_ssn = self._extract_with_pattern(document_text, r"(?:Employee's SSN|SSN)[^\n]*?(\d{3}-\d{2}-\d{4})")
        
        # Extract wage information
        wages = self._extract_amount(document_text, r"(?:Wages, tips, other compensation|Box 1)[^\n]*?(\$?[\d,.]+)")
        federal_tax = self._extract_amount(document_text, r"(?:Federal income tax withheld|Box 2)[^\n]*?(\$?[\d,.]+)")
        social_security_wages = self._extract_amount(document_text, r"(?:Social security wages|Box 3)[^\n]*?(\$?[\d,.]+)")
        medicare_wages = self._extract_amount(document_text, r"(?:Medicare wages and tips|Box 5)[^\n]*?(\$?[\d,.]+)")
        
        # Extract year
        tax_year = self._extract_with_pattern(document_text, r"(?:Tax Year|Year|For the year)[^\n]*?(\d{4})")
        if not tax_year:
            # Try to extract year from date fields
            year_match = re.search(r"\b(20\d{2})\b", document_text)
            tax_year = year_match.group(1) if year_match else None
        
        # Compile results
        result = {
            "document_type": "W2_FORM",
            "employer": {
                "name": employer_name,
                "ein": employer_ein
            },
            "employee": {
                "name": employee_name,
                "ssn_last_four": employee_ssn[-4:] if employee_ssn else None
            },
            "income": {
                "wages": wages,
                "federal_tax_withheld": federal_tax,
                "social_security_wages": social_security_wages,
                "medicare_wages": medicare_wages
            },
            "tax_year": tax_year,
            "verification_score": self._calculate_verification_score([
                employer_name, employer_ein, employee_name, employee_ssn, wages, federal_tax, tax_year
            ])
        }
        
        return json.dumps(result, indent=2)
    
    @sk_function(
        description="Extract key information from a pay stub",
        name="extractPayStubInformation"
    )
    @sk_function_context_parameter(
        name="document_text",
        description="The text content of the pay stub"
    )
    def extract_pay_stub_information(self, context: sk.SKContext) -> str:
        """
        Extract key information from a pay stub.
        
        Args:
            context: Semantic Kernel context containing document text
            
        Returns:
            JSON string with extracted information
        """
        document_text = context["document_text"]
        
        # Extract employer information
        employer_name = self._extract_with_pattern(document_text, r"(?:Company|Employer)[^\n]*?([A-Z][A-Za-z\s\.,]+)")
        
        # Extract employee information
        employee_name = self._extract_with_pattern(document_text, r"(?:Employee|Name)[^\n]*?([A-Z][A-Za-z\s\.,]+)")
        employee_id = self._extract_with_pattern(document_text, r"(?:Employee ID|ID Number)[^\n]*?([A-Z0-9]+)")
        
        # Extract pay period information
        pay_period = self._extract_with_pattern(document_text, r"(?:Pay Period|Period)[^\n]*?([\d/]+ - [\d/]+)")
        pay_date = self._extract_with_pattern(document_text, r"(?:Pay Date|Date)[^\n]*?([\d/]+)")
        
        # Extract income information
        gross_pay = self._extract_amount(document_text, r"(?:Gross Pay|Gross)[^\n]*?(\$?[\d,.]+)")
        net_pay = self._extract_amount(document_text, r"(?:Net Pay|Net)[^\n]*?(\$?[\d,.]+)")
        ytd_gross = self._extract_amount(document_text, r"(?:YTD Gross|Year to Date)[^\n]*?(\$?[\d,.]+)")
        
        # Extract year
        current_year = datetime.datetime.now().year
        year_match = re.search(r"\b(20\d{2})\b", document_text)
        year = year_match.group(1) if year_match else str(current_year)
        
        # Compile results
        result = {
            "document_type": "PAY_STUB",
            "employer": {
                "name": employer_name
            },
            "employee": {
                "name": employee_name,
                "employee_id": employee_id
            },
            "pay_period": {
                "period": pay_period,
                "pay_date": pay_date,
                "year": year
            },
            "income": {
                "gross_pay": gross_pay,
                "net_pay": net_pay,
                "ytd_gross": ytd_gross
            },
            "verification_score": self._calculate_verification_score([
                employer_name, employee_name, pay_period, pay_date, gross_pay, net_pay
            ])
        }
        
        return json.dumps(result, indent=2)
    
    @sk_function(
        description="Extract key information from a bank statement",
        name="extractBankStatementInformation"
    )
    @sk_function_context_parameter(
        name="document_text",
        description="The text content of the bank statement"
    )
    def extract_bank_statement_information(self, context: sk.SKContext) -> str:
        """
        Extract key information from a bank statement.
        
        Args:
            context: Semantic Kernel context containing document text
            
        Returns:
            JSON string with extracted information
        """
        document_text = context["document_text"]
        
        # Extract bank information
        bank_name = self._extract_with_pattern(document_text, r"(?:Bank|Financial Institution)[^\n]*?([A-Z][A-Za-z\s\.,]+)")
        
        # Extract account information
        account_holder = self._extract_with_pattern(document_text, r"(?:Account Holder|Customer)[^\n]*?([A-Z][A-Za-z\s\.,]+)")
        account_number = self._extract_with_pattern(document_text, r"(?:Account Number|Acct)[^\n]*?[^\d]*(\d+)")
        # Mask account number for security
        if account_number and len(account_number) > 4:
            account_number = "X" * (len(account_number) - 4) + account_number[-4:]
        
        # Extract statement period
        statement_period = self._extract_with_pattern(document_text, r"(?:Statement Period|Period)[^\n]*?([\d/]+ - [\d/]+)")
        
        # Extract balances
        beginning_balance = self._extract_amount(document_text, r"(?:Beginning Balance|Opening Balance)[^\n]*?(\$?[\d,.]+)")
        ending_balance = self._extract_amount(document_text, r"(?:Ending Balance|Closing Balance)[^\n]*?(\$?[\d,.]+)")
        
        # Extract deposits and withdrawals
        total_deposits = self._extract_amount(document_text, r"(?:Total Deposits|Deposits)[^\n]*?(\$?[\d,.]+)")
        total_withdrawals = self._extract_amount(document_text, r"(?:Total Withdrawals|Withdrawals)[^\n]*?(\$?[\d,.]+)")
        
        # Compile results
        result = {
            "document_type": "BANK_STATEMENT",
            "bank": {
                "name": bank_name
            },
            "account": {
                "holder": account_holder,
                "number": account_number
            },
            "statement_period": statement_period,
            "balances": {
                "beginning": beginning_balance,
                "ending": ending_balance
            },
            "transactions": {
                "deposits": total_deposits,
                "withdrawals": total_withdrawals
            },
            "verification_score": self._calculate_verification_score([
                bank_name, account_holder, account_number, statement_period, beginning_balance, ending_balance
            ])
        }
        
        return json.dumps(result, indent=2)
    
    @sk_function(
        description="Validate document completeness and identify missing information",
        name="validateDocumentCompleteness"
    )
    @sk_function_context_parameter(
        name="document_type",
        description="The type of document being validated"
    )
    @sk_function_context_parameter(
        name="extracted_data",
        description="JSON string of data extracted from the document"
    )
    def validate_document_completeness(self, context: sk.SKContext) -> str:
        """
        Validate the completeness of a document and identify missing information.
        
        Args:
            context: Semantic Kernel context containing document type and extracted data
            
        Returns:
            JSON string with validation results
        """
        document_type = context["document_type"]
        extracted_data = json.loads(context["extracted_data"])
        
        missing_fields = []
        is_valid = True
        
        if document_type == "W2_FORM":
            # Check for required W-2 fields
            required_fields = [
                ("employer.name", "Employer name"),
                ("employer.ein", "Employer EIN"),
                ("employee.name", "Employee name"),
                ("income.wages", "Wages"),
                ("tax_year", "Tax year")
            ]
            missing_fields = self._check_required_fields(extracted_data, required_fields)
            
            # Additional validation logic for W-2 forms
            if not missing_fields:
                # Check wage consistency if all values are present
                try:
                    wages = float(self._get_nested_value(extracted_data, "income.wages") or 0)
                    ss_wages = float(self._get_nested_value(extracted_data, "income.social_security_wages") or 0)
                    medicare_wages = float(self._get_nested_value(extracted_data, "income.medicare_wages") or 0)
                    
                    # Check for large discrepancies in reported wages
                    if ss_wages > 0 and abs(wages - ss_wages) / wages > 0.1:
                        missing_fields.append("Inconsistency between wages and social security wages")
                    if medicare_wages > 0 and abs(wages - medicare_wages) / wages > 0.1:
                        missing_fields.append("Inconsistency between wages and Medicare wages")
                except (ValueError, TypeError):
                    missing_fields.append("Invalid numeric values in income fields")
        
        elif document_type == "PAY_STUB":
            # Check for required pay stub fields
            required_fields = [
                ("employer.name", "Employer name"),
                ("employee.name", "Employee name"),
                ("pay_period.period", "Pay period"),
                ("income.gross_pay", "Gross pay"),
                ("income.net_pay", "Net pay")
            ]
            missing_fields = self._check_required_fields(extracted_data, required_fields)
            
            # Additional validation logic for pay stubs
            if not missing_fields:
                try:
                    gross = float(self._get_nested_value(extracted_data, "income.gross_pay") or 0)
                    net = float(self._get_nested_value(extracted_data, "income.net_pay") or 0)
                    
                    # Net pay should be less than gross pay
                    if net >= gross:
                        missing_fields.append("Net pay is greater than or equal to gross pay")
                    
                    # Net pay shouldn't be too low compared to gross pay
                    if net < gross * 0.5:
                        missing_fields.append("Net pay is unusually low compared to gross pay")
                except (ValueError, TypeError):
                    missing_fields.append("Invalid numeric values in income fields")
        
        elif document_type == "BANK_STATEMENT":
            # Check for required bank statement fields
            required_fields = [
                ("bank.name", "Bank name"),
                ("account.holder", "Account holder name"),
                ("account.number", "Account number"),
                ("statement_period", "Statement period"),
                ("balances.ending", "Ending balance")
            ]
            missing_fields = self._check_required_fields(extracted_data, required_fields)
            
            # Additional validation logic for bank statements
            if not missing_fields:
                try:
                    beginning = float(self._get_nested_value(extracted_data, "balances.beginning") or 0)
                    ending = float(self._get_nested_value(extracted_data, "balances.ending") or 0)
                    deposits = float(self._get_nested_value(extracted_data, "transactions.deposits") or 0)
                    withdrawals = float(self._get_nested_value(extracted_data, "transactions.withdrawals") or 0)
                    
                    # Check if balances and transactions are consistent
                    # Beginning balance + deposits - withdrawals should equal ending balance
                    if abs((beginning + deposits - withdrawals) - ending) > 0.01:
                        missing_fields.append("Inconsistency in balance calculation")
                except (ValueError, TypeError):
                    missing_fields.append("Invalid numeric values in balance fields")
        
        else:
            missing_fields.append(f"Unknown document type: {document_type}")
            is_valid = False
        
        # Determine validity based on missing fields
        if missing_fields:
            is_valid = False
        
        # Compile results
        result = {
            "document_type": document_type,
            "is_valid": is_valid,
            "missing_fields": missing_fields,
            "completeness_score": 1.0 if not missing_fields else max(0.0, 1.0 - (len(missing_fields) * 0.1)),
            "needs_manual_review": len(missing_fields) > 2
        }
        
        return json.dumps(result, indent=2)
    
    @sk_function(
        description="Verify consistency between multiple documents",
        name="verifyDocumentConsistency"
    )
    @sk_function_context_parameter(
        name="documents_data",
        description="JSON string containing data from multiple documents"
    )
    def verify_document_consistency(self, context: sk.SKContext) -> str:
        """
        Verify consistency between multiple documents.
        
        Args:
            context: Semantic Kernel context containing data from multiple documents
            
        Returns:
            JSON string with consistency verification results
        """
        documents_data = json.loads(context["documents_data"])
        
        inconsistencies = []
        verification_points = []
        
        # Extract names for comparison
        names = set()
        for doc in documents_data:
            # Extract any name fields from the document
            if "employee" in doc and "name" in doc["employee"] and doc["employee"]["name"]:
                names.add(doc["employee"]["name"].lower().strip())
            elif "account" in doc and "holder" in doc["account"] and doc["account"]["holder"]:
                names.add(doc["account"]["holder"].lower().strip())
        
        # Check if there are multiple names
        if len(names) > 1:
            inconsistencies.append(f"Multiple applicant names found: {', '.join(names)}")
        elif len(names) == 1:
            verification_points.append(f"Consistent applicant name across documents: {next(iter(names))}")
        
        # Compare income information across documents
        income_values = {}
        for doc in documents_data:
            doc_type = doc.get("document_type", "UNKNOWN")
            
            if doc_type == "W2_FORM" and "income" in doc and "wages" in doc["income"]:
                income_values["W2_wages"] = float(doc["income"]["wages"])
            
            elif doc_type == "PAY_STUB" and "income" in doc:
                if "gross_pay" in doc["income"]:
                    pay_period = doc.get("pay_period", {}).get("period", "")
                    key = f"PAY_STUB_gross_{pay_period}"
                    income_values[key] = float(doc["income"]["gross_pay"])
                
                if "ytd_gross" in doc["income"]:
                    income_values["PAY_STUB_ytd"] = float(doc["income"]["ytd_gross"])
        
        # Compare W-2 wages with pay stub YTD gross
        if "W2_wages" in income_values and "PAY_STUB_ytd" in income_values:
            w2_wages = income_values["W2_wages"]
            ytd_gross = income_values["PAY_STUB_ytd"]
            
            # Check if they're within 5% of each other
            percent_diff = abs(w2_wages - ytd_gross) / max(w2_wages, ytd_gross) * 100
            
            if percent_diff > 5:
                inconsistencies.append(f"W-2 wages ({w2_wages}) and pay stub YTD gross ({ytd_gross}) differ by {percent_diff:.1f}%")
            else:
                verification_points.append(f"W-2 wages consistent with pay stub YTD gross")
        
        # Check bank statement against reported income
        if any(k.startswith("PAY_STUB_gross_") for k in income_values.keys()) and any(d.get("document_type") == "BANK_STATEMENT" for d in documents_data):
            bank_doc = next((d for d in documents_data if d.get("document_type") == "BANK_STATEMENT"), None)
            
            if bank_doc and "transactions" in bank_doc and "deposits" in bank_doc["transactions"]:
                deposits = float(bank_doc["transactions"]["deposits"])
                
                # Get average monthly gross pay from pay stubs
                pay_stub_amounts = [v for k, v in income_values.items() if k.startswith("PAY_STUB_gross_")]
                if pay_stub_amounts:
                    avg_pay = sum(pay_stub_amounts) / len(pay_stub_amounts)
                    
                    # Check if deposits are at least 90% of reported income
                    if deposits < avg_pay * 0.9:
                        inconsistencies.append(f"Bank deposits ({deposits}) are less than 90% of average pay ({avg_pay})")
                    else:
                        verification_points.append(f"Bank deposits consistent with reported income")
        
        # Compile results
        consistency_score = max(0.0, 1.0 - (len(inconsistencies) * 0.2))
        result = {
            "is_consistent": len(inconsistencies) == 0,
            "inconsistencies": inconsistencies,
            "verification_points": verification_points,
            "consistency_score": consistency_score,
            "needs_manual_review": len(inconsistencies) > 0
        }
        
        return json.dumps(result, indent=2)
    
    @sk_function(
        description="Summarize key information from a document for human review",
        name="summarizeDocumentForReview"
    )
    @sk_function_context_parameter(
        name="document_type",
        description="The type of document being summarized"
    )
    @sk_function_context_parameter(
        name="extracted_data",
        description="JSON string of data extracted from the document"
    )
    def summarize_document_for_review(self, context: sk.SKContext) -> str:
        """
        Create a human-readable summary of a document for review.
        
        Args:
            context: Semantic Kernel context containing document type and extracted data
            
        Returns:
            Human-readable summary of the document
        """
        document_type = context["document_type"]
        extracted_data = json.loads(context["extracted_data"])
        
        summary = ""
        
        if document_type == "W2_FORM":
            employer_name = self._get_nested_value(extracted_data, "employer.name") or "Unknown Employer"
            employee_name = self._get_nested_value(extracted_data, "employee.name") or "Unknown Employee"
            wages = self._get_nested_value(extracted_data, "income.wages") or "N/A"
            tax_year = extracted_data.get("tax_year", "Unknown Year")
            
            summary = f"W-2 TAX FORM SUMMARY\n\n"
            summary += f"Tax Year: {tax_year}\n"
            summary += f"Employer: {employer_name}\n"
            summary += f"Employee: {employee_name}\n"
            summary += f"Wages: ${wages}\n"
            
            # Add federal tax withheld if available
            federal_tax = self._get_nested_value(extracted_data, "income.federal_tax_withheld")
            if federal_tax:
                summary += f"Federal Tax Withheld: ${federal_tax}\n"
            
            # Add verification score
            verification_score = extracted_data.get("verification_score", 0)
            summary += f"\nVerification Score: {verification_score:.2f} out of 1.0\n"
            
            # Add review notes
            if verification_score < 0.7:
                summary += "\nREVIEW NOTES: Document has low verification score. Please verify key information manually.\n"
            
        elif document_type == "PAY_STUB":
            employer_name = self._get_nested_value(extracted_data, "employer.name") or "Unknown Employer"
            employee_name = self._get_nested_value(extracted_data, "employee.name") or "Unknown Employee"
            pay_period = self._get_nested_value(extracted_data, "pay_period.period") or "Unknown Period"
            gross_pay = self._get_nested_value(extracted_data, "income.gross_pay") or "N/A"
            net_pay = self._get_nested_value(extracted_data, "income.net_pay") or "N/A"
            
            summary = f"PAY STUB SUMMARY\n\n"
            summary += f"Employer: {employer_name}\n"
            summary += f"Employee: {employee_name}\n"
            summary += f"Pay Period: {pay_period}\n"
            summary += f"Gross Pay: ${gross_pay}\n"
            summary += f"Net Pay: ${net_pay}\n"
            
            # Add YTD information if available
            ytd_gross = self._get_nested_value(extracted_data, "income.ytd_gross")
            if ytd_gross:
                summary += f"Year-to-Date Gross: ${ytd_gross}\n"
            
            # Add verification score
            verification_score = extracted_data.get("verification_score", 0)
            summary += f"\nVerification Score: {verification_score:.2f} out of 1.0\n"
            
            # Add review notes
            if verification_score < 0.7:
                summary += "\nREVIEW NOTES: Document has low verification score. Please verify key information manually.\n"
            
        elif document_type == "BANK_STATEMENT":
            bank_name = self._get_nested_value(extracted_data, "bank.name") or "Unknown Bank"
            account_holder = self._get_nested_value(extracted_data, "account.holder") or "Unknown Account Holder"
            account_number = self._get_nested_value(extracted_data, "account.number") or "Unknown Account"
            statement_period = extracted_data.get("statement_period", "Unknown Period")
            ending_balance = self._get_nested_value(extracted_data, "balances.ending") or "N/A"
            
            summary = f"BANK STATEMENT SUMMARY\n\n"
            summary += f"Bank: {bank_name}\n"
            summary += f"Account Holder: {account_holder}\n"
            summary += f"Account Number: {account_number}\n"
            summary += f"Statement Period: {statement_period}\n"
            summary += f"Ending Balance: ${ending_balance}\n"
            
            # Add transaction information if available
            deposits = self._get_nested_value(extracted_data, "transactions.deposits")
            if deposits:
                summary += f"Total Deposits: ${deposits}\n"
            
            withdrawals = self._get_nested_value(extracted_data, "transactions.withdrawals")
            if withdrawals:
                summary += f"Total Withdrawals: ${withdrawals}\n"
            
            # Add verification score
            verification_score = extracted_data.get("verification_score", 0)
            summary += f"\nVerification Score: {verification_score:.2f} out of 1.0\n"
            
            # Add review notes
            if verification_score < 0.7:
                summary += "\nREVIEW NOTES: Document has low verification score. Please verify key information manually.\n"
        
        else:
            summary = f"UNKNOWN DOCUMENT TYPE: {document_type}\n\n"
            summary += "The system could not determine the type of this document. "
            summary += "Please review the document manually."
        
        return summary
    
    @sk_function(
        description="Detect potential fraud indicators in documents",
        name="detectFraudIndicators"
    )
    @sk_function_context_parameter(
        name="document_type",
        description="The type of document being analyzed"
    )
    @sk_function_context_parameter(
        name="extracted_data",
        description="JSON string of data extracted from the document"
    )
    def detect_fraud_indicators(self, context: sk.SKContext) -> str:
        """
        Detect potential indicators of fraud in a document.
        
        Args:
            context: Semantic Kernel context containing document type and extracted data
            
        Returns:
            JSON string with fraud detection results
        """
        document_type = context["document_type"]
        extracted_data = json.loads(context["extracted_data"])
        
        fraud_indicators = []
        
        # Check verification score
        verification_score = extracted_data.get("verification_score", 0)
        if verification_score < 0.6:
            fraud_indicators.append("Low verification score indicates potential document alterations")
        
        if document_type == "W2_FORM":
            # Check for rounded income amounts (possible fraud indicator)
            wages = self._get_nested_value(extracted_data, "income.wages")
            if wages and float(wages) % 1000 == 0 and float(wages) > 10000:
                fraud_indicators.append("Income amount is suspiciously rounded to nearest thousand")
            
            # Check for excessive income compared to industry norms
            # This would be more sophisticated in a real system with industry benchmarks
            if wages and float(wages) > 500000:
                fraud_indicators.append("Unusually high income amount")
            
            # Check for tax year issues
            tax_year = extracted_data.get("tax_year")
            current_year = datetime.datetime.now().year
            if tax_year and (int(tax_year) > current_year or int(tax_year) < current_year - 5):
                fraud_indicators.append(f"Suspicious tax year: {tax_year}")
        
        elif document_type == "PAY_STUB":
            # Check for inconsistencies in pay amounts
            gross_pay = self._get_nested_value(extracted_data, "income.gross_pay")
            net_pay = self._get_nested_value(extracted_data, "income.net_pay")
            
            if gross_pay and net_pay:
                # Net pay should generally be 60-85% of gross pay
                net_to_gross_ratio = float(net_pay) / float(gross_pay) if float(gross_pay) > 0 else 0
                
                if net_to_gross_ratio > 0.9:
                    fraud_indicators.append("Net pay is suspiciously close to gross pay")
                elif net_to_gross_ratio < 0.5:
                    fraud_indicators.append("Net pay is unusually low compared to gross pay")
            
            # Check for pay date issues
            pay_date = self._get_nested_value(extracted_data, "pay_period.pay_date")
            if pay_date:
                try:
                    parts = pay_date.split("/")
                    if len(parts) == 3:
                        month, day, year = int(parts[0]), int(parts[1]), int(parts[2])
                        if month > 12 or day > 31:
                            fraud_indicators.append(f"Invalid date format: {pay_date}")
                except:
                    pass
        
        elif document_type == "BANK_STATEMENT":
            # Check for suspicious activity in transactions
            beginning_balance = self._get_nested_value(extracted_data, "balances.beginning")
            ending_balance = self._get_nested_value(extracted_data, "balances.ending")
            deposits = self._get_nested_value(extracted_data, "transactions.deposits")
            withdrawals = self._get_nested_value(extracted_data, "transactions.withdrawals")
            
            if beginning_balance and ending_balance and deposits and withdrawals:
                # Check if the math adds up
                try:
                    expected_ending = float(beginning_balance) + float(deposits) - float(withdrawals)
                    actual_ending = float(ending_balance)
                    
                    if abs(expected_ending - actual_ending) > 1.0:  # Allow for rounding
                        fraud_indicators.append("Balance calculation inconsistency")
                except:
                    pass
            
            # Check for round numbers in deposits
            if deposits and float(deposits) % 1000 == 0 and float(deposits) > 10000:
                fraud_indicators.append("Suspiciously rounded deposit amounts")
        
        # Compile results
        result = {
            "document_type": document_type,
            "fraud_indicators_detected": len(fraud_indicators) > 0,
            "fraud_indicators": fraud_indicators,
            "risk_score": min(1.0, 0.3 + (len(fraud_indicators) * 0.15)),
            "needs_manual_review": len(fraud_indicators) > 0
        }
        
        return json.dumps(result, indent=2)
    
    # Helper methods
    def _extract_with_pattern(self, text: str, pattern: str) -> Optional[str]:
        """Extract text using a regex pattern."""
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None
    
    def _extract_amount(self, text: str, pattern: str) -> Optional[str]:
        """Extract a monetary amount using a regex pattern."""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount = match.group(1).strip()
            # Remove currency symbols and commas
            amount = amount.replace("$", "").replace(",", "")
            return amount
        return None
    
    def _calculate_verification_score(self, fields: List[Any]) -> float:
        """Calculate a verification score based on field presence."""
        if not fields:
            return 0.0
            
        present_count = sum(1 for f in fields if f is not None)
        return present_count / len(fields)
    
    def _check_required_fields(self, data: Dict[str, Any], required_fields: List[Tuple[str, str]]) -> List[str]:
        """Check for the presence of required fields."""
        missing = []
        for field_path, field_name in required_fields:
            if not self._get_nested_value(data, field_path):
                missing.append(f"Missing {field_name}")
        return missing
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get a value from a nested dictionary using dot notation."""
        parts = path.split(".")
        value = data
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        return value