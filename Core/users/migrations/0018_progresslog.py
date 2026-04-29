from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0017_alter_userpreferences_dark_mode'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProgressLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('calories_burned', models.PositiveIntegerField(default=0)),
                ('workout_done', models.BooleanField(default=False)),
                ('steps', models.PositiveIntegerField(default=0)),
                ('water_intake', models.PositiveIntegerField(default=0, help_text='Water intake in cups')),
                ('user', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='progress_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
        migrations.AddConstraint(
            model_name='progresslog',
            constraint=models.UniqueConstraint(fields=('user', 'date'), name='unique_progress_log_per_user_per_day'),
        ),
    ]
