# Generated manually for utils app

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("profiles", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Specialization",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("description", models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Certification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("issuing_organization", models.CharField(max_length=100)),
                ("issue_date", models.DateField()),
                ("expiration_date", models.DateField(blank=True, null=True)),
                ("url", models.URLField(blank=True, null=True)),
                ("description", models.CharField(blank=True, max_length=255, null=True)),
                ("profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="profiles.profile")),
            ],
        ),
    ]
