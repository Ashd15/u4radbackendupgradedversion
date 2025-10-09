from django.core.paginator import Paginator
from django.http import JsonResponse
from api.models.EcgPdfReport import EcgReport

def fetch_ecg_pdf_reports(request):
    search = request.GET.get('search', '')
    test_date = request.GET.get('test_date', '')
    report_date = request.GET.get('report_date', '')
    location = request.GET.get('location', '')
    page_number = request.GET.get('page', 1)

    pdfs = EcgReport.objects.all().order_by('-id')

    # Apply filters
    if search:
        pdfs = pdfs.filter(name__icontains=search)  # corrected
    if test_date:
        pdfs = pdfs.filter(test_date=test_date)
    if report_date:
        pdfs = pdfs.filter(report_date=report_date)
    if location:
        pdfs = pdfs.filter(location=location)

    # Pagination
    paginator = Paginator(pdfs, 150)
    page_obj = paginator.get_page(page_number)

    # Prepare PDF data
    pdf_list = []
    for pdf in page_obj:
        pdf_list.append({
            "id": pdf.id,
            "patient_name": pdf.name,  # corrected
            "test_date": pdf.test_date.strftime('%Y-%m-%d') if pdf.test_date else None,
            "report_date": pdf.report_date.strftime('%Y-%m-%d') if pdf.report_date else None,
            "location": pdf.location,
            "pdf_file": pdf.pdf_file.url if pdf.pdf_file else None
        })

    # Filters
    test_dates = sorted({pdf.test_date.strftime('%Y-%m-%d') for pdf in pdfs if pdf.test_date})
    report_dates = sorted({pdf.report_date.strftime('%Y-%m-%d') for pdf in pdfs if pdf.report_date})
    locations = sorted({pdf.location for pdf in pdfs if pdf.location})

    return JsonResponse({
        "success": True,
        "data": {
            "pdfs": pdf_list,
            "pagination": {
                "current_page": page_obj.number,
                "total_pages": paginator.num_pages,
                "total_items": paginator.count,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous()
            },
            "Test_Date": test_dates,
            "Report_Date": report_dates,
            "Location": locations
        }
    })



# Download ECG PDF Report API
def download_ecg_pdf_report(request, report_id):
    try:
        pdf = EcgReport.objects.get(id=report_id)
        if not pdf.pdf_file:
            return JsonResponse({"success": False, "error": "PDF file not found."})

        # Return direct file URL
        return JsonResponse({"success": True, "url": pdf.pdf_file.url})

    except EcgReport.DoesNotExist:
        return JsonResponse({"success": False, "error": "Report not found."})
