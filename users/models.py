from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
import uuid


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self, email, password=None, **extra_fields):
            extra_fields.setdefault("is_staff", True)
            extra_fields.setdefault("is_superuser", True)
            extra_fields.setdefault("is_active", True)

            if extra_fields.get("is_staff") is not True:
                raise ValueError("Superuser must have is_staff=True.")
            if extra_fields.get("is_superuser") is not True:
                raise ValueError("Superuser must have is_superuser=True.")

            return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('recruiter', 'Recruiter'),
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    is_verified = models.BooleanField(default=False)
    avatar = models.URLField(blank=True, null=True)  # Google Drive URL
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']
    
    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return self.email
    
    def is_recruiter(self):
        """Check if user is a recruiter"""
        return self.role == 'recruiter'
    
    def is_admin(self):
        """Check if user is an admin"""
        return self.role == 'admin'
    
    def is_moderator(self):
        """Check if user is a moderator"""
        return self.role == 'moderator'
    
    def can_manage_job_postings(self):
        """Check if user can manage job postings"""
        return self.role in ['recruiter', 'admin', 'moderator']
    
    def can_review_job_postings(self):
        """Check if user can review job postings"""
        return self.role in ['admin', 'moderator']

class EmailVerificationToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    
    def is_expired(self):
        return timezone.now() > self.expires_at


