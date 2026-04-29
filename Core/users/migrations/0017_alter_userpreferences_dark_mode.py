from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0016_feedback_admin_response_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userpreferences',
            name='dark_mode',
            field=models.BooleanField(default=False),
        ),
    ]
