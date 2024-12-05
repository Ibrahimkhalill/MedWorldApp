from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.authtoken.models import Token
from .serializers import UserProfileSerializer, SurgerySerializer  # Your serializers
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import UserProfile , Surgery , OTP
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import authentication_classes, permission_classes
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string 
from .otpGenarate import generate_otp
from django.utils import timezone
from django.http import HttpResponse, FileResponse
from openpyxl import Workbook
from .models import Surgery
from fpdf import FPDF

# User Registration
@api_view(["POST"])
def register(request):
    if request.method == "POST":
        email = request.data.get("email")  # Use email as the username
        password = request.data.get("password")
        
        if not email or not password:
            return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)
     
        if User.objects.filter(username=email).exists():
            return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.create_user(username=email, email=email, password=password)
        user.save()
        
        UserProfile.objects.create(user=user)
        
        return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)
       

@api_view(["POST"])
def send_otp(request):
    if request.method == 'POST':
        email = request.data.get('email')
        try:
            # Generate OTP
            otp = generate_otp()
            # Save OTP to database
            OTP.objects.create(email=email, otp=otp)
            
            # Render the HTML template
            html_content = render_to_string('otp_email_template.html', {'otp': otp, 'email':email})
            
            # Send email
            msg = EmailMultiAlternatives(
                subject='Your OTP Code',
                body='This is an OTP email.',
                from_email='hijabpoint374@gmail.com',  # Sender's email address
                to=[email],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)  
            
            return Response({'message': 'OTP sent to your email.'})
        except Exception as e:
            return Response({'error': str(e)}, status=500)
    return Response({'message': 'Invalid method.'})


@api_view(["POST"])
def verify_otp(request):
    if request.method == 'POST':
        otp = request.data.get('otp')

        try:
                otp_record = OTP.objects.get(otp=otp)
                otp_record.attempts += 1  
                otp_record.save()  
                if (timezone.now() - otp_record.created_at).seconds > 120:
                    otp_record.delete()  
                    return Response({'message': ' Otp Expired'})
                else:
                    otp_record.delete()  
                    return Response('email verified', status=status.HTTP_200_OK)
        except OTP.DoesNotExist:
                return Response({'message': 'Invalid Otp'}, status=status.HTTP_400_BAD_REQUEST)
           
    return Response("Method is not allowed")

# User Login and Token Generation
@api_view(["POST"])
def login(request):
   
    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password:
        return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(request, username=email, password=password)

    if not user:
        return Response({"error": "Email or Password is wrong!"}, status=status.HTTP_401_UNAUTHORIZED)
    
    if not user.is_active:
        return Response({"error": "Account is inactive"}, status=status.HTTP_401_UNAUTHORIZED)


    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    return Response({
        "access_token": access_token,
        "refresh_token": str(refresh),
    }, status=status.HTTP_200_OK)
    


@api_view(["POST"])
def Password_reset_send_otp(request):
   
    email = request.data.get('email')
    print(email)

    try:
        # Check if the user exists
        existing_user = User.objects.get(username=email)
        
        if existing_user:
            print("existing_user", existing_user)
            
            # Generate OTP
            otp = generate_otp()
            
            # Save OTP to the database (assuming OTP model has 'email' and 'otp' fields)
            OTP.objects.create(email=email, otp=otp)
            
            # Prepare the HTML content for the OTP email
            html_content = render_to_string('otp_email_template.html', {'otp': otp, 'email': email})
            
            # Prepare email message
            msg = EmailMultiAlternatives(
                subject='Your OTP Code',
                body='This is an OTP email.',
                from_email='hijabpoint374@gmail.com',  # Replace with a valid sender email
                to=[email],
            )
            
            msg.attach_alternative(html_content, "text/html")
            
            # Send email and ensure it is sent without errors
            msg.send(fail_silently=False)
            
            return Response({'message': 'OTP sent to your email.'}, status=status.HTTP_200_OK)
    
    except User.DoesNotExist:
        # Handle the case where the user does not exist
        return Response({'message': 'The account you provided does not exist. Please try again with another account.'}, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        # Log the exception for debugging purposes (optional)
        print(f"Error occurred: {e}")
        return Response({'message': 'An unexpected error occurred. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    

@api_view(['POST'])
def reset_password(request):
    
    email =  request.data.get('email')
    new_password = request.data.get('newpassword')
    
    try:
        
        user = User.objects.get(username=email)
        
        if user:
            user.set_password(new_password)
            user.save()
            return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)
        
    
    except User.DoesNotExist:
        return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    

#google_login
@api_view(["POST"])
def google_register(request):
    
    email = request.data.get("email")  
    
    if User.objects.filter(username=email).exists():
        return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)
    
    user = User.objects.create_user(username=email)
    user.save()
    
    UserProfile.objects.create(user=user)
    
    return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)




# User Login and Token Generation
@api_view(["POST"])
def google_login(request):
    if request.method == "POST":
        email = request.data.get("email")
      

        if not email:
            return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        user= User.objects.filter(username=email).first()

        if not user:
            return Response({"error": "Email or Password is wrong!"}, status=status.HTTP_401_UNAUTHORIZED)
    
    
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({
            "access_token": access_token,
            "refresh_token": str(refresh),
        }, status=status.HTTP_200_OK)



@api_view(['POST'])
def refresh_access_token(request):
    refresh_token = request.data.get('refresh_token')
    if not refresh_token:
        return Response({"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        refresh = RefreshToken(refresh_token)
        new_access_token = str(refresh.access_token)
        return Response({
            'access_token': new_access_token
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": "Invalid refresh token"}, status=status.HTTP_400_BAD_REQUEST)
     
#userprofile       
@api_view(['GET', 'PUT', 'PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def user_profile(request):
    profile = get_object_or_404(UserProfile,user=request.user)

    if request.method == 'GET':
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
       
        serializer = UserProfileSerializer(profile, data=request.data, partial=(request.method == 'PATCH'))

        if request.FILES.get('profile_picture'):
          
            profile.profile_picture = request.FILES['profile_picture']
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
    

#surgery 
@api_view(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def surgery(request, surgery_id=None):
   
    if surgery_id:
        surgery_instance = get_object_or_404(Surgery, id=surgery_id, user=request.user)

    if request.method == 'GET':
        if surgery_id: 
            serializer = SurgerySerializer(surgery_instance)
            return Response(serializer.data)
        else: 
            user_surgery_data = Surgery.objects.filter(user=request.user)
            if user_surgery_data:
                serializer = SurgerySerializer(user_surgery_data, many=True)
                return Response(serializer.data)
            else:
                return Response({"message": "No surgeries found for the user."}, status=status.HTTP_404_NOT_FOUND)

    elif request.method == 'POST':
     
        serializer = SurgerySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method in ['PUT', 'PATCH']:
        if surgery_id:  
            serializer = SurgerySerializer(surgery_instance, data=request.data, partial=(request.method == 'PATCH'))
            if serializer.is_valid():
                serializer.save()  
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        if surgery_id:  
            surgery_instance.delete()
            return Response({"message": "Surgery record deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        
        
        
        
        
#excell


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
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
@authentication_classes([JWTAuthentication])
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
@authentication_classes([JWTAuthentication])
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


