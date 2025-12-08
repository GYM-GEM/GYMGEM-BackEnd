from django.db.models import Q, Prefetch
from django.db import models
from rest_framework.viewsets import ViewSet
from profiles.models import Profile
from trainees.models import Trainee
from utils.views import get_profile_id_from_token
from .models import Course, CourseLesson, LessonSection
from .serializers import (
    CourseLessonSerializer,
    CourseSerializer,
    CourseEnrollmentSerializer,
    CourseEnrollment,
    LessonSectionSerializer,
)
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from authenticationAndAuthorization.permissions import HasRole
from .validators import CourseValidator
from drf_spectacular.utils import extend_schema
from trainers.models import Trainer
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Sum, Count, Avg

# Create your views here.
class CoursesView(ViewSet):
    serializer_class = CourseSerializer
    queryset = Course.objects.all()

    @extend_schema(
        tags=["Courses"],
        summary="Get courses for trainees",
        description="Get all available courses for trainees to browse",
        responses={200: CourseSerializer(many=True)},
    )
    @action(
        methods=["get"],
        detail=False,
        permission_classes=[HasRole(["trainee"])],
        url_path="for-trainees",
    )
    def get_courses_for_trainees(self, request):
        params = request.query_params

        queryset = Course.objects.filter(status="published").select_related(
            'trainer_profile', 'category', 'level', 'language'
        )

        if params.get("category"):
            queryset = queryset.filter(category=params["category"])

        if params.get("level"):
            queryset = queryset.filter(level=params["level"])

        if params.get("language"):
            queryset = queryset.filter(language=params["language"])

        price_min = params.get("price_min")
        price_max = params.get("price_max")

        if price_min:
            queryset = queryset.filter(price__gte=price_min)

        if price_max:
            queryset = queryset.filter(price__lte=price_max)

        if params.get("trainer_profile"):
            queryset = queryset.filter(trainer_profile=params["trainer_profile"])

        if params.get("search"):
            s = params["search"]
            queryset = queryset.filter(
                Q(title__icontains=s) | Q(description__icontains=s)
            )

        if params.get("ordering"):
            queryset = queryset.order_by(params["ordering"])

        # Annotate courses with aggregated data in a single query
        queryset = queryset.annotate(
            total_duration=Sum('lessons__duration'),
            lesson_count=Count('lessons', distinct=True),
            average_rating=Avg('courseenrollment__rating', filter=models.Q(courseenrollment__status='completed')),
            total_ratings=Count('courseenrollment__rating', filter=models.Q(courseenrollment__rating__isnull=False), distinct=True),
            students_enrolled=Count('courseenrollment__trainee_profile', distinct=True)
        )
        
        # Serialize courses
        courses_data = CourseSerializer(queryset, many=True).data

        # Fetch trainer names in a single query
        trainer_profile_ids = [course["trainer_profile"] for course in courses_data]
        trainer_map = {
            trainer.profile_id_id: trainer.name
            for trainer in Trainer.objects.filter(profile_id__in=trainer_profile_ids).only('profile_id', 'name')
        }

        # Create a mapping of annotated data to each course ID
        annotated_data = {
            course.id: {
                'total_duration': course.total_duration or 0,
                'lesson_count': course.lesson_count or 0,
                'average_rating': course.average_rating,
                'total_ratings': course.total_ratings or 0,
                'students_enrolled': course.students_enrolled or 0,
            }
            for course in queryset
        }

        # Attach computed data to each course
        for course in courses_data:
            course_id = course["id"]
            profile_id = course["trainer_profile"]
            
            # Add trainer name
            course["trainer_profile_name"] = trainer_map.get(profile_id, "Unknown Trainer")
            
            # Add annotated fields
            if course_id in annotated_data:
                course.update(annotated_data[course_id])

        return Response(courses_data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Courses"],
        summary="Get courses of a trainer",
        description="Get all courses created by the logged-in trainer",
        responses={200: CourseSerializer(many=True)},
    )
    @action(
        methods=["get"],
        detail=False,
        permission_classes=[HasRole(["trainer"])],
        url_path="my-courses",
    )
    def get_courses_of_trainer(self, request):
        
        profile_id = get_profile_id_from_token(request)
        try:
            trainer_profile = Profile.objects.get(pk=profile_id)
        except Profile.DoesNotExist:
            return Response({"error": "Trainer profile not found."}, status=status.HTTP_404_NOT_FOUND)
        
        queryset = Course.objects.filter(
            trainer_profile=trainer_profile
        ).select_related(
            'trainer_profile',
            'category',
            'level',
            'language'
        ).annotate(
            total_duration=Sum('lessons__duration'),
            lesson_count=Count('lessons', distinct=True),
            average_rating=Avg('courseenrollment__rating', filter=models.Q(courseenrollment__status='completed')),
            students_enrolled=Count('courseenrollment__trainee_profile', distinct=True)
        )
        serializer = CourseSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Courses"],
        summary="Create new course",
        description="Create a new course (trainer only)",
        request=CourseSerializer,
        responses={201: CourseSerializer, 400: {"description": "Validation error"}},
    )
    @action(
        methods=["post"],
        detail=False,
        permission_classes=[HasRole(["trainer"])],
        url_path="create",
    )
    def create_course(self, request):
        profile_id = get_profile_id_from_token(request)
        trainer_profile = Profile.objects.get(pk=profile_id)
        serializer = CourseSerializer(data={**request.data, "trainer_profile": trainer_profile.pk})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Courses"],
        summary="Update course",
        description="Update an existing course (trainer only, must own the course)",
        request=CourseSerializer,
        responses={
            200: CourseSerializer,
            400: {"description": "Validation error"},
            404: {"description": "Course not found"},
        },
    )
    @action(
        methods=["put"],
        detail=True,
        permission_classes=[HasRole(["trainer"])],
        url_path="update",
    )
    def update_course(self, request, pk=None):
        try:
            
            course = CourseValidator.validate_course_exists(pk)
            CourseValidator.validate_course_belongs_to_trainer(
                course, request
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = CourseSerializer(course, data={**request.data, "trainer_profile": course.trainer_profile.pk})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Courses"],
        summary="Delete course",
        description="Delete an existing course (trainer only, must own the course)",
        responses={
            204: {"description": "Course deleted"},
            404: {"description": "Course not found"},
        },
    )
    @action(
        methods=["delete"],
        detail=True,
        permission_classes=[HasRole(["trainer"])],
        url_path="delete",
    )
    def delete_course(self, request, pk=None):
        try:
            course = CourseValidator.validate_course_exists(pk)
            CourseValidator.validate_course_belongs_to_trainer(
                course, request
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        course.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=["Courses"],
        summary="Get course detail",
        description="Get detailed information about a specific course with all lessons and sections",
        responses={200: CourseSerializer, 404: {"description": "Course not found"}},
    )
    @action(
        methods=["get"],
        detail=True,
        permission_classes=[HasRole(["trainee", "trainer"])],
        url_path="detail",
    )
    def get_course_detail(self, request, pk=None):
        try:
            # Fetch course with all related data in one go
            course = Course.objects.select_related(
                'trainer_profile',
                'category',
                'level',
                'language'
            ).prefetch_related(
                Prefetch(
                    'lessons',
                    queryset=CourseLesson.objects.prefetch_related(
                        Prefetch(
                            'sections',
                            queryset=LessonSection.objects.order_by('order', 'id')
                        )
                    ).order_by("order", "id")
                )
            ).get(pk=pk)
        except Course.DoesNotExist:
            return Response(
                {"error": f"Course with id {pk} does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )

        trainee_id = get_profile_id_from_token(request)
        enrollment = CourseEnrollment.objects.filter(
            course=course,
            trainee_profile=trainee_id
        ).first()

        course_data = CourseSerializer(course).data

        # Use prefetched lessons (no additional query)
        lessons = course.lessons.all()
        course_data["lessons"] = CourseLessonSerializer(lessons, many=True).data

        if not enrollment and course.trainer_profile.pk != trainee_id:
            course_data["lessons_details"] = []
        elif enrollment.status in ["in_progress", "completed"] or course.trainer_profile.pk == trainee_id:
            lessons_details = []
            for lesson in lessons:
                lesson_data = CourseLessonSerializer(lesson).data
                # Use prefetched sections (no additional query)
                lesson_data["sections"] = LessonSectionSerializer(
                    lesson.sections.all().order_by("order", "id"),
                    many=True
                ).data
                lessons_details.append(lesson_data)

            course_data["lessons_details"] = lessons_details

        # Ratings
        rating_stats = CourseEnrollment.objects.filter(
            course=course,
            status="completed",
            rating__isnull=False
        ).aggregate(
            average_rating=models.Avg("rating"),
            total_ratings=models.Count("rating")
        )
        course_data["ratings"] = rating_stats

        # Total duration - aggregate in single query
        total_duration = CourseLesson.objects.filter(
            course=course
        ).aggregate(total=Sum('duration'))['total']
        
        course_data["total_duration"] = (
            int(total_duration.total_seconds()) if total_duration else 0
        )

        # Students enrolled
        students_count = Trainee.objects.filter(
            profile_id__in=CourseEnrollment.objects.filter(
                course=course
            ).values_list("trainee_profile_id", flat=True)
        ).distinct().count()

        course_data["students_enrolled"] = students_count

        return Response(course_data)

class LessonsView(ViewSet):
    serializer_class = CourseLessonSerializer
    queryset = Course.objects.all()

    @extend_schema(
        tags=["Course Lessons"],
        summary="Get lessons for course",
        description="Get all lessons for a specific course",
        responses={
            200: CourseLessonSerializer(many=True),
            404: {"description": "Course not found"},
        },
    )
    @action(
        methods=["get"],
        detail=True,
        permission_classes=[HasRole(["trainee", "trainer"])],
        url_path="list",
    )
    def get_lessons_for_course(self, request, pk=None):
        try:
            course = CourseValidator.validate_course_exists(pk)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        try:
            lessons = CourseLesson.objects.filter(
                course=course
            ).select_related('course').order_by('order')
            serializer = CourseLessonSerializer(lessons, many=True)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["Course Lessons"],
        summary="Create lesson for course",
        description="Create a new lesson for a specific course (trainer only, must own the course)",
        request=CourseLessonSerializer,
        responses={
            201: CourseLessonSerializer,
            400: {"description": "Validation error"},
            404: {"description": "Course not found"},
        },
    )
    @action(
        methods=["post"],
        detail=True,
        permission_classes=[HasRole(["trainer"])],
        url_path="create",
    )
    def create_lesson_for_course(self, request, pk=None):
        try:
            course = CourseValidator.validate_course_exists(pk)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        try:
            CourseValidator.validate_course_belongs_to_trainer(course, request)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CourseLessonSerializer(
            data={**request.data, **{"course": course.pk}}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Course Lessons"],
        summary="Update lesson for course",
        description="Update an existing lesson (trainer only, must own the course)",
        request=CourseLessonSerializer,
        responses={
            200: CourseLessonSerializer,
            400: {"description": "Validation error"},
            404: {"description": "Lesson or course not found"},
        },
    )
    @action(
        methods=["put"],
        detail=True,
        permission_classes=[HasRole(["trainer"])],
        url_path="update",
    )
    def update_lesson_for_course(self, request, pk=None):
        try:
            
            lesson = CourseValidator.validate_lesson_exists(pk)
            course = lesson.course
            CourseValidator.validate_course_belongs_to_trainer(
                course, request
            )
            CourseValidator.validate_lesson_belongs_to_course(lesson, course)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = CourseLessonSerializer(lesson, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Course Lessons"],
        summary="Delete lesson for course",
        description="Delete an existing lesson (trainer only, must own the course)",
        responses={
            204: {"description": "Lesson deleted"},
            404: {"description": "Lesson or course not found"},
        },
    )
    @action(
        methods=["delete"],
        detail=True,
        permission_classes=[HasRole(["trainer"])],
        url_path="delete",
    )
    def delete_lesson_for_course(self, request, pk=None):
        try:
            
            lesson = CourseValidator.validate_lesson_exists(pk)
            course = lesson.course
            CourseValidator.validate_course_belongs_to_trainer(
                course, request
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        lesson.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=["Course Lessons"],
        summary="Get lesson detail",
        description="Get detailed information about a specific lesson",
        responses={
            200: CourseLessonSerializer,
            404: {"description": "Lesson or course not found"},
        },
    )
    @action(
        methods=["get"],
        detail=True,
        permission_classes=[HasRole(["trainee", "trainer"])],
        url_path="detail",
    )
    def get_lesson_detail(self, request, pk=None):
        try:
            lesson = CourseValidator.validate_lesson_exists(pk)
            course = lesson.course
            CourseValidator.validate_lesson_belongs_to_course(lesson, course)
            sections = LessonSection.objects.filter(lesson=lesson).order_by('order')
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = CourseLessonSerializer(lesson)
        return Response({"lesson": serializer.data, "sections": LessonSectionSerializer(sections, many=True).data})

class LessonSectionsView(ViewSet):
    serializer_class = LessonSectionSerializer
    queryset = Course.objects.all()  # Using Course as base since pk refers to lesson

    @extend_schema(
        tags=["Lesson Sections"],
        summary="Get sections for lesson",
        description="Get all sections for a specific lesson",
        responses={
            200: LessonSectionSerializer(many=True),
            404: {"description": "Lesson not found"},
        },
    )
    @action(
        methods=["get"],
        detail=True,
        permission_classes=[HasRole(["trainee", "trainer"])],
        url_path="list",
    )
    def get_sections_for_lesson(self, request, pk=None):
        try:
            lesson = CourseValidator.validate_lesson_exists(pk)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        sections = lesson.lessonsection_set.all().order_by('order')
        serializer = LessonSectionSerializer(sections, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Lesson Sections"],
        summary="Get section detail",
        description="Get detailed information about a specific section",
        responses={
            200: LessonSectionSerializer,
            404: {"description": "Section or lesson not found"},
        },
    )
    @action(
        methods=["get"],
        detail=True,
        permission_classes=[HasRole(["trainee", "trainer"])],
        url_path="detail",
    )
    def get_section_detail(self, request, pk=None):
        try:
            section = CourseValidator.validate_section_exists(pk)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = LessonSectionSerializer(section)
        return Response(serializer.data)

    @extend_schema(
        tags=["Lesson Sections"],
        summary="Create section for lesson",
        description="Create a new section for a specific lesson (trainer only)",
        request=LessonSectionSerializer,
        responses={
            201: LessonSectionSerializer,
            400: {"description": "Validation error"},
            404: {"description": "Lesson not found"},
        },
    )
    @action(
        methods=["post"],
        detail=False,
        permission_classes=[HasRole(["trainer"])],
        url_path="create",
    )
    def create_section_for_lesson(self, request):
        try:
            lesson = CourseValidator.validate_lesson_exists(request.data.get("lesson"))
            CourseValidator.validate_lesson_belongs_to_trainer(lesson, request)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = LessonSectionSerializer(
            data={**request.data, **{"lesson": lesson.pk}}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Lesson Sections"],
        summary="Update section for lesson",
        description="Update an existing section (trainer only)",
        request=LessonSectionSerializer,
        responses={
            200: LessonSectionSerializer,
            400: {"description": "Validation error"},
            404: {"description": "Section or lesson not found"},
        },
    )
    @action(
        methods=["put"],
        detail=True,
        permission_classes=[HasRole(["trainer"])],
        url_path="update",
    )
    def update_section_for_lesson(self, request, pk=None):
        try:
 
            section = CourseValidator.validate_section_exists(pk)
            CourseValidator.validate_lesson_belongs_to_trainer(
                section.lesson, request
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = LessonSectionSerializer(section, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Lesson Sections"],
        summary="Delete section for lesson",
        description="Delete an existing section (trainer only)",
        responses={
            204: {"description": "Section deleted"},
            404: {"description": "Section or lesson not found"},
        },
    )
    @action(
        methods=["delete"],
        detail=True,
        permission_classes=[HasRole(["trainer"])],
        url_path="delete",
    )
    def delete_section_for_lesson(self, request, pk=None):
        try:
            section = CourseValidator.validate_section_exists(pk)
            CourseValidator.validate_lesson_belongs_to_trainer(
                section.lesson, request
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        section.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CourseEnrollmentsView(ViewSet):
    serializer_class = CourseEnrollmentSerializer
    queryset = Course.objects.all()

    @extend_schema(
        tags=["Course Enrollments"],
        summary="Enroll in course",
        description="Enroll in a specific course (trainee only)",
        request=CourseEnrollmentSerializer,
        responses={
            201: CourseEnrollmentSerializer,
            400: {"description": "Validation error"},
            404: {"description": "Course not found"},
        },
    )
    @action(
        methods=["post"],
        detail=True,
        permission_classes=[HasRole(["trainee"])],
        url_path="enroll",
    )
    def enroll_in_course(self, request, pk=None):
        try:
            course = CourseValidator.validate_course_exists(pk)
            profile = get_profile_id_from_token(request)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = CourseEnrollmentSerializer(data={**request.data, "trainee_profile": profile, "course": course.pk})
        if serializer.is_valid():
            serializer.save(course=course)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Course Enrollments"],
        summary="add course to wishlist",
        description="Add a specific course to wishlist (trainee only)",
        request=CourseEnrollmentSerializer,
        responses={
            201: CourseEnrollmentSerializer,
            400: {"description": "Validation error"},
            404: {"description": "Course not found"},
        },
    )
    @action(
        methods=["post"],
        detail=True,
        permission_classes=[HasRole(["trainee"])],
        url_path="add-to-wishlist",
    )
    def add_course_to_wishlist(self, request, pk=None):
        try:
            course = CourseValidator.validate_course_exists(pk)
            profile = get_profile_id_from_token(request)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = CourseEnrollmentSerializer(data={**request.data, "trainee_profile": profile, "course": course.pk, "status": "wishlist"})
        if serializer.is_valid():
            serializer.save(course=course)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        tags=["Course Enrollments"],
        summary="Get enrollments for course",
        description="Get all enrollments for a specific course (trainer only, must own the course)",
        responses={
            200: CourseEnrollmentSerializer(many=True),
            404: {"description": "Course not found"},
        },
    )
    @action(
        methods=["get"],
        detail=True,
        permission_classes=[HasRole(["trainer"])],
        url_path="trainer-enrollments",
    )
    def get_enrollments_for_course(self, request, pk=None):
        try:
            course = CourseValidator.validate_course_exists(pk)
            CourseValidator.validate_course_belongs_to_trainer(
                course, request
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    
        enrollments = course.enrollments.all().select_related(
            'trainee_profile',
            'trainee_profile__account',
            'course'
        )
        serializer = CourseEnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        tags=["Course Enrollments"],
        summary="Get enrollments for trainee",
        description="Get all enrollments for the logged-in trainee",
        responses={200: CourseEnrollmentSerializer(many=True)},
    )
    @action(
        methods=["get"],
        detail=False,
        permission_classes=[HasRole(["trainee"])],
        url_path="my-enrollments",
    )
    def get_enrollments_for_trainee(self, request):
        try:
            profile_id = get_profile_id_from_token(request)
            trainee_profile = Profile.objects.get(pk=profile_id)
            CourseValidator.validate_trainee_profile_belongs_to_user(trainee_profile, request)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        enrollments = CourseEnrollment.objects.filter(
            trainee_profile=trainee_profile  
        ).select_related(
            'course',
            'course__trainer_profile',
            'course__category',
            'course__level',
            'course__language',
            'trainee_profile'
        )
        serializer = CourseEnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
        enrollments = CourseEnrollment.objects.filter(
            course__id=pk, trainee_profile=request.user.trainee_profile
        )
        serializer = CourseEnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)


    @extend_schema(
        tags=["Course Enrollments"],
        summary="Un-enroll from course",
        description="Delete my enrollment from a course (trainee only)",
        responses={
            204: {"description": "Enrollment deleted"},
            404: {"description": "Enrollment or course not found"},
        },
    )
    @action(
        methods=["delete"],
        detail=True,
        permission_classes=[HasRole(["trainee"])],
        url_path="delete-my-enrollment",
    )
    def delete_my_enrollment(self, request, pk=None):
        try:
            profile_id = get_profile_id_from_token(request)
            enrollment = CourseEnrollment.objects.get(
                pk=pk, trainee_profile=profile_id
            )
            if enrollment.status == "dropped":
                return Response(
                    {"error": "You have already dropped this enrollment."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            CourseValidator.validate_enrollment_belongs_to_trainee(
                enrollment, request
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        enrollment.status = "dropped"
        enrollment.save()
        return Response(status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Course Enrollments"],
        summary="rate course enrollment",
        description="Rate and review a completed course enrollment (trainee only)",
        request=CourseEnrollmentSerializer,
        responses={
            200: CourseEnrollmentSerializer,
            400: {"description": "Validation error"},
            404: {"description": "Enrollment not found"},
        },
    )
    @action(
        methods=["put"],
        detail=True,
        permission_classes=[HasRole(["trainee"])],
        url_path="rate-enrollment",
    )
    def rate_course_enrollment(self, request, pk=None):
        try:
            profile_id = get_profile_id_from_token(request)
            enrollment = CourseEnrollment.objects.get(
                pk=pk, trainee_profile=profile_id
            )
            CourseValidator.validate_enrollment_belongs_to_trainee(
                enrollment, request
            )
            enrollment.status = "completed"
            if enrollment.status != "completed":
                return Response(
                    {"error": "You can only rate completed enrollments."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = CourseEnrollmentSerializer(enrollment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)