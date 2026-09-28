from datetime import timedelta
from django.conf import settings
from django.db import models
from django.db.models import F, Sum

class Muscle(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Exercise(models.Model):
    CATEGORY_CHOICES = [
        ('push', 'Push'),
        ('pull', 'Pull'),
        ('run', 'Run'),
        ('core', 'Core'),
        ('skill', 'Skill'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=20)
    target_muscles = models.ManyToManyField(
        Muscle,
        blank=True,
        related_name='exercises'
    )

    def __str__(self):
        return self.name

class Workout(models.Model):
    WORKOUT_TYPE_CHOICES = [
        ('volume', 'Volume Training'),
        ('strength', 'Strength Training'),
        ('explosive', 'Explosive Power'),
        ('record', 'Record Training'),
        ('recovery', 'Recovery Training'),
        ('endurance', 'Endurance Training'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='workouts'
    )
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)
    type = models.CharField(choices=WORKOUT_TYPE_CHOICES, max_length=20)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user} - {self.type} ({self.started_at})"

    @property
    def total_duration(self):
        if self.finished_at and self.started_at:
            return self.finished_at - self.started_at
        return None

    @property
    def total_volume(self):
        result = self.sets.aggregate(
            total=Sum(F('reps') * F('weight'))
        )['total']
        return result or 0

class WorkoutSet(models.Model):
    workout = models.ForeignKey(
        Workout,
        on_delete=models.CASCADE,
        related_name='sets'
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name='workout_sets'
    )
    reps = models.PositiveIntegerField(null=True, blank=True)
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Lbs"
    )

    duration = models.DurationField(
        null=True,
        blank=True,
        help_text="Exercise duration (e.g., 00:01:30)"
    )

    rest_time = models.DurationField(
        default=timedelta(seconds=60),
        help_text="Rest time after a set (e.g., 00:01:30 or 90 seconds)"
    )

    def __str__(self):
        return f"{self.exercise.name} - {self.reps or 0} reps / {self.weight or 0} lbs"