from rest_framework import serializers

from courses.models import (
    Course,
    CourseLesson,
    LessonSection,
    CourseEnrollment,
)
from profiles.models import Profile
from trainees.models import Trainee


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")

    # def validate_trainer_profile(self, value: Profile) -> Profile:
    #     if value.profile_type != "trainer":
    #         raise serializers.ValidationError("trainer_profile must reference a trainer profile.")
    #     return value


class CourseLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseLesson
        fields = "__all__"


class LessonSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonSection
        fields = "__all__"

    # def validate(self, attrs):
    #     content_type = attrs.get("content_type")
    #     content_url = attrs.get("content_url")
    #     content_text = attrs.get("content_text")

    #     if content_type == "video" and not content_url:
    #         raise serializers.ValidationError({"content_url": "Video sections must include content_url."})
    #     if content_type == "article" and not content_text:
    #         raise serializers.ValidationError({"content_text": "Article sections must include content_text."})
    #     if content_type == "quiz" and not content_text:
    #         raise serializers.ValidationError({"content_text": "Quiz sections must include content_text."})

    #     return attrs



class CourseEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseEnrollment
        fields = "__all__"
        read_only_fields = ("enrollment_date",)

    # def validate_trainee_profile(self, value: Trainee) -> Trainee:
    #     profile = getattr(value, "profile_id", None)
    #     if profile is None or profile.profile_type != "trainee":
    #         raise serializers.ValidationError("trainee_profile must reference a trainee profile.")
    #     return value
