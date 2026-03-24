import os


class Config:
    """Central app configuration loaded from environment variables."""

    # Flask
    SECRET_KEY = os.getenv("RESUME_MATCHER_SECRET_KEY", "dev_insecure_key_change_me")

    # Uploads
    UPLOAD_FOLDER = os.getenv("RESUME_MATCHER_UPLOAD_FOLDER", "uploads/")
    MAX_CONTENT_LENGTH = int(os.getenv("RESUME_MATCHER_MAX_CONTENT_MB", "16")) * 1024 * 1024
    ALLOWED_EXTENSIONS = {"pdf"}

    # AI / external services
    GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyC5t9e7vcltXhwcuXKMRT0ZqNNZR_nkwNI")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Features / flags
    ENABLE_EMBEDDING_MATCH = os.getenv("ENABLE_EMBEDDING_MATCH", "true").lower() == "true"


config = Config()

