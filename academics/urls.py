from . import views
from django.urls import path

urlpatterns = [
    path('courses/', views.CourseListView.as_view()),
    path('courses/<uuid:pk>/', views.CourseDetailView.as_view()),
    path('enrollments/', views.EnrollmentListView.as_view()),
    path('enrollments/current/', views.current_enrollments),
]
