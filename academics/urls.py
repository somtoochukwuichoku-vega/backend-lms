from . import views
from django.urls import path

urlpatterns = [
    #UTILS
    path('categories/', views.CategoryListCreateView.as_view(), name='category-list'),
    path('levels/', views.LevelListCreateView.as_view(), name='level-list'),

    #ORGS-COURSES
    path('org/<uuid:org_id>/courses/', views.CourseListCreateView.as_view(), name='course-list-create'),
    path('org/<uuid:org_id>/courses/<uuid:pk>/', views.CourseDetailView.as_view(), name='course-detail'),

    # Modules — nested under org + course
    path('org/<uuid:org_id>/courses/<uuid:course_id>/modules/', views.ModuleListCreateView.as_view(), name='module-list-create'),
    path('org/<uuid:org_id>/modules/<uuid:pk>/', views.ModuleDetailView.as_view(), name='module-detail'),

    # Lessons — nested under org + module
    path('org/<uuid:org_id>/modules/<uuid:module_id>/lessons/', views.LessonListCreateView.as_view(), name='lesson-list-create'),
    path('org/<uuid:org_id>/lessons/<uuid:pk>/', views.LessonDetailView.as_view(), name='lesson-detail'),

    # AI summary — nested under org
    path('org/<uuid:org_id>/lessons/<uuid:lesson_id>/generate-summary/', views.GenerateLessonSummaryView.as_view(), name='generate-summary'),

    # Enrollments (authenticated user, any org)
    path('enrollments/', views.EnrollmentListView.as_view(), name='enrollment-list'),
    path('enrollments/current/', views.current_enrollments, name='current-enrollments'),

    # Cross-org enrollment view with enrollment status attached for students
    path('courses/', views.CourseListWithEnrollmentView.as_view(), name='course-list-with-enrollment'),

    # Assignments
    path('assignments/', views.AssignmentListCreateView.as_view(), name='assignment-list'),
    path('assignments/upcoming/', views.upcoming_assignments, name='upcoming-assignments'),
    path('assignments/<uuid:pk>/', views.AssignmentDetailView.as_view(), name='assignment-detail'),


]
