import os
import google.generativeai as genai
from config import config


def generate_resume_suggestions(resume_text, job_description, missing_keywords):
    """
    Generate resume improvement suggestions using Gemini API.
    Fallback to static suggestions if API key is not present or call fails.
    """
    api_key = config.GEMINI_API_KEY

    # Static fallback
    fallback_suggestions = [
        "AI suggestions are limited; showing basic tips:",
        f"Consider adding missing skills: {', '.join(missing_keywords[:5])}.",
        "Quantify your achievements in the experience section.",
        "Tailor your resume summary to align closer to the job description.",
        "Ensure your layout is simple for ATS parsing."
    ]

    if not api_key:
        return fallback_suggestions

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(config.GEMINI_MODEL)

        prompt = f"""
        You are a professional resume advisor. Analyze the following resume and job description and suggest improvements. Focus on missing skills, better phrasing, and ways to improve job alignment.
        Return your suggestions as a bulleted list. Limit to 4-5 high-impact suggestions. Keep them concise.

        Missing Skills identified: {', '.join(missing_keywords)}

        Job Description:
        {job_description[:1000]}

        Resume:
        {resume_text[:1500]}
        """

        response = model.generate_content(prompt)
        text = getattr(response, "text", "") or ""

        suggestions = []
        for line in text.split("\n"):
            line = line.strip().strip("*-•").strip()
            if line:
                suggestions.append(line)
                if len(suggestions) >= 5:
                    break

        return suggestions if suggestions else fallback_suggestions
    except Exception as e:
        print(f"Error calling AI API: {e}")
        return fallback_suggestions
