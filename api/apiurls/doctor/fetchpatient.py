from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from api.models.DICOMData import DICOMData
import traceback

class FetchDicomData(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            dicom_id = request.data.get('id')
            if not dicom_id:
                return Response({"error": "ID not provided"}, status=status.HTTP_400_BAD_REQUEST)

            # Convert string to int if ID is integer type
            try:
                dicom_id = int(dicom_id)
            except ValueError:
                pass  # leave as string if ID is UUID or string

            dicom = DICOMData.objects.get(id=dicom_id)

            # Build dictionary with required fields
            data = {
                "patient_name": dicom.patient_name,
                "patient_id": dicom.patient_id,
                "age": dicom.age,
                "gender": dicom.gender,
                "modality": dicom.Modality,
                "study_id": dicom.study_id,
                "study_description": dicom.study_description,
                "notes": dicom.notes,
                "body_part_examined": dicom.body_part_examined,
                "study_instance_uid": dicom.study_instance_uid,
                # Related files as lists of URLs
                "history_files": [hf.history_file.url for hf in dicom.history_files.all() if hf.history_file],
                "patient_reports": [
                    {
                        "report_file": pr.report_file.url,
                        "report_title": pr.report_title,
                        "uploaded_at": pr.uploaded_at
                    }
                    for pr in dicom.patient_reports.all()
                    if pr.report_file
                ]
            }

            return Response(data, status=status.HTTP_200_OK)

        except DICOMData.DoesNotExist:
            return Response({"error": "DICOM data not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "error": str(e),
                "trace": traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
