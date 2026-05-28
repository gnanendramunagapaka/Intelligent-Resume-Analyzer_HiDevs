"""
Flask web server for the Intelligent Resume Analyzer.
Exposes endpoints for file uploads, parsing, matching, and report browsing.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any
from flask import Flask, request, jsonify, render_template, send_from_directory, abort
from werkzeug.utils import secure_filename

from modules.file_handler import FileHandler
from modules.parser import ResumeParser
from modules.matcher import ResumeMatcher
from modules.report_generator import ReportGenerator

app = Flask(__name__)

# Configure upload and report folders
UPLOAD_FOLDER = os.path.join("data", "resumes")
REPORTS_FOLDER = os.path.join("data", "reports")
JOBS_FOLDER = os.path.join("data", "jobs")

FileHandler.ensure_directory(UPLOAD_FOLDER)
FileHandler.ensure_directory(REPORTS_FOLDER)
FileHandler.ensure_directory(JOBS_FOLDER)

# Allowed file extensions for resumes
ALLOWED_EXTENSIONS = {'.txt', '.pdf', '.docx', '.doc'}

def allowed_file(filename: str) -> bool:
    """Checks if the uploaded file has a supported resume extension."""
    _, ext = os.path.splitext(filename)
    return ext.lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    """Serves the main application web interface."""
    return render_template("index.html")

@app.route("/api/default-job", methods=["GET"])
def get_default_job():
    """Fetches the default job description JSON content."""
    default_job_path = os.path.join(JOBS_FOLDER, "job_description.json")
    try:
        if os.path.exists(default_job_path):
            job_data = FileHandler.read_json(default_job_path)
            return jsonify(job_data)
        else:
            # Fallback mock template if default description is missing
            fallback_job = {
                "job_title": "Software Engineer",
                "required_skills": ["Python", "SQL", "Git"],
                "preferred_skills": ["Docker", "AWS"],
                "min_experience_years": 3
            }
            return jsonify(fallback_job)
    except Exception as e:
        return jsonify({"error": f"Failed to load job description: {str(e)}"}), 500

@app.route("/api/reports", methods=["GET"])
def list_reports():
    """Lists summary info for all saved candidate evaluation reports."""
    try:
        reports_list = []
        if os.path.exists(REPORTS_FOLDER):
            for file_name in os.listdir(REPORTS_FOLDER):
                if file_name.endswith(".json"):
                    file_path = os.path.join(REPORTS_FOLDER, file_name)
                    try:
                        report_data = FileHandler.read_json(file_path)
                        profile = report_data.get("candidate_profile", {})
                        evaluation = report_data.get("evaluation", {})
                        metadata = report_data.get("metadata", {})
                        
                        reports_list.append({
                            "filename": file_name,
                            "candidate_name": profile.get("name", "Unknown"),
                            "job_title": evaluation.get("job_title", "N/A"),
                            "match_score": evaluation.get("final_match_score", 0.0),
                            "recommendation": evaluation.get("recommendation", "Reject"),
                            "timestamp": metadata.get("generated_at", "")
                        })
                    except Exception:
                        # Skip corrupted or malformed reports
                        continue
                        
        # Sort reports by timestamp descending (newest first)
        reports_list.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
        return jsonify(reports_list)
    except Exception as e:
        return jsonify({"error": f"Failed to list reports: {str(e)}"}), 500

@app.route("/api/reports/<filename>", methods=["GET"])
def get_report(filename: str):
    """Retrieves full details of a specific JSON report by filename."""
    # Prevent directory traversal attacks
    safe_filename = secure_filename(filename)
    report_path = os.path.join(REPORTS_FOLDER, safe_filename)
    
    if not os.path.exists(report_path):
        return jsonify({"error": "Report not found"}), 404
        
    try:
        report_data = FileHandler.read_json(report_path)
        return jsonify(report_data)
    except Exception as e:
        return jsonify({"error": f"Failed to load report: {str(e)}"}), 500

@app.route("/api/analyze", methods=["POST"])
def analyze_resume():
    """
    Accepts resume upload and job criteria, runs parsing and matching,
    saves the JSON report, and returns the result.
    """
    # 1. Validate file upload
    if 'resume' not in request.files:
        return jsonify({"error": "No resume file part in request"}), 400
        
    file = request.files['resume']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file format. Please upload PDF, DOCX, or TXT."}), 400

    try:
        # 2. Extract and parse job requirements from form parameters
        # Supports both a single 'job_description' JSON block or individual form inputs
        if 'job_description' in request.form:
            try:
                job_desc = json.loads(request.form['job_description'])
            except json.JSONDecodeError:
                return jsonify({"error": "Invalid job_description JSON syntax"}), 400
        else:
            # Reconstruct from separate form fields
            job_title = request.form.get("job_title", "Position")
            min_exp = request.form.get("min_experience_years", 0)
            try:
                min_exp = float(min_exp)
            except ValueError:
                min_exp = 0.0

            # Parse skills lists (support comma separated inputs)
            req_skills = request.form.get("required_skills", "")
            pref_skills = request.form.get("preferred_skills", "")
            
            def parse_skills_input(sk_str: str):
                if not sk_str.strip():
                    return []
                return [s.strip() for s in sk_str.split(",") if s.strip()]
                
            job_desc = {
                "job_title": job_title,
                "required_skills": parse_skills_input(req_skills),
                "preferred_skills": parse_skills_input(pref_skills),
                "min_experience_years": min_exp
            }

        # 3. Save uploaded file with a unique name to prevent collisions
        orig_name, ext = os.path.splitext(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = f"upload_{secure_filename(orig_name)}_{timestamp}{ext.lower()}"
        file_path = os.path.join(UPLOAD_FOLDER, safe_name)
        file.save(file_path)

        # 4. Extract and parse resume content
        try:
            resume_text = FileHandler.extract_text(file_path)
        except Exception as e:
            return jsonify({"error": f"Failed to extract text from resume: {str(e)}"}), 400

        resume_parser = ResumeParser(resume_text)
        candidate_info = resume_parser.parse()

        # 5. Match candidate against job description
        matcher = ResumeMatcher(job_desc)
        match_results = matcher.match(candidate_info, resume_parser.clean_text_content)

        # 6. Generate and save JSON report
        report_generator = ReportGenerator()
        report_path = report_generator.generate(match_results, candidate_info)
        report_filename = os.path.basename(report_path)

        # 7. Read report data and return it
        final_report = FileHandler.read_json(report_path)
        
        # Add filename details to return payload
        response_data = {
            "report_filename": report_filename,
            "report": final_report
        }
        
        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": f"An error occurred during analysis: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
