from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError

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
    
    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)
    
    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)


class LessonSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonSection
        fields = "__all__"
    
    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)
    
    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)

class CourseEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseEnrollment
        fields = "__all__"
        read_only_fields = ("enrollment_date",)
