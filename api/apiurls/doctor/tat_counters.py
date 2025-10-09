

from django.http import JsonResponse
from api.models.DICOMData import DICOMData
from api.models.Client import ServiceTATSetting, Institution, Client
from datetime import datetime, timedelta
import pytz
from django.contrib.auth.decorators import login_required
from django.db.models import Case, When, Value, IntegerField


@login_required
def fetch_tat_counters(request):
    user = request.user

    # Pagination parameters
    limit = int(request.GET.get("limit", 6))  # default 10
    cursor = request.GET.get("cursor")  # last fetched id

    # Determine user group
    if user.groups.filter(name='coordinator').exists():
        dicoms = DICOMData.objects.all()
    elif user.groups.filter(name='radiologist').exists():
        dicoms = DICOMData.objects.filter(radiologist__user=user)
    else:
        try:
            client = Client.objects.get(user=user)
            institutions = client.institutions.all()
            dicoms = DICOMData.objects.filter(
                institution_name__in=[i.name for i in institutions]
            )
        except Client.DoesNotExist:
            dicoms = DICOMData.objects.none()

    # Apply cursor: fetch only IDs greater than last fetched
    if cursor:
        dicoms = dicoms.filter(id__lt=int(cursor))

    # Always order by id ascending before slicing
    # dicoms = dicoms.order_by('-id')[:limit]
    dicoms = dicoms.annotate(
    priority_order=Case(
        When(urgent=True, then=Value(1)),
        When(Mlc=True, then=Value(2)),
        When(vip=True, then=Value(3)),
        default=Value(4),
        output_field=IntegerField(),
    )
).order_by('priority_order', '-id')[:limit]  # sort by priority, then newest fir



    dicoms_list = list(dicoms)
    next_cursor = dicoms_list[-1].id if dicoms_list else None

    now = datetime.now(pytz.utc)
    data = []

    for dicom in dicoms_list:
        institution_name = dicom.institution_name
        service_name = dicom.Modality
        upload_time = dicom.notes_modified_at or dicom.recived_on_db
        is_urgent = dicom.urgent

        if not (institution_name and service_name):
            continue

        try:
            institution_obj = Institution.objects.get(name__iexact=institution_name)
        except Institution.DoesNotExist:
            institution_obj = None

        try:
            tat_setting = ServiceTATSetting.objects.get(
                institution=institution_obj,
                service__name__iexact=service_name
            )
        except ServiceTATSetting.DoesNotExist:
            tat_setting = None

        hour = upload_time.astimezone(pytz.utc).hour
        if tat_setting:
            if is_urgent:
                tat_hours = tat_setting.urgent_tat_hours
            elif 0 <= hour <= 6:
                tat_hours = tat_setting.night_tat_hours
            else:
                tat_hours = tat_setting.normal_tat_hours
        else:
            tat_hours = 4

        deadline = upload_time + timedelta(hours=tat_hours)

        if dicom.isDone and dicom.marked_done_at:
            actual_done_time = dicom.marked_done_at
            time_remaining_seconds = int((deadline - actual_done_time).total_seconds())
        else:
            time_remaining_seconds = int((deadline - now).total_seconds())

        overdue_seconds = abs(time_remaining_seconds) if time_remaining_seconds <= 0 else 0
        tat_breached = time_remaining_seconds <= 0

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
                    "uploaded_at": r.uploaded_at.strftime("%Y-%m-%d %H:%M:%S")  # formatted date
                }
                for r in dicom.patient_reports.all() if r.report_file
            ]
        })

    return JsonResponse({
        "results": data,
        "next_cursor": next_cursor
    })
