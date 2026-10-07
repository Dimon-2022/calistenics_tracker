from datetime import timedelta

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Max, Q
from django.utils import timezone


class Muscle(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ExerciseQuerySet(models.QuerySet):
    def available_for(self, user):
        """Global catalog exercises plus the user's own custom ones."""
        return self.filter(Q(user__isnull=True) | Q(user=user))


class Exercise(models.Model):
    CATEGORY_CHOICES = [
        ('push', 'Push'),
        ('pull', 'Pull'),
        ('legs', 'Legs'),
        ('core', 'Core'),
        ('skill', 'Skill'),
    ]

    # How a set of this exercise is measured — drives progress calculation.
    METRIC_REPS = 'reps'
    METRIC_TIME = 'time'
    METRIC_WEIGHTED = 'weighted'
    METRIC_CHOICES = [
        (METRIC_REPS, 'Repetitions'),
        (METRIC_TIME, 'Hold time'),
        (METRIC_WEIGHTED, 'Added weight'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='custom_exercises'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=20)
    metric_type = models.CharField(choices=METRIC_CHOICES, max_length=20, default=METRIC_REPS)
    target_muscles = models.ManyToManyField(
        Muscle,
        blank=True,
        related_name='exercises'
    )

    objects = ExerciseQuerySet.as_manager()

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['user', 'name'], name='unique_exercise_name_per_user'),
        ]

    def __str__(self):
        return self.name

    @property
    def is_custom(self):
        return self.user_id is not None


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
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    type = models.CharField(choices=WORKOUT_TYPE_CHOICES, max_length=20)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.get_type_display()} — {timezone.localtime(self.started_at):%b %d, %Y %H:%M}"

    @property
    def total_duration(self):
        if self.finished_at and self.started_at:
            return self.finished_at - self.started_at
        return None


class WorkoutSet(models.Model):
    workout = models.ForeignKey(
        Workout,
        on_delete=models.CASCADE,
        related_name='sets'
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.PROTECT,
        related_name='workout_sets'
    )
    set_number = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Order of the set for this exercise within the workout (filled automatically if empty)"
    )
    reps = models.PositiveIntegerField(null=True, blank=True)
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(-200), MaxValueValidator(500)],
        help_text="Added weight in kg (negative for band / assisted)"
    )
    duration = models.DurationField(
        null=True,
        blank=True,
        help_text="Set duration or hold time (e.g., 00:01:30 or 90)"
    )
    rest_time = models.DurationField(
        default=timedelta(seconds=60),
        help_text="Rest time after the set (e.g., 00:01:30 or 90)"
    )
    rpe = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name="RPE",
        help_text="Rate of perceived exertion, 1–10"
    )
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['workout', 'id']

    def __str__(self):
        return f"{self.exercise.name} #{self.set_number} — {self.reps or 0} reps"

    def save(self, *args, **kwargs):
        if not self.set_number:
            last = WorkoutSet.objects.filter(
                workout_id=self.workout_id, exercise_id=self.exercise_id
            ).aggregate(m=Max('set_number'))['m']
            self.set_number = (last or 0) + 1
        super().save(*args, **kwargs)

    @property
    def performance(self):
        """Single comparable number for this set according to the exercise metric."""
        metric = self.exercise.metric_type
        if metric == Exercise.METRIC_TIME:
            return self.duration.total_seconds() if self.duration else None
        if metric == Exercise.METRIC_WEIGHTED:
            return float(self.weight) if self.weight is not None else None
        return self.reps
