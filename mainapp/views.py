from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.authtoken.models import Token
from .serializers import *
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import OTP, PercantageSurgery, Subscription, Surgery, UserProfile
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import authentication_classes, permission_classes
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string 
from authentications.otpGenarate import generate_otp
from django.utils import timezone
import django.http
from openpyxl import Workbook
from .models import Surgery
from fpdf import FPDF
from django.utils.timezone import now
from datetime import timedelta

from background_task import background

from django.core.mail import send_mail

#userprofile       
@api_view(['GET', 'PUT', 'PATCH'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated]) 
def user_profile(request):
    profile = get_object_or_404(UserProfile,user=request.user)

    if request.method == 'GET':
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
       
        serializer = UserProfileSerializer(profile, data=request.data, partial=(request.method == 'PATCH'))

        if request.FILES.get('profile_picture'):
            print("profile_picture", request.FILES['profile_picture'])
          
            profile.profile_picture = request.FILES['profile_picture']
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)
    
 
 

@api_view(['GET'])
@permission_classes([IsAuthenticated])  # Ensure only authenticated users can access
def get_surgery_names(request):
    # Filter surgeries by the logged-in user
    user = request.user
    names = PercantageSurgery.objects.filter(user=user).values_list('surgery_name', flat=True).distinct()
    return Response({"names": list(names)})
    

@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])  # Restrict to authenticated users
def percentage_surgery_view(request, pk=None):
    if request.method == 'GET':
        if pk:
            try:
                percentage = PercantageSurgery.objects.get(pk=pk, user=request.user)
                # Calculate completed surgeries for this percentage's surgery name
                completed_surgeries_count = Surgery.objects.filter(
                    user=request.user,
                    name_of_surgery=percentage.surgery_name,
                    
                ).count()

                serializer = PercantageSerializer(percentage)
                data = serializer.data
                data['completed_surgeries'] = completed_surgeries_count  # Append the count
                return Response(data, status=status.HTTP_200_OK)
            except PercantageSurgery.DoesNotExist:
                return Response({'error': 'PercantageSurgery not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            percentages = PercantageSurgery.objects.filter(user=request.user)
            serializer = PercantageSerializer(percentages, many=True)
            
            # Append completed surgeries count for each percentage
            data = []
            for percentage in serializer.data:
                completed_surgeries_count = Surgery.objects.filter(
                    user=request.user,
                    name_of_surgery=percentage['surgery_name'],
                    
                ).count()
                print("param ", completed_surgeries_count)
                percentage['completed_surgeries'] = completed_surgeries_count  # Append the count
                data.append(percentage)

            return Response(data, status=status.HTTP_200_OK)

    if request.method == 'POST':
        serializer = PercantageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)  # Associate with the logged-in user
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        if pk:
            try:
                percentage = PercantageSurgery.objects.get(pk=pk, user=request.user)
                percentage.delete()
                return Response({'message': 'PercantageSurgery deleted successfully'}, status=status.HTTP_200_OK)
            except PercantageSurgery.DoesNotExist:
                return Response({'error': 'PercantageSurgery not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'error': 'ID is required for deletion'}, status=status.HTTP_400_BAD_REQUEST)

# Surgery API Views
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated]) 
def surgery_view(request, pk=None):
    if request.method == 'GET':
        if pk:
            try:
                surgery = Surgery.objects.get(pk=pk, user=request.user)
                serializer = SurgerySerializer(surgery)
                return Response(serializer.data)
            except Surgery.DoesNotExist:
                return Response({'error': 'Surgery not found'}, status=status.HTTP_404_NOT_FOUND)
        
        surgeries = Surgery.objects.filter(user=request.user)
        
        complete_surgeries = []
        incomplete_surgeries = []
        
        def calculate_percentage(surgery):
            fields = [
                surgery.name_of_surgery,
                surgery.type_of_surgery,
                surgery.field_of_surgery,
                surgery.complications,
                surgery.histology,
                surgery.main_surgeon,
                surgery.date,
                surgery.histology_description,
                surgery.complications_description,
                surgery.notes1,
                surgery.notes2,
            ]
            filled_fields = sum(1 for field in fields if field not in [None, ""])
            total_fields = len(fields)
            return round((filled_fields / total_fields) * 100, 2)

        for surgery in surgeries:
            percentage_complete = calculate_percentage(surgery)
            surgery_data = SurgerySerializer(surgery).data
            surgery_data["percentage_complete"] = percentage_complete
            
            
            if percentage_complete == 100:  # Fully complete
                complete_surgeries.append(surgery_data)
            else:  # Incomplete
                incomplete_surgeries.append(surgery_data)
        suergies = SurgerySerializer(surgeries, many=True)
        
        return Response({
            'complete_surgeries': complete_surgeries,
            'incomplete_surgeries': incomplete_surgeries,
            'surgeries': suergies.data
        }, status=status.HTTP_200_OK)
        
    if request.method == 'POST':
        serializer = SurgerySerializer(data=request.data,partial=True)
        print("serializer",serializer)
        if serializer.is_valid():
            surgery = serializer.save(user=request.user)
            if surgery.histology or surgery.complications:
                schedule_notification_db(surgery)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print(serializer.errors)  # Log the errors for debugging
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'PUT':
        try:
            surgery = Surgery.objects.get(pk=pk, user=request.user)
            serializer = SurgerySerializer(surgery, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                if surgery.histology or surgery.complications:
                      schedule_notification_db(surgery)
                return Response(serializer.data , status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Surgery.DoesNotExist:
            return Response({'error': 'Surgery not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        try:
            surgery = Surgery.objects.get(pk=pk, user=request.user)
            surgery.delete()
            return Response({'message': 'Surgery deleted successfully'}, status=status.HTTP_200_OK)
        except Surgery.DoesNotExist:
            return Response({'error': 'Surgery not found'}, status=status.HTTP_404_NOT_FOUND)



def schedule_notification_db(surgery):
    notification_date = now() + timedelta(days=90)  # 3 months from now
    Notification.objects.create(
        user=surgery.user,
        title="Surgery Follow-Up Reminder",
        message=f"Reminder to follow up on the surgery '{surgery.name_of_surgery or 'Unnamed Surgery'}' performed on {surgery.date.date()}. Check the histology and complications.",
        data={"surgery_id": surgery.id},
        visible_at=notification_date,
    )



    
    
# Scientific API Views
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def scientific_view(request, pk=None):
    if request.method == 'GET':
        if pk:
            try:
                scientific = Scientific.objects.get(pk=pk, user=request.user)
                serializer = ScientificSerializer(scientific)
                return Response(serializer.data)
            except Scientific.DoesNotExist:
                return Response({'error': 'Scientific work not found'}, status=status.HTTP_404_NOT_FOUND)
        scientifics = Scientific.objects.filter(user=request.user)
        serializer = ScientificSerializer(scientifics, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = ScientificSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'PUT':
        try:
            scientific = Scientific.objects.get(pk=pk, user=request.user)
            serializer = ScientificSerializer(scientific, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Scientific.DoesNotExist:
            return Response({'error': 'Scientific work not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        try:
            scientific = Scientific.objects.get(pk=pk, user=request.user)
            scientific.delete()
            return Response({'message': 'Scientific work deleted successfully'}, status=status.HTTP_200_OK)
        except Scientific.DoesNotExist:
            return Response({'error': 'Scientific work not found'}, status=status.HTTP_404_NOT_FOUND)

# Course API Views
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def course_view(request, pk=None):
    if request.method == 'GET':
        if pk:
            try:
                course = Course.objects.get(pk=pk, user=request.user)
                serializer = CourseSerializer(course)
                return Response(serializer.data)
            except Course.DoesNotExist:
                return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
        courses = Course.objects.filter(user=request.user)
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = CourseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'PUT':
        try:
            course = Course.objects.get(pk=pk, user=request.user)
            serializer = CourseSerializer(course, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Course.DoesNotExist:
            return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        try:
            course = Course.objects.get(pk=pk, user=request.user)
            course.delete()
            return Response({'message': 'Course deleted successfully'}, status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)

# Budget API Views
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def budget_view(request, pk=None):
    if request.method == 'GET':
        if pk:
            try:
                budget = Budget.objects.get(pk=pk, user=request.user)
                serializer = BudgetSerializer(budget)
                return Response(serializer.data)
            except Budget.DoesNotExist:
                return Response({'error': 'Budget not found'}, status=status.HTTP_404_NOT_FOUND)
        budgets = Budget.objects.filter(user=request.user)
        serializer = BudgetSerializer(budgets, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = BudgetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'PUT':
        try:
            budget = Budget.objects.get(pk=pk, user=request.user)
            serializer = BudgetSerializer(budget, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Budget.DoesNotExist:
            return Response({'error': 'Budget not found'}, status=status.HTTP_404_NOT_FOUND)  

    if request.method == 'DELETE':
        try:
            budget = Budget.objects.get(pk=pk, user=request.user)
            budget.delete()
            return Response({'message': 'Budget deleted successfully'}, status=status.HTTP_200_OK)
        except Budget.DoesNotExist:
            return Response({'error': 'Budget not found'}, status=status.HTTP_404_NOT_FOUND)
        
        
        
        
        
#excell


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated]) 
def export_surgery_to_excel(request):
    # Create a new workbook and activate a worksheet
    wb = Workbook()
    ws = wb.active
    ws.title = "Surgery Data"

    # Define the column headers
    headers = ['ID', 'User', 'Name of Surgery', 'Type of Surgery', 'Complications']
    ws.append(headers)

    # Get surgery data
    surgeries = Surgery.objects.filter(user=request.user)

    # Add surgery data to the Excel file
    for surgery in surgeries:
        ws.append([
            surgery.id,
            surgery.user.username if surgery.user else "N/A",  # User's username
            surgery.name_of_surgery,
            surgery.type_of_surgery,
            surgery.complications,
        ])

    # Create a response and set the content type to Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=surgery_data.xlsx'

    # Save the workbook to the response
    wb.save(response)
    
    return response

#pdf




class PDF(FPDF):
    def create_table(self, table_data, title='', data_size = 10, title_size=15, align_data='L', align_header='L', cell_width='even', x_start='x_default',emphasize_data=[], emphasize_style=None,emphasize_color=(0,0,0)): 
        """
        table_data: 
                    list of lists with first element being list of headers
        title: 
                    (Optional) title of table (optional)
        data_size: 
                    the font size of table data
        title_size: 
                    the font size fo the title of the table
        align_data: 
                    align table data
                    L = left align
                    C = center align
                    R = right align
        align_header: 
                    align table data
                    L = left align
                    C = center align
                    R = right align
        cell_width: 
                    even: evenly distribute cell/column width
                    uneven: base cell size on lenght of cell/column items
                    int: int value for width of each cell/column
                    list of ints: list equal to number of columns with the widht of each cell / column
        x_start: 
                    where the left edge of table should start
        emphasize_data:  
                    which data elements are to be emphasized - pass as list 
                    emphasize_style: the font style you want emphaized data to take
                    emphasize_color: emphasize color (if other than black) 
        
        """
        default_style = self.font_style
        if emphasize_style == None:
            emphasize_style = default_style
        # default_font = self.font_family
        # default_size = self.font_size_pt
        # default_style = self.font_style
        # default_color = self.color # This does not work

        # Get Width of Columns
        def get_col_widths():
            col_width = cell_width
            if col_width == 'even':
                col_width = self.epw / len(data[0]) - 1  # distribute content evenly   # epw = effective page width (width of page not including margins)
            elif col_width == 'uneven':
                col_widths = []

                # searching through columns for largest sized cell (not rows but cols)
                for col in range(len(table_data[0])): # for every row
                    longest = 0 
                    for row in range(len(table_data)):
                        cell_value = str(table_data[row][col])
                        value_length = self.get_string_width(cell_value)
                        if value_length > longest:
                            longest = value_length
                    col_widths.append(longest + 4) # add 4 for padding
                col_width = col_widths



                        ### compare columns 

            elif isinstance(cell_width, list):
                col_width = cell_width  # TODO: convert all items in list to int        
            else:
                # TODO: Add try catch
                col_width = int(col_width)
            return col_width

        # Convert dict to lol
        # Why? because i built it with lol first and added dict func after
        # Is there performance differences?
        if isinstance(table_data, dict):
            header = [key for key in table_data]
            data = []
            for key in table_data:
                value = table_data[key]
                data.append(value)
            # need to zip so data is in correct format (first, second, third --> not first, first, first)
            data = [list(a) for a in zip(*data)]

        else:
            header = table_data[0]
            data = table_data[1:]

        line_height = self.font_size * 2.5

        col_width = get_col_widths()
        self.set_font(size=title_size)

        # Get starting position of x
        # Determin width of table to get x starting point for centred table
        if x_start == 'C':
            table_width = 0
            if isinstance(col_width, list):
                for width in col_width:
                    table_width += width
            else: # need to multiply cell width by number of cells to get table width 
                table_width = col_width * len(table_data[0])
            # Get x start by subtracting table width from pdf width and divide by 2 (margins)
            margin_width = self.w - table_width
            # TODO: Check if table_width is larger than pdf width

            center_table = margin_width / 2 # only want width of left margin not both
            x_start = center_table
            self.set_x(x_start)
        elif isinstance(x_start, int):
            self.set_x(x_start)
        elif x_start == 'x_default':
            x_start = self.set_x(self.l_margin)


        # TABLE CREATION #

        # add title
        if title != '':
            self.multi_cell(0, line_height, title, border=0, align='c', ln=3, max_line_height=self.font_size)
            self.ln(line_height * 1.5) # move cursor back to the left margin

        self.set_font(size=data_size)
        # add header
        y1 = self.get_y()
        if x_start:
            x_left = x_start
        else:
            x_left = self.get_x()
        x_right = self.epw + x_left
        if  not isinstance(col_width, list):
            if x_start:
                self.set_x(x_start)
            for datum in header:
                self.multi_cell(col_width, line_height, datum, border=0, align=align_header, ln=3, max_line_height=self.font_size)
                x_right = self.get_x()
            self.ln(line_height) # move cursor back to the left margin
            y2 = self.get_y()
            self.line(x_left,y1,x_right,y1)
            self.line(x_left,y2,x_right,y2)

            for row in data:
                if x_start: # not sure if I need this
                    self.set_x(x_start)
                for datum in row:
                    if datum in emphasize_data:
                        self.set_text_color(*emphasize_color)
                        self.set_font(style=emphasize_style)
                        self.multi_cell(col_width, line_height, datum, border=0, align=align_data, ln=3, max_line_height=self.font_size)
                        self.set_text_color(0,0,0)
                        self.set_font(style=default_style)
                    else:
                        self.multi_cell(col_width, line_height, datum, border=0, align=align_data, ln=3, max_line_height=self.font_size) # ln = 3 - move cursor to right with same vertical offset # this uses an object named self
                self.ln(line_height) # move cursor back to the left margin
        
        else:
            if x_start:
                self.set_x(x_start)
            for i in range(len(header)):
                datum = header[i]
                self.multi_cell(col_width[i], line_height, datum, border=0, align=align_header, ln=3, max_line_height=self.font_size)
                x_right = self.get_x()
            self.ln(line_height) # move cursor back to the left margin
            y2 = self.get_y()
            self.line(x_left,y1,x_right,y1)
            self.line(x_left,y2,x_right,y2)


            for i in range(len(data)):
                if x_start:
                    self.set_x(x_start)
                row = data[i]
                for i in range(len(row)):
                    datum = row[i]
                    if not isinstance(datum, str):
                        datum = str(datum)
                    adjusted_col_width = col_width[i]
                    if datum in emphasize_data:
                        self.set_text_color(*emphasize_color)
                        self.set_font(style=emphasize_style)
                        self.multi_cell(adjusted_col_width, line_height, datum, border=0, align=align_data, ln=3, max_line_height=self.font_size)
                        self.set_text_color(0,0,0)
                        self.set_font(style=default_style)
                    else:
                        self.multi_cell(adjusted_col_width, line_height, datum, border=0, align=align_data, ln=3, max_line_height=self.font_size) # ln = 3 - move cursor to right with same vertical offset # this uses an object named self
                self.ln(line_height) # move cursor back to the left margin
        y3 = self.get_y()
        self.line(x_left,y3,x_right,y3)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated]) 
def export_surgery_to_pdf(request):
    # Create the PDF
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Times", size=10)

    # Define header and rows
    data = [
        ["ID", "User", "Name of Surgery", "Type of Surgery", "Complication fgdfg shgfghfghfg", "Complications"]
    ]

    # Fetch surgery data dynamically
    surgeries = Surgery.objects.filter(user=request.user)
    for surgery in surgeries:
        data.append([
            str(surgery.id),
            surgery.user.username if surgery.user else "N/A",
            surgery.name_of_surgery,
            surgery.type_of_surgery,
            surgery.complications,
            surgery.complications,
        ])
    print("data", data)

    # Create table
    pdf.create_table(table_data=data, title="Surgery Data Report", cell_width='even')

    # Save PDF locally
    pdf_file_path = "test_surgery_data.pdf"
    pdf.output(pdf_file_path)  # Save the PDF locally

    # Serve the PDF as a file response
    try:
        file = open(pdf_file_path, 'rb')  # Open file in binary read mode
        response = FileResponse(file, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="surgery_data.pdf"'
        return response
    except FileNotFoundError:
        return HttpResponse("The file was not found on the server.", status=404)

#google sheet

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from django.conf import settings
from .models import Surgery

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated]) 
def export_surgery_to_google_sheets(request):
    # Set up the credentials and authenticate with Google Sheets API
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(settings.GOOGLE_SHEET_CREDS_JSON, scope)
    client = gspread.authorize(creds)

    # Create or open a Google Sheet
    spreadsheet = client.create('Surgery Data')
    sheet = spreadsheet.get_worksheet(0)

    # Add the headers to the Google Sheet
    headers = ['ID', 'User', 'Name of Surgery', 'Type of Surgery', 'Complications']
    sheet.append_row(headers)
    
    surgeries = Surgery.objects.filter(user=request.user)

    # Add surgery data to the Google Sheet
    for surgery in surgeries:
        row = [
            surgery.id,
            surgery.user.username if surgery.user else "N/A",
            surgery.name_of_surgery,
            surgery.type_of_surgery,
            surgery.complications,
        ]
        sheet.append_row(row)

    # Provide a link to the created Google Sheet as a response
    google_sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}/edit"
    return Response({
        "message": "Data successfully exported to Google Sheets",
        "sheet_url": google_sheet_url
    }, status=status.HTTP_200_OK)

@api_view(["POST"])
def send_support_email(request):
    if request.method == "POST":
        try:
           
          
            message = request.data.get("message")
            user_email = request.data.get("email")  # Fetch logged-in user's email
            admin_email = "hijabpoint374@gmail.com"  # Replace with admin's email

            if not message:
                return Response({"error": "Message content is required."}, status=400)

            # Send email to the admin
            send_mail(
                subject=f"Support Request from {request.user.username}",
                message=f"User Email: {user_email}\n\nMessage: {message}",
                from_email=user_email,
                recipient_list=[admin_email],
                fail_silently=False,
            )

            return Response({"success": "Your message has been sent successfully."} , status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

    return JsonReResponsesponse({"error": "Invalid request method."}, status=405)

