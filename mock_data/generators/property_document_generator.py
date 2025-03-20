"""
Property Document Generator

This module generates mock property-related documents for mortgage applications:
- Property appraisals

These are simplified representations with the key data that would be extracted
by the document processing agent.
"""

import random
import datetime
import uuid
from typing import Dict, Any, List, Optional

def generate_property_appraisal(property_data: Dict[str, Any], 
                               applicant_data: Dict[str, Any], 
                               appraisal_date: str) -> Dict[str, Any]:
    """
    Generate a mock property appraisal for a mortgage application.
    
    Args:
        property_data: Property information
        applicant_data: Applicant information (for reference)
        appraisal_date: Date of the appraisal
        
    Returns:
        Dictionary representing a property appraisal
    """
    property_address = property_data["address"]
    property_type = property_data["property_type"]
    estimated_value = property_data["estimated_value"]
    
    # Get property characteristics
    square_footage = property_data.get("square_footage", 1800)
    bedrooms = property_data.get("bedrooms", 3)
    bathrooms = property_data.get("bathrooms", 2)
    lot_size_acres = property_data.get("lot_size_acres", 0.25)
    year_built = property_data.get("year_built", 1980)
    
    # Generate appraisal company info
    appraisal_companies = [
        "Accurate Appraisal Services",
        "Premier Property Valuation",
        "National Appraisal Group",
        "Allied Residential Appraisers",
        "Metropolitan Valuation Services"
    ]
    
    appraiser_company = random.choice(appraisal_companies)
    appraiser_name = random.choice([
        "Michael Johnson",
        "Sarah Williams",
        "David Miller",
        "Jennifer Davis",
        "Robert Wilson",
        "Elizabeth Moore",
        "Thomas Anderson",
        "Patricia Taylor"
    ])
    
    appraiser_license = f"RA-{random.randint(10000, 99999)}"
    
    # Generate comparable properties
    num_comps = random.randint(3, 6)
    comparable_properties = generate_comparable_properties(
        property_data,
        num_comps,
        appraisal_date
    )
    
    # Calculate appraisal adjustments
    condition_adjustment = 0
    if random.random() < 0.7:
        # 70% chance of some adjustment for condition
        condition_factor = random.choice(["excellent", "good", "average", "fair", "poor"])
        if condition_factor == "excellent":
            condition_adjustment = round(estimated_value * random.uniform(0.03, 0.05))
        elif condition_factor == "good":
            condition_adjustment = round(estimated_value * random.uniform(0.01, 0.03))
        elif condition_factor == "average":
            condition_adjustment = 0
        elif condition_factor == "fair":
            condition_adjustment = -round(estimated_value * random.uniform(0.01, 0.03))
        else:  # poor
            condition_adjustment = -round(estimated_value * random.uniform(0.05, 0.10))
    
    # Market trends adjustment
    market_adjustment = 0
    market_trend = random.choice(["appreciating", "stable", "depreciating"])
    if market_trend == "appreciating":
        market_adjustment = round(estimated_value * random.uniform(0.01, 0.04))
    elif market_trend == "depreciating":
        market_adjustment = -round(estimated_value * random.uniform(0.01, 0.03))
    
    # Calculate final appraised value
    appraised_value = estimated_value + condition_adjustment + market_adjustment
    
    # Round to nearest thousand
    appraised_value = round(appraised_value / 1000) * 1000
    
    # Generate property features
    features = []
    possible_features = [
        "Central air conditioning", 
        "Forced air heating",
        "Fireplace",
        "Hardwood floors",
        "Updated kitchen",
        "Renovated bathrooms",
        "Finished basement",
        "Attached garage",
        "Detached garage",
        "Covered patio",
        "Deck",
        "Swimming pool",
        "Fenced yard",
        "Sprinkler system",
        "Solar panels",
        "Smart home features"
    ]
    
    num_features = random.randint(3, 8)
    features = random.sample(possible_features, num_features)
    
    # Generate property condition assessments
    condition_ratings = {
        "exterior": random.choice(["Excellent", "Good", "Average", "Fair", "Poor"]),
        "interior": random.choice(["Excellent", "Good", "Average", "Fair", "Poor"]),
        "foundation": random.choice(["Excellent", "Good", "Average", "Fair"]),
        "roof": random.choice(["Excellent", "Good", "Average", "Fair", "Poor"]),
        "electrical": random.choice(["Excellent", "Good", "Average", "Fair"]),
        "plumbing": random.choice(["Excellent", "Good", "Average", "Fair"]),
        "overall": random.choice(["Excellent", "Good", "Average", "Fair", "Poor"])
    }
    
    # Generate document
    document = {
        "document_type": "Property Appraisal",
        "appraisal_date": appraisal_date,
        "property": {
            "address": property_address,
            "property_type": property_type,
            "square_footage": square_footage,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "lot_size_acres": lot_size_acres,
            "year_built": year_built,
            "features": features
        },
        "appraiser": {
            "name": appraiser_name,
            "company": appraiser_company,
            "license_number": appraiser_license
        },
        "valuation": {
            "estimated_value": estimated_value,
            "condition_adjustment": condition_adjustment,
            "market_adjustment": market_adjustment,
            "appraised_value": appraised_value,
            "price_per_sqft": round(appraised_value / square_footage, 2),
            "valuation_method": "Sales Comparison Approach"
        },
        "condition_assessment": condition_ratings,
        "market_conditions": {
            "trend": market_trend,
            "average_days_on_market": random.randint(20, 120),
            "supply_and_demand": random.choice(["Oversupply", "Balanced", "Undersupply"])
        },
        "comparable_properties": comparable_properties,
        "metadata": {
            "document_id": str(uuid.uuid4()),
            "extraction_confidence": random.uniform(0.85, 0.99)
        }
    }
    
    return document

def generate_comparable_properties(property_data: Dict[str, Any], 
                                  num_comps: int, 
                                  appraisal_date: str) -> List[Dict[str, Any]]:
    """
    Generate comparable properties for a property appraisal.
    
    Args:
        property_data: Main property information
        num_comps: Number of comparable properties to generate
        appraisal_date: Date of the appraisal
        
    Returns:
        List of comparable properties
    """
    comps = []
    base_value = property_data["estimated_value"]
    square_footage = property_data.get("square_footage", 1800)
    bedrooms = property_data.get("bedrooms", 3)
    bathrooms = property_data.get("bathrooms", 2)
    lot_size_acres = property_data.get("lot_size_acres", 0.25)
    year_built = property_data.get("year_built", 1980)
    
    # Property address components for generating nearby addresses
    property_street = property_data["address"]["street"]
    property_city = property_data["address"]["city"]
    property_state = property_data["address"]["state"]
    property_zip = property_data["address"]["zip_code"]
    
    # Get the street number and name
    street_parts = property_street.split(" ", 1)
    if len(street_parts) == 2:
        street_num = int(street_parts[0]) if street_parts[0].isdigit() else 100
        street_name = street_parts[1]
    else:
        street_num = 100
        street_name = property_street
    
    # Generate nearby street names
    nearby_streets = [
        street_name,
        "Park " + street_name,
        street_name.replace("St", "Ave").replace("Ave", "St"),
        "North " + street_name,
        "South " + street_name,
        "East " + street_name,
        "West " + street_name,
        street_name.replace("Lane", "Road").replace("Road", "Lane"),
        street_name + " Circle",
        street_name + " Court"
    ]
    
    appraisal_date_obj = datetime.datetime.strptime(appraisal_date, "%Y-%m-%d")
    
    for i in range(num_comps):
        # Calculate variations for comparable property
        comp_sf = square_footage + random.randint(-200, 200)
        comp_bedrooms = max(1, bedrooms + random.randint(-1, 1))
        comp_bathrooms = max(1, bathrooms + random.randint(-1, 1))
        comp_lot = max(0.1, lot_size_acres + random.uniform(-0.15, 0.15))
        comp_year = max(1900, year_built + random.randint(-15, 15))
        
        # Calculate a reasonable comp value based on the variations
        sf_adjustment = ((comp_sf - square_footage) / square_footage) * 0.4
        bedroom_adjustment = ((comp_bedrooms - bedrooms) / max(1, bedrooms)) * 0.2
        bathroom_adjustment = ((comp_bathrooms - bathrooms) / max(1, bathrooms)) * 0.2
        lot_adjustment = ((comp_lot - lot_size_acres) / max(0.1, lot_size_acres)) * 0.1
        year_adjustment = ((comp_year - year_built) / max(1, year_built - 1900)) * 0.1
        
        total_adjustment = sf_adjustment + bedroom_adjustment + bathroom_adjustment + lot_adjustment + year_adjustment
        comp_value = base_value * (1 + total_adjustment + random.uniform(-0.05, 0.05))
        comp_value = round(comp_value / 1000) * 1000  # Round to nearest thousand
        
        # Generate a nearby address
        comp_street_num = street_num + random.randint(-20, 20) + (i * 4)
        comp_street = random.choice(nearby_streets)
        comp_address = {
            "street": f"{comp_street_num} {comp_street}",
            "city": property_city,
            "state": property_state,
            "zip_code": property_zip
        }
        
        # Generate a sale date within the last 6 months
        days_ago = random.randint(1, 180)
        sale_date = (appraisal_date_obj - datetime.timedelta(days=days_ago)).strftime("%Y-%m-%d")
        
        # Create the comparable property
        comp = {
            "address": comp_address,
            "sale_date": sale_date,
            "sale_price": comp_value,
            "square_footage": comp_sf,
            "bedrooms": comp_bedrooms,
            "bathrooms": comp_bathrooms,
            "lot_size_acres": round(comp_lot, 2),
            "year_built": comp_year,
            "distance_miles": round(random.uniform(0.1, 1.5), 1),
            "price_per_sqft": round(comp_value / comp_sf, 2),
            "adjustment_factors": []
        }
        
        # Add adjustment factors if there are significant differences
        if abs(comp_sf - square_footage) > 100:
            comp["adjustment_factors"].append(f"Square footage: {comp_sf} vs {square_footage}")
        
        if comp_bedrooms != bedrooms:
            comp["adjustment_factors"].append(f"Bedrooms: {comp_bedrooms} vs {bedrooms}")
        
        if comp_bathrooms != bathrooms:
            comp["adjustment_factors"].append(f"Bathrooms: {comp_bathrooms} vs {bathrooms}")
        
        if abs(comp_lot - lot_size_acres) > 0.1:
            comp["adjustment_factors"].append(f"Lot size: {comp_lot:.2f} acres vs {lot_size_acres:.2f} acres")
        
        if abs(comp_year - year_built) > 10:
            comp["adjustment_factors"].append(f"Year built: {comp_year} vs {year_built}")
        
        comps.append(comp)
    
    return comps

if __name__ == "__main__":
    # Test function - generate sample documents
    sample_property = {
        "address": {
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip_code": "90210",
            "country": "USA"
        },
        "property_type": "Single Family Home",
        "estimated_value": 450000,
        "year_built": 1995,
        "square_footage": 1800,
        "bedrooms": 3,
        "bathrooms": 2,
        "lot_size_acres": 0.25
    }
    
    sample_applicant = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "(555) 123-4567",
        "address": {
            "street": "456 Other St",
            "city": "Somewhere",
            "state": "CA",
            "zip_code": "90211",
            "country": "USA"
        },
    }
    
    import json
    
    # Generate property appraisal
    appraisal = generate_property_appraisal(sample_property, sample_applicant, "2023-05-15")
    print("Property Appraisal:")
    print(json.dumps(appraisal, indent=2))
    
    # Print key details
    print(f"\nAppraised Value: ${appraisal['valuation']['appraised_value']}")
    print(f"Market Trend: {appraisal['market_conditions']['trend']}")
    print(f"Number of Comps: {len(appraisal['comparable_properties'])}")