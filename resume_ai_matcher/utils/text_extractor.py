import pdfplumber

def extract_text_from_pdf(file_stream):
    """
    Extracts text from an uploaded PDF file stream using pdfplumber.
    """
    text = ""
    try:
        with pdfplumber.open(file_stream) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
    
    return text.strip()
