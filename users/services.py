from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

import os
import uuid
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from pathlib import Path

def send_password_reset_email(email: str) -> None:
    User = get_user_model()
    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        return

    token = PasswordResetTokenGenerator().make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    reset_link = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password/{uid}/{token}/"

    subject = "Password reset request"
    message = (
        "You requested a password reset.\n\n"
        f"Click the link to reset your password: {reset_link}\n\n"
        "If you did not request this, please ignore this email."
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as e:
        print("Password reset email error:", repr(e))


# Google Drive Service
class GoogleDriveService:
    def __init__(self):
        # Google Drive API configuration
        self.SCOPES = ['https://www.googleapis.com/auth/drive.file']
        self.SERVICE_ACCOUNT_FILE = getattr(settings, 'GOOGLE_SERVICE_ACCOUNT_FILE', 'service-account-key.json')
        self.FOLDER_ID = getattr(settings, 'GOOGLE_DRIVE_FOLDER_ID', '1KoGRTjneVb-KdQe43wDiDf1wG3Dvs-OA')
        
        # Allowed file types and sizes
        self.ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        self.MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

    def authenticate(self):
        """Authenticate with Google Drive using service account"""
        try:
            creds = service_account.Credentials.from_service_account_file(
                self.SERVICE_ACCOUNT_FILE, 
                scopes=self.SCOPES
            )
            service = build('drive', 'v3', credentials=creds)
            return service
        except Exception as e:
            raise Exception(f"Google Drive authentication failed: {str(e)}")

    def validate_file(self, file):
        """Validate file type and size"""
        # Check file size
        if file.size > self.MAX_FILE_SIZE:
            raise ValueError(f"File size too large. Maximum allowed: {self.MAX_FILE_SIZE // 1024 // 1024}MB")
        
        # Check file type
        if file.content_type not in self.ALLOWED_IMAGE_TYPES:
            raise ValueError(f"Invalid file type. Allowed types: {', '.join(self.ALLOWED_IMAGE_TYPES)}")

    def create_folder_if_not_exists(self, service, folder_name):
        """Create folder if it doesn't exist"""
        try:
            # Check if folder exists
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = service.files().list(q=query, fields="files(id, name)").execute()
            folders = results.get('files', [])
            
            if folders:
                return folders[0]['id']  # Return existing folder ID
            else:
                # Create new folder
                folder_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = service.files().create(body=folder_metadata, fields='id').execute()
                return folder['id']
        except Exception as e:
            raise Exception(f"Failed to create folder: {str(e)}")

    def upload_avatar(self, file, filename, folder_name="user_avatars"):
        """
        Upload avatar to Google Drive and return public URL
        
        Args:
            file: Django UploadedFile object
            filename: Original filename
            folder_name: Google Drive folder name
        
        Returns:
            str: Public URL of the uploaded image
        """
        try:
            # Validate file
            self.validate_file(file)
            
            # Authenticate with Google Drive
            service = self.authenticate()
            
            # Create or get folder
            folder_id = self.create_folder_if_not_exists(service, folder_name)
            
            # Generate unique filename
            file_extension = filename.split('.')[-1].lower()
            unique_filename = f"avatar_{uuid.uuid4()}.{file_extension}"
            
            # File metadata
            file_metadata = {
                'name': unique_filename,
                'parents': [folder_id]
            }
            
            # Handle file upload - two methods:

            # Method 1: Using temporary file (more reliable for large files)
            temp_path = None
            try:
                # Save file temporarily
                temp_path = default_storage.save(f'temp/{unique_filename}', ContentFile(file.read()))
                temp_file_path = default_storage.path(temp_path)
                
                media = MediaFileUpload(
                    temp_file_path,
                    mimetype=file.content_type,
                    resumable=True
                )
                
                # Upload file
                file_obj = service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, name, webViewLink, mimeType'
                ).execute()

            # Method 2: Using in-memory upload (faster for small files)
            # file_bytes = file.read()
            # media = MediaIoBaseUpload(
            #     io.BytesIO(file_bytes),
            #     mimetype=file.content_type,
            #     resumable=True
            # )
            # file_obj = service.files().create(
            #     body=file_metadata,
            #     media_body=media,
            #     fields='id, name, webViewLink, mimeType'
            # ).execute()

            finally:
                # Clean up temporary file
                if temp_path and default_storage.exists(temp_path):
                    default_storage.delete(temp_path)
            
            # Make file publicly accessible
            service.permissions().create(
                fileId=file_obj['id'],
                body={
                    'type': 'anyone',
                    'role': 'reader',
                    'allowFileDiscovery': False
                }
            ).execute()
            
            # Generate direct image URL (for embedding in HTML)
            direct_link = f"https://drive.google.com/uc?export=view&id={file_obj['id']}"
            
            # Alternative: Download URL (forces download)
            # download_link = f"https://drive.google.com/uc?export=download&id={file_obj['id']}"
            
            return {
                'success': True,
                'url': direct_link,
                'file_id': file_obj['id'],
                'filename': unique_filename,
                'web_view_link': file_obj.get('webViewLink'),
                'mime_type': file_obj.get('mimeType')
            }
            
        except Exception as e:
            # Clean up on error
            if 'temp_path' in locals() and temp_path and default_storage.exists(temp_path):
                default_storage.delete(temp_path)
            
            return {
                'success': False,
                'error': str(e),
                'url': None
            }

    def delete_file(self, file_id):
        """Delete file from Google Drive"""
        try:
            service = self.authenticate()
            service.files().delete(fileId=file_id).execute()
            return {'success': True, 'message': 'File deleted successfully'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_file_info(self, file_id):
        """Get file information"""
        try:
            service = self.authenticate()
            file_obj = service.files().get(
                fileId=file_id, 
                fields='id, name, mimeType, webViewLink, createdTime, modifiedTime, size'
            ).execute()
            return {'success': True, 'file': file_obj}
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Global instance
google_drive_service = GoogleDriveService()
