import re
from typing import Dict, Iterable, List, Set, Tuple
import nltk
from nltk.corpus import stopwords

# Ensure stopwords are downloaded
try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords", quiet=True)


def _get_stopwords_set() -> Set[str]:
    try:
        return set(stopwords.words("english"))
    except LookupError:
        # If NLTK data isn't available (common with SSL/cert issues),
        # continue without stopword filtering instead of crashing.
        return set()


# Curated skill vocabulary (can be extended or loaded from external file)
BASE_SKILLS: Set[str] = {
    # Core programming / data stack
    "python",
    "r",
    "java",
    "c++",
    "sql",
    "nosql",
    "pandas",
    "numpy",
    "scipy",
    "matplotlib",
    "seaborn",
    "excel",
    # ML / AI
    "machine learning",
    "deep learning",
    "artificial intelligence",
    "ai",
    "ml",
    "nlp",
    "natural language processing",
    "computer vision",
    "recommendation systems",
    "time series",
    "reinforcement learning",
    # Libraries / frameworks
    "scikit-learn",
    "sklearn",
    "tensorflow",
    "keras",
    "pytorch",
    "spark",
    "hadoop",
    "pyspark",
    "airflow",
    "dbt",
    # BI / viz
    "tableau",
    "power bi",
    "looker",
    "data studio",
    "superset",
    # Cloud / devops
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "k8s",
    # Data / statistics
    "statistics",
    "probability",
    "hypothesis testing",
    "a/b testing",
    "data analysis",
    "data analytics",
    "data engineering",
    "data visualization",
}

# Normalization mapping to unify aliases, acronyms, and variations
SKILL_NORMALIZATION_MAP: Dict[str, str] = {
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "sklearn": "scikit-learn",
    "data analytics": "data analysis",
    "data scientist": "data science",
    "k8s": "kubernetes",
}


def _normalize_skill(skill: str) -> str:
    s = skill.strip().lower()
    return SKILL_NORMALIZATION_MAP.get(s, s)


def _normalize_vocab(skills: Iterable[str]) -> Set[str]:
    return {_normalize_skill(s) for s in skills}


NORMALIZED_SKILLS: Set[str] = _normalize_vocab(BASE_SKILLS)


def _find_skills_in_text(text: str) -> Set[str]:
    """
    Detect skills from the curated vocabulary inside arbitrary text.
    Uses simple case-insensitive phrase matching for now.
    """
    lowered = text.lower()
    found: Set[str] = set()

    for raw_skill in NORMALIZED_SKILLS:
        # Match as a phrase, respecting word boundaries where possible.
        pattern = r"\b" + re.escape(raw_skill) + r"\b"
        if re.search(pattern, lowered):
            found.add(raw_skill)

    return found


def extract_top_skills(job_description: str, max_skills: int = 20) -> List[str]:
    """
    Extract top required skills from the job description text
    using the curated skill vocabulary.
    """
    jd_skills = list(_find_skills_in_text(job_description))

    # Preserve original order of appearance in the JD
    ordered: List[str] = []
    text = job_description.lower()
    for skill in jd_skills:
        idx = text.find(skill)
        if idx != -1:
            ordered.append((idx, skill))

    ordered.sort(key=lambda x: x[0])
    skills = [s for _, s in ordered]
    return skills[:max_skills]


def extract_and_compare_keywords(
    resume_text: str, job_description: str
) -> Tuple[List[str], List[str], Dict[str, List[str]]]:
    """
    Compare resume skills vs. JD skills using a curated vocabulary.

    Returns:
        matched_skills: list of normalized skills found in both JD and resume
        missing_skills: list of normalized skills present in JD but not resume
        importance_levels: dict with High / Medium / Low groupings of JD skills
    """
    jd_skills = extract_top_skills(job_description, max_skills=30)
    resume_skills = _find_skills_in_text(resume_text)

    if not jd_skills:
        empty = {"High Importance": [], "Medium Importance": [], "Low Importance": []}
        return [], [], empty

    matched = [s for s in jd_skills if s in resume_skills]
    missing = [s for s in jd_skills if s not in resume_skills]

    # Importance buckets based on ordering in the JD
    n = len(jd_skills)
    high_imp = jd_skills[: max(1, n // 3)]
    med_imp = jd_skills[max(1, n // 3) : max(2, 2 * n // 3)]
    low_imp = jd_skills[max(2, 2 * n // 3) : ]

    importance_levels = {
        "High Importance": high_imp,
        "Medium Importance": med_imp,
        "Low Importance": low_imp,
    }

    return matched, missing, importance_levels

