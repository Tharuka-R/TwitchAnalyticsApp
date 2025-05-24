from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch

def create_pdf(filename):
    c = canvas.Canvas(filename, pagesize=letter)
    c.setTitle("Twitch Streamer Performance Report")
    return c

def add_content_to_pdf(c, title, content):
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1 * inch, 10 * inch, title)
    c.setFont("Helvetica", 12)
    text = c.beginText(1 * inch, (10 * inch) - 20)
    text.setTextColor(colors.black)
    
    for line in content:
        text.textLine(line)
    
    c.drawText(text)

def save_pdf(c, filename):
    c.showPage()
    c.save()