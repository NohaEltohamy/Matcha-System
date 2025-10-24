# job_board/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Job, CV, CandidateJobMatch
from .serializers import JobSerializer, CVSerializer, CandidateJobMatchSerializer
from .permissions import IsRecruiterOrAdmin, IsOwnerOrAdmin # Using IsOwnerOrAdmin for object-level permissions
from .utils import generate_job_suggestions,generate_cv_evaluation # Import the helper function
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Job
from .serializers import JobSerializer
from django.db.models import Q

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

#job list
# Add this after your existing functions, before the JobViewSet class

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_recruiter_jobs(request):
    """
    API endpoint to list jobs for the logged-in recruiter
    Query parameters:
    - status: filter by job status (open, closed, draft)
    - search: search in title and description
    """
    # Step 1: Check if logged user is recruiter
    if not request.user.is_recruiter():
        return Response({
            "success": False,
            "message": "Only recruiters can view job lists",
            "data": None,
            "errors": ["insufficient_permissions"]
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Start with jobs for the logged-in recruiter
        queryset = Job.objects.filter(recruiter=request.user)
        
        # Apply status filter
        status_filter = request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Apply search filter
        search_query = request.GET.get('search')
        if search_query:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        # Apply ordering (newest first)
        queryset = queryset.order_by('-created_at')
        
        # Serialize the data
        serializer = JobSerializer(queryset, many=True)
        
        return Response({
            "success": True,
            "message": f"Found {queryset.count()} jobs for {request.user.username}",
            "data": serializer.data,
            "errors": []
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "success": False,
            "message": "Failed to retrieve jobs",
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_matched_cvs(request):
    """
    API endpoint to list candidate CVs filtered by job title and ordered by genai_score
    Query parameters:
    - job_title: filter CVs by job title (required)
    - min_score: minimum genai_score threshold (optional, default: 0)
    - limit: maximum number of results (optional, default: 50)
    """
    # Step 1: Check if logged user is recruiter or admin
    if not (request.user.is_recruiter() or request.user.is_staff):
        return Response({
            "success": False,
            "message": "Only recruiters and admins can view candidate CVs",
            "data": None,
            "errors": ["insufficient_permissions"]
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Step 2: Validate required parameters
    job_title = request.GET.get('job_title')
    if not job_title:
        return Response({
            "success": False,
            "message": "job_title parameter is required",
            "data": None,
            "errors": ["job_title_required"]
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Step 3: Get optional parameters
        min_score = float(request.GET.get('min_score', 0))
        limit = int(request.GET.get('limit', 50))
        
        # Step 4: Find jobs matching the title
        matching_jobs = Job.objects.filter(
            Q(title__icontains=job_title) | 
            Q(description__icontains=job_title)
        )
        
        if not matching_jobs.exists():
            return Response({
                "success": True,
                "message": f"No jobs found matching '{job_title}'",
                "data": [],
                "errors": []
            }, status=status.HTTP_200_OK)
        
        # Step 5: Get candidate matches for these jobs, ordered by genai_score
        candidate_matches = CandidateJobMatch.objects.filter(
            job__in=matching_jobs,
            genai_score__gte=min_score
        ).select_related(
            'cv', 'cv__candidate', 'job'
        ).order_by('-genai_score')[:limit]
        
        # Step 6: Serialize the data
        serializer = CandidateJobMatchSerializer(candidate_matches, many=True)
        
        # Step 7: Prepare response data with statistics
        response_data = {
            "candidate_matches": serializer.data,
            "statistics": {
                "total_matches": candidate_matches.count(),
                "job_title_searched": job_title,
                "matching_jobs_count": matching_jobs.count(),
                "min_score_threshold": min_score,
                "average_score": sum(match.genai_score for match in candidate_matches) / len(candidate_matches) if candidate_matches else 0,
                "highest_score": candidate_matches[0].genai_score if candidate_matches else 0,
            }
        }
        
        return Response({
            "success": True,
            "message": f"Found {candidate_matches.count()} candidate matches for '{job_title}'",
            "data": response_data,
            "errors": []
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response({
            "success": False,
            "message": "Invalid parameter values",
            "data": None,
            "errors": [str(e)]
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response({
            "success": False,
            "message": "Failed to retrieve candidate CVs",
            "data": None,
            "errors": [str(e)]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def evaluate_cv_by_genai(request):
    """
    API endpoint to evaluate a CV against a job using GenAI
    Required fields:
    - cv_id: ID of the CV to evaluate
    - job_id: ID of the job to match against
    """
    # Step 1: Check if logged user is recruiter or admin
    if not (request.user.is_recruiter() or request.user.is_staff):
        return Response({
            "success": False,
            "message": "Only recruiters and admins can evaluate CVs",
            "data": None,
            "errors": ["insufficient_permissions"]
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Step 2: Validate required fields
    cv_id = request.data.get('cv_id')
    job_id = request.data.get('job_id')
    
    if not cv_id or not job_id:
        return Response({
            "success": False,
            "message": "Both cv_id and job_id are required",
            "data": None,
            "errors": ["cv_id_and_job_id_required"]
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Step 3: Get CV and Job objects
        try:
            cv = CV.objects.get(id=cv_id)
            job = Job.objects.get(id=job_id)
        except CV.DoesNotExist:
            return Response({
                "success": False,
                "message": "CV not found",
                "data": None,
                "errors": ["cv_not_found"]
            }, status=status.HTTP_404_NOT_FOUND)
        except Job.DoesNotExist:
            return Response({
                "success": False,
                "message": "Job not found",
                "data": None,
                "errors": ["job_not_found"]
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Step 4: Generate AI evaluation
        ai_evaluation = generate_cv_evaluation(cv, job)
        
        # Step 5: Create or update CandidateJobMatch
        match, created = CandidateJobMatch.objects.get_or_create(
            cv=cv,
            job=job,
            defaults={
                'genai_score': ai_evaluation['genai_score'],
                'skills_match_score': ai_evaluation['skills_match_score'],
                'experience_match_score': ai_evaluation['experience_match_score'],
                'overall_fit_score': ai_evaluation['overall_fit_score'],
                'ai_analysis': ai_evaluation['ai_analysis'],
            }
        )
        
        # If match already exists, update it
        if not created:
            match.genai_score = ai_evaluation['genai_score']
            match.skills_match_score = ai_evaluation['skills_match_score']
            match.experience_match_score = ai_evaluation['experience_match_score']
            match.overall_fit_score = ai_evaluation['overall_fit_score']
            match.ai_analysis = ai_evaluation['ai_analysis']
            match.save()
        
        # Step 6: Serialize and return the result
        serializer = CandidateJobMatchSerializer(match)
        
        return Response({
            "success": True,
            "message": f"CV evaluated successfully. GenAI Score: {ai_evaluation['genai_score']}%",
            "data": serializer.data,
            "errors": []
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "success": False,
            "message": "Failed to evaluate CV",
            "data": None,
            "errors": [str(e)]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)