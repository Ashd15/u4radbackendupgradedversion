# from django.views.decorators.csrf import csrf_exempt
# from django.views.decorators.http import require_http_methods
# from django.http import JsonResponse
# from api.models.DICOMData import DICOMData

# @csrf_exempt
# @require_http_methods(["PUT"])
# def release_patient(request, dicom_id):
#     try:
#         dicom = DICOMData.objects.get(id=dicom_id)
#         dicom.twostepcheck = False
#         dicom.save()
#         return JsonResponse({"success": True, "message": "Patient released successfully."})
#     except DICOMData.DoesNotExist:
#         return JsonResponse({"success": False, "message": "Patient not found."}, status=404)
#     except Exception as e:
#         return JsonResponse({"success": False, "message": str(e)}, status=500)



from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from api.models.DICOMData import DICOMData

@csrf_exempt
@require_http_methods(["PUT"])
def release_patient(request, dicom_id):
    try:
        dicom = DICOMData.objects.get(id=dicom_id)
        
        # Parse JSON body to get reviewed_by
        body = json.loads(request.body)
        reviewer_name = body.get("reviewed_by", None)  # Optional field
        
        dicom.twostepcheck = False
        if reviewer_name:
            dicom.reviewed_by = reviewer_name
        dicom.save()
        
        return JsonResponse({"success": True, "message": "Patient released successfully."})
    
    except DICOMData.DoesNotExist:
        return JsonResponse({"success": False, "message": "Patient not found."}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)
