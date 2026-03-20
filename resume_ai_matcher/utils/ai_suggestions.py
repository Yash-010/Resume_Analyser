import os
import google.generativeai as genai
from config import config


def _build_model():
    api_key = config.GEMINI_API_KEY
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(config.GEMINI_MODEL)


def generate_resume_suggestions(resume_text, job_description, missing_keywords):
    """
    Generate resume improvement suggestions using Gemini API.
    Fallback to static suggestions if API key is not present or call fails.
    """
    # Static fallback
    fallback_suggestions = [
        "AI suggestions are limited; showing basic tips:",
        f"Consider adding missing skills: {', '.join(missing_keywords[:5])}.",
        "Quantify your achievements in the experience section.",
        "Tailor your resume summary to align closer to the job description.",
        "Ensure your layout is simple for ATS parsing."
    ]

    model = _build_model()
    if not model:
        return fallback_suggestions

    try:
        prompt = f"""
You are a senior resume coach and hiring manager.
Given the resume and job description below, propose concrete improvements.

Return:
- 2–3 suggestions about missing or weak skills to highlight.
- 2–3 rewritten bullet points that are more impact-focused.
- 1–2 tips to improve structure and clarity.

Missing Skills identified: {', '.join(missing_keywords)}

Job Description (truncated):
{job_description[:1200]}

Resume (truncated):
{resume_text[:1800]}
"""

        response = model.generate_content(prompt)
        text = getattr(response, "text", "") or ""

        suggestions = []
        for line in text.split("\n"):
            line = line.strip().strip("*-•").strip()
            if line:
                suggestions.append(line)
                if len(suggestions) >= 6:
                    break

        return suggestions if suggestions else fallback_suggestions
    except Exception as e:
        print(f"Error calling AI API: {e}")
        return fallback_suggestions


def generate_learning_path(missing_skills):
    """
    Generate short learning-path recommendations for key missing skills.
    """
    if not missing_skills:
        return []

    top_missing = missing_skills[:5]
    model = _build_model()

    if not model:
        return [
            f"For {skill}: search for an introductory course, then practice with small projects."
            for skill in top_missing
        ]

    try:
        prompt = f"""
Act as a mentor for an aspiring data / AI professional.
For each of the following missing skills, provide a very short learning path:
- 1 sentence on why the skill is important
- 3–4 bullet points of topics to study or practice

Missing skills:
{', '.join(top_missing)}
"""
        response = model.generate_content(prompt)
        text = getattr(response, "text", "") or ""
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        return lines
    except Exception as e:
        print(f"Error generating learning path: {e}")
        return [
            f"For {skill}: focus on fundamentals first, then practice with real datasets or projects."
            for skill in top_missing
        ]


def generate_interview_questions(resume_text, job_description):
    """
    Generate tailored interview questions based on the candidate resume and job description.
    """
    model = _build_model()
    fallback = [
        "Walk me through a machine learning project you are proud of.",
        "How do you typically handle missing data in a dataset?",
        "Explain a time when you improved a model's performance.",
    ]

    if not model:
        return fallback

    try:
        prompt = f"""
You are a technical interviewer hiring for a data / ML role.
Generate 6–8 interview questions based on the job description and candidate resume below.
Mix conceptual questions, experience-based questions, and scenario questions.

Job Description (truncated):
{job_description[:1200]}

Candidate Resume (truncated):
{resume_text[:1800]}
"""
        response = model.generate_content(prompt)
        text = getattr(response, "text", "") or ""
        questions = []
        for line in text.split("\n"):
            line = line.strip().strip("*-•").strip()
            if line.endswith("?"):
                questions.append(line)
            elif line and len(line.split()) > 5 and "?" in line:
                questions.append(line)
            if len(questions) >= 8:
                break

        return questions if questions else fallback
    except Exception as e:
        print(f"Error generating interview questions: {e}")
        return fallback

