import re
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.corpus import stopwords

# Ensure stopwords are downloaded
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

def _get_stopwords_set():
    try:
        return set(stopwords.words('english'))
    except LookupError:
        # If NLTK data isn't available (common with SSL/cert issues),
        # continue without stopword filtering instead of crashing.
        return set()

def extract_and_compare_keywords(resume_text, job_description):
    """
    Extract keywords from the job description and compare them with the resume.
    Returns matched, missing, and categorized keyword importance levels.
    """
    stop_words = _get_stopwords_set()
    
    def tokenize(text):
        text = text.lower()
        text = re.sub(r'[^a-z\s]', '', text)
        return [w for w in text.split() if w not in stop_words and len(w) > 2]
    
    jd_tokens = tokenize(job_description)
    resume_tokens = set(tokenize(resume_text))
    
    if not jd_tokens:
        return [], [], {"High Importance": [], "Medium Importance": [], "Low Importance": []}
        
    jd_sentences = [s.strip() for s in re.split(r'[.!?\n]', job_description) if len(s.strip()) > 10]
    if not jd_sentences:
        jd_sentences = [job_description]
        
    vectorizer = TfidfVectorizer(stop_words='english')
    try:
        tfidf_matrix = vectorizer.fit_transform(jd_sentences)
        feature_names = vectorizer.get_feature_names_out()
        
        # Calculate max or average TF-IDF score for each word
        scores = tfidf_matrix.mean(axis=0).A1
        keyword_scores = dict(zip(feature_names, scores))
    except ValueError:
        # Fallback if TF-IDF fails
        keyword_scores = {word: 1.0 for word in set(jd_tokens)}
        feature_names = list(set(jd_tokens))

    # Sort keywords by their score
    sorted_keywords = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)
    top_keywords = [kw[0] for kw in sorted_keywords[:min(30, len(sorted_keywords))]] # Top 30 words
    
    # If no top keywords derived via TFIDF, use frequency
    if not top_keywords:
        from collections import Counter
        freq = Counter(jd_tokens)
        top_keywords = [w for w, _ in freq.most_common(30)]
    
    matched_keywords = [kw for kw in top_keywords if kw in resume_tokens]
    missing_keywords = [kw for kw in top_keywords if kw not in resume_tokens]
    
    # Categorize into High, Medium, Low Importance
    n = len(top_keywords)
    high_imp = top_keywords[:max(1, n//3)]
    med_imp = top_keywords[max(1, n//3) : max(2, 2*n//3)]
    low_imp = top_keywords[max(2, 2*n//3):]
    
    importance_levels = {
        "High Importance": high_imp,
        "Medium Importance": med_imp,
        "Low Importance": low_imp
    }
    
    return matched_keywords, missing_keywords, importance_levels
