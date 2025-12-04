from rest_framework import serializers

from courses.models import (
    Course,
    CourseLesson,
    LessonSection,
    CourseEnrollment,
)

class CourseSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Course
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")

class CourseLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseLesson
        fields = "__all__"


class LessonSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonSection
        fields = "__all__"

class CourseEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseEnrollment
        fields = "__all__"
        read_only_fields = ("enrollment_date",)
