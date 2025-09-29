from django.contrib.auth import authenticate, login, logout, get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework import status,permissions
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import User
from .serializers import UserRegistrationSerializer, UserSerializer, LoginSerializer  # ← Import from same app

# Create your views here.
# from django.http import HttpResponse

# def home(request):
#     return HttpResponse("Hello, Django!")


@api_view(['POST'])
def register_user(request):
    # Use the serializer
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()  # Creates the user
        return Response({
            "success": True,
            "message": "User registered successfully",
            "data": UserSerializer(user).data  # Use different serializer for response
        })
    else:
        return Response({
            "success": False,
            "message": "Registration failed", 
            "errors": serializer.errors
        })
    

@api_view(['GET'])
def test_view(request):

    return Response({
        "success": True,
        "message": "DRF is working!",
        "data": None,
        "errors": []
    })

User = get_user_model()


@method_decorator(csrf_exempt, name='dispatch')  # dev-only; remove in prod if you enforce CSRF
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        login_identifier = serializer.validated_data['login_identifier']
        by_email = serializer.validated_data['by_email']
        password = serializer.validated_data['password']

        user = None
        if by_email:
            try:
                u = User.objects.get(email__iexact=login_identifier)
                user = authenticate(request, username=u.username, password=password)
            except User.DoesNotExist:
                user = None
        else:
            user = authenticate(request, username=login_identifier, password=password)

        if not user:
            return Response(data{
        "success": True,
        "message": "Invalid credentials.",
        "data": [],
        "errors": []
    })
            

        if not user.is_active:
            return Response(data{
        "success": True,
        "message": "User is disabled.",
        "data": [],
        "errors": []
    })
           

        login(request, user)
        return Response(data{
        "success": True,
        "message": "Login successful",
        "data": UserSerializer(user).data,
        "errors": []
    })
       

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'detail': 'Logged out.'}, status=status.HTTP_200_OK)

