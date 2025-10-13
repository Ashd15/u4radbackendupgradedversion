from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils.timezone import now
from api.models.patientdetails import PatientDetails
from api.models.Date import Date
from api.models.ecg_client import ECGClient
from api.models.Location import Location  # Import Location model
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@csrf_exempt
def upload_patient_ecg_api(request):
    query = request.GET.get("q", "")

    # ------------------------------
    # GET: fetch patients
    # ------------------------------
    if request.method == "GET":
        patients = PatientDetails.objects.all()  # Fetch all patients

        if query:
            patients = patients.filter(
                Q(PatientId__icontains=query) | Q(PatientName__icontains=query)
            )

        patients = patients.order_by("-id")

        paginator = Paginator(patients, 10)
        page_number = request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)

        patients_list = [
            {
                "id": p.id,
                "PatientId": p.PatientId,
                "PatientName": p.PatientName,
                "age": p.age,
                "gender": p.gender,
                "HeartRate": p.HeartRate,
                "PRInterval": p.PRInterval,
                "TestDate": p.TestDate,
                "ReportDate": p.ReportDate,
                "location": p.location.name if p.location else None,
                "image": p.image.url if p.image else None,
            }
            for p in page_obj
        ]

        return JsonResponse({
            "patients": patients_list,
            "page": page_obj.number,
            "total_pages": paginator.num_pages,
            "total_patients": paginator.count
        })

    # ------------------------------
    # POST: create patient
    # ------------------------------
    elif request.method == "POST":
        patient_id = request.POST.get("PatientId")
        patient_name = request.POST.get("PatientName")
        age = request.POST.get("age", "")
        gender = request.POST.get("gender", "")

        if not patient_id or not patient_name:
            return JsonResponse({"error": "PatientId and PatientName are required"}, status=400)

        patient = PatientDetails(
            PatientId=patient_id,
            PatientName=patient_name,
            age=age,
            gender=gender,
            HeartRate=request.POST.get("HeartRate"),
            PRInterval=request.POST.get("PRInterval")
        )

        today_str = now().strftime("%d-%m-%Y")
        patient.TestDate = today_str
        patient.ReportDate = today_str

        # Assign location: first try any ECGClient, else first Location in DB
        ecg_client = ECGClient.objects.first()
        if ecg_client:
            patient.location = ecg_client.location
        else:
            default_location = Location.objects.first()
            if default_location:
                patient.location = default_location
            else:
                # If no Location exists at all, create a default one
                patient.location = Location.objects.create(name="Default Location")

        # Ensure Date object has valid location
        date_obj, created = Date.objects.get_or_create(
            date_field=now().date(),
            location=patient.location
        )
        patient.date = date_obj

        if "image" in request.FILES:
            patient.image = request.FILES["image"]

        patient.save()

        return JsonResponse({
            "id": patient.id,
            "PatientId": patient.PatientId,
            "PatientName": patient.PatientName,
            "age": patient.age,
            "gender": patient.gender,
            "HeartRate": patient.HeartRate,
            "PRInterval": patient.PRInterval,
            "TestDate": patient.TestDate,
            "ReportDate": patient.ReportDate,
            "location": patient.location.name if patient.location else None,
            "image": patient.image.url if patient.image else None
        }, status=201)


@login_required
def get_ecg_client(request):
    if request.method == "GET":
        user = request.user
        try:
            ecg_client = ECGClient.objects.get(user=user)
        except ECGClient.DoesNotExist:
            return JsonResponse({"error": "ECG client not found"}, status=404)

        # Get patient records linked to the same location
        patients = PatientDetails.objects.filter(location=ecg_client.location)

        # Format patient data
        patient_data = [
            {
                "PatientId": p.PatientId,
                "PatientName": p.PatientName,
                "age": p.age,
                "gender": p.gender,
                "HeartRate": p.HeartRate,
                "TestDate": p.TestDate,
                "ReportDate": p.ReportDate,
                "Image": p.image.url if p.image else None,
                "status": p.status,
            }
            for p in patients
        ]

        # Return both client and patient data
        data = {
            "success": True,
            "client": {
                "username": ecg_client.user.username,
                "email": ecg_client.user.email,
                "location": str(ecg_client.location),
            },
            "patients": patient_data,
        }

        return JsonResponse(data, status=200)

    return JsonResponse({"error": "GET request required"}, status=400)
