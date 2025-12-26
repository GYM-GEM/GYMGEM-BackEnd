from rest_framework.routers import DefaultRouter
from .views import CourseProgressView, CoursesView, LessonsView, LessonSectionsView, CourseEnrollmentsView,CourseAdminView
from django.urls import path
router = DefaultRouter()
router.register(r'courses', CoursesView, basename='courses')
router.register(r'lessons', LessonsView, basename='lessons')
router.register(r'sections', LessonSectionsView, basename='sections')
router.register(r'enrollments', CourseEnrollmentsView, basename='enrollments')
router.register(r'progress', CourseProgressView, basename='progress')

urlpatterns = router.urls

urlpatterns += [
    path('admin/', CourseAdminView.as_view(), name='course-admin'),
]