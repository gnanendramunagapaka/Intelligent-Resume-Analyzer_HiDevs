# Intelligent Resume Analyzer

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org)
[![Framework](https://img.shields.io/badge/framework-Flask-lightgrey.svg)](https://flask.palletsprojects.com/)
[![NLP](https://img.shields.io/badge/NLP-spaCy%20%7C%20scikit--learn-green.svg)](https://spacy.io/)

An automated, production-ready ATS-style Resume Screening and Matching system.

---

## Project Overview

The **Intelligent Resume Analyzer** is an automated screening application designed to streamline recruiting workflows. The system extracts structured candidate information from unstructured resume documents, parses them against customizable job descriptions, calculates weighted matching scores, and generates detailed JSON reports alongside a visual analytics interface.

By leveraging **Natural Language Processing (NLP)**, **Regular Expressions (Regex)**, and word similarity models, it acts as an **ATS-style screening assistant** to help teams identify qualified applicants efficiently.

---

## Features

- 📄 **Multi-Format Parsing**: Full text extraction capabilities for **PDF**, **DOCX**, and **TXT** files.
- 🛠️ **Skill Extraction**: Scans and normalizes candidate skills against a standard database of over 70+ technology keywords (using exact boundary matches and alias translation).
- 📈 **Experience Analysis**: Dynamically computes overall professional years of experience from resume texts.
- 🎯 **Weighted Scoring Engine**: Calculates final match ratings:
  - **Skills Match (70% weight)**: Based on required and preferred skill overlaps.
  - **Experience Match (30% weight)**: Scaled relative to minimum requirement metrics.
- 🧠 **Semantic NLP Similarity**: Utilizes `scikit-learn` TF-IDF Vectorization and Cosine Similarity to compute a semantic correlation score between candidate profiles and job details.
- 📋 **Hiring Recommendations**: Automatically maps candidate ratings to standard actionable outcomes:
  - `85+` ➔ **Strong Match**
  - `70–84` ➔ **Consider**
  - `Below 70` ➔ **Reject**
- 💾 **JSON Reports**: Generates structured, timestamped candidate profile summaries stored automatically in the database directory.
- 🛡️ **Error Handling**: Graceful parsing recovery from corrupted, empty, or unsupported documents.
- 📦 **Modular Architecture**: Well-defined object-oriented modules structured under PEP 8 guidelines.

---

## Tech Stack

- **Python** (Core Logic)
- **Flask** (Localhost Server)
- **pdfplumber** (PDF parsing)
- **python-docx** (DOCX parsing)
- **spaCy** (NER / Name Extraction)
- **scikit-learn** (TF-IDF Similarity)
- **NLP** (Natural Language Processing)
- **JSON** (Report Storage)

---

## Project Structure

```text
Intelligent-Resume-Analyzer_HiDevs/
│
├── data/
│   ├── resumes/              # Cache for candidate uploaded resumes
│   ├── jobs/                 # Contains job descriptions config files
│   └── reports/              # Outputs for saved JSON reports
│
├── modules/
│   ├── __init__.py           # Package declarations
│   ├── file_handler.py       # Safe file reading/writing validations
│   ├── parser.py             # Resume parser (NER/Regex)
│   ├── matcher.py            # Scoring logic and NLP similarity
│   ├── report_generator.py   # Report builder
│   └── utils.py              # Text cleaning & phone normalization
│
├── templates/
│   └── index.html            # Web App Frontend Dashboard
│
├── app.py                    # Flask Web app entry point
├── main.py                   # CLI Application entry point
├── run_tests.py              # Automated test runner suite
├── requirements.txt          # Library dependencies listing
└── README.md                 # Project documentation
```

---

## Installation

Clone the repository and set up requirements:

```bash
git clone https://github.com/gnanendramunagapaka/Intelligent-Resume-Analyzer_HiDevs.git
cd Intelligent-Resume-Analyzer_HiDevs

pip install -r requirements.txt
```

*(Optional: Download the spaCy model explicitly if it does not download automatically)*
```bash
python -m spacy download en_core_web_sm
```

---

## Run Application

You can execute this system in two modes:

### 1. Terminal CLI Interface
Analyzes a sample resume against job specifications and prints a report card:
```bash
python main.py
```

### 2. Localhost Interactive Web Application
Serves the web dashboard on localhost:
```bash
python app.py
# or:
flask run
```
Then navigate to **`http://127.0.0.1:5000`** in your browser.

---

## Sample Workflow

1. **Upload Resume**: Submit TXT, DOCX, or PDF files via the drag-and-drop web uploader.
2. **Parse Resume**: Extract applicant details (Name, Contact Info, Skills, Experience) using modular parsers.
3. **Analyze Skills & Experience**: Clean and normalize terms (e.g. mapping "ML" to "Machine learning", "JS" to "Javascript").
4. **Compare with Job Requirements**: Evaluate candidate against target requirements.
5. **Generate Match Score**: Calculate weighted ATS rating.
6. **Save JSON Report**: Serialize the profiles and scores as a timestamped archive record.

---

## Sample Output

An example JSON report structure output:

```json
{
  "candidate_name": "John Doe",
  "match_score": 92,
  "recommendation": "Strong Match"
}
```

---

## Future Improvements

- 🤖 **AI-Powered Ranking**: Integrate large language model summarizations for abstract skill inferences.
- 📷 **OCR Integration**: Embed Tesseract OCR to support scanned resumes or image files.
- 🗃️ **Bulk Resume Analysis**: Enable folders scan upload to screen hundreds of candidates concurrently.
- 📊 **Dashboard Analytics**: Expand the UI to show aggregation stats on skill distributions and candidate funnels.
- ☁️ **Cloud Deployment**: Host the Flask app on AWS Elastic Beanstalk or Heroku.
- 🗄️ **Database Integration**: Connect relational schemas (PostgreSQL) or document stores (MongoDB) for profile index persistence.

---

## Author

GNANENDRA MUNAGAPAKA
