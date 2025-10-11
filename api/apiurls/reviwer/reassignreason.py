from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from api.models.DICOMData import DICOMData

@csrf_exempt
@require_http_methods(["POST"])
def reassign_case(request, dicom_id):
    try:
        dicom = DICOMData.objects.get(id=dicom_id)
        data = json.loads(request.body)
        reason = data.get("review_reason", "").strip()

        if not reason:
            return JsonResponse({"error": "Review reason is required."}, status=400)

        # Get the case
        case = DICOMData.objects.get(id=dicom_id)
        case.for_review = True
        case.review_reason = reason
        case.save()

        return JsonResponse({
            "success": True,
            "message": f"Case {case.patient_id} marked for review.",
            "for_review": case.for_review,
            "review_reason": case.review_reason
        })

    except DICOMData.DoesNotExist:
        return JsonResponse({"error": "Case not found."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
