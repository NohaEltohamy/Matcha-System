# job_board/serializers.py

from rest_framework import serializers
from .models import Job
from .models import Job, CV, CandidateJobMatch

class JobSerializer(serializers.ModelSerializer):
    recruiter_username = serializers.CharField(source='recruiter.username', read_only=True)

    class Meta:
        model = Job
        fields = [
            "id",
            "title",
            "description",
            "skills",
            "status",
            "opened_at",
            "closed_at",
            "recruiter",
            "recruiter_username",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "recruiter",
            "opened_at",
            "closed_at",
            "created_at",
            "updated_at",
        ]





class CVSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.name', read_only=True)
    candidate_email = serializers.CharField(source='candidate.email', read_only=True)
    
    class Meta:
        model = CV
        fields = [
            "id",
            "candidate",
            "candidate_name", 
            "candidate_email",
            "title",
            "file_url",
            "file_name",
            "file_size",
            "uploaded_at",
            "updated_at",
        ]
        read_only_fields = [
            "candidate",
            "uploaded_at",
            "updated_at",
        ]

class CandidateJobMatchSerializer(serializers.ModelSerializer):
    cv_data = CVSerializer(source='cv', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)
    job_id = serializers.IntegerField(source='job.id', read_only=True)
    
    class Meta:
        model = CandidateJobMatch
        fields = [
            "id",
            "cv",
            "cv_data",
            "job",
            "job_id",
            "job_title",
            "genai_score",
            "skills_match_score",
            "experience_match_score",
            "overall_fit_score",
            "ai_analysis",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
        ]