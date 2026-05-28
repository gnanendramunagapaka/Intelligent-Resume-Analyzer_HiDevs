"""
Main entry point for the Resume Analyzer System.
Orchestrates resume parsing, requirement matching, report generation, and CLI visualization.
"""

import os
import sys
import argparse
from datetime import datetime
from typing import Dict, Any

from modules.file_handler import FileHandler
from modules.parser import ResumeParser
from modules.matcher import ResumeMatcher
from modules.report_generator import ReportGenerator

# Try to reconfigure stdout to support UTF-8 formatting on Windows terminals
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# Enable ANSI terminal coloring on Windows
if sys.platform == "win32":
    os.system("color")

# ANSI Color Codes
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"
RESET = "\033[0m"

def get_recommendation_color(rec: str) -> str:
    """Returns color ANSI code based on hiring recommendation."""
    if rec == "Strong Match":
        return GREEN
    elif rec == "Consider":
        return YELLOW
    return RED

def print_banner() -> None:
    """Prints a styled professional ASCII banner."""
    print(f"{CYAN}{BOLD}" + "="*70)
    print("  ╦╔╗╔╔╦╗╔═╗╦  ╦  ╦╔═╗╔═╗╔╗╔╔╦╗  ╦═╗╔═╗╔═╗╦ ╦╔╦╗╔═╗  ╔═╗╔╗╔╔═╗╦  ╦ ╦╔═╗╔═╗╦═╗")
    print("  ║║║║ ║ ║╣ ║  ║  ║║ ╦║╣ ║║║ ║   ╠╦╝║╣ ╚═╗║ ║║║║║╣   ╠═╣║║║╠═╣║  ╚╦╝┌─┘║╣ ╠╦╝")
    print("  ╩╝╚╝ ╩ ╚═╝╩═╝╩═╝╩╚═╝╚═╝╝╚╝ ╩   ╩╚═╚═╝╚═╝╚═╝╩ ╩╚═╝  ╩ ╩╝╚╝╩ ╩╩═╝ ╩ └─┘╚═╝╩╚═")
    print("="*70 + f"{RESET}\n")

def print_report_card(report: Dict[str, Any], save_path: str) -> None:
    """
    Renders a clean, formatted report card in the terminal.
    
    Args:
        report (dict): The compiled matching report.
        save_path (str): Path where the report was saved.
    """
    profile = report["candidate_profile"]
    eval_data = report["evaluation"]
    
    rec = eval_data["recommendation"]
    rec_color = get_recommendation_color(rec)
    
    # 1. Header Box
    print(f"{BOLD}{BLUE}┌────────────────────────────────────────────────────────────────────┐")
    print(f"│ {RESET}{BOLD}CANDIDATE ANALYSIS: {profile['name'].upper():<46} │")
    print(f"{BOLD}{BLUE}├────────────────────────────────────────────────────────────────────┤{RESET}")
    
    # 2. Contact details
    email = profile["email"] or "N/A"
    phone = profile["phone"] or "N/A"
    print(f"  {BOLD}Email:{RESET} {email:<32} {BOLD}Phone:{RESET} {phone}")
    print(f"  {BOLD}Experience:{RESET} {profile['experience_years']} years (Required: {eval_data['min_experience_required']} years)")
    print(f"{BLUE}  " + "─"*66 + f"{RESET}")
    
    # 3. Job title
    print(f"  {BOLD}Position Applied:{RESET} {eval_data['job_title']}")
    print(f"{BLUE}  " + "─"*66 + f"{RESET}")
    
    # 4. Scores
    score = eval_data["final_match_score"]
    score_color = GREEN if score >= 85 else (YELLOW if score >= 70 else RED)
    
    print(f"  {BOLD}Scoring Breakdown:{RESET}")
    print(f"    • Skills Score (70% weight):      {eval_data['skills_score']}/100")
    print(f"    • Experience Score (30% weight):  {eval_data['experience_score']}/100")
    print(f"    • Semantic NLP Similarity:        {eval_data['semantic_similarity_score']}/100")
    print(f"    • {BOLD}OVERALL MATCH SCORE:            {score_color}{BOLD}{score}%{RESET}")
    print(f"{BLUE}  " + "─"*66 + f"{RESET}")
    
    # 5. Skills analysis
    print(f"  {BOLD}Skills Matching:{RESET}")
    
    # Required skills
    matched_req = ", ".join(eval_data["matched_required_skills"]) or "None"
    missing_req = ", ".join(eval_data["missing_required_skills"]) or "None"
    print(f"    {GREEN}✔ Matched Required:{RESET} {matched_req}")
    print(f"    {RED}✘ Missing Required:{RESET} {missing_req}")
    
    # Preferred skills
    matched_pref = ", ".join(eval_data["matched_preferred_skills"]) or "None"
    missing_pref = ", ".join(eval_data["missing_preferred_skills"]) or "None"
    print(f"    {GREEN}✔ Matched Preferred:{RESET} {matched_pref}")
    print(f"    {RED}✘ Missing Preferred:{RESET} {missing_pref}")
    
    print(f"{BLUE}  " + "─"*66 + f"{RESET}")
    
    # 6. Recommendation
    print(f"  {BOLD}Hiring Recommendation:  {rec_color}{BOLD}[ {rec.upper()} ]{RESET}")
    print(f"{BOLD}{BLUE}└────────────────────────────────────────────────────────────────────┘{RESET}")
    
    # 7. File location
    print(f"{GREEN}✔ Report saved successfully at:{RESET} {save_path}\n")

def main():
    """Main execution block."""
    parser = argparse.ArgumentParser(description="Intelligent Resume Analyzer CLI Tool")
    parser.add_argument(
        "--resume", 
        type=str, 
        default=os.path.join("data", "resumes", "sample_resume.txt"),
        help="Path to the resume file (PDF, DOCX, TXT)"
    )
    parser.add_argument(
        "--job", 
        type=str, 
        default=os.path.join("data", "jobs", "job_description.json"),
        help="Path to the job description JSON file"
    )
    args = parser.parse_args()

    print_banner()

    try:
        # Step 1: File check & path resolution
        resume_path = args.resume
        job_path = args.job

        print(f"{BLUE}[1/5] Validating input files...{RESET}")
        if not os.path.exists(resume_path):
            print(f"{RED}Error: Resume file not found at '{resume_path}'{RESET}", file=sys.stderr)
            sys.exit(1)
            
        if not os.path.exists(job_path):
            print(f"{RED}Error: Job description file not found at '{job_path}'{RESET}", file=sys.stderr)
            sys.exit(1)

        # Step 2: Load and parse files
        print(f"{BLUE}[2/5] Extracting content and parsing candidate details...{RESET}")
        try:
            resume_text = FileHandler.extract_text(resume_path)
        except Exception as e:
            print(f"{RED}Error reading resume: {str(e)}{RESET}", file=sys.stderr)
            sys.exit(1)

        try:
            job_desc = FileHandler.read_json(job_path)
        except Exception as e:
            print(f"{RED}Error reading job description: {str(e)}{RESET}", file=sys.stderr)
            sys.exit(1)

        # Initialize parsers
        resume_parser = ResumeParser(resume_text)
        candidate_info = resume_parser.parse()

        # Step 3: Match candidate with job description
        print(f"{BLUE}[3/5] Performing match analysis (Skills & Experience)...{RESET}")
        matcher = ResumeMatcher(job_desc)
        match_results = matcher.match(candidate_info, resume_parser.clean_text_content)

        # Step 4: Generate screening report
        print(f"{BLUE}[4/5] Building screening report...{RESET}")
        report_generator = ReportGenerator()
        report_path = report_generator.generate(match_results, candidate_info)

        # Step 5: Load report and render results
        print(f"{BLUE}[5/5] Screening complete. Rendering dashboard...\n{RESET}")
        final_report = FileHandler.read_json(report_path)
        print_report_card(final_report, report_path)

    except Exception as e:
        print(f"{RED}An unexpected critical error occurred: {str(e)}{RESET}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
