from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError

from courses.models import (
    Course,
    CourseLesson,
    LessonSection,
    CourseEnrollment,
    CourseProgress,
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
    trainee_name = serializers.SerializerMethodField()
    trainee_profile_picture = serializers.SerializerMethodField()
    class Meta:
        model = CourseEnrollment
        fields = "__all__"
        read_only_fields = ("enrollment_date",)

    def get_trainee_name(self, obj):
        try:
            return getattr(getattr(obj.trainee_profile, 'trainee', None), 'name', None)
        except Exception:
            return None

    def get_trainee_profile_picture(self, obj):
        try:
            return getattr(getattr(obj.trainee_profile, 'trainee', None), 'profile_picture', None)
        except Exception:
            return None

class CourseProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseProgress
        fields = "__all__"
        extra_kwargs = {
            'completed_at': {'read_only': True},
        }
    
    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        
    