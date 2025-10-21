# job_board/urls.py

from rest_framework.routers import DefaultRouter
from .views import JobViewSet

router = DefaultRouter()
router.register(r'jobs', JobViewSet)

urlpatterns = router.urls
