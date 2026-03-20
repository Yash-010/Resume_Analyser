import os
import re
import nltk
from nltk.corpus import stopwords
from config import config

# Ensure stopwords are downloaded beforehand
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

_EMBEDDING_MODEL = None


def _get_embedding_model():
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is not None:
        return _EMBEDDING_MODEL

    from sentence_transformers import SentenceTransformer

    model_name = os.getenv(
        "RESUME_MATCHER_EMBEDDING_MODEL",
        "all-MiniLM-L6-v2",
    )
    _EMBEDDING_MODEL = SentenceTransformer(model_name)
    return _EMBEDDING_MODEL


def _get_stopwords_set():
    try:
        return set(stopwords.words('english'))
    except LookupError:
        # NLTK download can fail in some environments (e.g., SSL issues).
        # Fall back to no stopword filtering rather than crashing the app.
        return set()

def preprocess_text(text):
    """
    Cleans text by lowering case, removing non-alphanumeric chars,
    and filtering out stopwords.
    """
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    tokens = text.split()
    stop_words = _get_stopwords_set()
    filtered_tokens = [word for word in tokens if word not in stop_words]
    return " ".join(filtered_tokens)

def calculate_similarity(resume_text, job_description):
    """
    Calculate match score between resume and job description.
    Uses semantic embeddings when available, otherwise falls back
    to a CountVectorizer + cosine similarity baseline.
    """
    clean_resume = preprocess_text(resume_text)
    clean_jd = preprocess_text(job_description)
    
    if not clean_resume or not clean_jd:
        return 0.0

    # Try semantic embeddings first if enabled
    if config.ENABLE_EMBEDDING_MATCH:
        try:
            from sentence_transformers import util

            model = _get_embedding_model()

            # normalize_embeddings=True makes cosine similarity == dot product
            resume_emb = model.encode(clean_resume, normalize_embeddings=True)
            jd_emb = model.encode(clean_jd, normalize_embeddings=True)

            base_score = float(util.dot_score(resume_emb, jd_emb).item()) * 100.0
            score = max(0.0, min(base_score, 100.0))
            return round(score, 2)
        except Exception as _:
            # Fall back silently to traditional vectorizer
            pass

    # Fallback: traditional bag-of-words similarity
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    vectorizer = CountVectorizer(stop_words="english", ngram_range=(1, 2))
    try:
        vectors = vectorizer.fit_transform([clean_resume, clean_jd])
        sim_matrix = cosine_similarity(vectors)
        base_score = float(sim_matrix[0, 1]) * 100
        score = min(base_score * 1.5, 100.0)
        return round(score, 2)
    except ValueError:
        return 0.0
