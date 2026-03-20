from typing import Dict, List, Tuple

from .similarity_engine import calculate_similarity
from .resume_section_analyzer import compute_completeness_score


def _skill_match_score(matched_skills: List[str], missing_skills: List[str]) -> float:
    total = len(matched_skills) + len(missing_skills)
    if total == 0:
        return 0.0
    return round((len(matched_skills) / total) * 100.0, 2)


def _keyword_density_score(resume_text: str, jd_skills: List[str]) -> float:
    """
    Approximate how densely JD skills appear in the resume.
    """
    if not resume_text or not jd_skills:
        return 0.0

    text = resume_text.lower()
    tokens = [t for t in text.split() if t.strip()]
    if not tokens:
        return 0.0

    hits = 0
    for skill in jd_skills:
        s = skill.lower()
        if s in text:
            hits += text.count(s)

    density = (hits / len(tokens)) * 1000.0
    density = max(0.0, min(density, 100.0))
    return round(density, 2)


def compute_scores(
    resume_text: str,
    job_description: str,
    sections: Dict[str, str],
    matched_skills: List[str],
    missing_skills: List[str],
    jd_top_skills: List[str],
) -> Dict[str, float]:
    """
    Compute a multi-factor resume score:

        50% Skill Match Score
        30% Experience Relevance (semantic similarity)
        10% Resume Structure Completeness
        10% Keyword Density

    Returns a dict with per-component scores and final combined score.
    """
    skill_score = _skill_match_score(matched_skills, missing_skills)
    experience_score = calculate_similarity(resume_text, job_description)
    structure_score = compute_completeness_score(sections)
    keyword_density = _keyword_density_score(resume_text, jd_top_skills)

    final = (
        0.5 * skill_score
        + 0.3 * experience_score
        + 0.1 * structure_score
        + 0.1 * keyword_density
    )

    return {
        "skill_match_score": round(skill_score, 2),
        "experience_score": round(experience_score, 2),
        "structure_score": round(structure_score, 2),
        "keyword_density_score": round(keyword_density, 2),
        "final_score": round(final, 2),
    }

