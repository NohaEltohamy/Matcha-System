# job_board/urls.py

from rest_framework.routers import DefaultRouter
from .views import *
from django.urls import path
from rest_framework.routers import DefaultRouter
# Create a router for the ViewSet
router = DefaultRouter()
router.register(r'list', JobViewSet, basename='job')


urlpatterns = [
    path('jpost/', post_job, name='post-job'),
    path('generate-description-skills/', generate_job_description_skills, name='generate-description-skills'),
    path('my-jobs/', list_recruiter_jobs, name='list-recruiter-jobs'),  # Add this line
    path('matched-cvs/', list_matched_cvs, name='list-matched-cvs'),  # Add this line
    path('evaluate-cv/', evaluate_cv_by_genai, name='evaluate-cv-by-genai'),  # Add this line
    path('cv/<int:cv_id>/', show_cv_by_id, name='show-cv-by-id'),  # Add this line
   
    
  # Include router URLs
] + router.urls
