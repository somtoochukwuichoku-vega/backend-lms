from . import views
from django.urls import path

urlpatterns = [
    # path('courses/', views.CourseListView.as_view()),
    path('courses/', views.courses_with_enrollment_status),
    path('categories/', views.CategoryListCreateView.as_view(), name='category-list'),
    path('levels/', views.LevelListCreateView.as_view(), name='level-list'),
    path('courses/<uuid:pk>/', views.CourseDetailView.as_view()),
    path('enrollments/', views.EnrollmentListView.as_view()),
    path('enrollments/current/', views.current_enrollments),
]
