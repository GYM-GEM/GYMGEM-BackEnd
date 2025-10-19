from django.contrib import admin
from .models import Item, Size,Store,StoreBranch
admin.site.register(Size)
admin.site.register(Store)
admin.site.register(StoreBranch)
admin.site.register(Item)
# Register your models here.
