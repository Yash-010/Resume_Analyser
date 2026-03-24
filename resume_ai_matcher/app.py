import os
from flask import Flask, render_template, request, flash, redirect, url_for, send_file, jsonify
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
import utils.pipeline as pipeline

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

def analyze_resume_text(resume_text, filename, job_description, jd_top_skills):
    """
    Shared analysis pipeline used by both Job Seeker and Recruiter modes.
    Returns a serializable dict for JSON responses.
    """
    candidate_name = extract_candidate_name(resume_text)

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

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/job-seeker', methods=['GET'])
def job_seeker_page():
    return render_template('job_seeker.html')

@app.route('/job-seeker/analyze', methods=['POST'])
def job_seeker_analyze_page():
    if "resume" not in request.files:
        flash("No resume file uploaded.", "error")
        return redirect(url_for("job_seeker_page"))

    resume_file = request.files["resume"]
    job_description = request.form.get("job_description", "")
    if not job_description.strip():
        flash("Please provide a job description.", "error")
        return redirect(url_for("job_seeker_page"))

    if not resume_file or resume_file.filename == "" or not allowed_file(resume_file.filename):
        flash("Please upload a valid PDF resume.", "error")
        return redirect(url_for("job_seeker_page"))

    filename = secure_filename(resume_file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    resume_file.save(file_path)

    with open(file_path, "rb") as f:
        resume_text = extract_text_from_pdf(f)

    jd_top_skills = extract_top_skills(job_description)
    result = pipeline.analyze_resume_text(resume_text, filename, job_description, jd_top_skills)

    return render_template(
        "job_seeker_result.html",
        result=result,
        top_required_skills=jd_top_skills,
        job_description=job_description,
    )


@app.route('/recruiter', methods=['GET'])
def recruiter_page():
    return render_template('recruiter.html')


@app.route('/recruiter/analyze', methods=['POST'])
def recruiter_analyze_page():
    if "resumes" not in request.files:
        flash("No resumes uploaded.", "error")
        return redirect(url_for("recruiter_page"))

    files = request.files.getlist("resumes")
    job_description = request.form.get("job_description", "")
    if not job_description.strip():
        flash("Please provide a job description.", "error")
        return redirect(url_for("recruiter_page"))

    jd_top_skills = extract_top_skills(job_description)
    results = []

    for file in files:
        if not file or file.filename == "" or not allowed_file(file.filename):
            continue

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        with open(file_path, "rb") as f:
            resume_text = extract_text_from_pdf(f)

        result = pipeline.analyze_resume_text(resume_text, filename, job_description, jd_top_skills)
        results.append(result)

    if not results:
        flash("No valid PDF resumes were processed.", "error")
        return redirect(url_for("recruiter_page"))

    results.sort(key=lambda x: x["score"], reverse=True)
    for index, res in enumerate(results):
        res["rank"] = index + 1

    recommended_candidate = results[0]

    return render_template(
        "recruiter_result.html",
        results=results,
        recommended_candidate=recommended_candidate,
        job_description=job_description,
    )


@app.route('/api/job-seeker/analyze', methods=['POST'])
def api_job_seeker_analyze():
    if "resume" not in request.files:
        return jsonify({"error": "No resume file uploaded."}), 400

    resume_file = request.files["resume"]
    job_description = request.form.get("job_description", "")
    if not job_description.strip():
        return jsonify({"error": "Please provide a job description."}), 400

    if not resume_file or resume_file.filename == "" or not allowed_file(resume_file.filename):
        return jsonify({"error": "Please upload a valid PDF resume."}), 400

    filename = secure_filename(resume_file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    resume_file.save(file_path)

    with open(file_path, "rb") as f:
        resume_text = extract_text_from_pdf(f)

    jd_top_skills = extract_top_skills(job_description)
    result = pipeline.analyze_resume_text(resume_text, filename, job_description, jd_top_skills)

    # For UI context
    result["top_required_skills"] = jd_top_skills
    return jsonify(result)


@app.route('/api/recruiter/analyze', methods=['POST'])
def api_recruiter_analyze():
    if "resumes" not in request.files:
        return jsonify({"error": "No resumes uploaded."}), 400

    files = request.files.getlist("resumes")
    job_description = request.form.get("job_description", "")
    if not job_description.strip():
        return jsonify({"error": "Please provide a job description."}), 400

    jd_top_skills = extract_top_skills(job_description)

    results = []
    for file in files:
        if not file or file.filename == "" or not allowed_file(file.filename):
            continue

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        with open(file_path, "rb") as f:
            resume_text = extract_text_from_pdf(f)

        result = pipeline.analyze_resume_text(resume_text, filename, job_description, jd_top_skills)
        results.append(result)

    if not results:
        return jsonify({"error": "No valid PDF resumes were processed."}), 400

    results.sort(key=lambda x: x["score"], reverse=True)
    for index, res in enumerate(results):
        res["rank"] = index + 1

    recommended_candidate = results[0]

    return jsonify(
        {
            "job_description": job_description,
            "top_required_skills": jd_top_skills,
            "results": results,
            "recommended_candidate": recommended_candidate,
        }
    )

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
