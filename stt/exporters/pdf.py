def export_pdf(text, output_path):
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError:
        print("reportlab not installed. Install with 'pip install reportlab' to export PDF.")
        return

    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    y = height - 50
    for line in text.splitlines():
        if y < 50:
            c.showPage()
            y = height - 50
        c.drawString(50, y, line[:120])
        y -= 14
    c.save()
