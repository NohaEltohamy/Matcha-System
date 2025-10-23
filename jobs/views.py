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
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Job
from .serializers import JobSerializer

User = get_user_model()


#job post
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_job(request):
    """
    API endpoint to post a new job
    Steps:
    1. Validate data
    2. Check if logged user is recruiter
    3. Store recruiter who posted the job
    """
    # Step 1: Validate data
    serializer = JobSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            "success": False,
            "message": "Invalid job data",
            "data": None,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Step 2: Check if logged user is recruiter
    if not request.user.is_recruiter():
        return Response({
            "success": False,
            "message": "Only recruiters can post jobs",
            "data": None,
            "errors": ["insufficient_permissions"]
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Step 3: Store recruiter who posted the job
    try:
        # Create the job with the authenticated recruiter
        job = serializer.save(recruiter=request.user)
        
        # Return success response with job data
        job_data = JobSerializer(job).data
        return Response({
            "success": True,
            "message": "Job posted successfully",
            "data": job_data,
            "errors": []
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            "success": False,
            "message": "Failed to create job",
            "data": None,
            "errors": [str(e)]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#genai generate job description
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_job_description_skills(request):
    """
    API endpoint to generate job description and skills only (without creating job)
    Useful for previewing AI suggestions before creating the job
    """
    
    # Step 1: Validate input
    job_title = request.data.get('title')
    if not job_title:
        return Response({
            "success": False,
            "message": "Job title is required",
            "data": None,
            "errors": ["title_required"]
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Step 2: Check if logged user is recruiter
    if not request.user.is_recruiter():
        return Response({
            "success": False,
            "message": "Only recruiters can generate job descriptions",
            "data": None,
            "errors": ["insufficient_permissions"]
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Step 3: Generate AI suggestions
    try:
        ai_suggestions = generate_job_suggestions(job_title)
        
        return Response({
            "success": True,
            "message": f"AI suggestions generated for '{job_title}'",
            "data": {
                "title": job_title,
                "suggested_description": ai_suggestions.get('description', ''),
                "suggested_skills": ai_suggestions.get('skills', [])
            },
            "errors": []
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "success": False,
            "message": "Failed to generate job description",
            "data": None,
            "errors": [str(e)]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
