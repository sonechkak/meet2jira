def extract_text_from_file(file_path: str, content_type: str) -> str:
    """Extract text from different file types."""

    if content_type == 'text/plain':
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    elif content_type == 'application/pdf':
        import PyPDF2
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text

    elif content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        # Word документы (.docx)
        from docx import Document
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text

    elif content_type.startswith('image/'):
        import pytesseract
        from PIL import Image
        image = Image.open(file_path)
        return pytesseract.image_to_string(image, lang='rus+eng')

    else:
        raise ValueError(f"Unsupported file type: {content_type}")
