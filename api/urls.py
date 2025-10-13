from django.conf import settings
from django.urls import path
from django.conf.urls.static import static

from api.Ecg_cardiologist import views_report
from api.Ecg_cardiologist.views_cardio import GreetingAPIView, LocationListAPIView, PatientDetailAPIView, PatientListAPIView
from .apiurls.reviwer.reassignreason import reassign_case
from .views import (
    fetch_tat_counters, server_data, dicom_list, update_dicom,
    upload_history_file, fetch_patient_reports, get_all_coordinators,
    fetch_radiologists, assign_radiologist, replace_radiologist,
    fetch_body_parts, upload_ecg_api, update_patient, ecg_stats_api,
    get_locations, get_ecg_patients, update_patient_status,
    manage_cardiologist, get_cardiologists, upload_patient_ecg_api,api_logout,api_login,personal_info, FetchDicomData,dicom_summary_counts,get_all_institutions,search_dicom_data,completed_twostep_patients,release_patient,get_ecg_client
)
from .apiurls.ECG.ecg_download import fetch_ecg_pdf_reports, download_ecg_pdf_report

urlpatterns = [
    path('fetch-tat-counters/', fetch_tat_counters),
    path('serverdata/', server_data),
    path('dicom-list/', dicom_list),
    path("update-dicom/<int:dicom_id>/", update_dicom, name="update-dicom"),
    path("upload-historyfile/<int:dicom_id>/", upload_history_file, name="upload-historyfile"),
    path("fetch-reports/<int:dicom_id>/", fetch_patient_reports, name="fetch-reports"),
    path('coordinators/', get_all_coordinators, name='get_all_coordinators'),
    path('radiologists/', fetch_radiologists, name='fetch_radiologists'),
    path('assign-radiologist/', assign_radiologist, name='assign_radiologist'),
    path('replace-radiologist/', replace_radiologist, name='replace_radiologist'),
    path("body-parts/", fetch_body_parts, name="fetch_body_parts"),
    path("upload-ecg/", upload_ecg_api, name="upload_ecg_api"),
    path("ecg_patients/", get_ecg_patients, name="get_ecg_patients"),
    path("ecg_patients/<int:patient_id>/update-status/", update_patient_status, name="update_patient_status"),
    path('get-locations/', get_locations, name='get_locations'),
    path('manage-cardiologist/', manage_cardiologist, name='manage_cardiologist'),
    path('cardiologists/', get_cardiologists, name='get_cardiologists'),
    path("ecg_patients/<int:patient_id>/", update_patient, name="update_patient"),
    path('ecg_stats/', ecg_stats_api, name='ecg_stats_api'),
    path('ecg-reports/', fetch_ecg_pdf_reports, name='fetch_ecg_pdf_reports'),
    path('ecg-reports/download/<int:report_id>/', download_ecg_pdf_report, name='download_ecg_pdf_report'),
    path('get-ecg-client/', get_ecg_client, name='get_ecg_client'),
    path('upload-patient-ecgs/', upload_patient_ecg_api, name='upload_patient_ecg_api'),
    path('login/', api_login, name='api_login'),
    path('logout/', api_logout, name='api_logout'),
    path('personal-info/', personal_info, name='personal_info'),
    path('fetch-dicom/', FetchDicomData.as_view(), name='fetch_dicom'),
    #cardiologist
    path('greeting/', GreetingAPIView.as_view(), name='greeting-api'),
    path('get_locations/', LocationListAPIView.as_view(), name='get_locations'),
    path('patients_ecg/', PatientListAPIView.as_view(), name='patients-list'),
    path('patients_ecg/<int:pk>/', PatientDetailAPIView.as_view(), name='patients-detail'),
    path('report/preview/', views_report.report_preview, name='report-preview'),
    path('report/finalize/', views_report.report_finalize, name='report-finalize'),
    path('report_reject/', views_report.report_reject, name='report_reject'),
    path('ecg_stat/', views_report.ecg_stat, name='ecg_stat'),
    path('case_counts/',dicom_summary_counts , name='dicom_summary_counts'),
    path('all_institute/',get_all_institutions , name='get_all_institutions'),
    
    path('search_patient/',search_dicom_data , name='search_dicom_data'),
    path('review_patient/',completed_twostep_patients , name='completed_twostep_patients'),
    path('release_patient/<int:dicom_id>/',release_patient , name='release_patient'),
    path('reassign_case/<int:dicom_id>/', reassign_case, name='reassign_case'),
    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)