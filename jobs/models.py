# job_board/models.py

from django.db import models
from django.contrib.auth import get_user_model # Added this import
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone

User = get_user_model()

class Job(models.Model):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("closed", "Closed"),
        ("draft", "Draft"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    skills = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="draft"
    )
    opened_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    recruiter = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="job_posts"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Retrieve the original instance to check for status changes
        if self.pk:
            original_job = Job.objects.get(pk=self.pk)
        else:
            original_job = None

        # Handle opened_at timestamp
        if self.status == "open" and (original_job is None or original_job.status != "open"):
            self.opened_at = timezone.now()
        elif self.status != "open" and (original_job and original_job.status == "open"):
            # If status changes from open to something else, clear opened_at
            self.opened_at = None

        # Handle closed_at timestamp
        if self.status == "closed" and (original_job is None or original_job.status != "closed"):
            self.closed_at = timezone.now()
        elif self.status != "closed" and (original_job and original_job.status == "closed"):
            # If status changes from closed to something else, clear closed_at
            self.closed_at = None

        super().save(*args, **kwargs)


# Add these models after your existing Job model
class CV(models.Model):
    """Model to store candidate CVs"""
    candidate = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="cvs"
    )
    title = models.CharField(max_length=255)  # Job title the CV is for
    file_url = models.URLField()  # URL to the CV file (e.g., Google Drive, S3)
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField()  # File size in bytes
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-uploaded_at"]
    
    def __str__(self):
        return f"{self.candidate.name} - {self.title}"

class CandidateJobMatch(models.Model):
    """Model to store AI-generated scores for candidate-job matches"""
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name="job_matches")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="candidate_matches")
    genai_score = models.FloatField(default=0.0)  # AI-generated compatibility score (0-100)
    skills_match_score = models.FloatField(default=0.0)  # Skills compatibility score
    experience_match_score = models.FloatField(default=0.0)  # Experience compatibility score
    overall_fit_score = models.FloatField(default=0.0)  # Overall fit score
    ai_analysis = models.TextField(blank=True, null=True)  # Detailed AI analysis
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['cv', 'job']  # One score per CV-Job combination
        ordering = ["-genai_score"]
    
    def __str__(self):
        return f"{self.cv.candidate.name} - {self.job.title} ({self.genai_score}%)"

# Add this at the end of your models.py file

class Interview(models.Model):
    """Model to store scheduled interviews"""
    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("no_show", "No Show"),
    ]
    
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name="interviews")
    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="scheduled_interviews")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="interviews")
    cv = models.ForeignKey(CV, on_delete=models.SET_NULL, null=True, blank=True, related_name="interviews")
    scheduled_at = models.DateTimeField()
    duration_minutes = models.IntegerField(default=30)
    interview_type = models.CharField(max_length=50, default="technical")
    meeting_link = models.URLField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    ai_prompt = models.TextField(blank=True, null=True)  # AI-generated interview questions
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-scheduled_at"]
    
    def __str__(self):
        return f"Interview: {self.candidate.name} - {self.job.title} ({self.scheduled_at})"