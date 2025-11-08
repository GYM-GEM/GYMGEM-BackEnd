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
from drf_spectacular.utils import extend_schema, extend_schema_view

# Create your views here.
class CoursesView(ViewSet):
    serializer_class = CourseSerializer
    queryset = Course.objects.all()

    @extend_schema(
        tags=['Courses'],
        summary='Get courses for trainees',
        description='Get all available courses for trainees to browse',
        responses={200: CourseSerializer(many=True)}
    )
    @action(methods=['get'], detail=False, permission_classes=[IsAuthenticated], url_path='for-trainees')
    def get_courses_for_trainees(self, request):
        courses = Course.objects.all()
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=['Courses'],
        summary='Create new course',
        description='Create a new course (trainer only)',
        request=CourseSerializer,
        responses={201: CourseSerializer, 400: {'description': 'Validation error'}}
    )
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

    @extend_schema(
        tags=['Courses'],
        summary='Update course',
        description='Update an existing course (trainer only, must own the course)',
        request=CourseSerializer,
        responses={200: CourseSerializer, 400: {'description': 'Validation error'}, 404: {'description': 'Course not found'}}
    )
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

    @extend_schema(
        tags=['Courses'],
        summary='Delete course',
        description='Delete an existing course (trainer only, must own the course)',
        responses={204: {'description': 'Course deleted'}, 404: {'description': 'Course not found'}}
    )
    @action(methods=['delete'], detail=True, permission_classes=[HasRole(['trainer'])], url_path='delete')
    def delete_course(self, request, pk=None):
        try:
            course = CourseValidator.validate_course_exists(pk)
            CourseValidator.validate_course_belongs_to_trainer(course, request.user.trainer_profile)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        course.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @extend_schema(
        tags=['Courses'],
        summary='Get course detail',
        description='Get detailed information about a specific course',
        responses={200: CourseSerializer, 404: {'description': 'Course not found'}}
    )
    @action(methods=['get'], detail=True, permission_classes=[IsAuthenticated], url_path='detail')
    def get_course_detail(self, request, pk=None):
        try:
            course = CourseValidator.validate_course_exists(pk)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = CourseSerializer(course)
        return Response(serializer.data)

class LessonsView(ViewSet):
    serializer_class = CourseLessonSerializer
    queryset = Course.objects.all()
    
    @extend_schema(
        tags=['Course Lessons'],
        summary='Get lessons for course',
        description='Get all lessons for a specific course',
        responses={200: CourseLessonSerializer(many=True), 404: {'description': 'Course not found'}}
    )
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

    @extend_schema(
        tags=['Course Lessons'],
        summary='Create lesson for course',
        description='Create a new lesson for a specific course (trainer only, must own the course)',
        request=CourseLessonSerializer,
        responses={201: CourseLessonSerializer, 400: {'description': 'Validation error'}, 404: {'description': 'Course not found'}}
    )
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

    @extend_schema(
        tags=['Course Lessons'],
        summary='Update lesson for course',
        description='Update an existing lesson (trainer only, must own the course)',
        request=CourseLessonSerializer,
        responses={200: CourseLessonSerializer, 400: {'description': 'Validation error'}, 404: {'description': 'Lesson or course not found'}}
    )
    @action(methods=['put'], detail=True, permission_classes=[HasRole(['trainer'])], url_path=r'lessons/update/(?P<lesson_pk>\d+)')
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

    @extend_schema(
        tags=['Course Lessons'],
        summary='Delete lesson for course',
        description='Delete an existing lesson (trainer only, must own the course)',
        responses={204: {'description': 'Lesson deleted'}, 404: {'description': 'Lesson or course not found'}}
    )
    @action(methods=['delete'], detail=True, permission_classes=[HasRole(['trainer'])], url_path=r'lessons/delete/(?P<lesson_pk>\d+)')
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
    
    @extend_schema(
        tags=['Course Lessons'],
        summary='Get lesson detail',
        description='Get detailed information about a specific lesson',
        responses={200: CourseLessonSerializer, 404: {'description': 'Lesson or course not found'}}
    )
    @action(methods=['get'], detail=True, permission_classes=[IsAuthenticated], url_path=r'lessons/detail/(?P<lesson_pk>\d+)')
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
    serializer_class = LessonSectionSerializer
    queryset = Course.objects.all()  # Using Course as base since pk refers to lesson
    
    @extend_schema(
        tags=['Lesson Sections'],
        summary='Get sections for lesson',
        description='Get all sections for a specific lesson',
        responses={200: LessonSectionSerializer(many=True), 404: {'description': 'Lesson not found'}}
    )
    @action(methods=['get'], detail=True, permission_classes=[IsAuthenticated], url_path='sections')
    def get_sections_for_lesson(self, request, pk=None):
        try:
            lesson = CourseValidator.validate_lesson_exists(pk)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        sections = lesson.sections.all()
        serializer = LessonSectionSerializer(sections, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Lesson Sections'],
        summary='Get section detail',
        description='Get detailed information about a specific section',
        responses={200: LessonSectionSerializer, 404: {'description': 'Section or lesson not found'}}
    )
    @action(methods=['get'], detail=True, permission_classes=[IsAuthenticated], url_path=r'section/(?P<section_pk>\d+)')
    def get_section_detail(self, request, pk=None, section_pk=None):
        try:
            lesson = CourseValidator.validate_lesson_exists(pk)
            section = CourseValidator.validate_section_exists(section_pk)
            CourseValidator.validate_section_belongs_to_lesson(section, lesson)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = LessonSectionSerializer(section)
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Lesson Sections'],
        summary='Create section for lesson',
        description='Create a new section for a specific lesson (trainer only)',
        request=LessonSectionSerializer,
        responses={201: LessonSectionSerializer, 400: {'description': 'Validation error'}, 404: {'description': 'Lesson not found'}}
    )
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

    @extend_schema(
        tags=['Lesson Sections'],
        summary='Update section for lesson',
        description='Update an existing section (trainer only)',
        request=LessonSectionSerializer,
        responses={200: LessonSectionSerializer, 400: {'description': 'Validation error'}, 404: {'description': 'Section or lesson not found'}}
    )
    @action(methods=['put'], detail=True, permission_classes=[HasRole(['trainer'])], url_path=r'sections/update/(?P<section_pk>\d+)')
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

    @extend_schema(
        tags=['Lesson Sections'],
        summary='Delete section for lesson',
        description='Delete an existing section (trainer only)',
        responses={204: {'description': 'Section deleted'}, 404: {'description': 'Section or lesson not found'}}
    )
    @action(methods=['delete'], detail=True, permission_classes=[HasRole(['trainer'])], url_path=r'sections/delete/(?P<section_pk>\d+)')
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
    serializer_class = CourseEnrollmentSerializer
    queryset = Course.objects.all()
    
    @extend_schema(
        tags=['Course Enrollments'],
        summary='Enroll in course',
        description='Enroll in a specific course (trainee only)',
        request=CourseEnrollmentSerializer,
        responses={201: CourseEnrollmentSerializer, 400: {'description': 'Validation error'}, 404: {'description': 'Course not found'}}
    )
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

    @extend_schema(
        tags=['Course Enrollments'],
        summary='Get enrollments for course',
        description='Get all enrollments for a specific course (trainer only, must own the course)',
        responses={200: CourseEnrollmentSerializer(many=True), 404: {'description': 'Course not found'}}
    )
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

    @extend_schema(
        tags=['Course Enrollments'],
        summary='Get my enrollments for course',
        description='Get my enrollments for a specific course (trainee only)',
        responses={200: CourseEnrollmentSerializer(many=True)}
    )
    @action(methods=['get'], detail=True, permission_classes=[HasRole(['trainee'])], url_path='my-enrollments')
    def get_my_enrollments(self, request, pk=None):
        enrollments = CourseEnrollment.objects.filter(course__id=pk, trainee_profile=request.user.trainee_profile)
        serializer = CourseEnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=['Course Enrollments'],
        summary='Get my enrollment detail',
        description='Get detailed information about my specific enrollment (trainee only)',
        responses={200: CourseEnrollmentSerializer, 404: {'description': 'Enrollment or course not found'}}
    )
    @action(methods=['get'], detail=True, permission_classes=[HasRole(['trainee'])], url_path=r'my-enrollment-detail/(?P<enrollment_pk>\d+)')
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

    @extend_schema(
        tags=['Course Enrollments'],
        summary='Un-enroll from course',
        description='Delete my enrollment from a course (trainee only)',
        responses={204: {'description': 'Enrollment deleted'}, 404: {'description': 'Enrollment or course not found'}}
    )
    @action(methods=['delete'], detail=True, permission_classes=[HasRole(['trainee'])], url_path=r'un-enroll/(?P<enrollment_pk>\d+)')
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
    

