from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, auth
from django.utils import timezone
from django.utils.timezone import now
from .forms import TimeframeForm, UserTimeframeForm, UserMonthlyForm
from .models import AttendanceRecord
from django.db.models import Sum
from datetime import timedelta
from datetime import datetime, time as dt_time
import requests


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
        user = auth.authenticate(username=username, password=password)

        if user is not None:
            today = datetime.now().date()
            attendance, created = AttendanceRecord.objects.get_or_create(user=user, date=today)
            if created:
                attendance.first_login = datetime.now().time()  # Store only the time part

                # Check if the first login is after 8:00 AM
                late_threshold = dt_time(8, 0, 0)  # 8:00 AM
                attendance.is_late = attendance.first_login > late_threshold

                attendance.save()

            auth.login(request, user)
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

    # If the user is a superuser, log them out immediately
    if user.is_superuser:
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
            'total_hours_formatted': total_hours,
            'is_late': record.is_late
            # Include other fields you want to display
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
                    daily_records.append({
                        'date': current_date,
                        'total_hours': record.total_hours_worked,
                        'first_login': record.first_login,
                        'is_late': record.is_late
                    })
                current_date += timedelta(days=1)

            # Format the dates for the template
            start_date_formatted = start_date.strftime('%B %d, %Y')
            end_date_formatted = end_date.strftime('%B %d, %Y')

            user_hours = {
                'user_id': user.id,
                'full_name': f"{user.first_name} {user.last_name}"
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
    start_date_formatted = end_date_formatted = None

    if request.method == 'POST':
        form = UserTimeframeForm(request.POST)
        if form.is_valid():
            user_id = form.cleaned_data['user_id']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            # Fetch the user by ID
            user = get_object_or_404(User, id=user_id)

            # Get attendance records and calculate total hours
            attendance_records = AttendanceRecord.objects.filter(user=user, date__range=[start_date, end_date])
            total_hours = attendance_records.aggregate(Sum('total_hours_worked'))[
                              'total_hours_worked__sum'] or timedelta()

            # Format total_hours to HH:MM:SS
            total_hours_formatted = str(total_hours)[:-7] if total_hours.days == 0 else str(total_hours)

            # Format the dates for the template
            start_date_formatted = start_date.strftime('%B %d, %Y')
            end_date_formatted = end_date.strftime('%B %d, %Y')

            user_hours = {
                'user_id': user_id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'total_hours': total_hours_formatted
            }

    else:
        form = UserTimeframeForm()

    context = {
        'form': form,
        'user_hours': user_hours,
        'start_date': start_date_formatted,
        'end_date': end_date_formatted
    }

    return render(request, 'report_for_given_time_frame_user.html', context)


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
                    'total_hours': total_hours_formatted
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
                "max_tokens": 300  # Adjust as needed
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
