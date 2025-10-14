
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.views.decorators.http import require_http_methods
# import json
# from api.models.Coordinator import Coordinator


# def get_all_coordinators(request):
#     coordinators = Coordinator.objects.all().values(
#         'id', 'first_name', 'last_name', 'email', 'about', 'profile_pic',
#         'tat_completed', 'tat_breached'
#     )
#     # Convert QuerySet to list
#     data = list(coordinators)
#     # For profile_pic, make sure to return full URL
#     for item in data:
#         if item['profile_pic']:
#             item['profile_pic'] = request.build_absolute_uri(item['profile_pic'])
#     return JsonResponse(data, safe=False)

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from api.models.Coordinator import Coordinator

@login_required
def get_all_coordinators(request):
    user = request.user
    print("Fetching coordinator profile for:", user.username)

    try:
        # ✅ Get only the coordinator linked to the logged-in user
        coordinator = Coordinator.objects.get(user=user)
    except Coordinator.DoesNotExist:
        return JsonResponse({'error': 'Coordinator profile not found'}, status=404)

    # ✅ Prepare response data
    data = {
        "id": coordinator.id,
        "first_name": coordinator.first_name,
        "last_name": coordinator.last_name,
        "email": coordinator.email,
        "about": coordinator.about,
        "profile_pic": request.build_absolute_uri(coordinator.profile_pic.url)
                        if coordinator.profile_pic else "",
        "tat_completed": coordinator.tat_completed,
        "tat_breached": coordinator.tat_breached,
    }

    return JsonResponse({"result": data})
