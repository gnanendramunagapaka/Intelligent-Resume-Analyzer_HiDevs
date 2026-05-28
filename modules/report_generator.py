"""
Report generation class to format candidate evaluations and output them to JSON files.
"""

import os
import re
from datetime import datetime
from typing import Dict, Any
from modules.file_handler import FileHandler

class ReportGenerator:
    """
    Formats the evaluation results of a candidate, appends metadata such as 
    timestamps, and saves the final screening report as a JSON file.
    """
    
    def __init__(self, output_dir: str = "data/reports"):
        """
        Initializes the report generator.
        
        Args:
            output_dir (str): Directory where reports should be saved.
        """
        self.output_dir = output_dir
        FileHandler.ensure_directory(self.output_dir)

    def generate(self, match_results: Dict[str, Any], candidate_info: Dict[str, Any]) -> str:
        """
        Assembles the report dictionary, serializes it, and saves it to a file.
        
        Args:
            match_results (dict): Match scores, missing skills, etc. from ResumeMatcher.
            candidate_info (dict): Parsed details from ResumeParser (email, phone, etc.).
            
        Returns:
            str: Absolute or relative path of the generated JSON report.
        """
        # Current local timestamp
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Build structured report
        report_data = {
            "metadata": {
                "system_name": "Intelligent Resume Analyzer",
                "version": "1.0.0",
                "generated_at": timestamp
            },
            "candidate_profile": {
                "name": candidate_info.get("name", "Unknown"),
                "email": candidate_info.get("email", ""),
                "phone": candidate_info.get("phone", ""),
                "extracted_skills": candidate_info.get("skills", []),
                "experience_years": candidate_info.get("experience_years", 0.0)
            },
            "evaluation": {
                "job_title": match_results.get("job_title", "Position"),
                "final_match_score": match_results.get("match_score", 0.0),
                "skills_score": match_results.get("skills_score", 0.0),
                "experience_score": match_results.get("experience_score", 0.0),
                "semantic_similarity_score": match_results.get("semantic_similarity_score", 0.0),
                "matched_skills": match_results.get("matched_skills", []),
                "missing_skills": match_results.get("missing_skills", []),
                "matched_required_skills": match_results.get("matched_required_skills", []),
                "missing_required_skills": match_results.get("missing_required_skills", []),
                "matched_preferred_skills": match_results.get("matched_preferred_skills", []),
                "missing_preferred_skills": match_results.get("missing_preferred_skills", []),
                "recommendation": match_results.get("recommendation", "Reject"),
                "min_experience_required": match_results.get("min_experience_required", 0.0)
            }
        }
        
        # Create a safe filename using the candidate name
        raw_name = candidate_info.get("name", "candidate").lower()
        # Replace non-alphanumeric characters with underscores
        safe_name = re.sub(r'[^a-z0-9]', '_', raw_name)
        # Trim multiple underscores
        safe_name = re.sub(r'_+', '_', safe_name).strip('_')
        
        filename = f"report_{safe_name}_{file_timestamp}.json"
        report_path = os.path.join(self.output_dir, filename)
        
        # Save to file
        FileHandler.write_json(report_path, report_data)
        
        return report_path
