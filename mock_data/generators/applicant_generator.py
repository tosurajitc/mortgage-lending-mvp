"""
Applicant Profile Generator

This script generates realistic but fictional applicant profiles for mortgage applications.
It creates various applicant types with appropriate demographic and financial attributes.
"""

import json
import random
import datetime
from typing import Dict, Any, List, Tuple, Optional

# Constants for more realistic data
STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", 
          "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", 
          "VA", "WA", "WV", "WI", "WY"]

EMPLOYMENT_STATUSES = ["Employed", "Self-Employed", "Retired", "Unemployed"]
JOB_TITLES = ["Software Engineer", "Teacher", "Nurse", "Doctor", "Accountant", "Manager", 
              "Sales Representative", "Administrative Assistant", "Consultant", "Project Manager", 
              "Business Analyst", "Chef", "Electrician", "Plumber", "Lawyer", "Pharmacist"]
EMPLOYERS = ["TechCorp Inc.", "National Education System", "City Hospital", "Global Finance Group", 
             "Metro Retail Chain", "Consulting Partners LLC", "Manufacturing Industries", 
             "Government Agency", "Self Employed", "State University", "Healthcare Associates"]

# Applicant profile types
PROFILE_TYPES = {
    "excellent": {
        "credit_score_range": (740, 850),
        "employment_years_range": (5, 30),
        "income_range": (75000, 200000),
        "debt_to_income_range": (0.1, 0.28),
        "savings_range": (50000, 500000)
    },
    "good": {
        "credit_score_range": (680, 739),
        "employment_years_range": (2, 20),
        "income_range": (60000, 150000),
        "debt_to_income_range": (0.28, 0.35),
        "savings_range": (20000, 150000)
    },
    "fair": {
        "credit_score_range": (620, 679),
        "employment_years_range": (1, 10),
        "income_range": (45000, 90000),
        "debt_to_income_range": (0.35, 0.43),
        "savings_range": (10000, 50000)
    },
    "poor": {
        "credit_score_range": (550, 619),
        "employment_years_range": (0, 5),
        "income_range": (30000, 60000),
        "debt_to_income_range": (0.43, 0.5),
        "savings_range": (1000, 15000)
    }
}

# Names for generating applicants
FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", 
               "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", 
               "Thomas", "Sarah", "Christopher", "Margaret", "Daniel", "Karen", "Matthew", "Nancy", 
               "Anthony", "Lisa", "Mark", "Betty", "Donald", "Dorothy", "Steven", "Sandra", 
               "Andrew", "Ashley", "Paul", "Kimberly", "Joshua", "Donna", "Kenneth", "Emily", 
               "Kevin", "Michelle", "Brian", "Carol", "George", "Amanda", "Timothy", "Melissa"]

LAST_NAMES = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", 
              "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", 
              "Thompson", "Garcia", "Martinez", "Robinson", "Clark", "Rodriguez", "Lewis", "Lee", 
              "Walker", "Hall", "Allen", "Young", "Hernandez", "King", "Wright", "Lopez", 
              "Hill", "Scott", "Green", "Adams", "Baker", "Gonzalez", "Nelson", "Carter", 
              "Mitchell", "Perez", "Roberts", "Turner", "Phillips", "Campbell", "Parker", "Evans"]

def generate_random_date(start_year: int, end_year: int) -> str:
    """Generate a random date within a year range in YYYY-MM-DD format."""
    year = random.randint(start_year, end_year)
    month = random.randint(1, 12)
    
    # Adjust max day based on month
    if month in [4, 6, 9, 11]:
        max_day = 30
    elif month == 2:
        # Simple leap year check
        if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
            max_day = 29
        else:
            max_day = 28
    else:
        max_day = 31
    
    day = random.randint(1, max_day)
    
    return f"{year}-{month:02d}-{day:02d}"

def generate_ssn_last_four() -> str:
    """Generate last four digits of a social security number."""
    return ''.join([str(random.randint(0, 9)) for _ in range(4)])

def generate_phone_number() -> str:
    """Generate a formatted US phone number."""
    area_code = random.randint(200, 999)
    prefix = random.randint(200, 999)
    line_number = random.randint(1000, 9999)
    return f"({area_code}) {prefix}-{line_number}"

def generate_email(first_name: str, last_name: str) -> str:
    """Generate an email address based on name."""
    domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com"]
    separators = [".", "_", ""]
    
    # Clean and lowercase names
    first = first_name.lower()
    last = last_name.lower()
    
    separator = random.choice(separators)
    domain = random.choice(domains)
    
    # Different email patterns
    patterns = [
        f"{first}{separator}{last}@{domain}",
        f"{first[0]}{separator}{last}@{domain}",
        f"{first}{separator}{last[0]}@{domain}",
        f"{first}.{last}{random.randint(1, 99)}@{domain}"
    ]
    
    return random.choice(patterns)

def generate_address() -> Dict[str, str]:
    """Generate a random US address."""
    street_numbers = list(range(100, 9999))
    street_names = ["Main", "Oak", "Pine", "Maple", "Cedar", "Elm", "Washington", "Park", 
                    "Lake", "Hill", "River", "Spring", "Sunset", "Valley", "Forest", "Meadow"]
    street_types = ["St", "Ave", "Blvd", "Dr", "Ln", "Rd", "Way", "Pl", "Ct"]
    cities = ["Springfield", "Franklin", "Greenville", "Bristol", "Clinton", "Georgetown", 
              "Salem", "Madison", "Oxford", "Arlington", "Burlington", "Manchester", "Milton"]
    zip_codes = [f"{random.randint(10000, 99999)}" for _ in range(50)]  # Generate random zip codes
    
    street_number = random.choice(street_numbers)
    street_name = random.choice(street_names)
    street_type = random.choice(street_types)
    city = random.choice(cities)
    state = random.choice(STATES)
    zip_code = random.choice(zip_codes)
    
    return {
        "street": f"{street_number} {street_name} {street_type}",
        "city": city,
        "state": state,
        "zip_code": zip_code,
        "country": "USA"
    }

def generate_applicant(profile_type: str = "good", age_range: Tuple[int, int] = (25, 65), 
                      with_coapplicant: bool = False) -> Dict[str, Any]:
    """
    Generate a primary applicant profile with optional co-applicant.
    
    Args:
        profile_type: The profile quality ("excellent", "good", "fair", "poor")
        age_range: Age range for the applicant
        with_coapplicant: Whether to include a co-applicant
    
    Returns:
        Dictionary with applicant information
    """
    if profile_type not in PROFILE_TYPES:
        profile_type = "good"  # Default to good profile
    
    profile_params = PROFILE_TYPES[profile_type]
    
    # Calculate birth date based on age range
    current_year = datetime.datetime.now().year
    min_age, max_age = age_range
    birth_year_min = current_year - max_age
    birth_year_max = current_year - min_age
    
    # Generate basic applicant info
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    
    # Always use the same address for primary and co-applicant
    address = generate_address()
    
    # Generate employment details
    employment_status = "Employed"  # Default
    employer_name = None
    years_at_current_job = None
    
    # Adjust employment status based on profile and random chance
    if profile_type == "excellent":
        employment_statuses = ["Employed", "Self-Employed", "Retired"]
        weights = [0.7, 0.2, 0.1]
    elif profile_type == "good":
        employment_statuses = ["Employed", "Self-Employed"]
        weights = [0.85, 0.15]
    elif profile_type == "fair":
        employment_statuses = ["Employed", "Self-Employed", "Unemployed"]
        weights = [0.8, 0.15, 0.05]
    else:  # poor
        employment_statuses = ["Employed", "Self-Employed", "Unemployed"]
        weights = [0.7, 0.15, 0.15]
    
    employment_status = random.choices(employment_statuses, weights=weights, k=1)[0]
    
    if employment_status in ["Employed", "Self-Employed"]:
        years_at_current_job = round(random.uniform(*profile_params["employment_years_range"]), 1)
        
        if employment_status == "Employed":
            employer_name = random.choice(EMPLOYERS)
        else:
            employer_name = "Self Employed"
    
    # Generate financial details
    annual_income = random.randint(*profile_params["income_range"])
    credit_score = random.randint(*profile_params["credit_score_range"])
    
    # Create primary applicant
    primary_applicant = {
        "first_name": first_name,
        "last_name": last_name,
        "email": generate_email(first_name, last_name),
        "phone": generate_phone_number(),
        "date_of_birth": generate_random_date(birth_year_min, birth_year_max),
        "ssn_last_four": generate_ssn_last_four(),
        "address": address,
        "employment_status": employment_status,
        "annual_income": annual_income,
        "credit_score": credit_score
    }
    
    # Add employment details if applicable
    if employer_name:
        primary_applicant["employer_name"] = employer_name
    
    if years_at_current_job is not None:
        primary_applicant["years_at_current_job"] = years_at_current_job
    
    # Generate co-applicant if requested
    co_applicant = None
    if with_coapplicant:
        # Co-applicant gets a slightly adjusted profile based on primary
        co_profile_type = profile_type
        
        # Occasionally improve or worsen the co-applicant's profile
        if random.random() < 0.3:
            profile_types = list(PROFILE_TYPES.keys())
            current_index = profile_types.index(profile_type)
            
            # Move up or down one level with bounds checking
            shift = random.choice([-1, 1])
            new_index = max(0, min(len(profile_types) - 1, current_index + shift))
            co_profile_type = profile_types[new_index]
        
        co_profile_params = PROFILE_TYPES[co_profile_type]
        
        # Generate co-applicant details (usually a spouse, so use different gender name lists)
        co_first_name = random.choice(FIRST_NAMES)
        # Usually same last name, but not always
        co_last_name = last_name if random.random() < 0.8 else random.choice(LAST_NAMES)
        
        # Create co-applicant with some correlation to primary
        co_employment_status = random.choices(employment_statuses, weights=weights, k=1)[0]
        co_employer_name = None
        co_years_at_current_job = None
        
        if co_employment_status in ["Employed", "Self-Employed"]:
            co_years_at_current_job = round(random.uniform(*co_profile_params["employment_years_range"]), 1)
            
            if co_employment_status == "Employed":
                co_employer_name = random.choice(EMPLOYERS)
            else:
                co_employer_name = "Self Employed"
        
        co_annual_income = random.randint(*co_profile_params["income_range"])
        co_credit_score = random.randint(*co_profile_params["credit_score_range"])
        
        co_applicant = {
            "first_name": co_first_name,
            "last_name": co_last_name,
            "email": generate_email(co_first_name, co_last_name),
            "phone": generate_phone_number(),
            "date_of_birth": generate_random_date(birth_year_min, birth_year_max),
            "ssn_last_four": generate_ssn_last_four(),
            "address": address,  # Same address as primary
            "employment_status": co_employment_status,
            "annual_income": co_annual_income,
            "credit_score": co_credit_score
        }
        
        # Add employment details if applicable
        if co_employer_name:
            co_applicant["employer_name"] = co_employer_name
        
        if co_years_at_current_job is not None:
            co_applicant["years_at_current_job"] = co_years_at_current_job
    
    result = {
        "primary_applicant": primary_applicant
    }
    
    if co_applicant:
        result["co_applicant"] = co_applicant
    
    return result

def generate_applicant_set(count: int = 10) -> List[Dict[str, Any]]:
    """
    Generate a diverse set of applicant profiles.
    
    Args:
        count: Number of applicant profiles to generate
    
    Returns:
        List of applicant profiles
    """
    applicants = []
    
    # Create a distribution of profile types
    profile_types = ["excellent", "good", "fair", "poor"]
    weights = [0.2, 0.5, 0.2, 0.1]  # Realistic distribution
    
    # Age groups with different likelihoods of co-applicants
    age_groups = [
        ((25, 35), 0.6),  # Young adults, 60% have co-applicants
        ((36, 50), 0.7),  # Middle-aged, 70% have co-applicants
        ((51, 65), 0.5),  # Older adults, 50% have co-applicants
        ((66, 85), 0.3)   # Seniors, 30% have co-applicants
    ]
    
    for _ in range(count):
        # Select profile type with weighting
        profile_type = random.choices(profile_types, weights=weights, k=1)[0]
        
        # Select age group and co-applicant probability
        age_range, co_app_prob = random.choice(age_groups)
        
        # Determine if there's a co-applicant
        with_coapplicant = random.random() < co_app_prob
        
        # Generate the applicant
        applicant = generate_applicant(
            profile_type=profile_type,
            age_range=age_range,
            with_coapplicant=with_coapplicant
        )
        
        applicants.append(applicant)
    
    return applicants

if __name__ == "__main__":
    # Generate and save sample applicant data
    applicants = generate_applicant_set(20)
    
    # Ensure output directory exists
    import os
    os.makedirs("mock_data/sample_data/applicants", exist_ok=True)
    
    # Save to file
    with open("mock_data/sample_data/applicants/sample_applicants.json", "w") as f:
        json.dump(applicants, f, indent=2)
    
    print(f"Generated {len(applicants)} applicant profiles.")
    
    # Display a sample
    print("\nSample applicant:")
    print(json.dumps(applicants[0], indent=2))