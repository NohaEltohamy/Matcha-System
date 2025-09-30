from django.urls import path
from . import views

urlpatterns = [
    # path('', views.home, name='home'),
    path('test/', views.test_view, name='test'),
    path('register/', views.register_user, name='register'),
    # path('verify-email/', views.verify_email, name='verify-email'),
    # path('resend-verification/', views.resend_verification_email, name='resend-verification'),

    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),
    path('google-login/', views.GoogleLoginView.as_view(), name='google-login'),

]
