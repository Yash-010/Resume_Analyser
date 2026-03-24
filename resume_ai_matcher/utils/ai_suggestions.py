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
You are a senior resume strategist, ATS optimization expert, and career coach with 15+ years of experience helping candidates get hired at top companies.

Your task is to analyze and improve the given resume based on a target job description.

-------------------------
INPUTS
-------------------------
Resume:
{resume_text}

Job Description:
{job_description}

Missing Skills Identified:
{', '.join(missing_keywords)}

-------------------------
OBJECTIVES
-------------------------

1. Improve the resume to be:
- ATS-friendly
- Results-oriented
- Impact-driven
- Aligned with the job description

2. Focus on:
- Strong action verbs
- Quantified achievements (numbers, %, impact)
- Industry-relevant keywords
- Clear and professional tone

3. Ensure:
- No generic advice
- No vague statements
- No repetition
- Practical and directly usable improvements

-------------------------
OUTPUT FORMAT (STRICT)
-------------------------

Return response in the following structured format:

1. KEY IMPROVEMENTS
Provide 4–6 concise bullet points of high-impact improvements.

2. MISSING SKILLS RECOMMENDATION
List the most important missing skills and how to incorporate them into the resume.

3. REWRITTEN BULLET POINTS
Rewrite 3–5 weak resume bullet points into strong, professional, ATS-optimized statements.

Each rewritten point must:
- Start with a strong action verb
- Include measurable impact if possible
- Be concise and professional

4. SECTION-WISE IMPROVEMENTS

Professional Summary:
(Rewrite or suggest improvement)

Skills Section:
(Suggest better structuring or additions)

Experience Section:
(Suggest improvements)

Projects Section:
(Suggest improvements if applicable)

5. FINAL ATS OPTIMIZATION TIPS
Give 3–5 actionable tips to improve ATS score.

-------------------------
IMPORTANT RULES
-------------------------

- Keep output clean and well-structured
- Use bullet points where needed
- Avoid long paragraphs
- Do NOT include explanations like "Here is your improved resume"
- Focus only on actionable improvements

-------------------------
GOAL
-------------------------

The final output should help transform the resume into a high-quality, job-winning resume aligned with the given job description.
"""

        response = model.generate_content(prompt)
        text = getattr(response, "text", "") or ""

        suggestions = []
        for line in text.split("\n"):
            line = line.strip().strip("*-•").strip()
            # Optionally remove bold formatting to look cleaner in HTML list output
            line = line.replace("**", "")
            if line:
                suggestions.append(line)

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
You are a senior technical interviewer with 15+ years of experience hiring candidates.

Your task is to analyze the candidate's resume and generate exactly 4 highly relevant and insightful interview questions.

-------------------------
INPUT
-------------------------

Candidate Resume:
{resume_text}

Job Description:
{job_description}

-------------------------
OBJECTIVES
-------------------------

1. Carefully analyze the resume and identify:
- technical skills
- projects
- tools and technologies used
- experience level

2. Generate interview questions that:
- are directly based on the candidate’s resume
- test real understanding (not theoretical definitions)
- are relevant to the job description
- assess problem-solving ability and practical knowledge

3. Questions must:
- be specific and personalized
- reference candidate’s experience/projects where possible
- NOT be generic questions like "What is machine learning?"
- challenge the candidate appropriately

-------------------------
QUESTION TYPES (IMPORTANT)
-------------------------

Ensure diversity in questions:

• 1 question about a project mentioned in the resume  
• 1 question about core technical skill (e.g., ML, Python, etc.)  
• 1 question about problem-solving or real-world scenario  
• 1 question about tools/technologies used  

-------------------------
OUTPUT FORMAT (STRICT)
-------------------------

Return exactly 4 questions in this format:

1. Question 1
2. Question 2
3. Question 3
4. Question 4

-------------------------
IMPORTANT RULES
-------------------------

- Do NOT add explanations
- Do NOT include headings
- Do NOT exceed 4 questions
- Keep questions concise but meaningful
- Make questions realistic as asked in real interviews

-------------------------
GOAL
-------------------------

Generate high-quality, personalized interview questions that help a recruiter effectively evaluate the candidate."""
        response = model.generate_content(prompt)
        text = getattr(response, "text", "") or ""
        import re
        questions = []
        for line in text.split("\n"):
            line = line.strip().strip("*-•").strip()
            line = line.replace("**", "")
            
            # If the line has more than 3 words, treat it as a valid output line
            if line and len(line.split()) > 3:
                # Strip leading numbers (e.g., "1. ") since the UI has its own formatting
                line = re.sub(r"^\d+\.\s*", "", line)
                questions.append(line)
                
            if len(questions) >= 4:
                break

        return questions if questions else fallback
    except Exception as e:
        print(f"Error generating interview questions: {e}")
        return fallback

