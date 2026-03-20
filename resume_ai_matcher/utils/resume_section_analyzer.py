import re

def analyze_sections(resume_text):
    """
    Detect if important resume sections exist.
    """
    sections = {
        "Skills Section": "Missing",
        "Projects Section": "Missing",
        "Experience Section": "Missing",
        "Education Section": "Missing",
        "Certifications Section": "Missing",
        "Summary Section": "Missing",
        "Internships Section": "Missing",
        "Achievements Section": "Missing",
    }
    
    text = resume_text.lower()
    
    # Keywords mapping for sections
    keywords = {
        "Skills Section": ["skills", "technical skills", "core competencies", "technologies"],
        "Projects Section": ["projects", "personal projects", "academic projects", "key projects"],
        "Experience Section": ["experience", "work experience", "professional experience", "employment history", "history"],
        "Education Section": ["education", "academic background", "qualifications", "degree", "academic"],
        "Certifications Section": ["certifications", "certificates", "courses", "licenses"],
        "Summary Section": ["summary", "professional summary", "profile", "about me"],
        "Internships Section": ["internships", "internship", "industrial training", "summer internship"],
        "Achievements Section": ["achievements", "awards", "honors", "accomplishments"],
    }
    
    for section, keys in keywords.items():
        for key in keys:
            # We look for the exact keyword acting as a header
            pattern = r'\b' + re.escape(key) + r'\b'
            if re.search(pattern, text):
                sections[section] = "Found"
                break
                
    return sections


def compute_completeness_score(sections):
    """
    Compute a simple completeness score (0–100) based on how many
    key sections are present.
    """
    if not sections:
        return 0.0
    total = len(sections)
    present = sum(1 for v in sections.values() if v == "Found")
    return round((present / total) * 100.0, 1)

