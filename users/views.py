from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import User
from .serializers import UserRegistrationSerializer, UserSerializer  # ← Import from same app

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