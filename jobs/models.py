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
