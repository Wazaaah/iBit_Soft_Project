from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from django.utils import timezone
from django.utils.timezone import now
from django.contrib.auth.decorators import user_passes_test
from .models import AttendanceRecord


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

        print(f"user: {user}, type: {type(user)}")

        if user is not None:
            today = timezone.now().date()
            attendance, created = AttendanceRecord.objects.get_or_create(user=user, date=today)
            if created:  # Only set first_login if the record is newly created
                attendance.first_login = timezone.now()
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
    if request.user.is_authenticated:
        user = request.user
        today = now().date()
        attendance = AttendanceRecord.objects.filter(user=user, date=today).first()
        if attendance and attendance.first_login:
            attendance.last_logout = now()
            attendance.total_hours_worked = attendance.last_logout - attendance.first_login
            attendance.save()

    auth.logout(request)
    return redirect('/')


def is_admin(user):
    return user.is_superuser

@user_passes_test(is_admin)
def admin_report_view(request):
    # Your code for generating the report
    return render(request, 'admin_report.html')
