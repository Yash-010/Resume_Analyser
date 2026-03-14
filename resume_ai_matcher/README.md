# AI Powered Resume – Job Description Matching System

## Project Overview

This is a full-stack web application designed to analyze multiple resumes against a given job description using Natural Language Processing (NLP) and Artificial Intelligence (AI). It determines how well each candidate matches the role, provides a percentage match score, extracts key skills, analyzes the resume structure, and uses a Large Language Model (LLM) to offer resume improvement suggestions.

## Main Features

- **Resume Upload**: Upload single or multiple PDF resumes simultaneously.
- **Job Description Input**: Text area to paste the targeted job description.
- **NLP Matching Engine**: Uses TF-IDF Vectorization and Cosine Similarity to calculate a percentage match score.
- **Skill Detection**: Identifies matched and missing skills by extracting them from the JD and comparing them with the resumes.
- **Keyword Importance**: Categorizes JD keywords into High, Medium, and Low importance levels.
- **Resume Section Analyzer**: Detects core sections like Skills, Projects, Experience, Education, and Certifications.
- **AI Resume Suggestions**: Integrates Google Gemini API to generate tailored recommendations to improve resume phrasing, align with the JD, and fill missing skill gaps.
- **Visual Score Representation**: Responsive Bootstrap UI with a colored progress bar and a ranking table.

## Technology Stack

- **Backend / NLP**: Python, Flask, scikit-learn (TF-IDF, Cosine Similarity), nltk
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **File Processing**: pdfplumber
- **AI Integration**: google-generativeai (Gemini API)

## Project Structure

```
resume_ai_matcher/
│
├── app.py
├── requirements.txt
├── README.md
│
├── templates/
│   ├── index.html
│   └── results.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
│
├── utils/
│   ├── text_extractor.py
│   ├── similarity_engine.py
│   ├── keyword_analyzer.py
│   ├── resume_section_analyzer.py
│   └── ai_suggestions.py
│
└── uploads/              # Created automatically
```

## Installation Instructions

1. **Clone or extract the project folder:**

   ```bash
   cd resume_ai_matcher
   ```

2. **Create a virtual environment (optional but recommended):**

   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```

3. **Install the required dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the AI API Key:**
   To enable AI Resume Suggestions, you must provide a Gemini API key.

   ```bash
   # On Windows Command Prompt:
   set GEMINI_API_KEY=your_api_key_here

   # On Windows PowerShell:
   $env:GEMINI_API_KEY="your_api_key_here"

   # On Mac/Linux:
   export GEMINI_API_KEY="your_api_key_here"
   ```

   _(Note: The system will gracefully fall back to default suggestions if an API key is not provided)._

## How to Run the Project

1. Start the backend Flask application processing:

   ```bash
   python app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

## Example Usage

1. Open the homepage.
2. Paste a job description for a specific role (e.g., Data Scientist or Full-stack Engineer) into the text area.
3. Select 1 or more sample PDF resumes from your system.
4. Click **Analyze Resumes**.
5. Wait a few seconds for NLP processing and AI evaluation.
6. Check the Ranking Results page to review the match percentage, skill gaps, resume structure evaluation, and tailored AI suggestions.
