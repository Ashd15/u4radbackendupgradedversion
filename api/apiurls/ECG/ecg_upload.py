import io
from datetime import datetime
from django.core.files.base import ContentFile
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.auth.models import Group
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from api.models.Date import  Date
from api.models.Location import Location
from api.models.City import City
from api.models.patientdetails import PatientDetails
from api.models.Total_cases import Total_Cases
import json
from PyPDF2 import PdfReader
from pdf2image import convert_from_bytes
from django.core.exceptions import ObjectDoesNotExist
from api.forms import ECGUploadForm
import PyPDF2
import fitz  # PyMuPDF
# from .s3_utils import upload_to_s3  # Assuming you have a helper function for S3

def extract_patient_id(text):
    try:
        id = ''
        if "Id :" in text:
            id = text.split("Id :")[1].split(" ")[1].split("\n")[0].strip().lower()
            if id == '':
                fetched_id = text.split("Id :")[1].split("Name :")[0].strip().lower()
                id = fetched_id
                if id == '':
                    id = text.split("Comments")[1].split("HR")[0].strip()
        elif "Id:" in text:
            id = text.split("Id:")[1].split(" ")[1].split("\n")[0].strip().lower()
            if id == '':
                fetched_id = text.split("Id:")[1].split("Name :")[0].strip().lower()
                id = fetched_id
                if id == '':
                    id = text.split("Comments")[1].split("HR")[0].strip()
                    if id == '':
                        id = text.split("Id:")[1].split("Name:")[0].strip()
        return id.replace(" ", "")
    except IndexError:
        return 'Missing'




    # try:
        # id = str(text).split("Id")[1].split("\n")[0]
        # print(id)
        # if ":" in id:
        #     return id.split(":")[1].strip()
        # else:
        #     return id.strip()
    # except IndexError:
        # Handle cases where the expected format is not found
        # if text.count('Comments') > 1:
        #     return str(text).split("Comments\nComments")[1].split("HR")[0].split('\n')[1].split('\n')[0]
        # else:
        #     return str(text).split("Comments")[1].split("HR")[0].strip()
        

def extract_patient_name(text):
    try:
        return str(text).split("Name")[1].split("\n")[0].split(":")[1].strip()
    except IndexError:
        return 'None'

def extract_patient_age(text):
    try:
        return str(text).split("Age")[1].split("\n")[0].split(":")[1].strip()
    except IndexError:
        return '0'  # Default age if not found

def extract_patient_gender(text):
    try:
        return str(text).split("Gender")[1].split("\n")[0].split(":")[1].strip()
    except IndexError:
        return 'Missing'

def extract_heart_rate(text):
    try:
        hr = str(text).split("HR:")[1].split("/")[0].strip()
        return hr
    except IndexError:
        return '0'  # Default heart rate if not found


def extract_pr_interval(text):
    try:
        return str(text).split("PR:")[1].split("QRS:")[0].split("ms")[0].strip()
    except IndexError:
        return '0'  # Default PR interval if not found

def extract_report_time(text):
    try:
        return str(text).split("Acquired on:")[1][12:17].strip()
    except IndexError:
        return '00:00'  # Default time if not found

def extract_date(text):
    try:
        if "Acquired on:" in str(text):
            raw_date = str(text).split("Acquired on:")[1][0:11].strip()
        
        # To resolve the extra space issue.
        if "Acquiredon:" in str(text):
            raw_date = str(text).split("Acquiredon:")[1][0:10].strip()

        if isinstance(raw_date, str):
            return datetime.strptime(raw_date, '%Y-%m-%d').date()
        else:
            return raw_date  # If raw_date is already a datetime.date, return it as is
    except (IndexError, ValueError):
        return datetime.now().date()  # Default to current date if not found

# To fix the duplicate extraction of some ecg graph pdf's.
def deduplicate_text(text):
    lines = text.split('\n')
    unique_lines = list(dict.fromkeys(lines))
    return '\n'.join(unique_lines)

# I am adding this function so that it can solve the issue of space after each character.
def clean_page_data(first_page_text):
    # Split the input data by lines
    lines = first_page_text.split('\n')
    
    # Initialize a list to hold cleaned lines
    cleaned_lines = []
    
    # Iterate through each line
    for line in lines:
        # Remove spaces after each character by replacing ' ' with '' and then joining characters
        cleaned_line = ''.join(line.split())
        
        # Append the cleaned line to the list
        cleaned_lines.append(cleaned_line)
    
    # Join the cleaned lines with newline characters for final output
    return '\n'.join(cleaned_lines)




@csrf_exempt
def upload_ecg_api(request):
    success_details = []
    missing_id = []
    processing_error = []

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Use POST method only'})

    form = ECGUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse({'success': False, 'error': 'Form not valid', 'form_errors': form.errors})

    location = form.cleaned_data['location']
    ecg_files = request.FILES.getlist('ecg_file[]') or request.FILES.getlist('ecg_file')

    for ecg_file in ecg_files:
        try:
            pdf_bytes = ecg_file.read()
            if not pdf_bytes:
                raise ValueError("Empty file")
        except Exception as e:
            processing_error.append({'name': ecg_file.name, 'error': f"File read error: {str(e)}"})
            continue

        # Extract text for patient ID
        try:
            pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
            first_page_text = pdf_reader.pages[0].extract_text() or ""
        except Exception:
            first_page_text = ""

        # Extract patient ID (replace with your function)
        patient_id = extract_patient_id(first_page_text)
        if not patient_id:
            missing_id.append({'id': None, 'name': ecg_file.name})
            continue

        # Ensure unique PatientId
        original_patient_id = patient_id
        suffix = 1
        while PatientDetails.objects.filter(PatientId=patient_id).exists():
            suffix += 1
            patient_id = f"{original_patient_id}-{suffix}"

        # Extract other patient info
        patient_name = extract_patient_name(first_page_text)
        patient_age = extract_patient_age(first_page_text)
        patient_gender = extract_patient_gender(first_page_text)
        heart_rate = extract_heart_rate(first_page_text)
        pr_interval = extract_pr_interval(first_page_text)
        formatted_date = extract_date(first_page_text)
        date_obj, _ = Date.objects.get_or_create(date_field=formatted_date, location=location)

        # Create patient record
        patient = PatientDetails.objects.create(
            PatientId=patient_id,
            PatientName=patient_name,
            age=patient_age,
            gender=patient_gender,
            HeartRate=heart_rate,
            PRInterval=pr_interval,
            TestDate=formatted_date,
            ReportDate=formatted_date,
            date=date_obj,
            location=location
        )

        # Convert first PDF page to JPEG using PyMuPDF
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            page = doc.load_page(0)  # first page
            pix = page.get_pixmap(dpi=200)  # render page to image
            img_bytes = pix.tobytes("jpeg")

            # Save image to ImageField
            filename = f"{patient.PatientId}.jpg"
            patient.image.save(filename, ContentFile(img_bytes), save=True)

            success_details.append({'id': patient_id, 'name': ecg_file.name})

        except Exception as e:
            processing_error.append({'id': patient_id, 'name': ecg_file.name, 'error': f"Image conversion failed: {str(e)}"})

    return JsonResponse({
        'success': True,
        'success_details': success_details,
        'missing_id': missing_id,
        'processing_error': processing_error
    })

@csrf_exempt
def get_locations(request):
    if request.method == "GET":
        locations = list(
            Location.objects.select_related("city").values(
                "id", "name", "technician_name", "city__id", "city__name"
            )
        )
        return JsonResponse({"success": True, "locations": locations})
    return JsonResponse({"success": False, "error": "Invalid request method"}, status=400)




@csrf_exempt
def update_patient(request, patient_id):
    try:
        patient = PatientDetails.objects.get(id=patient_id)
    except ObjectDoesNotExist:
        return JsonResponse({"error": "Patient not found."}, status=404)

    if request.method == "PATCH":
        try:
            data = json.loads(request.body.decode("utf-8"))

            # Update only provided fields
            if "PatientName" in data:
                patient.PatientName = data["PatientName"].strip()
            if "PatientId" in data:
                patient.PatientId = data["PatientId"].strip()
            if "Age" in data or "age" in data:
                patient.age = str(data.get("Age") or data.get("age"))
            if "HeartRate" in data:
                patient.HeartRate = str(data["HeartRate"])
            if "gender" in data:
                patient.gender = data["gender"]

            patient.save()

            return JsonResponse({
                "id": patient.id,
                "PatientName": patient.PatientName,
                "PatientId": patient.PatientId,
                "age": patient.age,
                "gender": patient.gender,
                "HeartRate": patient.HeartRate,
                "TestDate": patient.TestDate,
                "ReportDate": patient.ReportDate,
                "isDone": patient.isDone,
                "status": patient.status,
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request method."}, status=405)

@csrf_exempt
def ecg_stats_api(request):
    """Returns ECG statistics only"""
    if request.method == 'GET':
        total_current_uploaded = PatientDetails.objects.count()
        total_cases = Total_Cases.objects.first()
        total_uploaded_ecg = total_cases.total_uploaded_ecg if total_cases else 0
        total_reported_ecg = total_cases.total_reported_ecg if total_cases else 0

        total_reported_patients = PatientDetails.objects.filter(cardiologist__isnull=False, isDone=True).count()
        total_non_reportable = PatientDetails.objects.filter(NonReportable=True).count()  # Updated line

        total_unreported_and_unallocated = PatientDetails.objects.filter(cardiologist=None, isDone=False).count()
        total_unreported_and_allocated = PatientDetails.objects.filter(cardiologist__isnull=False, isDone=False).count()
        total_unreported_patients = total_unreported_and_unallocated + total_unreported_and_allocated

        stats = {
            "Current Uploaded": total_current_uploaded,
            "Current Reported": total_reported_patients,
            "Unreported Cases": total_unreported_patients,
            "Unallocated Cases": total_unreported_and_unallocated,
            "Total Uploaded Cases": total_uploaded_ecg,
            "Reported Cases": total_reported_ecg,
            "Rejected Cases": total_non_reportable  # Updated line
        }
        return JsonResponse({"stats": stats}, status=200)

    return JsonResponse({"error": "Only GET method allowed"}, status=405)