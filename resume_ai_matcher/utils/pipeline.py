from typing import Any, Dict, List

from .ai_suggestions import (
    generate_interview_questions,
    generate_learning_path,
    generate_resume_suggestions,
)
from .ats_checker import analyze_ats_compatibility
from .keyword_analyzer import extract_and_compare_keywords
from .resume_section_analyzer import analyze_sections, compute_completeness_score
from .scoring import compute_scores


def extract_candidate_name(resume_text: str) -> str:
    """
    Very lightweight heuristic to infer candidate name from resume text.
    """
    if not resume_text:
        return ""

    lines = [l.strip() for l in resume_text.splitlines() if l.strip()]
    if not lines:
        return ""

    for line in lines[:10]:
        if line.lower().startswith("name:"):
            return line.split(":", 1)[1].strip()

    for line in lines[:10]:
        lower = line.lower()
        if any(x in lower for x in ["email", "phone", "linkedin", "@"]):
            continue
        if len(line.split()) <= 5:
            return line

    return ""


def analyze_resume_text(
    resume_text: str,
    filename: str,
    job_description: str,
    jd_top_skills: List[str],
) -> Dict[str, Any]:
    """
    Shared analysis pipeline used by both Job Seeker and Recruiter modes.
    Returns a serializable dict for JSON responses.
    """
    candidate_name = extract_candidate_name(resume_text)

    try:
        matched, missing, importance = extract_and_compare_keywords(resume_text, job_description)
    except Exception as e:
        print(f"Error in keyword analysis for {filename}: {e}")
        matched, missing, importance = [], [], {
            "High Importance": [],
            "Medium Importance": [],
            "Low Importance": [],
        }

    try:
        sections = analyze_sections(resume_text)
    except Exception as e:
        print(f"Error analyzing sections for {filename}: {e}")
        sections = {}

    try:
        ats_score, ats_issues = analyze_ats_compatibility(resume_text, sections)
    except Exception as e:
        print(f"Error analyzing ATS for {filename}: {e}")
        ats_score, ats_issues = 0.0, ["ATS analysis failed."]

    try:
        score_components = compute_scores(
            resume_text,
            job_description,
            sections,
            matched,
            missing,
            jd_top_skills,
        )
    except Exception as e:
        print(f"Error computing scores for {filename}: {e}")
        score_components = {
            "skill_match_score": 0.0,
            "experience_score": 0.0,
            "structure_score": 0.0,
            "keyword_density_score": 0.0,
            "final_score": 0.0,
        }

    try:
        suggestions = generate_resume_suggestions(resume_text, job_description, missing)
    except Exception as e:
        print(f"Error generating AI suggestions for {filename}: {e}")
        suggestions = [
            "Unable to generate AI suggestions at this time.",
            "Focus on aligning your skills and experience more closely with the job description.",
        ]

    try:
        learning_path = generate_learning_path(missing)
    except Exception as e:
        print(f"Error generating learning path for {filename}: {e}")
        learning_path = []

    try:
        interview_questions = generate_interview_questions(resume_text, job_description)
    except Exception as e:
        print(f"Error generating interview questions for {filename}: {e}")
        interview_questions = []

    return {
        "filename": filename,
        "candidate_name": candidate_name,
        "score": score_components["final_score"],
        "score_breakdown": score_components,
        "matched_skills": matched,
        "missing_skills": missing,
        "keyword_importance": importance,
        "sections": sections,
        "resume_completeness": compute_completeness_score(sections),
        "ats_score": ats_score,
        "ats_issues": ats_issues,
        "suggestions": suggestions,
        "learning_path": learning_path,
        "interview_questions": interview_questions,
    }

