
# views.py
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods

GROUP_DASHBOARD = {
    'client': '/client-dashboard',
    'coordinator': '/coordinator',
    'radiologist': '/doctor-dashboard',
    'reviewer': '/viewer',
}

@csrf_exempt
def api_login(request):
    if request.method != 'POST':
        return JsonResponse({"error": "POST request required"}, status=400)

    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not username or not password:
        return JsonResponse({"error": "Username and password required"}, status=400)

    user = authenticate(request, username=username, password=password)
    if not user:
        return JsonResponse({"error": "Invalid credentials"}, status=401)

    # Log in user
    login(request, user)

    # Mark user online
    if hasattr(user, "personalinfo"):
        user.personalinfo.is_online = True
        user.personalinfo.save()

    group = user.groups.values_list('name', flat=True).first()
    dashboard = GROUP_DASHBOARD.get(group, '/')

    return JsonResponse({
        "success": True,
        "username": user.username,
        "first_name": user.first_name,  # send first name
        "last_name": user.last_name,    # send last name
        "group": group,
        "dashboard": dashboard,
        "user_id": user.id
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_logout(request):
    user_id = request.session.get('_auth_user_id')
    if not user_id:
        return JsonResponse({"success": False, "message": "No active user found"})

    try:
        user = User.objects.get(pk=user_id)

        # Mark user offline
        if hasattr(user, 'personalinfo'):
            user.personalinfo.is_online = False
            user.personalinfo.save()

        # Log out user (important!)
        logout(request)
        request.session.flush()

        return JsonResponse({"success": True, "message": "User logged out and marked offline"})
    except User.DoesNotExist:
        return JsonResponse({"success": False, "message": "User not found"})
