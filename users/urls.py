from django.urls import path
from . import views

urlpatterns = [
    # path('', views.home, name='home'),
    path('test/', views.test_view, name='test'),
    path('register/', views.register_user, name='register'),
    # path('verify-email/', views.verify_email, name='verify-email'),
    # path('resend-verification/', views.resend_verification_email, name='resend-verification'),

]
