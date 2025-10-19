from django.contrib import admin
from .models import Gym,GymBranch,GymSlot, Service,Package,GymService
# Register your models here.
admin.site.register(Gym)
admin.site.register(GymBranch)
admin.site.register(GymSlot)
admin.site.register(Service)
admin.site.register(Package)
admin.site.register(GymService)
