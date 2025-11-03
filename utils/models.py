from django.db import models
from profiles.models import Profile

# Create your models here.
class Specialization(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

class Certification(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    issuing_organization = models.CharField(max_length=100)
    issue_date = models.DateField()
    expiration_date = models.DateField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Certification<{self.name}> from {self.issuing_organization}"

class Category(models.Model):
    name = models.CharField(max_length=100, default='General')
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

class Language(models.Model):
    name = models.CharField(max_length=100, unique=True,default='English')
    code = models.CharField(max_length=10, primary_key = True ,default='EN')

    def __str__(self):
        return self.name
    
class Level(models.Model):
    name = models.CharField(max_length=100, choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')])
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name