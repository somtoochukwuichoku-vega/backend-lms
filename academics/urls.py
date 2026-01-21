from . import views
from django.urls import path


urlpatterns = [
    path('courses/', views.CourseListView.as_view()),
    path('courses/<int:pk>/', views.CourseDetailView.as_view()),
    
    # # Gerades
    # path('grades/', views.GradeListView),
    # path('grades/<int:pk>/', views.GradeDetailView.as_view()),

    # path('grades/<int:pk>/', views.GradeDetailView.as_view()),


]
