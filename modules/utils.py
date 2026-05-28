"""
Utility functions for text processing, skill normalization, and formatting.
"""

import re

# Dictionary to map skill synonyms or common abbreviations to a normalized name
SKILL_SYNONYMS = {
    "js": "javascript",
    "reactjs": "react",
    "react.js": "react",
    "node.js": "nodejs",
    "node": "nodejs",
    "ml": "machine learning",
    "nlp": "natural language processing",
    "postgres": "postgresql",
    "aws": "amazon web services",
    "gcp": "google cloud platform",
    "k8s": "kubernetes",
    "dl": "deep learning",
    "ai": "artificial intelligence",
}

def clean_text(text: str) -> str:
    """
    Cleans raw text by removing extra whitespaces, normalizing line breaks, 
    and converting to lowercase for consistent comparison.
    
    Args:
        text (str): The raw input text.
        
    Returns:
        str: The cleaned lowercase text.
    """
    if not text:
        return ""
    
    # Replace non-breaking spaces and formatting markers
    text = text.replace('\xa0', ' ')
    
    # Remove multiple spaces and newlines
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip().lower()

def normalize_skill(skill: str) -> str:
    """
    Normalizes a single skill name. Strips spaces, converts to lowercase, 
    removes extra punctuation, and maps synonyms.
    
    Args:
        skill (str): The skill name to normalize.
        
    Returns:
        str: The normalized skill name.
    """
    if not skill:
        return ""
    
    # Clean the skill name
    cleaned = skill.strip().lower()
    cleaned = re.sub(r'[\.\-\s]+', ' ', cleaned).strip() # replace dots/hyphens/spaces with space
    
    # Compress multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Check direct synonyms after initial cleaning
    if cleaned in SKILL_SYNONYMS:
        return SKILL_SYNONYMS[cleaned]
    
    # Check original cleaned without space-compression for synonyms
    original_cleaned = skill.strip().lower()
    if original_cleaned in SKILL_SYNONYMS:
        return SKILL_SYNONYMS[original_cleaned]
        
    return cleaned

def normalize_skills(skills: list) -> list:
    """
    Normalizes a list of skills. Removes duplicates and empty values.
    
    Args:
        skills (list): Raw list of skill strings.
        
    Returns:
        list: Sorted list of normalized, unique skill strings.
    """
    if not skills:
        return []
    
    normalized_set = set()
    for s in skills:
        norm = normalize_skill(s)
        if norm:
            normalized_set.add(norm)
            
    return sorted(list(normalized_set))

def parse_experience_years(text: str) -> float:
    """
    Extracts total years of experience from text descriptions using regex.
    Searches for patterns like '5 years', '3+ years', '2.5 years of experience'.
    
    Args:
        text (str): The text block to parse.
        
    Returns:
        float: The extracted years of experience, or 0.0 if not found.
    """
    if not text:
        return 0.0
        
    # Pattern to find numbers followed by "year", "years", "yr", "yrs" of experience
    # Supports decimals (e.g. 2.5 years) and + signs (e.g. 5+)
    pattern = r'(\d+(?:\.\d+)?)\s*\+?\s*(?:year|yr)s?\b'
    matches = re.findall(pattern, text, re.IGNORECASE)
    
    if not matches:
        return 0.0
        
    # Convert matches to float and return the maximum value found
    years = [float(val) for val in matches]
    return max(years) if years else 0.0

def format_phone(phone_str: str) -> str:
    """
    Cleans phone number string to remove non-numeric characters (except leading +).
    
    Args:
        phone_str (str): The raw phone number.
        
    Returns:
        str: Standardized format.
    """
    if not phone_str:
        return ""
        
    # Retain only digits and leading '+'
    cleaned = re.sub(r'(?<!^)\+|[^\d+]', '', phone_str.strip())
    return cleaned
