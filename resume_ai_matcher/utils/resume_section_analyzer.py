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
        "Certifications Section": "Missing"
    }
    
    text = resume_text.lower()
    
    # Keywords mapping for sections
    keywords = {
        "Skills Section": ["skills", "technical skills", "core competencies", "technologies"],
        "Projects Section": ["projects", "personal projects", "academic projects", "key projects"],
        "Experience Section": ["experience", "work experience", "professional experience", "employment history", "history"],
        "Education Section": ["education", "academic background", "qualifications", "degree","Academic"],
        "Certifications Section": ["certifications", "certificates", "courses", "licenses"],
    }
    
    for section, keys in keywords.items():
        for key in keys:
            # We look for the exact keyword acting as a header
            pattern = r'\b' + re.escape(key) + r'\b'
            if re.search(pattern, text):
                sections[section] = "Found"
                break
                
    return sections
