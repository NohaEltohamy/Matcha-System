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
from .serializers import UserRegistrationSerializer, UserSerializer, LoginSerializer, ForgotPasswordSerializer, ResetPasswordSerializer  # ← Import from same app
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from .services import send_password_reset_email
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from django.conf import settings
from rest_framework import status
from rest_framework.authtoken.models import Token
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from .serializers import GoogleLoginSerializer


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
        print(login_identifier, by_email, password )
        user = None
        
        if by_email:
            try:
                u = User.objects.get(email__iexact=login_identifier)                
                user = authenticate(request, email=u.email, password=password)
                
            except User.DoesNotExist:
                user = None
        else:
            user = authenticate(request, username=login_identifier, password=password)

        if not user:
            return Response(data={
        "success": True,
        "message": "Invalid credentials.",
        "data": [],
        "errors": []
    })
            

        if not user.is_active:
            return Response(data={
        "success": True,
        "message": "User is disabled.",
        "data": [],
        "errors": []
    })
           

        login(request, user)
        return Response(data={
        "success": True,
        "message": "Login successful",
        "data": UserSerializer(user).data,
        "errors": []
    })
       

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        print('in',request)
        logout(request)
        return Response(data={
            "success": True,
            "message": "Logged out.",
            "data": [],
            "errors": []
            })
            

class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            if email:
                res= send_password_reset_email(email)
                if not res:
                    # Always return generic success
                    return     Response(data={
                            "success": True,
                            "message": "I a password reset link has been sent.",
                            "data": [],
                            "errors": []
                        })
                else:
                    return     Response(data={
                            "success": False,
                            "message": "error",
                            "data": [],
                            "errors": [res]
                        })

            else:
                return     Response(data={
                        "success": True,
                        "message": "not exsist email",
                        "data": [],
                        "errors": []
                    })
                
class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = get_user_model().objects.get(pk=user_id)
        except Exception:
            # Generic response to avoid leaking info
            return 
            Response(data={
                "success": True,
                "message": "Password reset successful.",
                "data": [],
                "errors": []
            })

        if PasswordResetTokenGenerator().check_token(user, token):
            user.set_password(new_password)
            user.save()
            return Response(data={
                "success": True,
                "message": "Password reset successful.",
                "data": [],
                "errors": []
            })
    

        # Generic response even on invalid token
        return Response(data={
                "success": True,
                "message": "Password reset successful.",
                "data": [],
                "errors": []
            })
    



class GoogleLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        id_tok = serializer.validated_data.get('id_token')
        access_tok = serializer.validated_data.get('access_token')

        payload = None

        if id_tok:
            # Verify ID token signature and audience
            try:
                payload = google_id_token.verify_oauth2_token(
                    id_tok,
                    google_requests.Request(),
                    settings.GOOGLE_CLIENT_ID or None
                )
            except Exception:
                return Response(data={
                    "success": True,
                    "message": "Invalid Google token.",
                    "data": [],
                    "errors": []
                })
               
        else:
            # Fallback: validate access token by calling Google UserInfo endpoint
            try:
                req = Request(
                    'https://www.googleapis.com/oauth2/v3/userinfo',
                    headers={'Authorization': f'Bearer {access_tok}'}
                )
                with urlopen(req, timeout=10) as resp:
                    payload = json.loads(resp.read().decode('utf-8'))
            except (HTTPError, URLError, ValueError):
                return Response(data={
                    "success": True,
                    "message": "Invalid Google token.",
                    "data": [],
                    "errors": []
                })
                

        # Normalize fields from either payload shape (ID token vs userinfo)
        email = payload.get('email')
        email_verified = payload.get('email_verified', False)
        name = payload.get('name') or payload.get('given_name') or ''
        picture = payload.get('picture')

        if not email or not email_verified:
            return Response(data={
                    "success": True,
                    "message": "Email not verified with Google.",
                    "data": [],
                    "errors": []
                })
            

        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email__iexact=email)
        except UserModel.DoesNotExist:
            user = UserModel.objects.create_user(
                email=email,
                password=None,
                name=name or email.split('@')[0],
                avatar=picture
            )
            # Optionally mark as verified
            if hasattr(user, 'is_verified'):
                user.is_verified = True
                user.save(update_fields=['is_verified'])

        token, _ = Token.objects.get_or_create(user=user)
        return Response(data={
                    "success": True,
                    "message": "Google login successful.",
                    "data": {
            "token": token.key,
            "user": {
                "id": str(user.pk),
                "name": user.name,
                "email": user.email,
                "avatar": getattr(user, 'avatar', None),
            }},
                    "errors": []
                })
        
        