from django.contrib import admin
from .models import Specialization, Certification, Category, Language, Level
# Register your models here.
admin.site.register(Specialization)
admin.site.register(Certification)
admin.site.register(Category)
admin.site.register(Language)
admin.site.register(Level)