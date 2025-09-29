from django.contrib import admin

# Register your models here.
from .models import User  # Import from same app

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'name', 'is_verified']
