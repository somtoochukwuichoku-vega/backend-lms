from . import views
from django.urls import path

urlpatterns = [
    path('courses/', views.courses_with_enrollment_status),
    path('courses/<uuid:pk>/', views.CourseDetailView.as_view()),
    path('enrollments/', views.EnrollmentListView.as_view()),
    path('enrollments/current/', views.current_enrollments),
]
