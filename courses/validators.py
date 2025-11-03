from accounts.models import Account
from .models import Course, CourseEnrollment, CourseLesson, LessonSection

class CourseValidator:
    @staticmethod
    def validate_course_exists(course_id):
        try:
            return Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            raise ValueError("Course with the given ID does not exist.")
    
    @staticmethod
    def validate_course_belongs_to_trainer(course, trainer_profile):
        if course.trainer_profile != trainer_profile:
            raise ValueError("The course does not belong to the specified trainer profile.")
    
    @staticmethod
    def validate_trainer_profile_belongs_to_user(trainer_profile, user):
        """
        Validates that the given trainer profile belongs to the specified user.
        trainer_profile can be either a Profile object or an ID (int).
        """
        account = Account.objects.filter(pk=user.pk).first()
        if not account:
            raise ValueError("User account does not exist.")
        
        # Handle both Profile object and ID
        profile_id = trainer_profile.pk if hasattr(trainer_profile, 'pk') else trainer_profile
        
        profile_exists = account.profiles.filter(
            pk=profile_id,
            profile_type='trainer'
        ).exists()
        
        if not profile_exists:
            raise ValueError("The trainer profile does not belong to the requested user.")
    
    @staticmethod
    def validate_trainee_profile_belongs_to_user(trainee_profile, user):
        """
        Validates that the given trainee profile belongs to the specified user.
        trainee_profile can be either a Profile object or an ID (int).
        """
        account = Account.objects.filter(pk=user.pk).first()
        if not account:
            raise ValueError("User account does not exist.")
        
        # Handle both Profile object and ID
        profile_id = trainee_profile.pk if hasattr(trainee_profile, 'pk') else trainee_profile
        
        profile_exists = account.profiles.filter(
            pk=profile_id,
            profile_type='trainee'
        ).exists()
        
        if not profile_exists:
            raise ValueError("The trainee profile does not belong to the requested user.")
        
    @staticmethod
    def validate_lesson_exists(lesson_id):
        try:
            return CourseLesson.objects.get(id=lesson_id)
        except CourseLesson.DoesNotExist:
            raise ValueError("Lesson with the given ID does not exist.")
    
    @staticmethod
    def validate_lesson_belongs_to_course(lesson, course):
        if lesson.course != course:
            raise ValueError("The lesson does not belong to the specified course.") 

    @staticmethod
    def validate_enrollment_exists(enrollment_id):
        try:
            return CourseEnrollment.objects.get(id=enrollment_id)
        except CourseEnrollment.DoesNotExist:
            raise ValueError("Enrollment with the given ID does not exist.")
    @staticmethod
    def validate_lesson_belongs_to_trainer(lesson, trainer_profile):
        if lesson.course.trainer_profile != trainer_profile:
            raise ValueError("The lesson does not belong to the specified trainer profile.")
    
    @staticmethod
    def validate_enrollment_belongs_to_trainee(enrollment, trainee_profile):
        if enrollment.trainee_profile != trainee_profile:
            raise ValueError("The enrollment does not belong to the specified trainee profile.")
        
    @staticmethod
    def validate_section_exists(section_id):
        try:
            return LessonSection.objects.get(id=section_id)
        except LessonSection.DoesNotExist:
            raise ValueError("Section with the given ID does not exist.")

    @staticmethod
    def validate_enrollment_belongs_to_course(enrollment, course):
        if enrollment.course != course:
            raise ValueError("The enrollment does not belong to the specified course.")
        
    @staticmethod
    def validate_section_belongs_to_lesson(section, lesson):
        if section.lesson != lesson:
            raise ValueError("The section does not belong to the specified lesson.")
        