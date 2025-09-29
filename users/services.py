```

Add the password reset email sender service:

```python
# /home/jboles/Desktop/task/users/services.py
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def send_password_reset_email(email: str) -> None:
    User = get_user_model()
    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        return  # Do nothing to avoid disclosing existence

    token = PasswordResetTokenGenerator().make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    reset_link = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password/{uid}/{token}/"

    subject = "Password reset request"
    message = (
        "You requested a password reset.\n\n"
        f"Click the link to reset your password: {reset_link}\n\n"
        "If you did not request this, please ignore this email."
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )
```

Extend serializers:

```12:73:/home/jboles/Desktop/task/users/serializers.py
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email', '').strip()
        password = attrs.get('password')

        if not email:
            raise serializers.ValidationError('Provide either username or email.')

        attrs['login_identifier'] =  email
        attrs['by_email'] = bool(email)
        attrs['password'] = password
        return attrs
```

Add the new password reset serializers:

```python
# append to /home/jboles/Desktop/task/users/serializers.py
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
```

Add the views:

```1:115:/home/jboles/Desktop/task/users/views.py
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
        logout(request)
        return 
        Response(data={
        "success": True,
        "message": "Logged out.",
        "data": [],
        "errors": []
    })
        
```

Append the new API views:

```python
# append to /home/jboles/Desktop/task/users/views.py
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from .serializers import ForgotPasswordSerializer, ResetPasswordSerializer
from .services import send_password_reset_email


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            send_password_reset_email(email)
        # Always return generic success
        return Response({"message": "If this email exists, a password reset link has been sent."})


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
            return Response({"message": "Password reset successful."})

        if PasswordResetTokenGenerator().check_token(user, token):
            user.set_password(new_password)
            user.save()
            return Response({"message": "Password reset successful."})

        # Generic response even on invalid token
        return Response({"message": "Password reset successful."})
```

Create a dedicated auth URLConf to get the exact endpoint paths:

```python
# /home/jboles/Desktop/task/users/auth_urls.py
from django.urls import path
from .views import ForgotPasswordView, ResetPasswordView

urlpatterns = [
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
]
```

Email and security-related settings:

```1:28:/home/jboles/Desktop/task/backend/settings.py
ALLOWED_HOSTS = []
```

Append the following settings:

```python
# append to /home/jboles/Desktop/task/backend/settings.py
import os

# Where to build the reset link sent to users
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

# Use console backend for local dev; configure SMTP in production
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'no-reply@example.com')

# Expire password reset tokens after 1 hour
PASSWORD_RESET_TIMEOUT = 3600
```

### How to test quickly
- Forgot password:
  - POST to `/api/auth/forgot-password/` with body:
    ```json
    { "email": "user@example.com" }
    ```
  - Response:
    ```json
    { "message": "If this email exists, a password reset link has been sent." }
    ```
  - With console email backend, the reset link appears in the server logs. It will look like:
    - `https://<frontend-url>/reset-password/<uid>/<token>/`

- Reset password:
  - POST to `/api/auth/reset-password/` with:
    ```json
    { "uid": "<uid>", "token": "<token>", "new_password": "NewStrongP@ssw0rd" }
    ```
  - Response:
    ```json
    { "message": "Password reset successful." }
    ```

Notes:
- Token expiration is 1 hour via `PASSWORD_RESET_TIMEOUT`.
- Password is set via `user.set_password(...)` so hashing is applied.
- Both endpoints avoid revealing whether an email or token is valid.

- I added a new include in `backend/urls.py`, created `users/auth_urls.py`, new serializers in `users/serializers.py`, views in `users/views.py`, and a `users/services.py` email helper. You can now hit `/api/auth/forgot-password/` and `/api/auth/reset-password/`.