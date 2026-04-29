from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0015_feedback'),
    ]

    operations = [
        migrations.AddField(
            model_name='feedback',
            name='admin_response',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='feedback',
            name='responded_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
