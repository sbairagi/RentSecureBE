from weasyprint import HTML
import os

# HTML file path (use absolute path for image loading)
html_file = '/Users/sbairagi/Desktop/MVP Project/ai_platform_shared_be/test/rent_agreement.html'
abs_path = 'file://' + os.path.abspath(html_file)

# Generate PDF
HTML(abs_path).write_pdf('rent_agreement.pdf')

print("PDF generated successfully: rent_agreement.pdf")
