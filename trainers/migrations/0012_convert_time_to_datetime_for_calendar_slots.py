# Generated manually to convert TimeField to DateTimeField for calendar slots
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainers", "0011_alter_trainercalendarslot_slot_end_time_and_more"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE trainers_trainercalendarslot "
                        "ALTER COLUMN slot_start_time TYPE timestamp with time zone "
                        "USING (CURRENT_DATE::timestamp + slot_start_time);"
                    ),
                    reverse_sql=(
                        "ALTER TABLE trainers_trainercalendarslot "
                        "ALTER COLUMN slot_start_time TYPE time without time zone "
                        "USING (slot_start_time::time);"
                    ),
                ),
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE trainers_trainercalendarslot "
                        "ALTER COLUMN slot_end_time TYPE timestamp with time zone "
                        "USING (CASE WHEN slot_end_time IS NULL THEN NULL ELSE CURRENT_DATE::timestamp + slot_end_time END);"
                    ),
                    reverse_sql=(
                        "ALTER TABLE trainers_trainercalendarslot "
                        "ALTER COLUMN slot_end_time TYPE time without time zone "
                        "USING (CASE WHEN slot_end_time IS NULL THEN NULL ELSE slot_end_time::time END);"
                    ),
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="trainercalendarslot",
                    name="slot_start_time",
                    field=models.DateTimeField(),
                ),
                migrations.AlterField(
                    model_name="trainercalendarslot",
                    name="slot_end_time",
                    field=models.DateTimeField(null=True, blank=True),
                ),
            ],
        )
    ]
