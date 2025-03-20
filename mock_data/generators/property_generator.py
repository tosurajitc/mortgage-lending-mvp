"""
Property Generator

This script generates realistic but fictional property data for mortgage applications.
It creates various property types with appropriate characteristics and valuations.
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

# State to average home price mapping (representative values)
STATE_PRICE_FACTORS = {
    "CA": 1.5, "NY": 1.4, "MA": 1.3, "HI": 1.7, "WA": 1.2, "CO": 1.1, "OR": 1.1, "NJ": 1.2, 
    "MD": 1.1, "VA": 1.05, "DC": 1.4, "CT": 1.15, "AK": 1.1, "UT": 1.0, "NV": 1.0,
    "AZ": 0.95, "FL": 1.0, "GA": 0.9, "TX": 0.9, "NC": 0.9, "SC": 0.85, "TN": 0.85,
    "PA": 0.9, "IL": 0.9, "OH": 0.8, "MI": 0.8, "IN": 0.75, "KY": 0.75, "AL": 0.75,
    "MS": 0.7, "AR": 0.7, "OK": 0.75, "LA": 0.75, "MO": 0.8, "KS": 0.75, "NE": 0.75,
    "IA": 0.75, "MN": 0.85, "WI": 0.8, "SD": 0.7, "ND": 0.7, "MT": 0.8, "ID": 0.8,
    "WY": 0.75, "NM": 0.75, "DE": 0.9, "VT": 0.9, "NH": 0.95, "ME": 0.85, "RI": 1.0
}

# Property types with characteristics
PROPERTY_TYPES = {
    "Single Family Home": {
        "sqft_range": (1000, 4000),
        "lot_size_range": (0.1, 1.0),  # acres
        "bedroom_range": (2, 5),
        "bathroom_range": (1, 4),
        "year_built_range": (1950, 2023),
        "base_price_range": (150000, 500000),
        "stories_range": (1, 2),
        "garage_spaces_range": (0, 3),
        "has_basement_prob": 0.4
    },
    "Townhouse": {
        "sqft_range": (1000, 2500),
        "lot_size_range": (0.05, 0.25),
        "bedroom_range": (2, 4),
        "bathroom_range": (1, 3),
        "year_built_range": (1970, 2023),
        "base_price_range": (120000, 400000),
        "stories_range": (2, 3),
        "garage_spaces_range": (0, 2),
        "has_basement_prob": 0.3
    },
    "Condominium": {
        "sqft_range": (600, 2000),
        "lot_size_range": (0, 0),  # No individual lot
        "bedroom_range": (1, 3),
        "bathroom_range": (1, 2),
        "year_built_range": (1970, 2023),
        "base_price_range": (100000, 350000),
        "stories_range": (1, 1),  # Single floor
        "garage_spaces_range": (0, 2),
        "has_basement_prob": 0.0
    },
    "Multi-Family Home": {
        "sqft_range": (2000, 5000),
        "lot_size_range": (0.1, 1.0),
        "bedroom_range": (3, 8),
        "bathroom_range": (2, 5),
        "year_built_range": (1920, 2010),
        "base_price_range": (200000, 600000),
        "stories_range": (2, 3),
        "garage_spaces_range": (0, 4),
        "has_basement_prob": 0.5
    },
    "Manufactured Home": {
        "sqft_range": (800, 2400),
        "lot_size_range": (0.1, 0.5),
        "bedroom_range": (2, 4),
        "bathroom_range": (1, 2),
        "year_built_range": (1980, 2023),
        "base_price_range": (80000, 200000),
        "stories_range": (1, 1),
        "garage_spaces_range": (0, 2),
        "has_basement_prob": 0.1
    }
}

def generate_property_address() -> Dict[str, str]:
    """Generate a random US property address."""
    street_numbers = list(range(100, 9999))
    street_names = ["Main", "Oak", "Pine", "Maple", "Cedar", "Elm", "Washington", "Park", 
                    "Lake", "Hill", "River", "Spring", "Sunset", "Valley", "Forest", "Meadow",
                    "Highland", "Willow", "Cypress", "Bayou", "Mountain", "Ocean", "Harbor",
                    "Desert", "Canyon", "Prairie", "Ridge", "Creek", "Brook", "Meadow"]
    street_types = ["St", "Ave", "Blvd", "Dr", "Ln", "Rd", "Way", "Pl", "Ct", "Ter", "Circle"]
    cities = ["Springfield", "Franklin", "Greenville", "Bristol", "Clinton", "Georgetown", 
              "Salem", "Madison", "Oxford", "Arlington", "Burlington", "Manchester", "Milton",
              "Newport", "Ashland", "Fairfield", "Centerville", "Winchester", "Lexington",
              "Oakland", "Riverside", "Pineville", "Charleston", "Jamestown", "Cleveland"]
    
    street_number = random.choice(street_numbers)
    street_name = random.choice(street_names)
    street_type = random.choice(street_types)
    city = random.choice(cities)
    state = random.choice(STATES)
    
    # Generate a realistic zip code pattern
    zip_code = f"{random.randint(10000, 99999)}"
    
    return {
        "street": f"{street_number} {street_name} {street_type}",
        "city": city,
        "state": state,
        "zip_code": zip_code,
        "country": "USA"
    }

def calculate_property_value(property_type: str, characteristics: Dict[str, Any], address: Dict[str, str]) -> int:
    """
    Calculate a realistic property value based on characteristics and location.
    
    Args:
        property_type: Type of property
        characteristics: Property characteristics
        address: Property address
        
    Returns:
        Estimated property value
    """
    if property_type not in PROPERTY_TYPES:
        property_type = "Single Family Home"  # Default
    
    # Start with base price
    base_price_range = PROPERTY_TYPES[property_type]["base_price_range"]
    base_price = random.randint(*base_price_range)
    
    # Adjust for square footage (value per sq ft increases slightly for larger homes)
    sqft = characteristics["square_footage"]
    size_factor = 1.0 + (sqft - base_price_range[0]/200) / 10000
    
    # Adjust for age (newer homes are worth more)
    year_built = characteristics["year_built"]
    current_year = datetime.datetime.now().year
    age = current_year - year_built
    age_factor = max(0.7, 1.0 - (age / 100))  # Older homes lose value but stabilize
    
    # Adjust for location (state-based pricing)
    state = address["state"]
    location_factor = STATE_PRICE_FACTORS.get(state, 1.0)
    
    # Adjust for bedrooms and bathrooms
    bed_bath_factor = 1.0 + (characteristics["bedrooms"] * 0.05) + (characteristics["bathrooms"] * 0.05)
    
    # Adjust for special features
    features_factor = 1.0
    if characteristics.get("has_basement", False):
        features_factor += 0.1
    if characteristics.get("garage_spaces", 0) > 0:
        features_factor += characteristics["garage_spaces"] * 0.05
    
    # Calculate final value
    value = int(base_price * size_factor * age_factor * location_factor * bed_bath_factor * features_factor)
    
    # Add some randomness for market variations (±5%)
    randomness = random.uniform(0.95, 1.05)
    value = int(value * randomness)
    
    # Round to nearest thousand
    value = round(value / 1000) * 1000
    
    return value

def generate_property(property_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a random property with realistic characteristics.
    
    Args:
        property_type: Optional specific property type to generate
        
    Returns:
        Dictionary with property information
    """
    # If no type specified, choose one with realistic distribution
    if not property_type:
        property_types = list(PROPERTY_TYPES.keys())
        weights = [0.6, 0.15, 0.15, 0.05, 0.05]  # Distribution of property types
        property_type = random.choices(property_types, weights=weights, k=1)[0]
    
    # Get property characteristics ranges
    props = PROPERTY_TYPES[property_type]
    
    # Generate address
    address = generate_property_address()
    
    # Generate basic characteristics
    square_footage = random.randint(*props["sqft_range"])
    bedrooms = random.randint(*props["bedroom_range"])
    bathrooms = random.randint(*props["bathroom_range"])
    year_built = random.randint(*props["year_built_range"])
    
    # Generate additional characteristics
    stories = random.randint(*props["stories_range"])
    garage_spaces = random.randint(*props["garage_spaces_range"])
    has_basement = random.random() < props["has_basement_prob"]
    lot_size = round(random.uniform(*props["lot_size_range"]), 2) if props["lot_size_range"][1] > 0 else 0
    
    # Compile characteristics
    characteristics = {
        "square_footage": square_footage,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "year_built": year_built,
        "stories": stories,
        "garage_spaces": garage_spaces,
        "has_basement": has_basement,
        "lot_size": lot_size
    }
    
    # Calculate property value
    estimated_value = calculate_property_value(property_type, characteristics, address)
    
    # Generate zoning information (for multi-family)
    zoning = None
    if property_type == "Multi-Family Home":
        zoning_options = ["R2", "R3", "R4", "MF"]
        zoning = random.choice(zoning_options)
    
    # Generate HOA information (for condos and some townhouses)
    hoa_info = None
    if property_type == "Condominium" or (property_type == "Townhouse" and random.random() < 0.7):
        hoa_info = {
            "monthly_fee": random.choice([150, 200, 250, 300, 350, 400, 450, 500]),
            "includes": []
        }
        
        # Select included services
        possible_includes = ["water", "trash", "sewer", "exterior maintenance", 
                            "roof maintenance", "landscaping", "snow removal", 
                            "pool access", "gym access", "security"]
        
        # Select 3-7 services
        num_services = random.randint(3, 7)
        hoa_info["includes"] = random.sample(possible_includes, num_services)
    
    # Generate property information
    property_info = {
        "address": address,
        "property_type": property_type,
        "estimated_value": estimated_value,
        "year_built": year_built,
        "square_footage": square_footage,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "lot_size_acres": lot_size,
        "stories": stories,
        "garage_spaces": garage_spaces,
        "has_basement": has_basement
    }
    
    # Add conditional fields
    if zoning:
        property_info["zoning"] = zoning
    
    if hoa_info:
        property_info["hoa_info"] = hoa_info
    
    return property_info

def generate_property_set(count: int = 10) -> List[Dict[str, Any]]:
    """
    Generate a diverse set of properties.
    
    Args:
        count: Number of properties to generate
    
    Returns:
        List of property profiles
    """
    properties = []
    
    # Create a distribution of property types
    property_types = list(PROPERTY_TYPES.keys())
    weights = [0.6, 0.15, 0.15, 0.05, 0.05]  # Realistic distribution
    
    for _ in range(count):
        # Select property type with weighting
        property_type = random.choices(property_types, weights=weights, k=1)[0]
        
        # Generate the property
        property_info = generate_property(property_type)
        properties.append(property_info)
    
    return properties

if __name__ == "__main__":
    # Generate and save sample property data
    properties = generate_property_set(20)
    
    # Ensure output directory exists
    import os
    os.makedirs("mock_data/sample_data/properties", exist_ok=True)
    
    # Save to file
    with open("mock_data/sample_data/properties/sample_properties.json", "w") as f:
        json.dump(properties, f, indent=2)
    
    print(f"Generated {len(properties)} property profiles.")
    
    # Display a sample
    print("\nSample property:")
    print(json.dumps(properties[0], indent=2))