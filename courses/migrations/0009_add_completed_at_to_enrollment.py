from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0008_remove_enrollment_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='enrollment',
            name='completed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
