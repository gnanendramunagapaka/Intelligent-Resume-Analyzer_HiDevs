"""
Comprehensive unit test suite for the Resume Analyzer System.
Verifies utils, parsing regex, file operations, matching, and scoring computations.
"""

import os
import unittest
import json
from modules.utils import clean_text, normalize_skill, normalize_skills, parse_experience_years, format_phone
from modules.file_handler import FileHandler
from modules.parser import ResumeParser
from modules.matcher import ResumeMatcher
from modules.report_generator import ReportGenerator

class TestUtils(unittest.TestCase):
    """Test case for utility helper functions in utils.py."""

    def test_clean_text(self):
        self.assertEqual(clean_text("  Hello   World!  "), "hello world!")
        self.assertEqual(clean_text("Line\nBreak\xa0Space"), "line break space")
        self.assertEqual(clean_text(""), "")

    def test_normalize_skill(self):
        self.assertEqual(normalize_skill("JS"), "javascript")
        self.assertEqual(normalize_skill("  ReactJS  "), "react")
        self.assertEqual(normalize_skill("Machine Learning"), "machine learning")
        self.assertEqual(normalize_skill("ML"), "machine learning")
        self.assertEqual(normalize_skill(""), "")

    def test_normalize_skills(self):
        skills = ["Python", "JS", "ReactJS", "ML", "python", "javascript"]
        normalized = normalize_skills(skills)
        # Expected distinct, normalized, sorted skills
        self.assertEqual(normalized, ["javascript", "machine learning", "python", "react"])

    def test_parse_experience_years(self):
        self.assertEqual(parse_experience_years("5 years of experience"), 5.0)
        self.assertEqual(parse_experience_years("I have 3+ yrs working"), 3.0)
        self.assertEqual(parse_experience_years("Worked for 2.5 years at Google"), 2.5)
        self.assertEqual(parse_experience_years("No experience mentioned"), 0.0)

    def test_format_phone(self):
        self.assertEqual(format_phone("+1-123-456-7890"), "+11234567890")
        self.assertEqual(format_phone("(123) 456-7890"), "1234567890")
        self.assertEqual(format_phone(""), "")


class TestFileHandler(unittest.TestCase):
    """Test case for file handler operations."""

    def setUp(self):
        self.test_json_path = "test_data.json"
        self.test_txt_path = "test_data.txt"

    def tearDown(self):
        for path in [self.test_json_path, self.test_txt_path]:
            if os.path.exists(path):
                os.remove(path)

    def test_write_and_read_json(self):
        data = {"key": "value", "list": [1, 2, 3]}
        FileHandler.write_json(self.test_json_path, data)
        loaded = FileHandler.read_json(self.test_json_path)
        self.assertEqual(loaded, data)

    def test_write_and_read_txt(self):
        content = "Testing text operations."
        with open(self.test_txt_path, "w", encoding="utf-8") as f:
            f.write(content)
        read_content = FileHandler.read_txt(self.test_txt_path)
        self.assertEqual(read_content, content)

    def test_validation(self):
        self.assertFalse(FileHandler.validate_file("nonexistent.txt"))
        with open(self.test_txt_path, "w", encoding="utf-8") as f:
            f.write("Some text")
        self.assertTrue(FileHandler.validate_file(self.test_txt_path, [".txt"]))
        self.assertFalse(FileHandler.validate_file(self.test_txt_path, [".pdf"]))


class TestResumeParser(unittest.TestCase):
    """Test case for regex-based resume parser."""

    def test_empty_resume(self):
        parser = ResumeParser("")
        parsed = parser.parse()
        self.assertEqual(parsed["name"], "Unknown")
        self.assertEqual(parsed["email"], "")
        self.assertEqual(parsed["phone"], "")
        self.assertEqual(parsed["skills"], [])
        self.assertEqual(parsed["experience_years"], 0.0)

    def test_typical_resume_parsing(self):
        resume_text = """
        Alice Smith
        Email: alice.smith@domain.com
        Phone: (555) 019-2834
        
        Summary:
        Senior Data Scientist with 6 years of professional experience in analyzing data.
        
        Skills:
        Python, SQL, PyTorch, Docker, Git, ML
        """
        parser = ResumeParser(resume_text)
        parsed = parser.parse()
        
        self.assertEqual(parsed["name"], "Alice Smith")
        self.assertEqual(parsed["email"], "alice.smith@domain.com")
        self.assertEqual(parsed["phone"], "5550192834")
        self.assertIn("python", parsed["skills"])
        self.assertIn("pytorch", parsed["skills"])
        self.assertIn("machine learning", parsed["skills"])  # "ML" normalized
        self.assertEqual(parsed["experience_years"], 6.0)


class TestResumeMatcher(unittest.TestCase):
    """Test case for score calculations and recommendation logic."""

    def setUp(self):
        self.job_desc = {
            "job_title": "Senior Data Scientist",
            "required_skills": ["Python", "SQL", "Git"],
            "preferred_skills": ["PyTorch", "Docker"],
            "min_experience_years": 5
        }
        self.matcher = ResumeMatcher(self.job_desc)

    def test_perfect_match(self):
        # Candidate meets all requirements and experience
        candidate = {
            "name": "Perfect Candidate",
            "skills": ["python", "sql", "git", "pytorch", "docker"],
            "experience_years": 6.0
        }
        result = self.matcher.match(candidate)
        self.assertEqual(result["skills_score"], 100.0)
        self.assertEqual(result["experience_score"], 100.0)
        self.assertEqual(result["match_score"], 100.0)
        self.assertEqual(result["recommendation"], "Strong Match")

    def test_partial_match(self):
        # Candidate has 2/3 required, 1/2 preferred, and 2.5/5 years of experience
        candidate = {
            "name": "Partial Candidate",
            "skills": ["python", "sql", "pytorch"], # missing: git, docker
            "experience_years": 2.5
        }
        result = self.matcher.match(candidate)
        
        # Required score: 2/3 = 66.67%
        # Preferred score: 1/2 = 50.00%
        # Skills score: (66.67 * 0.8) + (50.00 * 0.2) = 53.33 + 10.00 = 63.33%
        # Experience score: 2.5 / 5.0 = 50.0%
        # Final Match Score: (63.33 * 0.7) + (50.0 * 0.3) = 44.33 + 15.0 = 59.33% (rounded to 59.3)
        self.assertAlmostEqual(result["skills_score"], 63.3, places=1)
        self.assertEqual(result["experience_score"], 50.0)
        self.assertEqual(result["match_score"], 59.3)
        self.assertEqual(result["recommendation"], "Reject")

    def test_borderline_match(self):
        # Candidate matches enough for "Consider"
        # 3/3 required skills = 100%. 0/2 preferred = 0%. Skills score = 80%.
        # Experience: 4/5 years = 80%. Experience score = 80%.
        # Match score = 80% (80 * 0.7 + 80 * 0.3 = 80)
        # Recommendation: Consider (since 70-84 is Consider)
        candidate = {
            "name": "Borderline Candidate",
            "skills": ["python", "sql", "git"],
            "experience_years": 4.0
        }
        result = self.matcher.match(candidate)
        self.assertEqual(result["match_score"], 80.0)
        self.assertEqual(result["recommendation"], "Consider")


if __name__ == "__main__":
    unittest.main()
