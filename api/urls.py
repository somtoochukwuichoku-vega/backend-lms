from . import views
from django.urls import path

urlpatterns = [
    path('students/', views.studentsView),
    path('students/<int:pk>/', views.studentDatailView),
    path('dashboard/stats/', views.dashboard_stats),
]
