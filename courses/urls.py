from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CoursesView, LessonsView, LessonSectionsView, CourseEnrollmentsView

router = DefaultRouter()
router.register(r'courses', CoursesView, basename='courses')
router.register(r'lessons', LessonsView, basename='lessons')
router.register(r'sections', LessonSectionsView, basename='sections')
router.register(r'enrollments', CourseEnrollmentsView, basename='enrollments')

urlpatterns = router.urls