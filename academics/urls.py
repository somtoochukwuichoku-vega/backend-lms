from . import views
from django.urls import path

urlpatterns = [
    # path('courses/', views.CourseListView.as_view()),
    path('courses/', views.CourseListWithEnrollmentView.as_view()),
    path('courses/<uuid:pk>/', views.CourseDetailView.as_view()),

    path('organizations/<uuid:org_id>/courses/create/', views.CourseCreateView.as_view(), name='course-create'),
    
    path('categories/', views.CategoryListCreateView.as_view(), name='category-list'),
    path('levels/', views.LevelListCreateView.as_view(), name='level-list'),

    path('enrollments/', views.EnrollmentListView.as_view()),
    path('enrollments/current/', views.current_enrollments),

    path('assignments/', views.AssignmentListCreateView.as_view(), name='assignment-list'),
    path('assignments/<uuid:pk>/', views.AssignmentDetailView.as_view(), name='assignment-detail'),
    path('assignments/upcoming/', views.upcoming_assignments, name='upcoming-assignments'),

    #MOdules
    path('org/<uuid:org_id>/courses/<uuid:course_id>/modules/', views.ModuleListCreateView.as_view(), name='module-list-create'),
    path('org/<uuid:org_id>/modules/<uuid:pk>/', views.ModuleDetailView.as_view(), name='module-detail'),

    # lessons
    path('org/<uuid:org_id>/modules/<uuid:module_id>/lessons/', views.LessonListCreateView.as_view(), name='lesson-list-create'),
    path('org/<uuid:org_id>/lessons/<uuid:pk>/', views.LessonDetailView.as_view(), name='lesson-detail'),

    path('lessons/<uuid:lesson_id>/generate-summary/', views.GenerateLessonSummaryView.as_view(), name='generate-summary'),
]
