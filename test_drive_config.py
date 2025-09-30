import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from users.services import google_drive_service
from django.conf import settings

def test_configuration():
    print("🧪 Testing Google Drive Configuration")
    print("=" * 50)
    
    print(f"📁 Service account file: {settings.GOOGLE_SERVICE_ACCOUNT_FILE}")
    print(f"✅ File exists: {os.path.exists(settings.GOOGLE_SERVICE_ACCOUNT_FILE)}")
    
    print(f"📂 Google Drive folder ID: {settings.GOOGLE_DRIVE_FOLDER_ID}")
    
    # Test authentication
    try:
        google_drive_service.test_connection()
        print("🎉 All configurations are correct!")
    except Exception as e:
        print(f"❌ Configuration error: {e}")

if __name__ == "__main__":
    test_configuration()


# Run the test:
# python test_drive_config.py
