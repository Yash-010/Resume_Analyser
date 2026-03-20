import os
from flask import Flask, render_template, request, flash, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from io import StringIO
import csv
from utils.text_extractor import extract_text_from_pdf
from utils.similarity_engine import calculate_similarity
from utils.keyword_analyzer import (
    extract_and_compare_keywords,
    extract_top_skills,
)
from utils.resume_section_analyzer import analyze_sections, compute_completeness_score
from utils.ai_suggestions import (
    generate_resume_suggestions,
    generate_learning_path,
    generate_interview_questions,
)
from utils.ats_checker import analyze_ats_compatibility
from utils.scoring import compute_scores
from config import config

app = Flask(__name__)
# Secret key for session management (flash messages)
app.secret_key = config.SECRET_KEY
app.config["UPLOAD_FOLDER"] = config.UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH

# Ensure upload directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def extract_candidate_name(resume_text: str) -> str:
    """
    Very lightweight heuristic to infer candidate name from resume text.
    """
    if not resume_text:
        return ""

    lines = [l.strip() for l in resume_text.splitlines() if l.strip()]
    if not lines:
        return ""

    # Prefer an explicit "Name:" field if present
    for line in lines[:10]:
        if line.lower().startswith("name:"):
            return line.split(":", 1)[1].strip()

    # Otherwise, take the first non-empty line that doesn't look like contact info
    for line in lines[:10]:
        lower = line.lower()
        if any(x in lower for x in ["email", "phone", "linkedin", "@"]):
            continue
        if len(line.split()) <= 5:
            return line

    return ""

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS
    )

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'resumes' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('index'))
        
    files = request.files.getlist('resumes')
    job_description = request.form.get('job_description', '')
    
    if not job_description.strip():
        flash('Please provide a job description.', 'error')
        return redirect(url_for('index'))
        
    if not files or files[0].filename == '':
        flash('No files selected.', 'error')
        return redirect(url_for('index'))
        
    results = []
    jd_top_skills = extract_top_skills(job_description)
    
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Extract text
            with open(file_path, "rb") as f:
                resume_text = extract_text_from_pdf(f)

            # Per-resume safety: allow partial failures
            try:
                matched, missing, importance = extract_and_compare_keywords(
                    resume_text, job_description
                )
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

            # Compute ATS compatibility
            ats_score, ats_issues = analyze_ats_compatibility(resume_text, sections)

            # Compute multi-factor scores
            score_components = compute_scores(
                resume_text,
                job_description,
                sections,
                matched,
                missing,
                jd_top_skills,
            )

            # AI-based enhancements
            try:
                suggestions = generate_resume_suggestions(
                    resume_text, job_description, missing
                )
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
                interview_questions = generate_interview_questions(
                    resume_text, job_description
                )
            except Exception as e:
                print(f"Error generating interview questions for {filename}: {e}")
                interview_questions = []

            results.append(
                {
                    "filename": filename,
                    "candidate_name": extract_candidate_name(resume_text),
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
                    # raw text could be used for UI heatmaps; keep for now
                    "resume_text": resume_text,
                }
            )

    if not results:
        flash(
            "No valid PDF resumes were processed. Please upload one or more PDF files (file must end in .pdf).",
            "error",
        )
        return redirect(url_for("index"))

    # Sort results directly by score descending
    results.sort(key=lambda x: x["score"], reverse=True)

    # Assign ranks
    for index, res in enumerate(results):
        res["rank"] = index + 1

    recommended_candidate = results[0] if results else None

    return render_template(
        "results.html",
        results=results,
        job_description=job_description,
        top_required_skills=jd_top_skills,
        recommended_candidate=recommended_candidate,
    )


@app.route("/export_csv", methods=["POST"])
def export_csv():
    """
    Export analysis results as a CSV.
    Expects the same POST as /analyze; re-runs analysis in a lightweight form.
    """
    if "resumes" not in request.files:
        flash("No file part", "error")
        return redirect(url_for("index"))

    files = request.files.getlist("resumes")
    job_description = request.form.get("job_description", "")

    if not job_description.strip() or not files or files[0].filename == "":
        flash("Please provide job description and at least one resume.", "error")
        return redirect(url_for("index"))

    rows = [["Filename", "Score", "Matched skills", "Missing skills"]]

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)

            with open(file_path, "rb") as f:
                resume_text = extract_text_from_pdf(f)

            score = calculate_similarity(resume_text, job_description)
            matched, missing, _ = extract_and_compare_keywords(
                resume_text, job_description
            )

            rows.append(
                [
                    filename,
                    score,
                    ", ".join(matched),
                    ", ".join(missing),
                ]
            )

    csv_buffer = StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerows(rows)
    csv_buffer.seek(0)

    return send_file(
        csv_buffer,
        mimetype="text/csv",
        as_attachment=True,
        download_name="resume_analysis.csv",
    )

if __name__ == '__main__':
    app.run(debug=True)
