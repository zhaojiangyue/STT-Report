def export_docx(text, output_path):
    try:
        from docx import Document
    except ImportError:
        print("python-docx not installed. Install with 'pip install python-docx' to export DOCX.")
        return
    doc = Document()
    for line in text.splitlines():
        doc.add_paragraph(line)
    doc.save(output_path)
