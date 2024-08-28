from . import views
from django.urls import path

urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.login, name='login'),
    path('register', views.register, name='register'),
    path('logout', views.logout, name='logout'),
    path('admin_report', views.admin_report, name='admin_report'),
    path('report_for_today', views.report_for_today, name='report_for_today'),
    path('report_for_the_month', views.report_for_the_month, name='report_for_the_month'),
    path('report_for_the_month_user', views.report_for_the_month_user, name='report_for_the_month_user'),
    path('report_for_given_time_frame_user', views.report_for_given_time_frame_user,
         name='report_for_given_time_frame_user'),
    path('report_for_given_time_frame', views.report_for_given_time_frame, name='report_for_given_time_frame'),

]




