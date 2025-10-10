from django.http import JsonResponse
from api.models.DICOMData import DICOMData
# from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET

# @login_required
@require_GET
def dicom_summary_counts(request):
    total_cases = DICOMData.objects.count()
    reported_cases = DICOMData.objects.filter(isDone=True).count()
    pending_cases = DICOMData.objects.filter(isDone=False).count()
    

    data = {
        "total_cases": total_cases,
        "reported_cases": reported_cases,
        "pending_cases": pending_cases,
    }

    return JsonResponse(data, safe=False)
