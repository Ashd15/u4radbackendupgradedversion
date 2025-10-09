# backend/dicom_upload/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import FileResponse
from django.conf import settings
import tempfile, os
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from api.models.EcgPdfReport import EcgReport

@api_view(['GET'])
def add_logo_to_ecg_pdf_api(request, pdf_id):
    """
    API to add logo and footer to locally stored ECG PDF and return modified PDF
    """
    try:
        report = EcgReport.objects.get(id=pdf_id)

        # Get path of local PDF file
        original_pdf_path = report.pdf_file.path

        # Read original PDF
        reader = PdfReader(original_pdf_path)
        writer = PdfWriter()

        # Create overlay PDF with logo and footer
        with tempfile.NamedTemporaryFile(delete=False) as overlay_temp:
            c = canvas.Canvas(overlay_temp.name, pagesize=letter)

            # Logo
            logo_path = os.path.join(settings.BASE_DIR, 'users', 'static', 'company_logos', 'logo.png')
            c.drawImage(logo_path, x=40, y=735, width=320, height=60, mask='auto')

            # Footer
            footer_path = os.path.join(settings.BASE_DIR, 'users', 'static', 'company_logos', 'footer.png')
            c.drawImage(footer_path, x=30, y=20, width=550, height=50, mask='auto')

            c.save()
            overlay_pdf_path = overlay_temp.name

        overlay = PdfReader(overlay_pdf_path)

        # Merge overlay on first page
        for i, page in enumerate(reader.pages):
            if i == 0:  # First page only
                page.merge_page(overlay.pages[0])
            writer.add_page(page)

        # Save final modified PDF
        with tempfile.NamedTemporaryFile(delete=False) as final_output:
            writer.write(final_output)
            final_output_path = final_output.name

        filename = os.path.basename(report.pdf_file.name)
        return FileResponse(open(final_output_path, "rb"), as_attachment=True, filename=filename)

    except EcgReport.DoesNotExist:
        return Response({"error": "Report not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
