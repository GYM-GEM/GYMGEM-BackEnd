from django.contrib import admin
from .models import Store,StoreBranch,StoreItemSize,StoreItemInventory,StoreItem,Order,OrderItem,InventoryLog
# Register your models here.
admin.site.register(Store)
admin.site.register(StoreBranch)
admin.site.register(StoreItemSize)
admin.site.register(StoreItemInventory)     
admin.site.register(StoreItem)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(InventoryLog)
