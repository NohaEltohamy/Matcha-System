from django.contrib.auth import authenticate, login, logout, get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework import status,permissions
from rest_framework.decorators import api_view,parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail

from rest_framework.views import APIView
from rest_framework.response import Response
from .models import User, EmailVerificationToken

from .serializers import UserRegistrationSerializer, UserSerializer, LoginSerializer, ForgotPasswordSerializer, ResetPasswordSerializer, EmailVerificationSerializer, ResendVerificationSerializer # ← Import from same app
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
from .services import google_drive_service
import logging

logger = logging.getLogger(__name__)

# Create your views here.
# from django.http import HttpResponse

# def home(request):
#     return HttpResponse("Hello, Django!")


# @api_view(['POST'])
# def register_user(request):
#     # Use the serializer
#     serializer = UserRegistrationSerializer(data=request.data)
    
#     if serializer.is_valid():
#         user = serializer.save()  # Creates the user
#         return Response({
#             "success": True,
#             "message": "User registered successfully",
#             "data": UserSerializer(user).data  # Use different serializer for response
#         })
#     else:
#         return Response({
#             "success": False,
#             "message": "Registration failed", 
#             "errors": serializer.errors
#         })

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def register_user(request):
    """
    User Registration Endpoint
    POST /api/auth/register/
    
    Request Body (multipart/form-data or JSON):
    {
        "name": "John Doe",
        "email": "john@example.com", 
        "password": "StrongPassword123",
        "password_confirm": "StrongPassword123",
        "phone": "+1234567890",
        "avatar": <file> (optional)
    }
    """
    try:
        data = request.data.copy()
        avatar_file = request.FILES.get('avatar')
        
        # Handle avatar upload to Google Drive
        if avatar_file:
            upload_result = google_drive_service.upload_avatar(
                file=avatar_file,
                filename=avatar_file.name
            )
            
            if upload_result['success']:
                data['avatar'] = upload_result['url']
                logger.info(f"Avatar uploaded successfully for {data.get('email')}")
            else:
                return Response({
                    "success": False,
                    "message": f"Avatar upload failed: {upload_result['error']}",
                    "data": None,
                    "errors": ["avatar_upload_failed"]
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate and create user
        serializer = UserRegistrationSerializer(data=data)
        
        if serializer.is_valid():
            user = serializer.save()
            logger.info(f"User registered successfully: {user.email}")
            
            # Create email verification token
            expires_at = timezone.now() + timedelta(hours=24)
            verification_token = EmailVerificationToken.objects.create(
                user=user,
                expires_at=expires_at
            )
            
            # Send verification email
            verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token.token}"
            
            try:
                send_mail(
                    subject='Verify Your Email Address',
                    message=f'''
Hello {user.name},

Please verify your email address by clicking the link below:

{verification_url}

This link will expire in 24 hours.

If you didn't create an account, please ignore this email.

Best regards,
Your App Team
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                logger.info(f"Verification email sent to {user.email}")
            except Exception as e:
                logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
            
            # Return success response
            user_data = UserSerializer(user).data
            
            return Response({
                "success": True,
                "message": "User registered successfully. Please check your email for verification.",
                "data": user_data,
                "errors": []
            }, status=status.HTTP_201_CREATED)
            
        else:
            logger.warning(f"Registration failed for {data.get('email')}: {serializer.errors}")
            return Response({
                "success": False,
                "message": "Registration failed",
                "data": None,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return Response({
            "success": False,
            "message": "An error occurred during registration",
            "data": None,
            "errors": [str(e)]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def verify_email(request):
    """
    Email Verification Endpoint
    POST /api/auth/verify-email/
    
    Request Body (JSON):
    {
        "token": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    }
    """
    serializer = EmailVerificationSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            "success": False,
            "message": "Invalid request data",
            "data": None,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    token = serializer.validated_data['token']
    
    try:
        verification_token = EmailVerificationToken.objects.select_related('user').get(token=token)
        
        if verification_token.is_expired():
            verification_token.delete()
            return Response({
                "success": False,
                "message": "Verification token has expired",
                "data": None,
                "errors": ["token_expired"]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = verification_token.user
        user.is_verified = True
        user.save()
        
        # Delete used token
        verification_token.delete()
        
        logger.info(f"Email verified successfully for {user.email}")
        
        return Response({
            "success": True,
            "message": "Email verified successfully",
            "data": {
                "user": UserSerializer(user).data
            },
            "errors": []
        }, status=status.HTTP_200_OK)
        
    except EmailVerificationToken.DoesNotExist:
        return Response({
            "success": False,
            "message": "Invalid verification token",
            "data": None,
            "errors": ["invalid_token"]
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def resend_verification_email(request):
    """
    Resend Verification Email Endpoint
    POST /api/auth/resend-verification/
    
    Request Body (JSON):
    {
        "email": "john@example.com"
    }
    """
    serializer = ResendVerificationSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            "success": False,
            "message": "Invalid request data",
            "data": None,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    
    try:
        user = User.objects.get(email=email)
        
        if user.is_verified:
            return Response({
                "success": False,
                "message": "Email is already verified",
                "data": None,
                "errors": ["already_verified"]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Delete any existing tokens for this user
        EmailVerificationToken.objects.filter(user=user).delete()
        
        # Create new verification token
        expires_at = timezone.now() + timedelta(hours=24)
        verification_token = EmailVerificationToken.objects.create(
            user=user,
            expires_at=expires_at
        )
        
        # Send verification email
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token.token}"
        
        try:
            send_mail(
                subject='Verify Your Email Address',
                message=f'''
Hello {user.name},

Please verify your email address by clicking the link below:

{verification_url}

This link will expire in 24 hours.

If you didn't request this verification, please ignore this email.

Best regards,
Your App Team
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info(f"Verification email resent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to resend verification email to {user.email}: {str(e)}")
            return Response({
                "success": False,
                "message": "Failed to send verification email",
                "data": None,
                "errors": ["email_send_failed"]
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            "success": True,
            "message": "Verification email sent successfully",
            "data": None,
            "errors": []
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            "success": False,
            "message": "User with this email does not exist",
            "data": None,
            "errors": ["user_not_found"]
        }, status=status.HTTP_404_NOT_FOUND)


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
        
        
