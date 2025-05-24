from fpdf import FPDF
from datetime import datetime

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Twitch Streamer Performance Report', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf_report(viewer_data, follower_data, subscriber_data, bit_donor_data, gift_subber_data, donor_data, report_type='daily'):
    pdf = PDF()
    pdf.add_page()

    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f'{report_type.capitalize()} Performance Report', 0, 1, 'C')
    pdf.ln(10)

    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Viewer Count Data', 0, 1)
    pdf.set_font('Arial', '', 12)
    for entry in viewer_data:
        pdf.cell(0, 10, f"Date: {entry['date']}, Viewers: {entry['count']}", 0, 1)

    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Follower Data', 0, 1)
    pdf.set_font('Arial', '', 12)
    for entry in follower_data:
        pdf.cell(0, 10, f"Date: {entry['date']}, Followers: {entry['count']}", 0, 1)

    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Subscriber Data', 0, 1)
    pdf.set_font('Arial', '', 12)
    for entry in subscriber_data:
        pdf.cell(0, 10, f"Date: {entry['date']}, Subscribers: {entry['count']}", 0, 1)

    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Bit Donor Data', 0, 1)
    pdf.set_font('Arial', '', 12)
    for entry in bit_donor_data:
        pdf.cell(0, 10, f"Date: {entry['date']}, Bits Donated: {entry['count']}", 0, 1)

    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Gift Subber Data', 0, 1)
    pdf.set_font('Arial', '', 12)
    for entry in gift_subber_data:
        pdf.cell(0, 10, f"Date: {entry['date']}, Gift Subs: {entry['count']}", 0, 1)

    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Donor Data', 0, 1)
    pdf.set_font('Arial', '', 12)
    for entry in donor_data:
        pdf.cell(0, 10, f"Date: {entry['date']}, Total Donated: {entry['amount']}", 0, 1)

    pdf_file_name = f"twitch_report_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(pdf_file_name)
    return pdf_file_name