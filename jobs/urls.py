# job_board/urls.py

from rest_framework.routers import DefaultRouter
from .views import *
from django.urls import path


urlpatterns = [
    path('jpost/', post_job, name='post-job'),
    path('generate-description-skills/', generate_job_description_skills, name='generate-description-skills'),
]
