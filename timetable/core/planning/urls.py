from django.urls import path
from . import views

urlpatterns = [
    path('session/<int:session_id>/generate/', views.generate_timetable, name='generate_timetable'),
    path('session/<int:session_id>/view/', views.view_timetable, name='view_timetable'),
]