from django.forms import models


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

class Workout(models.Model):
    # user = current user
    # started_at = 28.09.2026 17:00
    # finished_at = 28.09.2026 17:00
    # type = volume training, strength, explosive power, record, recovery training, endurance
    # notes = ...

class WorkoutSet(models.Model):
    # workout = workout instance
    # exercise =
    # reps =
    # weight =
    # duration =
    # rest_time =