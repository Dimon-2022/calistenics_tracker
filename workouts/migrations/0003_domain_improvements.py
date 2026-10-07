import datetime
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workouts', '0002_exercise_user'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='exercise',
            options={'ordering': ['name']},
        ),
        migrations.AlterModelOptions(
            name='muscle',
            options={'ordering': ['name']},
        ),
        migrations.AlterModelOptions(
            name='workout',
            options={'ordering': ['-started_at']},
        ),
        migrations.AlterModelOptions(
            name='workoutset',
            options={'ordering': ['workout', 'id']},
        ),
        migrations.AddField(
            model_name='exercise',
            name='metric_type',
            field=models.CharField(choices=[('reps', 'Repetitions'), ('time', 'Hold time'), ('weighted', 'Added weight')], default='reps', max_length=20),
        ),
        migrations.AddField(
            model_name='workoutset',
            name='notes',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='workoutset',
            name='rpe',
            field=models.PositiveSmallIntegerField(blank=True, help_text='Rate of perceived exertion, 1–10', null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)], verbose_name='RPE'),
        ),
        migrations.AddField(
            model_name='workoutset',
            name='set_number',
            field=models.PositiveSmallIntegerField(blank=True, help_text='Order of the set for this exercise within the workout (filled automatically if empty)', null=True),
        ),
        migrations.AlterField(
            model_name='exercise',
            name='category',
            field=models.CharField(choices=[('push', 'Push'), ('pull', 'Pull'), ('legs', 'Legs'), ('core', 'Core'), ('skill', 'Skill')], max_length=20),
        ),
        migrations.AlterField(
            model_name='muscle',
            name='name',
            field=models.CharField(max_length=50, unique=True),
        ),
        migrations.AlterField(
            model_name='workout',
            name='started_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='workoutset',
            name='duration',
            field=models.DurationField(blank=True, help_text='Set duration or hold time (e.g., 00:01:30 or 90)', null=True),
        ),
        migrations.AlterField(
            model_name='workoutset',
            name='exercise',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='workout_sets', to='workouts.exercise'),
        ),
        migrations.AlterField(
            model_name='workoutset',
            name='rest_time',
            field=models.DurationField(default=datetime.timedelta(seconds=60), help_text='Rest time after the set (e.g., 00:01:30 or 90)'),
        ),
        migrations.AlterField(
            model_name='workoutset',
            name='weight',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Added weight in kg (negative for band / assisted)', max_digits=5, null=True, validators=[django.core.validators.MinValueValidator(-200), django.core.validators.MaxValueValidator(500)]),
        ),
        migrations.AddConstraint(
            model_name='exercise',
            constraint=models.UniqueConstraint(fields=('user', 'name'), name='unique_exercise_name_per_user'),
        ),
    ]
