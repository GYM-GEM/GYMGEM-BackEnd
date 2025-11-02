from django.contrib import admin
from .models import Trainer, TrainerSpecialization, TrainerCalendarSlot, TrainerExperience, TrainerRecord
# Register your models here.
admin.site.register(Trainer)
admin.site.register(TrainerSpecialization)
admin.site.register(TrainerCalendarSlot)
admin.site.register(TrainerExperience)
admin.site.register(TrainerRecord)
