from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from api.models.personalinfo import PersonalInfo

@login_required
def personal_info(request):
    """
    Returns logged-in doctor's info for sidebar without serializer.
    """
    try:
        doctor = PersonalInfo.objects.get(user=request.user)
        data = {
            "user": {
                "id": doctor.user.id,
                "username": doctor.user.username,
                "first_name": doctor.user.first_name,
                "last_name": doctor.user.last_name,
                "email": doctor.user.email
            },
            "uploadpicture": doctor.uploadpicture.url if doctor.uploadpicture else "",
            "about_me": doctor.about_me or "",
            "total_reported": doctor.total_reported,
            "phone": doctor.phone or "",
            "cnfpassword": doctor.cnfpassword or "",
            "title": doctor.title or "Senior Radiologist",
            "hospital": doctor.hospital or "U4rad Hospital"
        }
        return JsonResponse(data, safe=False)
    except PersonalInfo.DoesNotExist:
        return JsonResponse({"error": "Doctor info not found"}, status=404)
