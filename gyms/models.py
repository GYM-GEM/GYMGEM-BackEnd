from django.db import models
import uuid
from utiles.models import Status

# Create your models here.
class Gym(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	profile_picture = models.CharField(max_length=255, null=True, blank=True)
	name = models.CharField(max_length=100)
	description = models.CharField(max_length=255, null=True, blank=True)
	status = models.ForeignKey(Status, null=True, blank=True, on_delete=models.SET_NULL)

	class Meta:
		db_table = 'gyms'

	def __str__(self) -> str:
		return self.name


class GymBranch(models.Model):
	id = models.AutoField(primary_key=True)
	gym = models.ForeignKey(Gym, on_delete=models.CASCADE, db_column='gym_id')
	country = models.CharField(max_length=50, null=True, blank=True)
	state = models.CharField(max_length=50, null=True, blank=True)
	street = models.CharField(max_length=100, null=True, blank=True)
	zip_code = models.CharField(max_length=20, null=True, blank=True)

	class Meta:
		db_table = 'gym_branches'

	def __str__(self) -> str:
		return f"{self.gym.name} - {self.id}"


class GymSlot(models.Model):
	id = models.AutoField(primary_key=True)
	gym = models.ForeignKey(Gym, on_delete=models.CASCADE, db_column='gym_id')
	branch = models.ForeignKey(GymBranch, on_delete=models.CASCADE, db_column='branch_id')
	GENDER_M = 'm'
	GENDER_F = 'f'
	GENDER_MIX = 'mix'
	GENDER_CHOICES = [
		(GENDER_M, 'Male'),
		(GENDER_F, 'Female'),
		(GENDER_MIX, 'Mixed'),
	]
	gender = models.CharField(max_length=3, choices=GENDER_CHOICES)
	opening_time = models.TimeField(null=True, blank=True)
	closing_time = models.TimeField(null=True, blank=True)

	class Meta:
		db_table = 'gym_slots'

	def __str__(self) -> str:
		return f"{self.gym.name} slot ({self.branch.id})"

class Service(models.Model):
    id = models.SmallAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, null=True, blank=True)
    fees = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'services'

    def __str__(self) -> str:
        return self.name


class Package(models.Model):
    id = models.SmallAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, null=True, blank=True)
    discount = models.SmallIntegerField(default=0)
    # Duration/INTERVAL -> use DurationField (maps to Postgres INTERVAL)
    duration = models.DurationField()

    class Meta:
        db_table = 'packages'

    def __str__(self) -> str:
        return self.name


class GymService(models.Model):
    # composite primary key in SQL represented here as unique_together
    gym = models.ForeignKey('gyms.Gym', on_delete=models.CASCADE, db_column='gym_id')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, db_column='service_id')
    branch = models.ForeignKey('gyms.GymBranch', on_delete=models.CASCADE, db_column='branch_id')

    class Meta:
        db_table = 'gym_services'
        unique_together = (('gym', 'service', 'branch'),)

    def __str__(self) -> str:
        return f"{self.gym} - {self.service} - branch {self.branch.id}"

# Create your models here.
