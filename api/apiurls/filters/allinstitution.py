from django.http import JsonResponse
from api.models.Client import Institution  # adjust import if needed
from django.views.decorators.http import require_GET

@require_GET
def get_all_institutions(request):
    institutions = Institution.objects.all().values_list('name', flat=True)
    data = list(institutions)
    return JsonResponse({'institutions': data}, status=200)
