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
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    cover = models.URLField(blank=True, null=True)
    duration = models.DurationField()
    status = models.CharField(max_length=20, choices=[('draft', 'Draft'), ('published', 'Published')], default='draft')
    order = models.PositiveIntegerField()

    def __str__(self):
        return f"Lesson {self.order}: {self.title} for Course {self.course.title}"
    
class LessonSection(models.Model):
    lesson = models.ForeignKey(CourseLesson, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=20, choices=[('video', 'Video'), ('article', 'Article'), ('quiz', 'Quiz'),
                                                            ('pdf', 'PDF'), ('image', 'Image'), ('audio', 'Audio'),
                                                            ('doc', 'Document'), ('ppt', 'PowerPoint'), ('other', 'Other')])
    content_url = models.URLField(blank=True, null=True)
    content_text = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField()

    def __str__(self):
        return f"Section {self.order}: {self.title} for Lesson {self.lesson.title}"
    
    
class CourseEnrollment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    trainee_profile = models.ForeignKey('trainees.Trainee', on_delete=models.CASCADE)
    enrollment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('in_progress', 'In Progress'), ('completed', 'Completed'), ('dropped', 'Dropped')], default='in_progress')
    rating = models.PositiveIntegerField(blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(100)])
    permanent_access = models.BooleanField(default=False)
    due_date = models.DateTimeField(blank=True, null=True)
    def __str__(self):
        return f"Enrollment of {self.trainee_profile} in Course {self.course.title}"