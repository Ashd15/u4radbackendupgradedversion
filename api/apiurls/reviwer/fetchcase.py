from django.http import JsonResponse
from api.models.DICOMData import DICOMData

def completed_twostep_patients(request):
    # Filter DICOMData where isDone=True and twostepcheck=True
    # Order by marked_done_at descending (latest first)
    dicoms = DICOMData.objects.filter(isDone=True, twostepcheck=True).order_by('-marked_done_at')
    
    data = []
    for dicom in dicoms:
        # Get related history files
        history_files = [hf.history_file.url for hf in dicom.history_files.all() if hf.history_file]
        
        # Get related patient reports
        patient_reports = [
            {
                "report_file": pr.report_file.url if pr.report_file else None,
                "report_title": pr.report_title,
                "uploaded_at": pr.uploaded_at
            }
            for pr in dicom.patient_reports.all()
        ]
        
        data.append({
             "id": dicom.id,
            "patient_name": dicom.patient_name,
            "patient_id": dicom.patient_id,
            "age": dicom.age,
            "gender": dicom.gender,
            "recived_on_db": dicom.recived_on_db,
            "notes": dicom.notes,
            "history_files": history_files,
            "patient_reports": patient_reports,
            "marked_done_at": dicom.marked_done_at
        })
    
    return JsonResponse(data, safe=False)
