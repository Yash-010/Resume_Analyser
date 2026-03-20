import re


def analyze_ats_compatibility(resume_text, sections):
    """
    Heuristic ATS compatibility checker.

    Returns:
        score (0–100 float)
        issues (list of human-readable strings)
    """
    issues = []
    text = resume_text or ""
    lowered = text.lower()

    # Section-based checks
    required_core = ["Skills Section", "Experience Section", "Education Section"]
    missing_core = [s for s in required_core if sections.get(s) != "Found"]
    if missing_core:
        issues.append(
            "Missing core sections: " + ", ".join(s.replace(" Section", "") for s in missing_core)
        )

    # Graphics / formatting heuristics
    if re.search(r"\.(png|jpg|jpeg|svg)", lowered):
        issues.append("Contains image references; pure text is safer for ATS.")

    # Very long lines or heavy table-like formatting
    lines = text.splitlines()
    long_lines = sum(1 for l in lines if len(l) > 180)
    if long_lines > 5:
        issues.append("Contains many very long lines; may be hard for ATS to parse.")

    # If extraction produced very few lines, ATS parsing is often worse
    if len(lines) <= 5 and len(text.split()) > 200:
        issues.append("Resume text looks like one long paragraph; headings/spacing may be hard for ATS.")

    # Bullet characters that are often safe but can be overused
    fancy_bullets = sum(1 for l in lines if "•" in l or "▪" in l or "●" in l)
    if fancy_bullets > 30:
        issues.append("Uses many non-standard bullet characters; simple '-' or '*' is safer.")

    # Basic scoring: start from a neutral baseline and adjust.
    score = 60.0

    # Reward: all core sections present
    if not missing_core:
        score += 10.0

    # Reward: reasonable length (not extremely short or extremely long)
    token_count = len(text.split())
    if 200 <= token_count <= 2000:
        score += 10.0
    elif token_count < 120:
        issues.append("Very short resume text; ATS content match may be weak.")
        score -= 18.0
    elif token_count < 200:
        score -= 8.0
    elif token_count > 2500:
        issues.append("Very long resume text; may reduce clarity for ATS.")
        score -= 6.0

    # Reward: presence of some bullets for readability
    simple_bullets = sum(1 for l in lines if l.strip().startswith(("-", "*")))
    if simple_bullets >= 5:
        score += 5.0
    elif simple_bullets == 0:
        issues.append("No simple bullet points detected; bullets improve ATS readability.")
        score -= 8.0
    elif simple_bullets < 3:
        score -= 3.0

    # Penalties for problematic patterns
    score -= len(missing_core) * 8.0
    if re.search(r"\.(png|jpg|jpeg|svg)", lowered):
        score -= 10.0
    score -= min(long_lines * 2.0, 20.0)
    score -= min(fancy_bullets * 0.5, 15.0)
    if len(lines) <= 5 and token_count > 200:
        score -= 10.0

    score = max(0.0, min(score, 100.0))
    return round(score, 1), issues

