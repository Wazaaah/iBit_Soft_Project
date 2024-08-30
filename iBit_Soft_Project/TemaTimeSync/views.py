from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, auth
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import now
from .forms import TimeframeForm, UserTimeframeForm, UserMonthlyForm
from .models import AttendanceRecord, UserOffDay
from django.db.models import Sum
from datetime import timedelta
from datetime import datetime, time as dt_time
from datetime import time
import requests
import pandas as pd
from django.http import HttpResponse
from django.contrib.auth import authenticate, login as auth_login


# Create your views here.
def register(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        username = request.POST['username']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            if User.objects.filter(username=username).exists():
                messages.info(request, 'Username Already Taken')
                return redirect('register')
            elif User.objects.filter(email=email).exists():
                messages.info(request, "Email Taken")
                return redirect('register')
            else:
                user = User.objects.create_user(username=username, email=email, password=password1,
                                                first_name=first_name, last_name=last_name)
                user.save()
                messages.info(request, "User Created")
                return redirect('login')
        else:
            messages.info(request, "Passwords Do Not Match")
            return redirect('register')

    else:
        return render(request, 'register.html')


def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            today = datetime.now().date()
            day_name = today.strftime('%A')  # Get the current day of the week

            # Check if today is the user's off day
            if UserOffDay.objects.filter(user=user, off_day=day_name).exists():
                messages.info(request, "You cannot log in on your off day.")
                return redirect('login')

            attendance, created = AttendanceRecord.objects.get_or_create(user=user, date=today)
            if created:
                attendance.first_login = datetime.now().time()  # Store only the time part

                # Check if the first login is after 8:00 AM
                late_threshold = dt_time(8, 0, 0)  # 8:00 AM
                attendance.is_late = attendance.first_login > late_threshold

                attendance.save()

            auth_login(request, user)
            return redirect('/')
        else:
            messages.info(request, "Invalid Credentials")
            return redirect('login')
    else:
        return render(request, 'login.html')


def index(request):
    return render(request, 'index.html')


def logout(request):
    user = request.user

    if user.is_superuser:

        today = now().date()
        attendance = AttendanceRecord.objects.filter(user=user, date=today).first()
        if attendance and attendance.first_login:
            current_time = now().time()
            attendance.last_logout = current_time

            # Calculate total hours worked
            first_login_datetime = datetime.combine(today, attendance.first_login)
            last_logout_datetime = datetime.combine(today, current_time)
            total_hours_worked = last_logout_datetime - first_login_datetime
            attendance.total_hours_worked = total_hours_worked

            # Check if user logged out after 4:00 PM
            end_of_workday = time(16, 0)  # 5:00 PM
            if current_time > end_of_workday:
                overtime_duration = last_logout_datetime - datetime.combine(today, end_of_workday)
                attendance.overtime = True
                attendance.overtime_hours = overtime_duration
            else:
                attendance.overtime = False
                attendance.overtime_hours = timedelta(0)

            attendance.save()

        auth.logout(request)
        return redirect('/')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(username=username, password=password)

        if user is not None and user.is_authenticated:
            today = now().date()
            attendance = AttendanceRecord.objects.filter(user=user, date=today).first()
            if attendance and attendance.first_login:
                current_time = now().time()
                attendance.last_logout = current_time

                # Calculate total hours worked
                first_login_datetime = datetime.combine(today, attendance.first_login)
                last_logout_datetime = datetime.combine(today, current_time)
                total_hours_worked = last_logout_datetime - first_login_datetime
                attendance.total_hours_worked = total_hours_worked

                # Check if user logged out after 5:00 PM
                end_of_workday = time(17, 0)  # 5:00 PM
                if current_time > end_of_workday:
                    overtime_duration = last_logout_datetime - datetime.combine(today, end_of_workday)
                    attendance.overtime = True
                    attendance.overtime_hours = overtime_duration
                else:
                    attendance.overtime = False
                    attendance.overtime_hours = timedelta(0)

                attendance.save()

            auth.logout(request)
            return redirect('/')
        else:
            messages.error(request, "Invalid Credentials or you are not logged in.")
            return redirect('login')
    else:
        return render(request, 'logout.html')


def is_admin(user):
    return user.is_superuser


def admin_report(request):
    # Get today's date
    today = timezone.now().date()

    # Fetch attendance records for today
    records = AttendanceRecord.objects.filter(date=today)

    context = {
        'records': records
    }

    return render(request, 'admin_report.html', context)


def report_for_today(request):
    # Get today's date
    today = timezone.now().date()

    # Fetch attendance records for today
    records = AttendanceRecord.objects.filter(date=today)

    # Create a list to hold formatted records
    formatted_records = []

    for record in records:
        total_hours = record.total_hours_worked
        # Format total_hours to HH:MM:SS
        # total_hours_formatted = str(total_hours)[:-7] if total_hours.days == 0 else str(total_hours)

        # Add the record with formatted total hours to the list
        formatted_records.append({
            'user': record.user,
            'date': record.date,
            'first_login': record.first_login,
            'total_hours_formatted': total_hours,
            'is_late': record.is_late,
            'expected_hours': record.expected_hours,
            'overtime': record.overtime,
            'overtime_hours': record.overtime_hours
        })

    context = {
        'records': formatted_records
    }

    return render(request, 'report_for_today.html', context)


def report_for_the_month(request):
    end_date = timezone.now().date()
    start_date = end_date.replace(day=1)

    # Fetch all users
    users = User.objects.all()

    # Prepare a dictionary to hold user_id, full name, and total hours
    user_hours = {}

    for user in users:
        attendance_records = AttendanceRecord.objects.filter(user=user, date__range=[start_date, end_date])
        total_hours = attendance_records.aggregate(Sum('total_hours_worked'))['total_hours_worked__sum'] or timedelta()

        # Format total_hours to HH:MM:SS
        total_hours_formatted = str(total_hours)[:-7] if total_hours.days == 0 else str(total_hours)

        # Store user details including user_id, full name, and total hours
        user_hours[user.id] = {
            'full_name': f"{user.first_name} {user.last_name}",
            'total_hours': total_hours_formatted
        }

    # Format the dates for the template
    start_date_formatted = start_date.strftime('%B %Y')
    end_date_formatted = end_date.strftime('%B %Y')

    context = {
        'user_hours': user_hours,
        'start_date': start_date_formatted,
        'end_date': end_date_formatted
    }

    return render(request, 'report_for_the_month.html', context)


def report_for_the_month_user(request):
    user_hours = None
    start_date_formatted = end_date_formatted = None
    daily_records = []
    total_hours_for_month = timedelta()

    if request.method == 'POST':
        form = UserMonthlyForm(request.POST)
        if form.is_valid():
            user_id = form.cleaned_data['user_id']
            end_date = timezone.now().date()
            start_date = end_date.replace(day=1)

            user = get_object_or_404(User, id=user_id)

            # Get attendance records for each day in the month
            current_date = start_date
            while current_date <= end_date:
                record = AttendanceRecord.objects.filter(user=user, date=current_date).first()

                if record:
                    total_hours_worked = record.total_hours_worked or timedelta()  # Default to timedelta() if None
                    total_hours_for_month += total_hours_worked  # Sum the total hours worked

                    daily_records.append({
                        'date': current_date,
                        'total_hours': total_hours_worked,
                        'first_login': record.first_login,
                        'is_late': record.is_late,
                        'expected_hours': record.expected_hours,
                        'overtime': record.overtime,
                        'overtime_hours': record.overtime_hours
                    })
                current_date += timedelta(days=1)

            # Format the dates for the template
            start_date_formatted = start_date.strftime('%B %d, %Y')
            end_date_formatted = end_date.strftime('%B %d, %Y')

            user_hours = {
                'user_id': user.id,
                'full_name': f"{user.first_name} {user.last_name}",
                'total_hours_for_month': str(total_hours_for_month)[:-7]  # Format total_hours to HH:MM:SS
            }

    else:
        form = UserMonthlyForm()

    context = {
        'form': form,
        'user_hours': user_hours,
        'start_date': start_date_formatted,
        'end_date': end_date_formatted,
        'daily_records': daily_records
    }

    return render(request, 'report_for_the_month_user.html', context)


def report_for_given_time_frame_user(request):
    user_hours = None
    daily_records = []

    # Retrieve the query parameters
    user_id = request.GET.get('user_id')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Ensure all parameters are present
    if user_id and start_date and end_date:
        user = get_object_or_404(User, id=user_id)

        start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()

        # Get attendance records and calculate total hours
        attendance_records = AttendanceRecord.objects.filter(user=user, date__range=[start_date, end_date])

        total_hours = timedelta()
        for record in attendance_records:
            daily_records.append({
                'date': record.date,
                'first_login': record.first_login,
                'is_late': record.is_late,
                'last_logout': record.last_logout,
                'total_hours_worked': record.total_hours_worked,
                'expected_hours': record.expected_hours,
                'overtime': record.overtime,
                'overtime_hours': record.overtime_hours
            })
            total_hours += record.total_hours_worked or timedelta()

        total_hours_formatted = str(total_hours)[:-7] if total_hours.days == 0 else str(total_hours)

        user_hours = {
            'user_id': user_id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'total_hours': total_hours_formatted
        }

        start_date_formatted = start_date.strftime('%B %d, %Y')
        end_date_formatted = end_date.strftime('%B %d, %Y')

        context = {
            'user_hours': user_hours,
            'daily_records': daily_records,
            'start_date': start_date_formatted,
            'end_date': end_date_formatted
        }
        return render(request, 'report_for_given_time_frame_user.html', context)
    else:
        # If required parameters are missing, redirect or show an error
        return redirect('report_for_given_time_frame')


def report_for_given_time_frame(request):
    user_hours = {}
    start_date_formatted = end_date_formatted = None

    if request.method == 'POST':
        form = TimeframeForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            # Fetch all users
            users = User.objects.all()

            # Prepare a dictionary to hold user_id, full name, and total hours
            for user in users:
                attendance_records = AttendanceRecord.objects.filter(user=user, date__range=[start_date, end_date])
                total_hours = attendance_records.aggregate(Sum('total_hours_worked'))[
                    'total_hours_worked__sum'] or timedelta()

                # Format total_hours to HH:MM:SS
                total_hours_formatted = str(total_hours)[:-7] if total_hours.days == 0 else str(total_hours)

                # Store user details including user_id, full name, and total hours
                user_hours[user.id] = {
                    'full_name': f"{user.first_name} {user.last_name}",
                    'total_hours': total_hours_formatted,
                    'detail_link': reverse('report_for_given_time_frame_user') + f"?user_id={user.id}&start_date={start_date}&end_date={end_date}"
                }

            # Format the dates for the template
            start_date_formatted = start_date.strftime('%B %d, %Y')
            end_date_formatted = end_date.strftime('%B %d, %Y')

    else:
        form = TimeframeForm()

    context = {
        'form': form,
        'user_hours': user_hours,
        'start_date': start_date_formatted,
        'end_date': end_date_formatted
    }

    return render(request, 'report_for_given_time_frame.html', context)


def predict_lateness_for_the_rest_of_the_month(request):
    prediction = None
    if request.method == 'POST':
        form = UserMonthlyForm(request.POST)
        if form.is_valid():
            user_id = form.cleaned_data['user_id']
            end_date = timezone.now().date()
            start_date = end_date.replace(day=1)
            user = get_object_or_404(User, id=user_id)

            # Fetch attendance records for the month so far
            records = AttendanceRecord.objects.filter(user=user, date__range=[start_date, end_date])

            # Prepare data for the model
            attendance_data = ""
            for record in records:
                attendance_data += (
                    f"Date: {record.date}, "
                    f"First Login: {record.first_login}, "
                    f"Total Hours: {record.total_hours_worked}, "
                    f"Was Late: {record.is_late}\n"
                )

            # Generate the prompt for the API
            prompt = (
                f"I am the manager of this company 'iBit Soft Ltd'."
                f"The following data represents the attendance of the user {user.get_full_name()} "
                f"for the month:\n\n"
                f"{attendance_data}\n\n"
                "Based on this data, predict the likelihood of the user being late for the rest of the month. "
                f"Ensure that the maximum words you give is 300. Therefore, be as specific as possible"
            )

            # API call to Cohere (or any other model you want to use)
            cohere_api_key = "omFu9KFgafnalHdiwZX7qxiAOaiK7sX8HQo5XzCA"  # Secure your API key
            cohere_api_url = "https://api.cohere.ai/v1/generate"
            headers = {
                "Authorization": f"Bearer {cohere_api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "command-xlarge",
                "prompt": prompt,
                "max_tokens": 500  # Adjust as needed
            }

            response = requests.post(cohere_api_url, json=payload, headers=headers)
            if response.status_code == 200:
                prediction = response.json().get('generations')[0].get('text')
            else:
                prediction = "Error in generating prediction. Please try again later."

    else:
        form = UserMonthlyForm()

    return render(request, 'predict_lateness_for_the_rest_of_the_month.html', {
        'form': form,
        'prediction': prediction,
    })


def generate_payroll(request):
    end_date = timezone.now().date()
    start_date = end_date.replace(day=1)

    # Fetch all users
    users = User.objects.all()

    # Prepare a dictionary to hold payroll data
    payroll_data = {}

    # Define hourly rates
    normal_hourly_rate = 20.0
    overtime_hourly_rate = 5.0

    for user in users:
        attendance_records = AttendanceRecord.objects.filter(user=user, date__range=[start_date, end_date])
        total_hours = attendance_records.aggregate(Sum('total_hours_worked'))['total_hours_worked__sum'] or timedelta()

        # Calculate total overtime hours
        total_overtime_hours = attendance_records.filter(overtime=True).aggregate(Sum('overtime_hours'))['overtime_hours__sum'] or timedelta()

        # Convert total hours worked and overtime hours to float representing hours
        total_hours_float = total_hours.total_seconds() / 3600
        total_overtime_hours_float = total_overtime_hours.total_seconds() / 3600

        # Calculate normal hours
        normal_hours_float = total_hours_float - total_overtime_hours_float

        # Calculate salary based on hourly rates
        normal_salary = normal_hours_float * normal_hourly_rate
        overtime_salary = total_overtime_hours_float * overtime_hourly_rate
        total_salary = normal_salary + overtime_salary

        # Round hours and salary to two decimal places
        normal_hours_rounded = round(normal_hours_float, 2)
        total_overtime_hours_rounded = round(total_overtime_hours_float, 2)
        total_salary_rounded = round(total_salary, 2)

        # Add the user's payroll info to the dictionary
        payroll_data[user.id] = {
            'full_name': f"{user.first_name} {user.last_name}",
            'normal_hours': normal_hours_rounded,
            'overtime_hours': total_overtime_hours_rounded,
            'total_hours': round(total_hours_float, 2),
            'normal_hourly_rate': normal_hourly_rate,
            'overtime_hourly_rate': overtime_hourly_rate,
            'salary': total_salary_rounded,
        }

    context = {'payroll_data': payroll_data}
    return render(request, 'payroll.html', context)


def export_to_excel(request):
    end_date = timezone.now().date()
    start_date = end_date.replace(day=1)

    # Fetch all users
    users = User.objects.all()

    # Prepare a list to hold payroll data
    payroll_data = []

    # Define hourly rates
    normal_hourly_rate = 20.0
    overtime_hourly_rate = 5.0

    for user in users:
        attendance_records = AttendanceRecord.objects.filter(user=user, date__range=[start_date, end_date])
        total_hours = attendance_records.aggregate(Sum('total_hours_worked'))['total_hours_worked__sum'] or timedelta()

        # Calculate total overtime hours
        total_overtime_hours = attendance_records.filter(overtime=True).aggregate(Sum('overtime_hours'))['overtime_hours__sum'] or timedelta()

        # Convert total hours worked and overtime hours to float representing hours
        total_hours_float = total_hours.total_seconds() / 3600
        total_overtime_hours_float = total_overtime_hours.total_seconds() / 3600

        # Calculate normal hours
        normal_hours_float = total_hours_float - total_overtime_hours_float

        # Calculate salary based on hourly rates
        normal_salary = normal_hours_float * normal_hourly_rate
        overtime_salary = total_overtime_hours_float * overtime_hourly_rate
        total_salary = normal_salary + overtime_salary

        # Round hours and salary to two decimal places
        normal_hours_rounded = round(normal_hours_float, 2)
        total_overtime_hours_rounded = round(total_overtime_hours_float, 2)
        total_salary_rounded = round(total_salary, 2)

        # Add the user's payroll info to the list
        payroll_data.append({
            'UserID': user.id,
            'Full Name': f"{user.first_name} {user.last_name}",
            'Normal Hours Worked': normal_hours_rounded,
            'Overtime Hours Worked': total_overtime_hours_rounded,
            'Normal Hourly Rate': normal_hourly_rate,
            'Overtime Hourly Rate': overtime_hourly_rate,
            'Salary': total_salary_rounded
        })

    # Create a DataFrame from the payroll data
    payroll_df = pd.DataFrame(payroll_data)

    # Export the DataFrame to an Excel file
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=payroll.xlsx'
    payroll_df.to_excel(response, index=False)

    return response
