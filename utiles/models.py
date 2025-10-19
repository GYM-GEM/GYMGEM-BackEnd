from django.db import models

# Create your models here.
class Status_types(models.TextChoices):
    USER = 'user', 'User'
    COURSE = 'course', 'Course'
    GYM = 'gym', 'Gym'
    STORE = 'store', 'Store'
    INVOICE = 'invoice', 'Invoice'
    # to be continued...


class Status(models.Model):
    id = models.SmallAutoField(primary_key=True)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=255, null=True, blank=True)
    type = models.CharField(max_length=10, choices=Status_types.choices, default=Status_types.USER)

    class Meta:
        db_table = 'status'
        constraints = [
            models.CheckConstraint(
                check=models.Q(type__in=[c.value for c in Status_types]),
                name='status_type_valid'
            )
        ]
    def __str__(self) -> str:
        return self.name
class Category_types(models.TextChoices):
    COURSE = 'course', 'Course'
    ITEM = 'item', 'Item'
    # to be continued...
class Category(models.Model):
    id = models.SmallAutoField(primary_key=True)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=255, null=True, blank=True)
    type = models.CharField(max_length=10, choices=Category_types.choices, default=Category_types.COURSE)
    class Meta:
        db_table = 'categories'

    def __str__(self) -> str:
        return self.name
    
    