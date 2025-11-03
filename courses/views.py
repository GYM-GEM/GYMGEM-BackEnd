from rest_framework.viewsets import ViewSet

from profiles.models import Profile
from .models import Course
from .serializers import CourseLessonSerializer, CourseSerializer, CourseEnrollmentSerializer, CourseEnrollment, LessonSectionSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from authenticationAndAuthorization.permissions import HasRole
from .validators import CourseValidator

# Create your views here.
class CoursesView(ViewSet):

    @action(methods=['get'], detail=False, permission_classes=[IsAuthenticated], url_path='for-trainees')
    def get_courses_for_trainees(self, request):
        courses = Course.objects.all()
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)

    @action(methods=['post'], detail=False, permission_classes=[HasRole(['trainer'])], url_path='create')
    def create_course(self, request):
        try:
            CourseValidator.validate_trainer_profile_belongs_to_user(request.data.get('trainer_profile'), request.user)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = CourseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['put'], detail=True, permission_classes=[HasRole(['trainer'])], url_path='update')
    def update_course(self, request, pk=None):
        try:
            course = CourseValidator.validate_course_exists(pk)
            CourseValidator.validate_course_belongs_to_trainer(course, request.user.trainer_profile)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = CourseSerializer(course, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['delete'], detail=True, permission_classes=[HasRole(['trainer'])], url_path='delete')
    def delete_course(self, request, pk=None):
        try:
            course = CourseValidator.validate_course_exists(pk)
            CourseValidator.validate_course_belongs_to_trainer(course, request.user.trainer_profile)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        course.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(methods=['get'], detail=True, permission_classes=[IsAuthenticated], url_path='detail')
    def get_course_detail(self, request, pk=None):
        try:
            course = CourseValidator.validate_course_exists(pk)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = CourseSerializer(course)
        return Response(serializer.data)

class LessonsView(ViewSet):
    @action(methods=['get'], detail=True, permission_classes=[IsAuthenticated], url_path='lessons')
    def get_lessons_for_course(self, request, pk=None):
        try:
            course = CourseValidator.validate_course_exists(pk)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        try:
            lessons = course.lessons.all()
            serializer = CourseLessonSerializer(lessons, many=True)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    @action(methods=['post'], detail=True, permission_classes=[HasRole(['trainer'])], url_path='lessons/create')
    def create_lesson_for_course(self, request, pk=None):
        try:
            course = CourseValidator.validate_course_exists(pk)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        try:
            trainer = Profile.objects.get(pk=request.user.pk)
            print (trainer, "++++++++++",request.user.pk,"++++++++++", course.trainer_profile)
            CourseValidator.validate_course_belongs_to_trainer(course, trainer)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CourseLessonSerializer(data={**request.data, **{"course": course.pk}})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['put'], detail=True, permission_classes=[HasRole(['trainer'])], url_path='lessons/update/(?P<lesson_pk>\d+)')
    def update_lesson_for_course(self, request, pk=None, lesson_pk=None):
        try:
            course = CourseValidator.validate_course_exists(pk)
            lesson = CourseValidator.validate_lesson_exists(lesson_pk)
            CourseValidator.validate_course_belongs_to_trainer(course, request.user.trainer_profile)
            CourseValidator.validate_lesson_belongs_to_course(lesson, course)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = CourseLessonSerializer(lesson, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['delete'], detail=True, permission_classes=[HasRole(['trainer'])], url_path='lessons/delete/(?P<lesson_pk>\d+)')
    def delete_lesson_for_course(self, request, pk=None, lesson_pk=None):
        try:
            course = CourseValidator.validate_course_exists(pk)
            lesson = CourseValidator.validate_lesson_exists(lesson_pk)
            CourseValidator.validate_lesson_belongs_to_course(lesson, course)
            CourseValidator.validate_course_belongs_to_trainer(course, request.user.trainer_profile)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        lesson.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(methods=['get'], detail=True, permission_classes=[IsAuthenticated], url_path='lessons/detail/(?P<lesson_pk>\d+)')
    def get_lesson_detail(self, request, pk=None, lesson_pk=None):
        try:
            course = CourseValidator.validate_course_exists(pk)
            lesson = CourseValidator.validate_lesson_exists(lesson_pk)
            CourseValidator.validate_lesson_belongs_to_course(lesson, course)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = CourseLessonSerializer(lesson)
        return Response(serializer.data)

class LessonSectionsView(ViewSet):
    @action(methods=['get'], detail=True, permission_classes=[IsAuthenticated], url_path='sections')
    def get_sections_for_lesson(self, request, pk=None):
        try:
            lesson = CourseValidator.validate_lesson_exists(pk)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        sections = lesson.sections.all()
        serializer = LessonSectionSerializer(sections, many=True)
        return Response(serializer.data)
    
    @action(methods=['get'], detail=True, permission_classes=[IsAuthenticated], url_path='section/(?P<section_pk>\d+)')
    def get_section_detail(self, request, pk=None, section_pk=None):
        try:
            lesson = CourseValidator.validate_lesson_exists(pk)
            section = CourseValidator.validate_section_exists(section_pk)
            CourseValidator.validate_section_belongs_to_lesson(section, lesson)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = LessonSectionSerializer(section)
        return Response(serializer.data)
    
    @action(methods=['post'], detail=True, permission_classes=[HasRole(['trainer'])], url_path='sections/create')
    def create_section_for_lesson(self, request, pk=None):
        try:
            lesson = CourseValidator.validate_lesson_exists(pk)
            print("++++++++++", request.user)
            trainer = Profile.objects.get(pk=request.user.pk)
            CourseValidator.validate_lesson_belongs_to_trainer(lesson, trainer)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = LessonSectionSerializer(data={**request.data, **{"lesson": lesson.pk}})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['put'], detail=True, permission_classes=[HasRole(['trainer'])], url_path='sections/update/(?P<section_pk>\d+)')
    def update_section_for_lesson(self, request, pk=None, section_pk=None):
        try:
            lesson = CourseValidator.validate_lesson_exists(pk)
            section = CourseValidator.validate_section_exists(section_pk)
            CourseValidator.validate_section_belongs_to_lesson(section, lesson)
            CourseValidator.validate_lesson_belongs_to_trainer(lesson, request.user.trainer_profile)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = LessonSectionSerializer(section, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['delete'], detail=True, permission_classes=[HasRole(['trainer'])], url_path='sections/delete/(?P<section_pk>\d+)')
    def delete_section_for_lesson(self, request, pk=None, section_pk=None):
        try:
            lesson = CourseValidator.validate_lesson_exists(pk)
            section = CourseValidator.validate_section_exists(section_pk)
            CourseValidator.validate_section_belongs_to_lesson(section, lesson)
            CourseValidator.validate_lesson_belongs_to_trainer(lesson, request.user.trainer_profile)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        section.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class CourseEnrollmentsView(ViewSet):
    @action(methods=['post'], detail=True, permission_classes=[HasRole(['trainee'])], url_path='enroll')
    def enroll_in_course(self, request, pk=None):
        try:
            course = CourseValidator.validate_course_exists(pk)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = CourseEnrollmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(course=course)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'], detail=True, permission_classes=[HasRole(['trainer'])], url_path='enrollments')
    def get_enrollments_for_course(self, request, pk=None):
        try:
            course = CourseValidator.validate_course_exists(pk)
            CourseValidator.validate_course_belongs_to_trainer(course, request.user.trainer_profile)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        enrollments = course.enrollments.all()
        serializer = CourseEnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)

    @action(methods=['get'], detail=True, permission_classes=[HasRole(['trainee'])], url_path='my-enrollments')
    def get_my_enrollments(self, request, pk=None):
        enrollments = CourseEnrollment.objects.filter(course__id=pk, trainee_profile=request.user.trainee_profile)
        serializer = CourseEnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)

    @action(methods=['get'], detail=True, permission_classes=[HasRole(['trainee'])], url_path='my-enrollment-detail/(?P<enrollment_pk>\d+)')
    def get_my_enrollment_detail(self, request, pk=None, enrollment_pk=None):
        try:
            course = CourseValidator.validate_course_exists(pk)
            enrollment = CourseValidator.validate_enrollment_exists(enrollment_pk)
            CourseValidator.validate_enrollment_belongs_to_course(enrollment, course)
            CourseValidator.validate_enrollment_belongs_to_trainee(enrollment, request.user.trainee_profile)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = CourseEnrollmentSerializer(enrollment)
        return Response(serializer.data)

    @action(methods=['delete'], detail=True, permission_classes=[HasRole(['trainee'])], url_path='un-enroll/(?P<enrollment_pk>\d+)')
    def delete_my_enrollment(self, request, pk=None, enrollment_pk=None):
        try:
            course = CourseValidator.validate_course_exists(pk)
            enrollment = CourseValidator.validate_enrollment_exists(enrollment_pk)
            CourseValidator.validate_enrollment_belongs_to_course(enrollment, course)
            CourseValidator.validate_enrollment_belongs_to_trainee(enrollment, request.user.trainee_profile)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        enrollment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

