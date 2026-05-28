"""
Resume parsing class to extract candidate name, email, phone, skills, and experience.
"""

import re
import logging
from typing import Dict, Any, List
from modules.utils import clean_text, normalize_skills, parse_experience_years, format_phone

# Configure logger
logger = logging.getLogger(__name__)

# List of common industry skills to match against resume text
SKILL_TAXONOMY = [
    "python", "sql", "java", "javascript", "c++", "c#", "ruby", "php", "go", "rust",
    "html", "css", "react", "angular", "vue", "node.js", "nodejs", "express", "django",
    "flask", "fastapi", "spring", "asp.net", "dotnet", ".net", "bootstrap",
    "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn", "pandas", "numpy",
    "scipy", "nltk", "spacy", "opencv", "tableau", "powerbi", "excel",
    "aws", "azure", "gcp", "docker", "kubernetes", "git", "jenkins", "ansible",
    "terraform", "ci/cd", "linux", "unix", "postgresql", "mysql", "mongodb", "redis",
    "sqlite", "oracle", "elasticsearch", "graphql", "rest api", "api", "microservices",
    "machine learning", "deep learning", "natural language processing", "nlp",
    "computer vision", "data analysis", "data science", "data engineering",
    "agile", "scrum", "project management", "product management", "system design"
]

class ResumeParser:
    """
    Parses resume text to extract candidate details like Name, Email, Phone,
    Skills, and total Years of Experience.
    """
    
    def __init__(self, raw_text: str):
        """
        Initializes the parser with the raw resume text.
        
        Args:
            raw_text (str): The raw text extracted from the resume.
        """
        self.raw_text = raw_text or ""
        self.clean_text_content = clean_text(self.raw_text)
        
        # Load spaCy NLP model if available, fallback gracefully if not
        self.nlp = None
        try:
            import spacy
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                # If model is not downloaded, try to log and skip
                logger.warning("spaCy model 'en_core_web_sm' not found. Falling back to heuristic-based name extraction.")
        except ImportError:
            logger.warning("spaCy is not installed. Falling back to heuristic-based name extraction.")

    def parse(self) -> Dict[str, Any]:
        """
        Orchestrates the parsing process and returns a dictionary of extracted information.
        
        Returns:
            dict: Extracted resume fields.
        """
        if not self.raw_text.strip():
            return {
                "name": "Unknown",
                "email": "",
                "phone": "",
                "skills": [],
                "experience_years": 0.0
            }
            
        return {
            "name": self.extract_name(),
            "email": self.extract_email(),
            "phone": self.extract_phone(),
            "skills": self.extract_skills(),
            "experience_years": self.extract_experience()
        }

    def extract_name(self) -> str:
        """
        Extracts the candidate's name. First attempts using spaCy NER on the top portion of the resume,
        then falls back to checking the first non-empty lines.
        
        Returns:
            str: Extracted name or 'Unknown'.
        """
        if not self.raw_text.strip():
            return "Unknown"

        # 1. NLP approach (spaCy)
        if self.nlp:
            # We look at the first 300 characters, which usually contain the name and contact info
            doc = self.nlp(self.raw_text[:300])
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    name = ent.text.strip()
                    # Validate that the name is not just a label or single word
                    if len(name.split()) >= 2 and not any(term in name.lower() for term in ["resume", "cv", "curriculum", "vitae"]):
                        # Remove newlines/extra spaces inside name
                        return re.sub(r'\s+', ' ', name)

        # 2. Heuristic fallback: check the first 3 non-empty lines
        lines = [line.strip() for line in self.raw_text.split('\n') if line.strip()]
        for line in lines[:3]:
            # Skip lines containing email, phone, URLs, or labels
            if "@" in line or any(char.isdigit() for char in line) or "http" in line:
                continue
            # A valid name is usually 2 or 3 capitalized words (e.g. John Doe, Jane A. Smith)
            words = line.split()
            if 2 <= len(words) <= 4:
                # Basic check for capital letters
                if all(word[0].isupper() or word == "A." for word in words if word):
                    return line

        # If all else fails, use the first non-empty line
        if lines:
            first_line = lines[0]
            if len(first_line) < 50: # Avoid returning long summary paragraphs
                return first_line
                
        return "Unknown"

    def extract_email(self) -> str:
        """
        Extracts email address using regex.
        
        Returns:
            str: Extracted email or empty string if not found.
        """
        # Common regex for email validation
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        match = re.search(email_pattern, self.raw_text)
        return match.group(0).strip() if match else ""

    def extract_phone(self) -> str:
        """
        Extracts phone number using regex, covering standard international/domestic formats.
        
        Returns:
            str: Extracted and formatted phone number or empty string.
        """
        # Matches patterns like +1-123-456-7890, (123) 456-7890, 123.456.7890, 1234567890
        phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        match = re.search(phone_pattern, self.raw_text)
        return format_phone(match.group(0)) if match else ""

    def extract_skills(self) -> List[str]:
        """
        Extracts candidate skills by scanning the resume text for keywords
        from a defined skill taxonomy.
        
        Returns:
            List[str]: Sorted list of unique, normalized skills found in the resume.
        """
        extracted = []
        for skill in SKILL_TAXONOMY:
            # We want to match whole words/phrases to prevent partial matches 
            # e.g., 'go' shouldn't match 'google' or 'django'
            
            # Handle special characters in skill names like C++, C#, .NET
            escaped_skill = re.escape(skill)
            
            if skill in ["c++", "c#", ".net"]:
                # Custom boundary matching for skills ending or starting with symbols
                if skill == "c++":
                    pattern = r'\bc\+\+(?:\b|[^\w]|$)'
                elif skill == "c#":
                    pattern = r'\bc\#(?:\b|[^\w]|$)'
                elif skill == ".net":
                    pattern = r'(?:^|[^\w])\.net(?:\b|$)'
            else:
                pattern = r'\b' + escaped_skill + r'\b'
                
            if re.search(pattern, self.clean_text_content, re.IGNORECASE):
                extracted.append(skill)
                
        # Also look for explicit comma-separated skills in a "Skills:" block if any
        # This acts as an auxiliary extraction method
        skills_section_match = re.search(
            r'(?:skills|technologies|technical skills|core competencies)\s*[:\-–]\s*(.*?)(?:\n\n|\n[A-Z]|$)', 
            self.raw_text, 
            re.IGNORECASE | re.DOTALL
        )
        if skills_section_match:
            raw_skills_block = skills_section_match.group(1)
            # Split by commas, semicolons, bullets, or bars
            split_skills = re.split(r'[,;•|\t]|\s{2,}', raw_skills_block)
            for raw_sk in split_skills:
                cleaned_sk = raw_sk.strip()
                if cleaned_sk and len(cleaned_sk) < 30: # discard long descriptive lines
                    extracted.append(cleaned_sk)

        return normalize_skills(extracted)

    def extract_experience(self) -> float:
        """
        Extracts total experience in years. First scans for total experience keywords,
        otherwise parses all mentions of experience throughout the resume.
        
        Returns:
            float: Number of years of experience.
        """
        # Look for explicit summaries like "5 years of experience", "overall 4+ years of experience"
        summary_patterns = [
            r'(\d+(?:\.\d+)?)\s*\+?\s*(?:year|yr)s?\s*(?:of)?\s*(?:overall|total|professional)?\s*experience',
            r'(?:overall|total|professional)\s*experience\s*(?:of)?\s*(\d+(?:\.\d+)?)\s*\+?\s*(?:year|yr)s?'
        ]
        
        for pat in summary_patterns:
            match = re.search(pat, self.raw_text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        
        # If no explicit summary phrase is found, fallback to parsing all experience numbers
        # and finding the maximum or scanning the job descriptions.
        # We will use parse_experience_years to look for all mentions and extract the max
        # because taking the max of years mentions in a resume is a strong heuristic for overall exp
        # when a specific total is not stated.
        return parse_experience_years(self.raw_text)
