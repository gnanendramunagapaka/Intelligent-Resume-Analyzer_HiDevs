"""
Resume matching class to calculate similarity scores and generate recommendations.
"""

from typing import Dict, Any, List
import logging
from modules.utils import normalize_skill, normalize_skills

# Configure logger
logger = logging.getLogger(__name__)

class ResumeMatcher:
    """
    Matches candidate resume profiles against job descriptions.
    Calculates weighted matching scores (70% skills, 30% experience) 
    and generates recruitment recommendations.
    """
    
    def __init__(self, job_requirements: Dict[str, Any]):
        """
        Initializes the matcher with the target job requirements.
        
        Args:
            job_requirements (dict): Job requirements containing title, 
                                     required_skills, preferred_skills, and min_experience_years.
        """
        self.job_requirements = job_requirements or {}
        
        # Extract and normalize job requirements
        self.job_title = self.job_requirements.get("job_title", "Position")
        
        req_skills = self.job_requirements.get("required_skills", [])
        self.required_skills = normalize_skills(req_skills)
        
        pref_skills = self.job_requirements.get("preferred_skills", [])
        self.preferred_skills = normalize_skills(pref_skills)
        
        self.min_experience = float(self.job_requirements.get("min_experience_years", 0))

    def match(self, parsed_resume: Dict[str, Any], resume_clean_text: str = "") -> Dict[str, Any]:
        """
        Compares candidate details against job requirements and computes scoring.
        
        Args:
            parsed_resume (dict): Extracted resume data (name, email, phone, skills, experience_years).
            resume_clean_text (str): Optional. The fully cleaned raw text for NLP similarity.
            
        Returns:
            dict: Match results containing score breakdown, recommendations, and status.
        """
        # Get normalized candidate skills
        candidate_skills = normalize_skills(parsed_resume.get("skills", []))
        candidate_exp = float(parsed_resume.get("experience_years", 0.0))
        
        # 1. Skills Matching
        matched_required = []
        missing_required = []
        for skill in self.required_skills:
            if skill in candidate_skills:
                matched_required.append(skill)
            else:
                missing_required.append(skill)
                
        matched_preferred = []
        missing_preferred = []
        for skill in self.preferred_skills:
            if skill in candidate_skills:
                matched_preferred.append(skill)
            else:
                missing_preferred.append(skill)

        # Calculate skills score (0 - 100)
        # We weigh required skills at 80% and preferred at 20% of the total skill portion
        req_score = 100.0
        if self.required_skills:
            req_score = (len(matched_required) / len(self.required_skills)) * 100.0
            
        pref_score = 100.0
        if self.preferred_skills:
            pref_score = (len(matched_preferred) / len(self.preferred_skills)) * 100.0
            
        if self.required_skills and self.preferred_skills:
            skills_score = (req_score * 0.8) + (pref_score * 0.2)
        elif self.required_skills:
            skills_score = req_score
        elif self.preferred_skills:
            skills_score = pref_score
        else:
            skills_score = 100.0 # No skills specified in job description
            
        # 2. Experience Matching (0 - 100)
        if self.min_experience <= 0:
            experience_score = 100.0
        else:
            if candidate_exp >= self.min_experience:
                experience_score = 100.0
            else:
                experience_score = (candidate_exp / self.min_experience) * 100.0
                
        # 3. Final Score (70% Skills + 30% Experience)
        final_score = (skills_score * 0.70) + (experience_score * 0.30)
        final_score = round(final_score, 1)
        
        # 4. Semantic similarity using TF-IDF (NLP requirement)
        semantic_score = 0.0
        if resume_clean_text:
            try:
                semantic_score = self._calculate_semantic_similarity(resume_clean_text)
            except Exception as e:
                logger.error(f"Failed to calculate semantic similarity: {str(e)}")

        # 5. Determine recommendation
        if final_score >= 85.0:
            recommendation = "Strong Match"
        elif final_score >= 70.0:
            recommendation = "Consider"
        else:
            recommendation = "Reject"
            
        # All matched and missing skills lists
        all_matched_skills = sorted(list(set(matched_required + matched_preferred)))
        all_missing_skills = sorted(list(set(missing_required + missing_preferred)))
        
        return {
            "job_title": self.job_title,
            "candidate_name": parsed_resume.get("name", "Unknown"),
            "match_score": final_score,
            "skills_score": round(skills_score, 1),
            "experience_score": round(experience_score, 1),
            "semantic_similarity_score": round(semantic_score, 1),
            "matched_skills": all_matched_skills,
            "missing_skills": all_missing_skills,
            "matched_required_skills": matched_required,
            "missing_required_skills": missing_required,
            "matched_preferred_skills": matched_preferred,
            "missing_preferred_skills": missing_preferred,
            "recommendation": recommendation,
            "experience_years": candidate_exp,
            "min_experience_required": self.min_experience
        }

    def _calculate_semantic_similarity(self, resume_text: str) -> float:
        """
        Helper method to calculate TF-IDF Cosine Similarity between resume text 
        and job requirements text.
        
        Args:
            resume_text (str): Cleaned resume text.
            
        Returns:
            float: Score between 0.0 and 100.0.
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
        except ImportError:
            logger.warning("scikit-learn is not installed. Semantic similarity score will default to 0.")
            return 0.0

        # Construct a representative job description text block
        job_text_elements = [
            self.job_title,
            " ".join(self.required_skills),
            " ".join(self.preferred_skills),
            f"{self.min_experience} years of experience"
        ]
        job_text = " ".join(job_text_elements).lower()

        if not resume_text or not job_text:
            return 0.0

        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([resume_text, job_text])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        
        return float(similarity * 100.0)
