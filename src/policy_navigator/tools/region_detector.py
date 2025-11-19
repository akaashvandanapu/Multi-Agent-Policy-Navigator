"""
Region Detection Tool - Detects if query mentions AP or non-AP regions
Detects states, cities, and districts to determine if query is about Andhra Pradesh
"""

import json
from typing import Dict, List
from crewai.tools import tool

# Andhra Pradesh Districts (comprehensive list)
AP_DISTRICTS = [
    "anantapur", "kadapa", "cuddapah", "kurnool", "chittoor", "krishna", 
    "guntur", "prakasam", "east godavari", "west godavari", "visakhapatnam", 
    "vizag", "vishakhapatnam", "srikakulam", "vizianagaram", "nellore", 
    "nandyal", "eluru", "kakinada", "rajahmundry", "tirupati", "vijayawada",
    "amaravati", "kurnool", "ongole", "chirala", "tenali", "machilipatnam",
    "bhimavaram", "tadepalligudem", "palakollu", "narasaraopet", "guntur city"
]

# Andhra Pradesh Cities
AP_CITIES = [
    "vijayawada", "visakhapatnam", "vizag", "guntur", "nellore", "kurnool",
    "rajahmundry", "kakinada", "tirupati", "eluru", "ongole", "anantapur",
    "kadapa", "cuddapah", "chittoor", "nandyal", "machilipatnam", "tenali",
    "proddatur", "chirala", "bhimavaram", "tadepalligudem", "palakollu",
    "narasaraopet", "amaravati", "srikakulam", "vizianagaram"
]

# Indian States (excluding Andhra Pradesh)
NON_AP_STATES = [
    "telangana", "maharashtra", "karnataka", "tamil nadu", "kerala",
    "odisha", "orissa", "west bengal", "bihar", "uttar pradesh", "up",
    "madhya pradesh", "mp", "rajasthan", "gujarat", "punjab", "haryana",
    "himachal pradesh", "hp", "uttarakhand", "jharkhand", "chhattisgarh",
    "assam", "manipur", "meghalaya", "mizoram", "nagaland", "tripura",
    "arunachal pradesh", "sikkim", "goa", "delhi", "jammu and kashmir",
    "j&k", "ladakh", "puducherry", "pondicherry", "andaman and nicobar",
    "daman and diu", "dadra and nagar haveli", "lakshadweep"
]

# Major non-AP cities (for better detection)
NON_AP_MAJOR_CITIES = [
    "hyderabad", "secunderabad", "mumbai", "pune", "bangalore", "bengaluru",
    "chennai", "madras", "kochi", "cochin", "thiruvananthapuram", "trivandrum",
    "bhubaneswar", "kolkata", "calcutta", "patna", "lucknow", "kanpur",
    "bhopal", "jaipur", "ahmedabad", "surat", "chandigarh", "gurgaon",
    "noida", "dehradun", "ranchi", "raipur", "guwahati", "imphal",
    "shillong", "aizawl", "kohima", "agartala", "itanagar", "gangtok",
    "panaji", "new delhi", "srinagar", "jammu", "leh", "kashmir"
]

# AP state variations
AP_VARIANTS = [
    "andhra pradesh", "andhra", "ap", "ap state", "andhra pradesh state"
]


@tool("Region Detector Tool")
def region_detector_tool(query: str) -> str:
    """Detect if query mentions regions in Andhra Pradesh or other states/cities/districts.
    
    This tool analyzes the query text to identify:
    - Andhra Pradesh regions (districts, cities, state name)
    - Non-AP regions (other Indian states, cities)
    - Returns structured information about detected regions
    
    Use this tool FIRST when analyzing a query to determine if it's about AP or other regions.
    This helps decide whether to use RAG (for AP) or web search (for non-AP).
    
    Args:
        query: User query text to analyze for region mentions.
    
    Returns:
        JSON string with region detection results:
        {
            "is_ap_region": bool,
            "detected_regions": List[str],
            "region_type": "ap" | "non_ap" | "mixed",
            "ap_regions": List[str],
            "non_ap_regions": List[str]
        }
        
    Note: If no region is detected in the query, defaults to Andhra Pradesh.
    In this case, region_type will be "ap" and "Andhra Pradesh" will be added to ap_regions.
    """
    query_lower = query.lower()
    
    detected_ap_regions = []
    detected_non_ap_regions = []
    
    # Check for AP state name variations
    for variant in AP_VARIANTS:
        if variant in query_lower:
            detected_ap_regions.append("Andhra Pradesh")
            break
    
    # Check for AP districts
    for district in AP_DISTRICTS:
        if district in query_lower:
            # Capitalize first letter of each word
            formatted = ' '.join(word.capitalize() for word in district.split())
            if formatted not in detected_ap_regions:
                detected_ap_regions.append(formatted)
    
    # Check for AP cities
    for city in AP_CITIES:
        if city in query_lower:
            formatted = city.capitalize()
            if formatted not in detected_ap_regions:
                detected_ap_regions.append(formatted)
    
    # Check for non-AP states
    for state in NON_AP_STATES:
        if state in query_lower:
            # Capitalize properly
            if state in ["up", "mp", "hp", "j&k"]:
                formatted = state.upper()
            else:
                formatted = ' '.join(word.capitalize() for word in state.split())
            if formatted not in detected_non_ap_regions:
                detected_non_ap_regions.append(formatted)
    
    # Check for non-AP major cities
    for city in NON_AP_MAJOR_CITIES:
        if city in query_lower:
            formatted = ' '.join(word.capitalize() for word in city.split())
            if formatted not in detected_non_ap_regions:
                detected_non_ap_regions.append(formatted)
    
    # Determine region type
    has_ap = len(detected_ap_regions) > 0
    has_non_ap = len(detected_non_ap_regions) > 0
    
    if has_ap and has_non_ap:
        region_type = "mixed"
        is_ap_region = False  # Mixed means we should use web search
    elif has_ap:
        region_type = "ap"
        is_ap_region = True
    elif has_non_ap:
        region_type = "non_ap"
        is_ap_region = False
    else:
        # Default to Andhra Pradesh when no region is mentioned
        region_type = "ap"
        is_ap_region = True
        # Explicitly add Andhra Pradesh to detected regions for clarity
        if "Andhra Pradesh" not in detected_ap_regions:
            detected_ap_regions.append("Andhra Pradesh")
    
    # Combine all detected regions
    all_detected = detected_ap_regions + detected_non_ap_regions
    
    result = {
        "is_ap_region": is_ap_region,
        "detected_regions": all_detected,
        "region_type": region_type,
        "ap_regions": detected_ap_regions,
        "non_ap_regions": detected_non_ap_regions
    }
    
    return json.dumps(result, indent=2)

