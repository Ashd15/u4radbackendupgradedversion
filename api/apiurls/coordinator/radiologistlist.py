# api/views/user_views.py

from django.contrib.auth.models import User
from django.http import JsonResponse
from api.models.personalinfo import PersonalInfo


def fetch_radiologists(request):
    # Filter users in the "radiologist" group
    users = User.objects.filter(groups__name="radiologist").values(
        "id", "username", "first_name", "last_name", "email", "is_active"
    )

    # Add is_online from PersonalInfo
    users_list = []
    for user in users:
        try:
            personal_info = PersonalInfo.objects.get(user_id=user["id"])
            user["is_online"] = personal_info.is_online
        except PersonalInfo.DoesNotExist:
            user["is_online"] = False  # default if no PersonalInfo exists
        users_list.append(user)

    return JsonResponse(users_list, safe=False)
