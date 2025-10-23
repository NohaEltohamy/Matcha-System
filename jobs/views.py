# job_board/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Job
from .serializers import JobSerializer
from .permissions import IsRecruiterOrAdmin, IsOwnerOrAdmin # Using IsOwnerOrAdmin for object-level permissions
from .utils import generate_job_suggestions # Import the helper function
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt




@method_decorator(csrf_exempt, name='dispatch')  
class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["recruiter", "status"]
    permission_classes = [IsRecruiterOrAdmin] # Apply general permission for viewset actions

    def get_queryset(self):
        # Admins can see all jobs
        if self.request.user.is_staff:
            return Job.objects.all()
        # Recruiters can only see their own jobs if not an admin.
        # This is a simplification; you might want recruiters to see all 'open' jobs.
        # For now, adhering strictly to "recruiters can manage their own jobs".
        # If a recruiter should see all open jobs, you'd modify this.
        return Job.objects.filter(recruiter=self.request.user)

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create', 'list']:
            permission_classes = [IsRecruiterOrAdmin]
        elif self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            # For retrieve, update, delete on a specific object, use IsOwnerOrAdmin
            # This allows owners (recruiters) to manage their jobs and admins to manage all.
            permission_classes = [IsOwnerOrAdmin]
        else:
            permission_classes = [IsRecruiterOrAdmin] # Default for other actions

        return [permission() for permission in permission_classes]
    @method_decorator(csrf_exempt, name='dispatch')  
    def perform_create(self, serializer):
        
        if self.request.user.is_authenticated:
                serializer.save(recruiter=self.request.user)
        else:
            # Assign a default recruiter for unauthenticated users
            # You must have a user in your database with this username or ID
            try:
                default_recruiter = User.objects.create(username='anonymous_user') # Or by ID, e.g., pk=1
            except User.DoesNotExist:
                # Handle case where default user doesn't exist (e.g., create it or raise an error)
                # For demonstration, let's assume it exists or you handle this.
                raise Exception("Default anonymous_user not found. Please create one.")
            serializer.save(recruiter=default_recruiter)
    
    @action(detail=False, methods=['post'], url_path='suggest-description')
    def suggest_job_description(self, request):
        """
        Custom action to suggest job description and skills based on title.
        Requires 'title' in the request body.
        """
        title = request.data.get('title')
        if not title:
            return Response(
                {"error": "Job title is required for suggestions."},
                status=status.HTTP_400_BAD_REQUEST
            )

        suggestions = generate_job_suggestions(title)
        return Response(suggestions, status=status.HTTP_200_OK)
