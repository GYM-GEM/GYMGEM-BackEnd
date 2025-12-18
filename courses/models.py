from django.utils import timezone 
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
# Create your models here.

class Course(models.Model):

    trainer_profile = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    category = models.ForeignKey('utils.Category', on_delete=models.SET_NULL, null=True)
    level = models.ForeignKey('utils.Level', on_delete=models.SET_NULL, null=True)
    language = models.ForeignKey('utils.Language', on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    cover = models.URLField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[('draft', 'Draft'), ('published', 'Published')], default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField()
    preview_video = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.title
    
class CourseLesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    cover = models.URLField(blank=True, null=True)
    duration = models.DurationField()
    status = models.CharField(max_length=20, choices=[('draft', 'Draft'), ('published', 'Published')], default='draft')
    order = models.PositiveIntegerField()
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.course and self.order:
            # Check if order is unique within the course (excluding current instance)
            duplicate = CourseLesson.objects.filter(
                course=self.course, 
                order=self.order
            ).exclude(pk=self.pk).exists()
            if duplicate:
                raise ValidationError({"order": "Order must be unique within the course."})
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Lesson {self.order}: {self.title} for Course {self.course.title}"
    
class LessonSection(models.Model):
    lesson = models.ForeignKey(CourseLesson, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=20, choices=[('video', 'Video'), ('article', 'Article'), ('quiz', 'Quiz'),
                                                            ('pdf', 'PDF'), ('image', 'Image'), ('audio', 'Audio'),
                                                            ('doc', 'Document'), ('ppt', 'PowerPoint'), ('other', 'Other')])
    content_url = models.URLField(blank=True, null=True)
    content_text = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField()
    
    # is_done = models.BooleanField(default=False)
    
    def clean(self):
        from django.core.exceptions import ValidationError
        errors = {}
        
        # Check if order is unique within the lesson (excluding current instance)
        if self.lesson and self.order:
            duplicate = LessonSection.objects.filter(
                lesson=self.lesson, 
                order=self.order
            ).exclude(pk=self.pk).exists()
            if duplicate:
                errors['order'] = "Order must be unique within the lesson."
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Section {self.order}: {self.title} for Lesson {self.lesson.title}"

class CourseProgress(models.Model):
    lesson_section = models.ForeignKey(LessonSection, on_delete=models.CASCADE)
    trainee_profile = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Progress of {self.trainee_profile} on Section {self.lesson_section.title}: {'Completed' if self.is_completed else 'Not Completed'}"
    
class CourseEnrollment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    trainee_profile = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE)
    enrollment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('in_progress', 'In Progress'), ('completed', 'Completed'), ('dropped', 'Dropped'),('wishlist', 'Wishlist')], default='in_progress')
    rating = models.PositiveIntegerField(blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(100)])
    review = models.TextField(blank=True, null=True)
    review_date = models.DateTimeField(blank=True, null=True)
    permanent_access = models.BooleanField(default=False)
    due_date = models.DateTimeField(blank=True, null=True)
    def save(self, *args, **kwargs):
        if not self.review_date:
            self.review_date = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Enrollment of {self.trainee_profile} in Course {self.course.title}"