# job_board/serializers.py

from rest_framework import serializers
from .models import Job

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
