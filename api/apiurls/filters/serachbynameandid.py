from django.http import JsonResponse
from django.views.decorators.http import require_GET
from api.models.DICOMData import DICOMData
from django.db.models import Q

@require_GET
def search_dicom_data(request):
    patient_name = request.GET.get('patient_name', '').strip()
    patient_id = request.GET.get('patient_id', '').strip()

    # Filter using Q objects for flexible searching
    query = Q()
    if patient_name:
        query |= Q(patient_name__icontains=patient_name)
    if patient_id:
        query |= Q(patient_id__icontains=patient_id)

    if not query:
        return JsonResponse({'error': 'Please provide patient_name or patient_id for searching.'}, status=400)

    # Fetch matching records
    dicoms = DICOMData.objects.filter(query).prefetch_related('radiologist', 'corporatecoordinator', 'history_files', 'patient_reports')

    data = []
    for dicom in dicoms:
        overdue_seconds = 0  # calculate if needed
        tat_breached = False  # calculate if needed
        time_remaining_seconds = 0  # calculate if needed

        data.append({
            "id": dicom.id,
            "patient_name": dicom.patient_name or "Unknown",
            "patient_id": dicom.patient_id or "Unknown",
            "age": dicom.age or "Unknown",
            "gender": dicom.gender or "Unknown",
            "study_date": dicom.study_date or "Unknown",
            "study_time": dicom.study_time.isoformat() if dicom.study_time else None,
            "recived_on_orthanc": dicom.recived_on_orthanc.isoformat() if dicom.recived_on_orthanc else None,
            "recived_on_db": dicom.recived_on_db.isoformat() if dicom.recived_on_db else None,
            "modality": dicom.Modality or "Unknown",
            "study_id": dicom.study_id or "Unknown",
            "study_description": dicom.study_description or "No description",
            "is_done": dicom.isDone,
            "NonReportable": dicom.NonReportable,
            "Mlc": dicom.Mlc,
            "urgent": dicom.urgent,
            "vip": dicom.vip,
            "twostepcheck": dicom.twostepcheck,
            "notes": dicom.notes or "No notes",
            "location": dicom.location or "Unknown",
            "radiologist": [
                f"{r.user.first_name} {r.user.last_name}" if r.user else "Unknown"
                for r in dicom.radiologist.all()
            ],
            "corporatecoordinator": [c.name for c in dicom.corporatecoordinator.all()],
            "body_part_examined": dicom.body_part_examined or "Unknown",
            "institution_name": dicom.institution_name or "None",
            "referring_doctor_name": dicom.referring_doctor_name or "None",
            "whatsapp_number": dicom.whatsapp_number or "Unknown",
            "radiologist_assigned_at": dicom.radiologist_assigned_at.isoformat() if dicom.radiologist_assigned_at else None,
            "marked_done_at": dicom.marked_done_at.isoformat() if dicom.marked_done_at else None,
            "notes_modified_at": dicom.notes_modified_at.isoformat() if dicom.notes_modified_at else None,
            "study_instance_uid": dicom.study_instance_uid or "Unknown",
            "contrast_used": dicom.contrast_used,
            "is_follow_up": dicom.is_follow_up,
            "imaging_views": dicom.imaging_views or "None",
            "inhouse_patient": dicom.inhouse_patient,
            "email": dicom.email or "Unknown",
            "overdue_seconds": overdue_seconds,
            "tat_breached": tat_breached,
            "time_remaining": time_remaining_seconds,
            "history_files": [
                request.build_absolute_uri(f.history_file.url)
                for f in dicom.history_files.all() if f.history_file
            ],
            "patient_reports": [
                {
                    "title": r.report_title or "Unnamed Report",
                    "url": request.build_absolute_uri(r.report_file.url),
                    "uploaded_at": r.uploaded_at.strftime("%Y-%m-%d %H:%M:%S")
                }
                for r in dicom.patient_reports.all() if r.report_file
            ]
        })

    return JsonResponse({'results': data}, status=200)
