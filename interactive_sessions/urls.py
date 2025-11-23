from rest_framework.routers import DefaultRouter
from .views import InteractiveSessionView

router = DefaultRouter()
router.register(r'', InteractiveSessionView, basename='interactive-sessions')

urlpatterns = router.urls